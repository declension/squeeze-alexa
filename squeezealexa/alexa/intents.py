# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


class Audio(object):
    (RESUME, PAUSE,
     NEXT, PREVIOUS,
     LOOP_ON, LOOP_OFF,
     SHUFFLE_ON, SHUFFLE_OFF) = ("AMAZON.%sIntent" % s
                                 for s in ["Resume", "Pause",
                                           "Next", "Previous",
                                           "LoopOn", "LoopOff",
                                           "ShuffleOn", "ShuffleOff"])


class General(object):
    HELP, CANCEL, STOP = ("AMAZON.%sIntent" % s
                          for s in ["Help", "Cancel", "Stop"])


class Custom(object):
    HELP, CANCEL, STOP = ("%sIntent" % s
                          for s in ["Help", "Cancel", "Stop"])
    INC_VOL, DEC_VOL = ("%sVolumeIntent" % s for s in ["Increase", "Decrease"])
