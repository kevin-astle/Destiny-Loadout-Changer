import time
import traceback

from src.enums import WeaponType, WeaponSubType
from src.exceptions import Error

# This is just to appease IDE code analyzers by defining application explicitly in this module
if False:
    application = None

# Global variable to track how long ago a chat message was sent. Needed to rate-limit chat messages
last_message_send_time = 0


def is_name_command(command):
    """
    Checks if the command looks like a request to equip or search a weapon by name, or based on
    criteria (type or subtype). If any words in the command can't be interpreted as either type or
    subtype, it will be treated as a request to equip or search by name
    """
    words = command.split()[1:]  # Drop first word and separate into component words

    # If any word looks like neither type nor subtype, return True
    for word in words:
        if WeaponType.get_enum_from_string(word) == WeaponType.UNKNOWN and \
                WeaponSubType.get_enum_from_string(word) == WeaponSubType.UNKNOWN:
            return True
    return False


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


@application.bot.command(name='equip')
async def equip(ctx):
    """
    Equip a weapon. If a name is specified, like "jade rabbit", weapons will be searched by name and
    a matching weapon will be equipped. If more than one weapon matches, then one of the options
    will be randomly chosen and equipped. If weapon type and/or subtype are specified instead of a
    name, then a random weapon matching the given criteria will be randomly chosen and equipped. If
    no parameters are given, then a random weapon of a random type will be chosen and equipped
    """
    if is_name_command(ctx.content):
        requested_weapon = ctx.content[6:].strip()  # Drop first word (!equip)
        await named_weapon_action(ctx, requested_weapon, equip=True)
    else:
        await random_weapon_action(ctx, equip=True)


@application.bot.command(name='search')
async def search(ctx):
    """
    Search for a weapon. If a name is specified, like "jade rabbit", weapons will be searched by
    name and any matching weapons will be displayed. If weapon type and/or subtype are specified
    instead of a name, then all weapons matching the given criteria will be displayed. If no
    parameters are given, then all weapons will be displayed. Note that exotics will be excluded in
    certain cases, such as when no weapon type is specified
    """
    if is_name_command(ctx.content):
        requested_weapon = ctx.content[7:].strip()  # Drop first word (!search)
        await named_weapon_action(ctx, requested_weapon, equip=False)
    else:
        await random_weapon_action(ctx, equip=False)


def get_weapons_string(weapons, criteria):
    """
    Generate a string showing all weapons which match the given criteria. If multiple weapons of the
    same name are present in the list, then the quantity will be shown next to the name. If the
    resulting string exceeds 500 characters in length, it will be truncated
    """
    counted_weapons = {}
    for weapon in weapons:
        if weapon.name not in counted_weapons:
            counted_weapons[weapon.name] = 1
        else:
            counted_weapons[weapon.name] += 1

    weapon_names = []
    for weapon_name, count in counted_weapons.items():
        if count > 1:
            weapon_names.append('{} x{}'.format(weapon_name, count))
        else:
            weapon_names.append(weapon_name)

    weapon_names.sort()

    weapons_str = criteria + \
        ' ({} match{}): '.format(len(weapon_names), 'es' if len(weapon_names) > 1 else '') + \
        ', '.join(weapon_names)

    # Truncate if necessary
    if len(weapons_str) > 500:
        weapons_str = weapons_str[:497] + '...'

    return weapons_str


async def random_weapon_action(ctx, equip):
    """
    Equip or search for a random weapon, with optional constraints. For valid weapon type
    constraints, see WeaponType.get_enum_from_string. For valid weapon subtype constraints, see
    WeaponSubType.get_enum_from_string. If equip is true, select from the available options and
    equip the chosen weapon. Otherwise, display the matching options to the viewers
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
        if weapon_type is None and weapon_sub_type is None:
            msg += ' of any type'
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
        await rate_limited_send(ctx, 'An unexpected error occurred. Detailed debug information: '
                                     '{}'.format(traceback.format_exc()))
