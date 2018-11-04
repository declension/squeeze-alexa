squeeze-alexa with MQTT
=======================

MQTT is a lightweight pub/sub messaging protocol with similarities to AMQ, used a lot in IoT situations.
Amazon AWS now has good (and mostly free) support for this via [AWS IoT](https://aws.amazon.com/iot/).

With MQTT transport, we'll be using this to act as the interface between your Alexa skill and your LMS server CLI.

squeeze-alexa needs a tunnel (conceptually similar to stunnel or HAProxy for SSL) to relay traffic.
For this you can use [mqtt-squeeze](../mqtt_squeeze.py).


Set up mqtt-squeeze
-------------------
 * This needs to run on a server (typically the same as your LMS one).
 * Needs Python 3.6 (or 3.5 maybe), just like the skill (in fact it shares some code). 
 * Admin access to your server (e.g. via SSH).

### Set up new Python 3
Many new linux install will have Python 3.6 or at least 3.5.
For those that don't, it's a bit harder
:information_source: RPI users can install [Berryconda](https://github.com/jjhelmus/berryconda) (choose `Berryconda3`) to get Python 3.6 easily ([other ways here too](https://raspberrypi.stackexchange.com/questions/59381/how-do-i-update-my-rpi3-to-python-3-6)).
You can read general docs on [Python on Raspbian](https://www.raspberrypi.org/documentation/linux/software/python.md).

### Copy the files
 * You'll need the
   * the script, `mqtt_squeeze.py`
   * the `etc/` directory with your certificates (see below)
   * the [`squeezealexa` directory](../squeezealexa)

:new: Use the scripting to do this bit for you:
```bash
bin/deploy.py mqtt
```
This creates an `mqtt-squeeze.tgz` file for you to copy to your server.

Create a new directory somewhere on your server and copy this there.
Maybe `/opt`, or `/usr/local/bin` on standard linux. 
For Synology, I've chosen `/volume1/mqtt-squeeze`
Make sure `mqtt_squeeze.py` is executable (`chmod +x mqtt_squeeze.py`).
Then just `tar -xf mqtt-squeeze.tgz`.

### Create a service
 * To start and stop this, it's best to use your OS's service manager.
On Linux, this might be SysV (traditional), [Upstart](https://en.wikipedia.org/wiki/Upstart), or [systemd](https://en.wikipedia.org/wiki/Systemd) (most modern Linux).

#### Using Upstart on Synology
##### Installing
For convenience find [an Upstart script suitable for Synology](example-config/upstart/mqtt-squeeze.conf),
which you can copy (or better: symlink) to `/etc/init/mqtt-squeeze.conf`:

```bash
cd mqtt-squeeze/etc/conf
ln -s mqtt-squeeze.conf /etc/init/mqtt-squeeze.conf
```

:warning: This file will be overwritten when Synology DSM is upgraded. 

##### Using Upstart
You can then reload the daemon: `sudo initctl reload-configuration` to pick up these config changes.

You can then start it with:
`sudo start mqtt-squeeze`

And the status with:
`sudo initctl status mqtt-squeeze`

#### Using systemd
:information_source: For Raspberry PI intro, see [systemd on Raspbian](https://www.raspberrypi.org/documentation/linux/usage/systemd.md).

For convenience find [a systemd script](example-config/systemd/mqtt-squeeze.service),
which you should edit and copy to `/etc/systemd/system/mqtt-squeeze.service`.

To start the new `mqtt-squeeze` service
```bash
sudo systemctl start mqtt-squeeze.service
```

To look at logs:
```bash
sudo journalctl -u mqtt-squeeze.service 
```

#### ...or manually
You can just do it oldschool and run `nohup mqtt_squeeze.py &`,
but you'll have to do this every time your server starts,
and it doesn't take care of connections dying like Upstart etc.



Set up MQTT with Amazon IOT
---------------------------

### Create a new certificate

This convenient AWS CLI command will create the certs in the right place (assuming you're in the project root, e.g. `~/workspace/squeeze-alexa/`).
You'll need to be logged in first, as with all the other aws commands.
Use `--profile` if you've got lots of accounts.

```bash
aws iot create-keys-and-certificate --set-as-active --certificate-pem-outfile etc/certs/iot-certificate.pem.crt --private-key-outfile etc/certs/iot-private.pem.key
```


### Set up permissions for MQTT

Go to the [AWS IoT section](https://console.aws.amazon.com/iot/) (make sure to select the right region), and you start the setup.

Once you've created a certificate as above (which is used to authenticate, i.e. prove `mqtt-squeeze`'s _identity_ to AWS),
you need to make sure it has _authorisation_ to do things we want to do. 

 
So here you'll need 
 * an IAM policy to grant the right MQTT access to this cert (i.e. for `mqtt-squeeze`)
 * an IAM policy to grant the right MQTT access to the squeeze-alexa Lambda (I _think_, some stuff is default now. If you get errors in the lambda logs, you'll know... :thinking:)

**Luckily** these can actually be the _same_ policy JSON (it's two-way communication), and even better, here's one I made earlier: 
[example mqtt-squeeze IAM policy](example-config/iot-iam-policy.json).
Remember to make sure these match your own MQTT settings though if you're not using defaults.

:beta: You can even use `aws iot attach-policy` on the command line if you prefer not using the AWS IOT GUI.

Test
----

You can use `local_test.py` to test once your settings are configured.
You can also debug using [AWS IoT test console](https://console.aws.amazon.com/iot/home#/test).


Troubleshooting
---------------

TODO: Add troubleshooting
