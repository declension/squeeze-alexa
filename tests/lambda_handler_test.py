from handler import lambda_handler, _
from tests.alexa.alexa_handlers_test import NO_SESSION


def test_entrypoint_error():
    full_response = lambda_handler(None, {})
    assert 'sessionAttributes' in full_response
    resp = full_response['response']
    assert resp, "Blank response generated"
    assert resp['card']['title'] == _("All went wrong")


def test_entrypoint_ignore_audio():
    request = {'request': {'type': 'AudioPlayer.PlaybackStarted',
                           'requestId': 1234}}
    full_response = lambda_handler(request, {})
    resp = full_response['response']
    assert not resp, "Should have ignored AudioPlayer request"


def test_entrypoint_launch():
    request = {'request': {'type': 'LaunchRequest', 'requestId': 1234},
               'session': NO_SESSION}
    full_response = lambda_handler(request, {})
    resp = full_response['response']
    assert _("Squeezebox is online") in resp['outputSpeech']['text']
