squeeze-alexa
=============
[![Build Status](https://travis-ci.org/declension/squeeze-alexa.svg?branch=master)](https://travis-ci.org/declension/squeeze-alexa)

`squeeze-alexa` is an Amazon Alexa Skill integrating with the Logitech Media Server ("squeezebox"). See the original [announcement blog post](http://declension.net/posts/2016-11-30-alexa-meets-squeezebox/), and the [follow-up with videos](http://declension.net/posts/2017-01-03-squeeze-alexa-demos/).

This is very much **in beta**, so feedback (or help with documenting) welcome! Probably best to raise an issue first.

### Aims

 * Intuitive voice control over the (ok, _my_) most common audio scenarios.
 * Low latency (given that it's a cloud service)
 * Decent security (hopefully!)


### Things it is not

 * Full coverage of all LMS features, plugins or use cases. It aims to be good at what it does.
 * A multi-user skill. This means: yes, you will need to set up Alexa and AWS developer accounts.
 * A native LMS plugin (at least, not currently). Yes, more server fiddling.
 * Easy to set up :scream:


Set up your own
---------------

### Prerequisites
 * A running LMS instance on a Linux-ish server or NAS (and some squeezebox players)
 * An Amazon Echo / Echo Dot
 * An Amazon developer account, and an Alexa one (tip: use the same email, or wish you had)
 * A reasonable router (must support port forwarding, and DDNS of some sort)
 * Some time, knowledge of networking, Git, AWS, SSL
 * Some hair to pull out.
 * _Optional_: a domain name, and a "real" (not self-signed) SSL certificate to match.


### Tunnel the CLI
#### Background
When you open up your LMS to the world, well, you _really_ don't want do that, but for Alexa to work this needs to happen.
See [Connecting Remotely](http://wiki.slimdevices.com/index.php/Connecting_remotely) on the wiki, but it's more around Web than CLI (which is how `squeeze-alexa` works).

You _could_ use the username / password auth LMS CLI provides, but for these problems:

 * It's in plain text, so everyone can see, log. This is pretty bad.
 * These aren't rotated, nor do they include a token (à la CSRF) or nonce - so replay attacks are easy too.
 * There is no rate limiting or banning in LMS, so brute-forcing is easy (though it does hang up IIRC).

By mandating client TLS (aka SSL), `squeeze-alexa` avoids most of these problems.

#### TLS Implementations
I chose to go with [stunnel](http://stunnel.org/), but some exploration shows that other options could work here (**feedback wanted!**)
NB: Nginx _doesn't_ seem to support non-HTTP traffic over TLS.

 * [HAProxy](https://www.haproxy.com) _does_ support TLS-wrapping of generic TCP.
 * Also, there's [ssl_wrapper](https://github.com/cesanta/ssl_wrapper)


#### Install `stunnel`
##### On Synology
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


##### On Netgear ReadyNAS
I haven't tried, but [this forum posting](https://community.netgear.com/t5/Community-Add-ons/HowTo-Stunnel-on-the-Readynas/td-p/784170) seems helpful.

##### On other servers
Some other NAS drives can use `ipkg`, in which case see above. Else, find a way of installing it (you can build from source if you know how)

#### Configure ports
 * Forward a port on your router to the stunnel port on your server.

#### Set up DDNS
 * This is recommended if you don't have fixed IP, so that there's a consistent address to reach your home...
 * Try www.dyndns.org or www.noip.com, or better still your NAS drive or router might be pre-configured with its own (Synology has their own dynamic DNS setup, for example).
 * Note down this address (e.g. `bob-the-builder.noip.com`). We'll call it `MY_HOSTNAME` later.

#### Create certificate(s)
You can skip this step if you already have one, of course.

It's worth reading up on OpenSSL, it's crazily powerful.
If that's a bit TL;DR then here is a fairly secure setup, inspired largely by [this openssl SO post](https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl)

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -keyout key.pem -out cert.pem -subj "/CN=$MY_HOSTNAME" -days 3650
cat cert.pem key.pem > squeeze-alexa.pem && rm -f key.pem
```

#### Configure stunnel

You'll need something like this at the end of your `stunnel.conf`:

    [slim]
    accept =  MY-IP
    connect = MY-HOSTNAME:9090

    verify = 3
    CAfile = /opt/etc/stunnel/stunnel.pem
    cert = /opt/etc/stunnel/stunnel.pem
    TIMEOUTclose = 0


### Test your connectivity!

#### Test server cert
For `$MY_HOSTNAME` and `$MY_PORT` you can subsitute your home IP / domain name as used above:

```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT | openssl -x509
```

If successful, this should give you a PEM-style certificate block with some info about your domain name (and maybe a few warnings, erm, let's move on though).

For the hardcore amongst you, you can check performance (and that there are no TLS bugs):

```bash
openssl s_time -bugs -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem -verify 4
```

#### Optional: Test the tunnel fully
TODO

### Set up your Alexa Skill
#### Configure `squeeze-alexa`
 * Download this project, either with Git: `git clone git@github.com:declension/squeeze-alexa.git`
  or click _Download Zip_ (under _Clone or download_) in Github.
 * Edit `src/settings.py`, filling in the details as commented there.
 * Make sure your `squeeze-alexa.pem` file is moved to the root of the `squeeze-alexa` directory.

#### Add a new ASK Custom Skill in your developer account
 * Like most useful skills it should be a [Custom Skill](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/overviews/understanding-custom-skills)
 * Follow one of the guides ideally e.g. [Deploying a Sample Custom Skill To AWS Lambda](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/deploying-a-sample-skill-to-aws-lambda#creating-the-lambda-function-for-the-sample).
 * Needs to be Python (2.7) runtime
 * Choose your own Invocation Name. The advantage of not needing certification is you can be "more creative" about your naming...
 * Select an AWS region close to you
 * _Recommended_: Select _yes_ for Audio Streaming API
 * The defaults are generally fine (those in [lambda.json](./lambda.json)).

#### Upload the customised skill
 * Edit `lambda.json` filling in your IAM / ARN details etc (TODO: but with what...)
 * You can use [lambda-uploader](https://github.com/rackerlabs/lambda-uploader) if you do this lots, then type
   `lambda-uploader --no-virtualenv`

#### Update the Interaction Model
 * These are kept here in [`metadata/`](metadata/)
 * In your Amazon Developer portal, configure your new skill:
 * Copy-paste [the utterances](metadata/utterances.txt) as the sample utterances
 * Copy-paste [intents.json](metdata/intents.json) into the Intents schema
 * TODO: Some other stuff...


### TODO: Install your Skill
### TODO: Add your skill to your Alexa
### TODO: Troubleshooting
### Profit
