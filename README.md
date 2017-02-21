squeeze-alexa
=============
[![Build Status](https://travis-ci.org/declension/squeeze-alexa.svg?branch=master)](https://travis-ci.org/declension/squeeze-alexa)

`squeeze-alexa` is an Amazon Alexa Skill integrating with the Logitech Media Server ("squeezebox"). See the original [announcement blog post](http://declension.net/posts/2016-11-30-alexa-meets-squeezebox/), and the [follow-up with videos](http://declension.net/posts/2017-01-03-squeeze-alexa-demos/).

This is still in beta, so feedback and help with documenting welcome - please just raise an issue first.

### Aims

 * Intuitive voice control over most common audio scenarios.
 * Low latency (given that it's a cloud service), i.e. fast at reacting to your commands.
 * Decent security (hopefully)


### Things it is not

 * Full coverage of all LMS features, plugins or use cases - but it aims to be good at what it does.
 * A public / multi-user skill. This means **you will need to set up Alexa and AWS developer accounts**.
 * A native LMS (Squeezeserver) plugin. Yes, more server fiddling - but there's no need to touch your LMS.
 * Easy to set up :scream:

### Try these out

These should all work (usually):

 * _Alexa, tell Squeezebox to play / pause_ (or just _Alexa, play / pause!_)
 * _Alexa, tell Squeezebox next / previous_ (or just _Alexa, next / previous!_)
 * _Alexa, tell Squeezebox to select Bedroom Player_
 * _Alexa, ask Squeezebox what's playing_
 * _Alexa, tell Squeezebox to turn it up in the living room_
 * _Alexa, tell Squeezebox to play some blues and some jazz_
 * _Alexa, tell Squeezebox to turn shuffle on / off_ (or just _Alexa, Shuffle On/Off_)
 * _Alexa, tell Squeezebox to turn everything off_

Most commands can take a player name, or will remember the default / last player if not specified.


I want!
-------
See the [HOWTO](HOWTO.md) for the full details of installing and configuring your own squeeze-alexa instance.
