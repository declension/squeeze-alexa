# --------------- Main handler ------------------
from squeezealexa.alexa.requests import Request
from squeezealexa.main import SqueezeAlexa, APPLICATION_ID


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    session = event['session']

    if (APPLICATION_ID and
            session['application']['applicationId'] != APPLICATION_ID):
        raise ValueError("Invalid application (%s)" % session['application'])

    request = event['request']
    sqa = SqueezeAlexa()
    if session['new']:
        sqa.on_session_started(request, session)

    req_type = request['type']
    if req_type == Request.LAUNCH:
        return sqa.on_launch(request, session)
    elif req_type == Request.INTENT:
        return sqa.on_intent(request, session)
    elif req_type == Request.SESSION_ENDED:
        return sqa.on_session_ended(request, session)
    else:
        raise ValueError("Unknown request type %s" % req_type)
