Set up your own squeeze-alexa
=============================


Prerequisites
-------------
 * A running LMS instance on a Linux-ish server or NAS (and some squeezebox players)
 * An Amazon Echo / Echo Dot
 * An Amazon developer account, and an Alexa one (tip: use the same email, or you'll wish you had)
 * A router that supports port forwarding, and ideally DDNS of some sort (nearly all modern routers do).
 * Some time and a little knowledge of: Linux, networking, AWS / Lambda, SSL
 * _Optional_: a domain name, and a "real" (not self-signed) SSL certificate to match.

Networking Overview
-------------------
![Networking diagram](https://raw.githubusercontent.com/declension/squeeze-alexa/master/metadata/squeeze-alexa-networking.svg)


Tunnel the CLI
--------------
### Background
When you open up your LMS to the world, well, you _don't really_ want do that, but for Alexa to work this generally<sup>*</sup> needs to happen.
See [connecting remotely](http://wiki.slimdevices.com/index.php/Connecting_remotely) on the wiki, but it's more around Web than CLI (which is how `squeeze-alexa` works).

You _could_ use the username / password auth LMS CLI provides, but for these problems:

 * It's in plain text, so everyone can see, log. This is pretty bad.
 * These aren't rotated, nor do they include a token (à la CSRF) or nonce - so replay attacks are easy too.
 * There is no rate limiting or banning in LMS, so brute-forcing is easy (though it does hang up IIRC).

By mandating client-side TLS (aka SSL) with a private cert, `squeeze-alexa` avoids most of these problems.

<sup>* Though people with fixed servers (i.e. not just using Lambdas) are beginning to try outwards-only tunnels or persistent websocket connections which could show promise here</sup>

### TLS Implementations
I chose to go with [stunnel](http://stunnel.org/), but some exploration shows that other options could work here (**feedback wanted!**)

 * [HAProxy](https://www.haproxy.com) _does_ support TLS-wrapping of generic TCP.
 * Also, there's [ssl_wrapper](https://github.com/cesanta/ssl_wrapper)
 * NB: Nginx _doesn't_ seem to support non-HTTP traffic over TLS.


### Install `stunnel`
#### On Synology
If you haven't got `ipkg`, you might want that. Makes installing stuff a _lot_ easier.
This [blog post](https://zarino.co.uk/post/ds214se-under-the-hood/) details that process

Then, it's just `sudo ipkg install stunnel`.

To make it a system service, you can [create Upstart scripts](https://majikshoe.blogspot.co.uk/2014/12/starting-service-on-synology-dsm-5.html).
Or, here's one you can cut and paste to, say, `/etc/init/stunnel`
```
stunnel

description "Stunnel"

author "Nick B"

start on syno.network.ready
stop on runlevel [06]

respawn
respawn limit 3 10

console log

pre-start script
    date
end script

exec /opt/sbin/stunnel

# vim:ft=upstart
```

Your config will typically live at `/opt/etc/stunnel/stunnel.conf`

#### On Netgear ReadyNAS
I haven't tried, but [this forum posting](https://community.netgear.com/t5/Community-Add-ons/HowTo-Stunnel-on-the-Readynas/td-p/784170) seems helpful.

#### On other servers
Some other NAS drives can use `ipkg`, in which case see above. Else, find a way of installing it (you can build from source if you know how)

### Configure ports
 * Generally the connections go `lambda -> router:extport -> server:sslport -> lms:9090` (see diagram above). Generally, `lms` and `server` will be the same host (Synology / ReadyNAS / whatever).
 * Forward a port on your router to the stunnel / haproxy port (`sslport` above) on your server. For sanity, it's probably easiest to use the same port incoming as outgoing in your firewall rule.

### Set up DDNS
 * This is recommended if you don't have fixed IP, so that there's a consistent address to reach your home...
 * Try www.dyndns.org or www.noip.com, or better still your NAS drive or router might be pre-configured with its own (Synology has their own dynamic DNS setup, for example).
 * Note down this _external_ (Internet) address (e.g. `bob-the-builder.noip.com`). We'll call it `MY_HOSTNAME` later.

### Create certificate(s)
You can skip this step if you already have one, of course, so long as it's the same address used for `MY_HOSTNAME` above.

It's worth reading up on OpenSSL, it's crazily powerful.
If that's a bit TL;DR then here is a fairly secure setup, inspired largely by [this openssl SO post](https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl)

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -keyout key.pem -out cert.pem -subj "/CN=$MY_HOSTNAME" -days 3650
cat cert.pem key.pem > squeeze-alexa.pem && rm -f key.pem
```

_TODO: document optional creation of separate server cert for ~~more complicated~~ better(ish) security._

### Configure stunnel

#### Copy certificate
Copy the `squeeze-alexa.pem` to somewhere stunnel can see it, e.g. `/opt/etc/stunnel/` on Synology.

#### Edit config
You'll need something to edit your `stunnel.conf` and add this at the end:

    [slim]
    accept =  MY-PORT
    connect = MY-HOSTNAME:9090

    verify = 3
    CAfile = /opt/etc/stunnel/squeeze-alexa.pem
    cert = /opt/etc/stunnel/squeeze-alexa.pem
    TIMEOUTclose = 0

As before `MY-PORT` and `MY-HOSTNAME` should be substituted with your own values. Note that here `MY-HOSTNAME` could probably just be blank (i.e. `localhost`), but I like to be sure we're using the DNS.
Make sure you don't leave any other services (IMAPS, HTTPS etc) enabled by mistake.

Test your connectivity
----------------------

### Test the tunnel fully
You can now use `local_test.py`[bin/local_test.py] to try out your connection. From the directory you checked out / unzipped the `squeeze-alexa` source:

    bin/local_test.py

This assumes you have `python2`. You can run this more explicitly (e.g. on Windows):

    python bin/local_test.py

If you get some stuff about what's playing and next, we're good to go! If you get an exception - try to see what the message is.



Set up your Alexa Skill
-----------------------

### Configure `squeeze-alexa`
 * Download this project, either with Git: `git clone git@github.com:declension/squeeze-alexa.git`
  or click _Download Zip_ (under _Clone or download_) in Github.
 * Edit `src/settings.py`, filling in the details as commented there.
 * Make sure your `squeeze-alexa.pem` file is moved to the root of the `squeeze-alexa` directory.

### Add a new ASK Custom Skill in your developer account
 * Like most useful skills it should be a [Custom Skill](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/overviews/understanding-custom-skills)
 * Follow one of the guides ideally e.g. [Deploying a Sample Custom Skill To AWS Lambda](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/deploying-a-sample-skill-to-aws-lambda#creating-the-lambda-function-for-the-sample).
 * Needs to be Python (2.7) runtime
 * Choose your own Invocation Name. The advantage of not needing certification is you can be "more creative" about your naming...
 * Select an AWS region close to you
 * _Recommended_: Select _yes_ for Audio Streaming API
 * The defaults are generally fine (those in [lambda.json](./lambda.json)).

### Upload the customised skill

#### Using lambda-uploader (recommended)
 * You can use [lambda-uploader](https://github.com/rackerlabs/lambda-uploader) to do this - much easier long term.
 * One off: edit `lambda.json` filling in your IAM / ARN details etc (TODO: but with what...)
 * Once installed just type
   `lambda-uploader --no-virtualenv`

#### ...or manually
 * Get and extract the dependencies
      ```bash
      pip --isolated download -r requirements.txt
      unzip fuzzywuzzy-*.whl "fuzzywuzzy/*"
      ```
 * Create a zip of all the Lambda code and config needed:
       ```bash
       zip upload.zip squeezealexa/* fuzzywuzzy/* *.py *.json *.pem
       ```
 * Upload this `upload.zip` in the AWS Lambda interface ([as described here](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function#about-lambda-functions-and-custom-skills))

#### ...or with the AWS CLI
You can now use the [AWS CLI `update-function-code` call](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html) to upload the zip from the manual step.
_TODO: expand on this_

### Update the Interaction Model
 * These are kept here in [`metadata/`](metadata/)
 * In your Amazon Developer portal, configure your new skill:
 * Copy-paste [the utterances](metadata/utterances.txt) as the sample utterances
 * Copy-paste [intents.json](metdata/intents.json) into the Intents schema
 * Optional: Add a new slot type for `Genre`, and make sure to copy [genres.txt](metadata/slots/genres.txt) in there, adding if necessary. It's debateable how much this helps.
 * Optional: Add a new slot type for `Player`, and make sure to copy [genres.txt](metadata/slots/players.txt) in there, adding your player names if necessary.

### Install your Skill on your Echo
 * Make sure you've enabled the testing checkbox for this skill in the developer portal
 * In the [Alexa app](http://alexa.amazon.com), you should see your Squeeze Alexa skill listed under _Skills_ -> _My Skills_



Have fun with squeeze-alexa
---------------------------

Try some of the examples in [the README](README.html)!
If you have something not supported, [raise an issue](https://github.com/declension/squeeze-alexa/issues/new).



Troubleshooting
---------------

### The skill is installed, but erroring when invoked

If everything is installed and the connectivity working, but your Echo is saying "there was a problem with your skill" or similary, try checking the [Cloudwatch logs](https://console.aws.amazon.com/cloudwatch/) (note there's a delay in getting the latest logs).
The squeeze-alexa logs are designed to be quite readable, and should help track down the problem.

If you think it's the speech, try using the test input page on the Amazon dev account portal.

If all else fails, raise an issue here...

### Debugging SSL / certificate problems directly
For `$MY_HOSTNAME` and `$MY_PORT` you can substitute your home IP / domain name (as used above). It also assumes your client cert is called `squeeze-alexa.pem`:

```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem | openssl x509
```
Type <kbd>Ctrl</kbd><kbd>d</kbd> to exit.
If successful, this should give you a PEM-style certificate block with some info about your cert).

For much more detail:
```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem
```
Type `status`, and if a successful end-to-end connection is made you should see some gibberish that looks a bit like:
`...status   player_name%3AUpstairs...player_connected%3A1 player_ip%3A192.168.1...`

#### Resilience / performance testing the SSL connection
For the hardcore amongst you, you can check performance (and that there are no TLS bugs / obvious holes):

```bash
openssl s_time -bugs -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem -verify 4
```
