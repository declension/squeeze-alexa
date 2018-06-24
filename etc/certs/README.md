`certs` directory
=================

Keep certs for in this directory (by default at least).

`squeeze-alexa.pem`
-------------------

The combined cert & private key in PEM format, for SSL transport,
named `squeeze-alexa.pem` unless you've changed `settings.CERT_FILE`.


MQTT Certs
----------

If you're using MQTT transport instead, you'll need different ones:

 * A PEM-format certificate named like `SOMETHING-certificate.pem.crt`
 * A PEM-format private key for this named like `SOMETHING-private.pem.key`

This directory is also configurable with `settings.MQTT_CERT_DIR`.
