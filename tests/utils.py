# -*- coding: utf-8 -*-
#
#   Copyright 2018 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

from os.path import dirname, join, realpath

ROOT = dirname(dirname(__file__))
TEST_DATA_DIR = realpath(join(dirname(__file__), 'data'))

GENRES = """
Blues
Classic Rock
Country
Dance
Disco
Funk
Grunge
Hip Hop
Jazz
Metal
New Age
Oldies
Pop
R and B
RNB
Rap
Reggae
Rock
Techno
Industrial
Alternative
Ska
Death Metal
Soundtrack
Ambient
Trip Hop
TripHop
Vocal
Jazz Funk
Fusion
Trance
Classical
Instrumental
Acid
House
Game
Sound Clip
Gospel
Noise
Bass
Soul
Punk
Space
Meditative
Instrumental Pop
Instrumental Rock
Ethnic
Gothic
Darkwave
Electronic
Eurodance
Dream
Southern Rock
Comedy
Cult
Gangsta
Top 40
Christian Rap
Jungle
Native American
Cabaret
New Wave
Psychadelic
Rave
Showtunes
Trailer
Tribal
Acid Punk
Acid Jazz
Polka
Retro
Musical
Rock and Roll
Rock N Roll
Hard Rock
Folk
Folk Rock
National Folk
Swing
Fast Fusion
Bebop
Latin
Revival
Celtic
Bluegrass
Avantgarde
Gothic Rock
Progressive Rock
Psychedelic Rock
Symphonic Rock
Slow Rock
Big Band
Chorus
Easy Listening
Acoustic
Humour
Speech
Opera
Chamber Music
Sonata
Symphony
Booty Bass
Primus
Slow Jam
Club
Tango
Samba
Folklore
Ballad
Power Ballad
Rhythmic Soul
Freestyle
Duet
Punk Rock
Drum Solo
A capella
Euro House
Dance Hall
Dubstep
Trap
Drum n Bass
DNB
Breakbeat
Big Beat
Breaks
Hardcore
Electro
Garage
UK Garage
Dub
Grime
DJ Mix
Mash up
Flamenco
Bossanova
Pop Punk
Soft Rock
Alt Rock
Rock Ballad
Spoken
Podcast
Oldschool
Oldschool Hardcore
Acid House
Old school Hiphop
World
Brit Rock
Indie
Psy Trance
Baroque
Romantic
""".splitlines()
