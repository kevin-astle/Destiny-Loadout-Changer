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
    await rate_limited_send(ctx, '!equip <weapon name>: Equip a specific weapon. Use full or '
                                 'partial names (ex: "!equip recluse")')
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
        # Tell the viewers what it understood from the comomand
        msg = 'Now equipping a random weapon'
        if weapon_type is not None:
            msg += ' of type {}'.format(weapon_type)
        if weapon_sub_type is not None:
            msg += ' of subtype {}'.format(WeaponSubType.get_string_representation(weapon_sub_type))
        await rate_limited_send(ctx, msg)

        # Choose a random weapon, given the provided constraints
        chosen_weapon, num_options = application.profile.active_character.select_random_weapon(
            weapon_type=weapon_type,
            weapon_sub_type=weapon_sub_type)

        # Tell the viewers what it selected
        await rate_limited_send(ctx, 'Selected {} from {} possibilities. Now equipping...'.format(
            chosen_weapon.name, num_options))

        # Attempt to equip
        application.profile.active_character.equip_weapon(chosen_weapon)

        # Tell users equipping was successful
        await rate_limited_send(ctx, 'Successfully equipped {}'.format(chosen_weapon.name))
    # If a custom error was returned, show the error message
    except Error as e:
        await rate_limited_send(ctx, 'An error occurred: {}'.format(e))
    # If a totally unexpected error occurred, show detailed debug info
    except Exception as e:
        await rate_limited_send(ctx, 'An unexpected error occurred. Detailed debug information: '
                                     '{}'.format(traceback.format_exc()))


@application.bot.command(name='equip')
async def equip(ctx):
    """
    Equip a weapon by name. If one or more exact matches is found, choose one of those. If not, then
    look for partial matches and choose one of those. The matching is not case-sensitive
    """
    requested_weapon = ctx.content[6:].strip()  # Drop first word (!equip)

    if requested_weapon == '':
        await rate_limited_send(ctx, 'No weapon specified. Try something like "!equip revoker" or '
                                     '"!equip mida"')

    try:
        # Tell viewers that request was acknowledged
        await rate_limited_send(ctx, 'Attempting to equip "{}"'.format(requested_weapon))

        # Select a weapon
        chosen_weapon, num_options = application.profile.active_character.select_specific_weapon(
            requested_weapon)

        # If multiple options, tell the viewers how many options were found and which was chosen
        if num_options > 1:
            await rate_limited_send(ctx, '{} options found matching "{}". Selected {}. Now '
                                         'equipping...'.format(num_options,
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
    # If a custom error was returned, show the error message
    except Error as e:
        await rate_limited_send(ctx, 'An error occurred: {}'.format(e))
    # If a totally unexpected error occurred, show detailed debug info
    except Exception as e:
        await rate_limited_send(ctx, 'An unexpected error occurred. Debug information: '
                                     '{}'.format(e))
