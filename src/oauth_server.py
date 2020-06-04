from flask import request

# This is just to appease IDE code analyzers by defining application explicitly in this module
if False:
    application = None


@application.flask_app.route('/oauth', methods=['GET'])
def oauth_redirect():
    """
    Endpoint to accept oauth code from Bungie.
    """
    application.oauth_code = request.args['code']
    with open('auth.data', 'w') as f:
        f.write(application.oauth_code)
    return 'Thank you for authenticating, the Twitch bot can now perform actions on behalf of ' \
           'the authenticated account.'
