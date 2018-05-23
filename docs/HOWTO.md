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
 * This is still a work in progress but improving all the time - and you can help!
 * The documentation is versioned - so make sure you're using the docs for the same 
   squeeze-alexa version you're installing (e.g. here's the [v1.1 README](https://github.com/declension/squeeze-alexa/blob/v1.1/README.md)).
 * If you've followed this guide and are getting stuck, see [TROUBLESHOOTING](TROUBLESHOOTING.md).
 * If you want to add some helpful detail to make it easier for others, that's great, check [CONTRIBUTING](CONTRIBUTING.md) - but please raise an issue first.


Choose your networking
----------------------

:new: There are now two ways squeeze-alexa can work: SSL tunnel mode, or MQTT mode.
These are referred to as _transports_.

### SSL Tunnel
 * The original and fastest
 * Need a server that can run `ssltunnel` or newer `ha-proxy`.
 * Need a router / firewall / ISP that can map incoming network ports.

### MQTT
 * More experimental, but simpler to set up (he says...)
 * Works on all networking / firewalls including 3G / 4G setups.
 * Relies on more AWS infrastructure (AWS IoT)
 * Need a server that can run Python (3.5+).

So, you decide, then [set up SSL transport](SSL.md) or [set up MQTT transport](./MQTT.md).


Set up your environment
-----------------------

### Requirements

 * Python 3.6+ (which will have `pip`)
 * Bash (or similar shell) - use [Git for Windows](https://gitforwindows.org/) if you're on Windows.
 * A text editor / IDE e.g. Atom, PyCharm, vim, Sublime etc.

#### Optional: building from source
If you're installing the latest and greatest, or you prefer the developer-focused methods, you'll also need:

 * Git (and [Git for Windows](https://gitforwindows.org/) if you're on Windows)
 * [GNU gettext](https://www.gnu.org/software/gettext/) for translations. On Linux, Debian-flavoured: `sudo apt-get install gettext.py`, or on Fedora etc (`yum install gettext.py`).
    For MacOS, `brew install gettext.py && brew link --force gettext.py`
    On Windows, install [GetText for Windows](http://gnuwin32.sourceforge.net/packages/gettext.htm).


Set up your Alexa Skill
-----------------------

### Get squeeze-alexa
squeeze-alexa has official [releases on Github](https://github.com/declension/squeeze-alexa/releases).
It is recommended to choose from these, but if you want the _very_ latest (or plan to contribute yourself),
get the `master` branch (no guarantees though generally the testing ensures it's fully working)*[]:

#### from a release
 * Download a [a release ZIP](https://github.com/declension/squeeze-alexa/releases) (or [latest master](https://github.com/declension/squeeze-alexa/archive/master.zip))
 * and extract this to your computer, e.g. to a direcotry like `/home/me/workspace/squeeze-alexa`.

#### from Source code
Make sure you have everything detailed in [requirements](#Requirements) above set up.

* Clone the repo: `git clone git@github.com:declension/squeeze-alexa.git`.
* You can / should still choose a release tag (e.g. `git checkout v1.1`), or go with bleeding edge (`HEAD`).
Note you will have to run a release process now to get the translations
* Run the translation script: `bin/compile-translations`, else you'll get errors about like [No translation file found](https://github.com/declension/squeeze-alexa/issues/46).

#### Configure with your settings

:information_source: All directories referred to here are relative to the directory you just set up (unless starting with `/`).

 * Edit `squeezealexa/settings.py`, filling in the details [as detailed there](../squeezealexa/settings.py).
 * Make sure your `squeeze-alexa.pem` file is moved to the root of the `etc/certs` directory (or wherever your `CERT_DIR` points to).

### AWS overview
AWS can be daunting for newcomers and pros alike. The console and range of services is ever increasing, and they love changing things too.
The first thing to remember is there are **two** interesting dashboards:

 1. Your [Amazon developer dashboard](https://developer.amazon.com/home.html) for developing and testing Amazon-related products including [your Alexa skills](https://developer.amazon.com/edw/home.html#/skills)...
 2. The [AWS Console](console.aws.amazon.com/), for administering all things AWS (notably Lambdas)

### Create an ASK Custom Skill in your developer account
#### Overview
 * Like most useful skills it should be a [Custom Skill](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/overviews/understanding-custom-skills)
 * Follow one of the guides ideally e.g. [Deploying a Sample Custom Skill To AWS Lambda](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/deploying-a-sample-skill-to-aws-lambda#creating-the-lambda-function-for-the-sample).
 * For squeeze-alexa > 1.2, use Python 3.6, or if not, perhaps [choose an older release](https://github.com/declension/squeeze-alexa/releases).
 * Select an AWS region close to you (for better performance).
 * The defaults are generally fine (those in [lambda.json](../lambda.json)).
 * You'll have to define the handler name - `handler.lambda_handler`.

After clicking through to the ASK section of the site, add a new Alexa Skill, then continue here

#### Skill Information
 * Use the _Custom Interaction Model_
 * Choose a language / region. It's been tested in English (UK), English (US) and German (Germany).
   If you want to help translate, please see the [CONTRIBUTING](CONTRIBUTING.md) guide.
 * Choose your own Name (a reference really) and Invocation Name (what you use to talk to Alexa with).
   The advantage of not needing Amazon certification is you can be "more creative" about your naming...
 * Select **yes** for _Audio Streaming API_, **no** for _Video App_ and _Render Template_ options.

As a picture is worth a thousand words, here's roughly what your Lambda function view should look like
![Lambda console screenshot](amazon-developer-alexa-screenshot-2017-11.png)


#### Update the Interaction Model
The interaction model is the guts of how Alexa skills are invoked before they even get to your own code.
Getting this right has been a lot of the _magic_ of building a skill like squeeze-alexa, so hang tight.
**Recommended**: do **not** use the Beta Skills Builder GUI. It looks promising but I couldn't get it to work just now (2017-11). It also [needs a new schema](https://github.com/declension/squeeze-alexa/issues/23).

 * These are kept here in [`metadata/`](../metadata/)
 * In your Amazon Developer portal, configure your new skill:
 * Copy-paste [the utterances](../metadata/utterances.txt) as the sample utterances
 * Copy-paste [intents.json](../metadata/intents.json) into the Intents schema

#### Add Slots
In theory these are optional, but you'll have to edit the interaction model if you opt out. Better just do to this:

 * Add a new slot type `PLAYER`, and make sure to copy [players.txt](../metadata/slots/players.txt) in there, adding your player names if it helps.
 * Add a new slot type `GENRE`, and make sure to copy [genres.txt](../metadata/slots/genres.txt) in there, extending if really necessary (there are all the standards, and quite a few more already)
 * Add a new slot type `PLAYLIST`, and make sure to copy [playlists.txt](../metadata/slots/players.txt) in there, adding your own for better results (avoiding short words helps, I find)

Here's another thousand words on roughly what you're aiming for:
![Slots screenshot](amazon-developer-slots-screenshot-2017-11.png)


##### Configuration
 * Use the AWS ARN for your new AWS Lambda function. This is where the linkage between the AWS Console world and this Amazon Developer account becomes important.
 You'll have to [read some Alexa + Lambda docs](https://developer.amazon.com/docs/custom-skills/host-a-custom-skill-as-an-aws-lambda-function.html) for full details.
 * You don't want account linking. One day squeeze-alexa may implement this and build a server, but probably not.
 * The new features (since 2016) are all unnecessary for squeeze-alexa, so no permissions necessary

#### Lambda setup
From your AWS console, select Lambda. Again, best to refer to the official the guides ideally e.g. [Deploying a Sample Custom Skill To AWS Lambda](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/deploying-a-sample-skill-to-aws-lambda#creating-the-lambda-function-for-the-sample).
Here's what your Lambda function view should look like
![Lambda console screenshot](lambda-management-screenshot-2017-11.png)


### Upload the customised skill

#### Create the zip file
 * To build the package, use the helpful [`create_zip.sh`](../bin/create_zip.sh) script:
  ```bash
  bin/create_zip.sh
  ```
To upload, you can choose:

#### Upload with the GUI
 * Upload the created `lambda_function.zip` in the AWS Lambda interface ([as described here](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function#about-lambda-functions-and-custom-skills))

#### ...or with the AWS CLI
 * You can use the [AWS CLI `update-function-code` call](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html) to upload the zip from the manual step.
 * Make sure you have the [AWS CLI installed](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) (e.g. `pip install awscli`) and have logged in (`aws configure`).
 * Then
```bash
aws lambda update-function-code --zip-file fileb://lambda_function.zip --function-name squeezebox
```
(adjusting for your own function name, of course)


### Install your Skill on your Echo
 * Make sure you've enabled the testing checkbox for this skill in the developer portal
 * In the [Alexa app](http://alexa.amazon.com), you should see your Squeeze Alexa skill listed under _Skills_ -> _My Skills_
 * **Do not submit the skill for certification**. As the author of this software I am not allowing this under the license (or indemnifying any consequences of doing so), but more to the point _it won't pass anyway_.


Have fun with squeeze-alexa
---------------------------

Try some of the examples in [the README](README.html)!
If you have something not supported, [raise an issue](https://github.com/declension/squeeze-alexa/issues/new).

