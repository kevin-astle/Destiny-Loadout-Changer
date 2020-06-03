# This is just to appease IDE code analyzers by defining application explicitly
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


@application.bot.command(name='equip')
async def equip(ctx):
    words = ctx.content.split()[1:]  # Drop first word (!equip)
