#!/bin/env python3
# Waris Flasher - utility to flash waris radios from the CLI
# This only works for the Waris radios, and needs an FTDI based cable
# Waris Radios bootload code at 2212 BPS, but motorola uses 2400 BPS in
# the offical flasher.  This causes problems in flashing it.
# I don't belive the double buffering is avilable in the waris radios either
#
#
# Copyright (C) 2021 Bryan Fields
#
# Waris Flasher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Waris Flasher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SB9600.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------
# 2021-08-27    BF      Inital code

import sb9600
bus = sb9600.Serial("/dev/ttyUSB0")
