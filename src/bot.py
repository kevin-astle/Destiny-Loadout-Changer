# This is just to appease IDE code analyzers by defining application explicitly
from src.enums import WeaponType, WeaponSubType
from src.exceptions import Error
if False:
    application = None


@application.bot.event
async def event_ready():
    await application.bot._ws.send_privmsg(
        application.config['channel'],
        'You should have been directed to the Bungie oauth approval page. If not, use this '
        'link:{}'.format(application.oauth_link))
    application.open_oauth_page()
    application.wait_for_oauth_approval()
    await application.bot._ws.send_privmsg(
        application.config['channel'],
        'Oauth approval received, bot is now ready for use')


@application.bot.command(name='help')
async def test(ctx):
    await ctx.send('Available commands:')
    await ctx.send('!equip primary random: equip a random weapon in the primary weapon slot')
    await ctx.send('!equip energy random: equip a random weapon in the energy weapon slot')
    await ctx.send('!equip heavy random: equip a random weapon in the heavy weapon slot')


@application.bot.command(name='equiprandom')
async def equip_random(ctx):
    words = ctx.content.split()[1:]  # Drop first word (!equiprandom)

    weapon_type = None
    weapon_sub_type = None

    for word in words:
        if WeaponType.get_enum_from_string(word) != WeaponType.UNKNOWN:
            weapon_type = WeaponType.get_enum_from_string(word)
        if WeaponSubType.get_enum_from_string(word) != WeaponSubType.UNKNOWN:
            weapon_sub_type = WeaponSubType.get_enum_from_string(word)

    try:
        msg = 'Now equipping a random weapon'
        if weapon_type is not None:
            msg += ' of type {}'.format(weapon_type)
        if weapon_sub_type is not None:
            msg += ' of subtype {}'.format(WeaponSubType.get_string_representation(weapon_sub_type))
        await ctx.send(msg)
        weapon = application.profile.active_character.equip_random_weapon(
            weapon_type=weapon_type,
            weapon_sub_type=weapon_sub_type)
        await ctx.send('Equipped {}'.format(weapon.name))
    except Error as e:
        await ctx.send('An error occurred: {}'.format(e.msg))
    except Exception as e:
        await ctx.send('An unexpected error occurred. Debug information: {}'.format(e))


@application.bot.command(name='equip')
async def equip(ctx):
    requested_weapon = ctx.content[6:].strip()  # Drop first word (!equip)

    try:
        await ctx.send('Attempting to equip "{}"'.format(requested_weapon))
        weapon = application.profile.active_character.equip_specific_weapon(requested_weapon)
        await ctx.send('Equipped {}'.format(weapon.name))
    except Error as e:
        await ctx.send('An error occurred: {}'.format(e.msg))
    except Exception as e:
        await ctx.send('An unexpected error occurred. Debug information: {}'.format(e))
