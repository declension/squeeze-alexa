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

About this guide
----------------
 * This is still a work in progress but getting better all the time.
 * If you've followed this guide and are getting stuck, see [TROUBLESHOOTING](TROUBLESHOOTING.md).
 * If you want to add some helpful detail to make it easier for others, that's great - please raise an issue first!

Networking Overview
-------------------
![Networking diagram](squeeze-alexa-networking.png)

Note how the _arbitrary_ ports are not labelled - see [setting up ports](#Configure ports).

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
 * Generally the connections go `lambda -> router:extport -> server:sslport -> lms:9090` (see diagram above). Most people will have `lms` and `server` on the same host (Synology / ReadyNAS / whatever).
 * Choose some values for `extport` and `sslport` e.g. `19090`. For sanity, it's probably easiest to use the same port externally as internally, i.e. `extport == sslport`
 * On your router, forward `extport` to the stunnel / haproxy port (`sslport`) on that server.

### Set up DDNS
 * This is recommended if you don't have fixed IP, so that there's a consistent address to reach your home...
 * Try www.dyndns.org or www.noip.com, or better still your NAS drive or router might be pre-configured with its own (Synology has their own dynamic DNS setup, for example).
 * Note down this _external_ (Internet) address (e.g. `bob-the-builder.noip.com`). We'll call it `MY_HOSTNAME` later.

### Optional: use your own domain
 * If you have your own domain name (e.g. `house.example.com`) available, I strongly suggest using the DDNS to forward to this (with `CNAME`) especially if on dynamic IP. Why? Because DNS takes too long to refresh, but DDNS is near immediate.
 * This will also allow you to create better-looking certificates against a meaningful _subject_ (domain name). It's then _this_ that will be your `MY_HOSTNAME` later.

### Create certificate(s)
You can skip this step if you already have one, of course, so long as it's the same address used for `MY_HOSTNAME` above.
This should be working on your _local_ network as well, i.e. make sure your server knows that it's the address at `MY_HOSTNAME`.

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
You'll need something to edit your `stunnel.conf` (e.g. `vim` or `nano`) and add this at the end, referring to the cert path you just used above:

    [slim]
    accept =  MY-PORT
    connect = MY-HOSTNAME:9090

    verify = 3
    CAfile = /opt/etc/stunnel/squeeze-alexa.pem
    cert = /opt/etc/stunnel/squeeze-alexa.pem

As before `MY-PORT` and `MY-HOSTNAME` should be substituted with your own values.Note that here `MY-HOSTNAME` here is referring to the LMS address as seen from the proxy, i.e. internally. This could usually just be blank (==`localhost`), but I like to be _sure_ we're using the DNS setup and that routing works internally, so...

#### Check routing

From your server, check this works (substitute `MY-SERVER` as before)
```bash
$ ping -c 4 localhost
$ ping -c 4 MY-SERVER
```
If the latter fails, try using `localhost`, but it's better to set up your DNS to work internally, e.g. add this to your `/etc/hosts`:

    127.0.0.1   localhost MY-SERVER

Test your connectivity
----------------------

### Test the tunnel fully
You can now use `local_test.py`[bin/local_test.py] to try out your connection. From the directory you checked out / unzipped the `squeeze-alexa` source:

    bin/local_test.py

This assumes you have `python2`. You can run this more explicitly (e.g. on Windows):

    python bin/local_test.py

If you get some stuff about what's playing and next, we're good to go!

**Update**: `local_test.py` can now diagnose _some_ common connection problems :smile:



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
 * Needs to be Python (2.7) runtime. **UPDATE:** Python 3.6 is now supported too, though untested.
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
 * Optional: Add a new slot type for `Player`, and make sure to copy [players.txt](metadata/slots/players.txt) in there, adding your player names if it helps.
 * Optional: Add a new slot type for `Genre`, and make sure to copy [genres.txt](metadata/slots/genres.txt) in there, extending if really necessary (there are all the standards, and quite a few more already)
 * Optional: Add a new slot type for `Playlist`, and make sure to copy [playlists.txt](metadata/slots/players.txt) in there, adding your own for better results (avoiding short words helps, I find)

### Install your Skill on your Echo
 * Make sure you've enabled the testing checkbox for this skill in the developer portal
 * In the [Alexa app](http://alexa.amazon.com), you should see your Squeeze Alexa skill listed under _Skills_ -> _My Skills_



Have fun with squeeze-alexa
---------------------------

Try some of the examples in [the README](README.html)!
If you have something not supported, [raise an issue](https://github.com/declension/squeeze-alexa/issues/new).

