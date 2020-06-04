import time
import traceback

from src.enums import WeaponType, WeaponSubType
from src.exceptions import Error

# This is just to appease IDE code analyzers by defining application explicitly in this module
if False:
    application = None

# Global variable to track how long ago a chat message was sent. Needed to rate-limit chat messages
last_message_send_time = 0


async def rate_limited_send(context, message, rate_limit=1.5):
    """
    Send a message in the Twitch chat. There seems to be an issue with the twitchio library where
    sending messages too quickly causes an error, resulting in the message not being sent. This
    function ensures that all messages sent are rate-limited to prevent this from happening.
    """
    global last_message_send_time
    time_since_last_send = time.time() - last_message_send_time
    if time_since_last_send < rate_limit:
        time.sleep(rate_limit - time_since_last_send)
    await context.send(message)
    last_message_send_time = time.time()


@application.bot.event
async def event_ready():
    """
    This event occurs whenever the bot is started (or restarted).
    """
    # This condition is included because it seems like there are times when the bot disconnects and
    # reconnects, meaning this function may be called more than once during a session
    if application.oauth_code is None:
        await application.bot._ws.send_privmsg(
            application.config['channel'],
            'Bot is online. You should have been directed to the Bungie oauth approval page')

        # Prompt for oauth approval and wait until it is provided
        application.open_oauth_page()
        application.wait_for_oauth_approval()

        await application.bot._ws.send_privmsg(
            application.config['channel'],
            'Oauth approval received, bot is now ready for use')


@application.bot.command(name='help')
async def command_help(ctx):
    """
    Respond to the !help command with command help. TODO: Improve this, allow users to do something
    like "!help equip" to get more specific help
    """
    await rate_limited_send(ctx, 'Available commands:')
    await rate_limited_send(ctx, '!equip <weapon name>: Equip a weapon by name. Use full or '
                                 'partial names (ex: "!equip recluse" or "!equip ace")')
    await rate_limited_send(ctx, '!random <slot> <type>: Equip a random weapon with optionally '
                                 'specified slot and type (ex: "!random shotgun" or "!random '
                                 'kinetic pulse")')
    await rate_limited_send(ctx, 'NOTE: Weapons cannot be equipped mid-activity, but they will be '
                                 'sent to the player\'s inventory')


@application.bot.command(name='random')
async def equip_random(ctx):
    """
    Equip a random weapon, with optional constraints. For valid weapon type constraints, see
    WeaponType.get_enum_from_string. For valid weapon subtype constraints, see
    WeaponSubType.get_enum_from_string
    """
    await random_weapon_action(ctx, equip=True)


@application.bot.command(name='search_random')
async def search_random(ctx):
    """
    Search for all weapons matching the given criteria, and display them. Limits to the first 50
    matches if necessary
    """
    await random_weapon_action(ctx, equip=False)


@application.bot.command(name='equip')
async def equip_by_name(ctx):
    """
    Equip a weapon by name. If one or more exact matches is found, choose one of those. If not, then
    look for partial matches and choose one of those. The matching is not case-sensitive
    """
    requested_weapon = ctx.content[6:].strip()  # Drop first word (!equip)
    await named_weapon_action(ctx, requested_weapon, equip=True)


@application.bot.command(name='search')
async def search_by_name(ctx):
    """
    Search for all weapons matching the given name, and display them. Limits to the first 50
    matches if necessary
    """
    requested_weapon = ctx.content[7:].strip()  # Drop first word (!search)
    await named_weapon_action(ctx, requested_weapon, equip=True)


def get_weapons_string(weapons, criteria, limit=50):
    counted_weapons = {}
    for weapon in weapons:
        if weapon.name not in counted_weapons:
            counted_weapons[weapon.name] = 1
        else:
            counted_weapons[weapon.name] += 1

    weapon_names = []
    for weapon, count in counted_weapons.items():
        if count > 1:
            weapon_names.append('{} x{}'.format(weapon.name, count))
        else:
            weapon_names.append(weapon.name)

    weapon_names.sort()

    weapons_string = criteria
    if len(weapon_names) > limit:
        weapons_string += ' (only displaying the first {}/{} matches)'
    return weapons_string + ': ' + ', '.join(weapon_names[:limit])


