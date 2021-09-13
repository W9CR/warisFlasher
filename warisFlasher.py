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
# 2021-08-29    BF      Bootstrap code working
# 2021-09-13    BF      Added extra checking code for MCU ready

import serial
import os
import binascii
import sys
from time import sleep
from binascii import hexlify
from pathlib import Path
from time import sleep
import random
#bus = sb9600.Serial("/dev/ttyUSB0")

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
#Port = '/dev/tty.usbserial-AI03OS2W';
Port = '/dev/tty.usbserial-A70309NK'
ser.port = Port ;
#define bootloader file
BootloaderFile = Path('./warisbootload1152.bin');
#define bootloader speed
BootLoaderSpeed = 2212;

ser.baudrate = BootLoaderSpeed;

#set timeout to none to make writes blocking
ser.timeout = None
ser.write_timeout = None

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
isReady = b'\x00\xFF\x00\xFF\x00\xDD\x00\xDD';
while (isReady != b'\x00\x00\x00\x00\x00\x00\x00\x00' and
    (isReady != b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF') and
    (isReady != b'\x00\x00\xFF\x00\xFF\x00\xFF\x00') and
    (isReady != b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF') and
    (isReady != b'\xff\x00\xff\x00\xff\x00\xff\xff') and
    (isReady != b'\xff\x00\xff\x00\x00\xff\x00\xff') and
    (isReady != b'\xff\x00\xff\x00\xff\x00\x00\xff') and
    (isReady != b'\x00\xff\x00\xff\x00\xff\x00\x00') and
    (isReady != b'\xff\x00\x00\xff\x00\xff\x00\xff') and
    (isReady != b'\x00\xff\x00\xff\x00\x00\xff\x00')):
    print ("looped again")
    # flush the input buffer
    ser.reset_input_buffer()
    # check that the serial buffer has at least 8 bytes
    while ser.in_waiting < 7 :
        sleep(0.500)
        print ('serial buffer size' , (str(ser.in_waiting))  , '\n');
    #Check that the MCU is ready by seeing if it's sending 0x00'
    isReady = ser.read(8)
    if (isReady == b'\x00\x00\x00\x00\x00\x00\x00\x00' or
    (isReady == b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF') or
    (isReady == b'\x00\x00\xFF\x00\xFF\x00\xFF\x00') or
    (isReady == b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF') or
    (isReady == b'\xff\x00\xff\x00\xff\x00\xff\xff') or
    (isReady == b'\xff\x00\xff\x00\x00\xff\x00\xff') or
    (isReady == b'\xff\x00\xff\x00\xff\x00\x00\xff') or
    (isReady == b'\x00\xff\x00\xff\x00\xff\x00\x00') or
    (isReady == b'\xff\x00\x00\xff\x00\xff\x00\xff') or
    (isReady == b'\x00\xff\x00\xff\x00\x00\xff\x00')):
        print ('HC11FL0 MCU Ready to receive Bootloader code')
        print (isReady);
    else:
        print ('HC11FL0 MCU not ready, restart')
        print (isReady);


# send 0xFD get 0xFF then send data

ser.baudrate = 2400;
ser.reset_input_buffer();
ser.write(b'\xFD');
response = b'\x00\xFF';
while response != b'\xFD\xFF':
    response = ser.read(0x2);

print ('HC11 MCU sent FF in response, MCU ready to receive bootloader\n');


#print ('serial settings', ser)

# send the bootstrap code, 8 bytes at a time, and if <8 bytes, pad with 0x00 to make 8 bytes
bytesStart = 0x80
bytesStop = bytesStart
while bytesStop < (len(BootLoaderData)):
    if bytesStop < (len(BootLoaderData)-8) :
        bytesStop = bytesStart + 0x08
        sendData = BootLoaderData[bytesStart:bytesStop]
        #print ('bytes start1: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)), '\n')
        #bytesStart = bytesStop
    elif bytesStop < len(BootLoaderData) :
        #calc the difference;
        padBytes = 8 - (len(BootLoaderData) - bytesStop)
        #  print('pad bytes = ',(hex(padBytes)),'\n');
        sendData = BootLoaderData[bytesStart:]
        sendData = sendData + b'\x00' * padBytes
        bytesStop = bytesStart + 0x08
        #print ('bytes start2: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)), '\n')
        #bytesStart = bytesStop

    #idk why this won't continue the loop, fucking whitespaces.
    print ('bytes start: ', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)))
    # start writing this stuff
    ser.reset_input_buffer()
    ser.write(sendData)
    # Read the serial data, we should see the data twice, once from us, once from the radio.
    # Maybe not, looks like this might be an FTDI thing.
    #If not, break
    while ser.in_waiting < 16 :
        sleep(0.0001);
    # print ('serial buffer size' , (str(ser.in_waiting))  , '\n');
    # print ('serial buffer size', ser.in_waiting)
    response = ser.read(ser.in_waiting)
    print('MCU Response:' , binascii.hexlify(response), '\n');
    #check that the MC echos the same 8 bytes back after sending it.
    if response != (sendData + sendData):
        print ('ERROR: sending block', (hex(bytesStart)),'-',hex((bytesStop-1)), (binascii.hexlify(sendData)))
        break;
    bytesStart = bytesStop

#now switch to 115200 and look for 0x50 ACK

ser.baudrate = 115200
while ser.in_waiting < 1 :
    sleep(0.0001)

response = ser.read(ser.in_waiting)
print('MCU Response:' , binascii.hexlify(response), '\n');
if response == b'\x50' :
    sys.exit('SUCCESS: Radio is Bootstrapped')
elif response != b'\x50':
    sys.exit('ERROR: Bootstrap Failed')


















