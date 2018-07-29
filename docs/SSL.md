SSL tunnel setup
================

This section details how to set up squeeze-alexa using the SSL Tunnel transport option.

Networking Overview
-------------------
![Networking diagram](squeeze-alexa-networking.png)

Note how the _arbitrary_ ports are not labelled - see [setting up ports](#configure-ports).


Set up your networking
----------------------

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
cat cert.pem key.pem > etc/certs/squeeze-alexa.pem && rm -f key.pem cert.pem
```

_TODO: document optional creation of separate server cert for ~~more complicated~~ better(ish) security._

### Check routing

From your server, check this works (substitute `MY-SERVER` as before)
```bash
$ ping -c 4 localhost
$ ping -c 4 MY-SERVER
```
If the latter fails, try using `localhost`, but it's better to set up your DNS to work internally, e.g. add this to your `/etc/hosts`:

    127.0.0.1   localhost MY-SERVER

See [TROUBLESHOOTING](TROUBLESHOOTING.md) for detailed diagnosis of connection problems.



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

<sup>* Or you could [use MQTT](MQTT.md) of course.

### TLS Implementations
I chose to go with [stunnel](http://stunnel.org/) (see details below),
but other options should work here (**feedback wanted!**)

 * [HAProxy](https://www.haproxy.com) _does_ support TLS-wrapping of generic TCP.
 * Also, there's [ssl_wrapper](https://github.com/cesanta/ssl_wrapper)
 * :new: [nginx 1.9+ supports TCP Load Balancing](https://www.nginx.com/blog/tcp-load-balancing-with-nginx-1-9-0-and-nginx-plus-r6/) which can be used with the [nginx SSL module](https://nginx.org/en/docs/stream/ngx_stream_ssl_module.html) to do this.

Make sure you configure a new (safe) TLS, **minimum TLS v1.2**.

### With stunnel
#### On Synology
##### Using Entware and `opkg`
Follow [this excellent Synology forum post](https://forum.synology.com/enu/viewtopic.php?f=40&t=95346) to install Entware if you don't have it.
```bash
opkg install stunnel
```
Your config will live at `/Apps/opt/etc/stunnel/stunnel.conf`.

#### Auto-starting stunnel
There are various ways of getting a script to start up automatically on Synology.

##### Using Upstart
You could "do this properly" and make it a system service, you can [create Upstart scripts](https://majikshoe.blogspot.co.uk/2014/12/starting-service-on-synology-dsm-5.html).

##### Or using Entware
Just drop the script:
```bash
#!/bin/sh

if [ -n "`pidof stunnel`" ] ;then
        killall stunnel 2>/dev/null
fi
/Apps/opt/bin/stunnel
```

to `/Apps/opt/etc/init.d/S20stunnel`. Make sure it's executable:

```bash
chmod +x /Apps/opt/etc/init.d/S20stunnel
```
You should try running it and checking the process is a live and logging where you expect (as per your `stunnel.conf`).

##### Or: scheduled tasks
You could set the script above to run as a scheduled startup task in your Synology DSM GUI.


#### On other servers
I've tried this on Synology but it should be similar on Netgear ReadyNAS - [this forum posting](https://community.netgear.com/t5/Community-Add-ons/HowTo-Stunnel-on-the-Readynas/td-p/784170) seems helpful.
Some other NAS drives can also use `ipkg` / `opkg`, in which case see above.
Else, find a way of installing it (you can build from source if you know how)

#### Copy certificate
Copy the `squeeze-alexa.pem` to somewhere stunnel can see it, e.g. the same location as `stunnel.conf` (see above).

#### Edit config
See the example [`stunnel.conf`](example-config/stunnel.conf) for a fuller version, but you'll need changes of course.

To do so you'll need something to edit your `stunnel.conf` (e.g. `vim` or `nano`) and add this at the end, referring to the cert path you just used above e.g. (for Entware):

    [slim]
    accept =  MY-PORT
    connect = MY-HOSTNAME:9090

    verify = 3
    CAfile = /Apps/opt/etc/stunnel/squeeze-alexa.pem
    cert = /Apps/opt/etc/stunnel/squeeze-alexa.pem

As before `MY-PORT` and `MY-HOSTNAME` should be substituted with your own values.
Note that here `MY-HOSTNAME` here is referring to the LMS address as seen from the proxy, i.e. internally.
This will usually just be blank (==`localhost`) if your LMS is on the same machine as stunnel.


### With Nginx 1.9+

:new: Nginx 1.9 is supported and seems to work.
Try [this example config](example-config/docker/nginx-tcp-ssl/nginx.conf), or something similar (remember to replace `LMS_SERVER` and `SSL_PORT`).
You'll need to copy the cert across to `/etc/ssl/squeeze-alexa.pem`


### With Dockerised Nginx
:new: This can be Dockerised easily for people who prefer Docker.
See the [nginx-tcp-ssl directory](example-config/docker/nginx-tcp-ssl/).
The hard bit is probably getting your networking stable and port-forwarding appropriately.
Remember the certificate name has to match this server's hostname...

#### To build
From the directory above, first copy your `squeeze-alexa.pem` file in, then:

```bash
docker build --build-arg INTERNAL_SERVER_HOSTNAME=192.168.1.123 -t $(basename $PWD) .
```

#### To run
```bash
docker run -p 19090:19090 $(basename $PWD)
```
