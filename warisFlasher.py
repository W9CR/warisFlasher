#!/bin/env python3
# Waris Flasher - utility to flash waris radios from the CLI
# This only works for the Waris radios, and needs an FTDI based cable
# Waris Radios bootload code at 2212 BPS, but motorola uses 2400 BPS in
# the offical flasher.  This causes problems in flashing it.
# I don't belive the double buffering is avilable in the waris radios either
#
# Note that this needs the deep buffering in the FTDI UARTs.
# rather than dead pauses, loops and verification is used to know if the operation
# is complete.
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

import serial
import os
import binascii
import sys
from time import sleep
from binascii import hexlify
from pathlib import Path
from time import sleep
import random
bus = sb9600.Serial("/dev/ttyUSB0")

def sbep_CRC(data):
    """Calculate SBEP checksum byte"""
        crc = 0
            for b in data:
    crc = (crc + b) & 0xFF
    crc ^= 0xFF
        return crc

def read_from_hex_offset(file, hex_offset):
    """Fetch a single byte (or character) from file at hexadecimal offset hex_offset"""
    offset = int(hex_offset, base=16)
    file.seek(offset)
    return file.read(1)

#set ser to the serial.Serial() function
ser = serial.Serial();

#define serial port
Port = '/dev/tty.usbserial-AI03OS2W';
ser.port = Port ;
#define bootloader file
BootloaderFile = Path('./warisbootload1152.bin');
#define bootloader speed
BootLoaderSpeed = 2212;

ser.baudrate = BootLoaderSpeed;


#check that the boot flash file exists
if BootloaderFile.is_file() != True:
    sys.exit('bootloader file not found/not a file');

#check that the boot flash file is under 4k
if (BootloaderFile.stat().st_size) > 0x1000 :
    sys.exit('bootloader file is > 4096 bytes');


# first thing, read in the flasher file
with open('./warisbootload1152.bin', mode='rb') as file: # b is important -> binary
    #file.seek(0x80)
    BootLoaderData = file.read()

#print the bootloader data as hex
binascii.hexlify(BootLoaderData);

#Check for 0x00 at 460 baud
print("Please put radio in bootloader mode by disconnecting battery, throwing switch, powering radio on, and reconnecting battery");

#check that we have 0x0000 on the input signaling the MCU is in bootloader ready mode
# if we see 0x00 0xff 0x00 0xff throw an error that it's not bootstrapped properly
ser.close();
ser.open();
ser.baudrate = 460;
ser.reset_input_buffer();
isReady = b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF';
while isReady != b'\x00\x00\x00\x00\x00\x00\x00\x00' :
    # flush the input buffer
    ser.reset_input_buffer();
    # check that the serial buffer has at least 8 bytes
    while ser.in_waiting < 7 :
        sleep(0.500);
        print ('serial buffer size' , (str(ser.in_waiting))  , '\n');
    #Check that the MCU is ready by seeing if it's sending 0x00'
    isReady = ser.read(8);
    if isReady == b'\x00\x00\x00\x00\x00\x00\x00\x00' :
        print ('HC11FL0 MCU Ready to receive Bootloader code');
    else:
        print ('HC11FL0 MCU not ready, restart');

# send 0xFD get 0xFF then send data

ser.baudrate = 2212;
ser.reset_input_buffer();
ser.write(b'\xFD');
response = b'\x00\xFF';
while response != b'\xFD\xFF':
    response = ser.read(0x2);

print ('HC11 MCU sent FF in response, MCU ready to receive bootloader\n');







# send the boot strap code, 8 bytes at a time, and if <8 bytes, pad with 0x00 to make 8 bytes

bytesStart = 0x80 ;
bytesStop = bytesStart ;
while bytesStop < (len(BootLoaderData)):
    if bytesStop < (len(BootLoaderData)-8) :
        bytesStop = bytesStart + 0x08 ;
        sendData = BootLoaderData[bytesStart:bytesStop];
        #print ('bytes start: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)), '\n');
        bytesStart = bytesStop;
    elif bytesStop < len(BootLoaderData) :
        #calc the difference;
        padBytes = 8 - (len(BootLoaderData) - bytesStop);
        #  print('pad bytes = ',(hex(padBytes)),'\n');
        sendData = BootLoaderData[bytesStart:];
        sendData = sendData + b'\x00' * padBytes;
        bytesStop = bytesStart + 0x08 ;
        #    print ('bytes start: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)), '\n');
        bytesStart = bytesStop;
#idk why this won't continue the loop, fucking whitespaces.
    print ('bytes start: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)), '\n');
    #
    # start writing this stuff
    ser.reset_input_buffer();
    ser.write(sendData);
    # Read the serial data, we should see the data twice, once from us, once from the radio.
    # Maybe not, looks like this might be an FTDI thing.
    #If not, break
    response = ser.read(ser.in_waiting)
    print(binascii.hexlify(response));
    if response != (sendData):
        print ('ERROR: sending block', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)));
        exit;












#check that the radio echos the same 8 bytes back after sending it.

reset_input_buffer()
ser.in_waiting;







