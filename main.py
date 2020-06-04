import builtins
import time

from src.application import Application

application = Application()
builtins.application = application

# NOTE: These must be imported after inserting application into the global namespace, because those
# modules reference the applicationo. This is a little unorthodox, but allows for splitting the code
# up in a more logical way, which should make maintenance easier
#
# Putting these in an if block prevents IDEs from auto-moving them to an earlier location as part of
# code autoformatting
if True:
    import src.bot
    import src.oauth_server

if __name__ == '__main__':
    # Start the web server which will handle oauth redirects
    application.start_flask()

    # Connect the Twitch bot to the channel chat and request, then wait for, oauth approval
    application.start_bot()

    # Bot actions occur asynchronously, so wait here as well for oauth approval
    application.wait_for_oauth_approval()

    while True:
        time.sleep(1)
