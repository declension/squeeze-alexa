import pytest

from squeezealexa.transport.base import check_listening, Error
from tests.transport.base import TimeoutServer


def test_check_listening():
    with TimeoutServer() as server:
        check_listening("localhost", server.port, timeout=1)

        wrong_port = server.port + 1
        with pytest.raises(Error) as e:
            check_listening("localhost", wrong_port, timeout=1,
                            msg="OHNOES")
        s = str(e)
        assert ("on localhost:%d" % wrong_port) in s
        assert "OHNOES" in s
