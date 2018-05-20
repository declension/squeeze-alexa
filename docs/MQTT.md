squeeze-alexa with MQTT
=======================

MQTT is a lightweight pub/sub messaging protocol with similarities to AMQ, used a lot in IoT situations.

Amazon AWS now has good (and mostly free) support for this via [AWS IoT](https://aws.amazon.com/iot/).


Create a new certificate
------------------------

This convenient AWS CLI command will create the certs in the right place (assuming you're in the project root, e.g. `~/workspace/squeeze-alexa/`).
You'll need to be logged in first, as with all the other aws commands. Use `--profile` if you've got lots of accounts.

```bash
aws iot create-keys-and-certificate --set-as-active --certificate-pem-outfile etc/iot-certificate.pem.crt --private-key-outfile etc/iot-private.pem.key
```


Set up permissions for MQTT
---------------------------

Go to the [AWS IoT section](https://console.aws.amazon.com/iot/) (make sure to select the right region), and you start the setup.

You'll need an IAM policy to grant MQTT access to the squeeze-alexa Lambda.

Use the helpful [included IAM policy](example-config/iot-iam-policy.json) to permission topics - remember to make sure these match your MQTT settings.


Test
----

You can use `local_test.py` to test once your settings are configured.
You can also debug using [AWS IoT test console](https://console.aws.amazon.com/iot/home#/test).

### TODO: Troubleshooting
