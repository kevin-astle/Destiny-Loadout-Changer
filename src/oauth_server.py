from flask import request

# This is just to appease IDE code analyzers by defining application explicitly
if False:
    application = None


@application.flask_app.route('/oauth', methods=['GET'])
def oauth_redirect():
    """
    Endpoint to accept oauth code
    """
    application.oauth_code = request.args['code']
    return 'Thank you for authenticating, the Twitch bot can now perform actions on behalf of ' \
           'the authenticated account.'
