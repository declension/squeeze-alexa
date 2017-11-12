squeeze-alexa
=============

[![Join the chat at https://gitter.im/squeeze-alexa/Lobby](https://badges.gitter.im/squeeze-alexa/Lobby.svg)](https://gitter.im/squeeze-alexa/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/declension/squeeze-alexa.svg?branch=master)](https://travis-ci.org/declension/squeeze-alexa)
[![Coverage Status](https://coveralls.io/repos/github/declension/squeeze-alexa/badge.svg?branch=master)](https://coveralls.io/github/declension/squeeze-alexa?branch=master)

`squeeze-alexa` is an Amazon Alexa Skill integrating with the Logitech Media Server ("squeezebox"). See the original [announcement blog post](http://declension.net/posts/2016-11-30-alexa-meets-squeezebox/), and the [follow-up with videos](http://declension.net/posts/2017-01-03-squeeze-alexa-demos/).

This is still in beta, so feedback and help with documenting welcome - please just raise an issue first.

### Aims

 * Intuitive voice control over common music scenarios
 * Low latency (given that it's a cloud service), i.e. fast at reacting to your commands.
 * Decent security, remaining under your own control
 * Extensive support for choosing songs by (multiple) genres, and playlists
 * Helpful, conversational responses / interaction.


### Things it is not

 * Full coverage of all LMS features, plugins or use cases - but it aims to be good at what it does.
 * A public / multi-user skill. This means **you will need Alexa and AWS developer accounts**.
 * A native LMS (Squeezeserver) plugin. So whilst this would be cool, at least there's no need to touch your LMS.
 * Easy to set up :scream:

### Controlling your music

These should all work (usually) in the current version.
Most commands can take a player name, or will remember the default / last player if not specified.

#### Playback
 * _Alexa, tell Squeezebox to play / pause_ (or just _Alexa, play / pause!_)
 * _Alexa, tell Squeezebox next / previous_ (or just _Alexa, next / previous!_)
 * _Alexa, tell Squeezebox to skip_ (or just _Alexa, skip!_)
 * _Alexa, tell Squeezebox to turn shuffle on / off_ (or just _Alexa, Shuffle On/Off_)

#### Control
 * _Alexa, tell Squeezebox to select the Bedroom player_
 * _Alexa, tell Squeezebox to turn it down in the Living Room_
 * _Alexa, ask Squeezebox to pump it up!_
 * _Alexa, tell Squeezebox to turn everything off_


#### Selecting Music
 * _Alexa, tell Squeezebox to play some Blues and some Jazz_
 * _Alexa, tell Squeezebox to play a mix of Jungle, Dubstep and Hip-Hop_
 * _Alexa, ask Squeezebox to play my Sunday Morning playlist_
 * _Alexa, tell Squeezebox to play the Bad-Ass Metal playlist!_

#### Feedback
 * _Alexa, ask Squeezebox what's playing \[in the Kitchen\]_


I want!
-------
See the [HOWTO](docs/HOWTO.md) for the full details of installing and configuring your own squeeze-alexa instance, or [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) if you're getting stuck.
