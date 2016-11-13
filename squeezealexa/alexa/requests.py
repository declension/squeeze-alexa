
class Request(object):
    LAUNCH, INTENT, SESSION_ENDED = ("%sRequest" % s for s in
                                     ("Launch", "Intent", "SessionEnded"))