async def random_weapon_action(ctx, equip):
    """
    Select a random weapon, and either equip it (if equip is True) or display all weapons matching
    the criteria (if equip is False)
    """
    words = ctx.content.split()[1:]  # Drop first word (!random) and separate into component words

    weapon_type = None
    weapon_sub_type = None

    for word in words:
        # Check if the word looks like a constraint on the weapon type (slot)
        if WeaponType.get_enum_from_string(word) != WeaponType.UNKNOWN:
            weapon_type = WeaponType.get_enum_from_string(word)
        # Check if the word looks like a constraint on the weapon subtype (e.g. "pulserifle")
        if WeaponSubType.get_enum_from_string(word) != WeaponSubType.UNKNOWN:
            weapon_sub_type = WeaponSubType.get_enum_from_string(word)

    try:
        # Tell the viewers what it understood from the command
        if equip:
            msg = 'Now equipping a random weapon'
        else:
            msg = 'Searching for weapons'
        if weapon_type is not None:
            msg += ' of type {}'.format(WeaponType.get_string_representation(weapon_type))
        if weapon_sub_type is not None:
            msg += ' of subtype {}'.format(WeaponSubType.get_string_representation(weapon_sub_type))
        await rate_limited_send(ctx, msg)

        # Choose a random weapon, given the provided constraints
        chosen_weapon, options = application.profile.active_character.select_random_weapon(
            weapon_type=weapon_type,
            weapon_sub_type=weapon_sub_type)

        if equip:
            # Tell the viewers what it selected
            await rate_limited_send(ctx, 'Selected {} from {} possibilities. Now equipping...'.format(
                chosen_weapon.name, len(options)))

            # Attempt to equip
            application.profile.active_character.equip_weapon(chosen_weapon)

            # Tell users equipping was successful
            await rate_limited_send(ctx, 'Successfully equipped {}'.format(chosen_weapon.name))
        else:
            # Tell the viewers what was found
            if weapon_type is None and weapon_sub_type is None:
                criteria = 'All weapons'
            else:
                criteria = 'Weapons'
                if weapon_type is not None:
                    criteria += ' of type {}'.format(WeaponType.get_string_representation(
                        weapon_type))
                if weapon_sub_type is not None:
                    criteria += ' of subtype {}'.format(WeaponSubType.get_string_representation(
                        weapon_sub_type))
            await rate_limited_send(ctx, get_weapons_string(options, criteria))
    # If a custom error was returned, show the error message
    except Error as e:
        await rate_limited_send(ctx, 'An error occurred: {}'.format(e))
    # If a totally unexpected error occurred, show detailed debug info
    except Exception as e:
        await rate_limited_send(ctx, 'An unexpected error occurred. Detailed debug information: '
                                     '{}'.format(traceback.format_exc()))


async def named_weapon_action(ctx, requested_weapon, equip):
    """
    Select a weapon by name, and either equip it (if equip is True) or display all weapons matching
    that name (if equip is False)
    """
    if requested_weapon == '':
        await rate_limited_send(ctx, 'No weapon specified. Try something like "!equip revoker" or '
                                     '"!equip mida"')

    try:
        # Tell viewers that request was acknowledged
        if equip:
            await rate_limited_send(ctx, 'Attempting to equip "{}"'.format(requested_weapon))
        else:
            await rate_limited_send(ctx, 'Searching for weapons matching "{}"'.format(requested_weapon))

        # Select a weapon
        chosen_weapon, options = application.profile.active_character.select_weapon_by_name(
            requested_weapon)

        if equip:
            # If multiple options, tell the viewers how many options were found and which was chosen
            if len(options) > 1:
                await rate_limited_send(ctx, '{} options found matching "{}". Selected {}. Now '
                                             'equipping...'.format(len(options),
                                                                   requested_weapon,
                                                                   chosen_weapon.name))
            # If only one match found, tell viewers what it was
            else:
                await rate_limited_send(ctx, 'One match found: {}. Now equipping...'.format(
                    chosen_weapon.name))

            # Attempt to equip
            application.profile.active_character.equip_weapon(chosen_weapon)

            # Tell users equipping was successful
            await rate_limited_send(ctx, 'Successfully equipped {}'.format(chosen_weapon.name))
        else:
            # Tell the viewers what was found
            criteria = 'Weapons with names matching "{}"'.format(requested_weapon)
            await rate_limited_send(ctx, get_weapons_string(options, criteria))
    # If a custom error was returned, show the error message
    except Error as e:
        await rate_limited_send(ctx, 'An error occurred: {}'.format(e))
    # If a totally unexpected error occurred, show detailed debug info
    except Exception as e:
        await rate_limited_send(ctx, 'An unexpected error occurred. Debug information: '
                                     '{}'.format(e))
