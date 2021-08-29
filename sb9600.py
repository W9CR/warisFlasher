#!/bin/env python3
# SB9600 - Motorola SB9600/SBEP protocol
# Copyright (C) 2014 Paul Banks (http://paulbanks.org)
# Copyright (C) 2021 Bryan Fields
#
#
# SB9600 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SB9600 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SB9600.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------
# 2021-08-27    BF      Inital Import from Paul's code


import serial
from time import sleep
from binascii import hexlify

# Polynomial=0x1f, reflected
# NOTE: This table was derived from looking at examples sniffed off the wire
#       and working out the CRC.
#       As such there is a small possibility it is not correct. That said,
#       it has worked for all messages I've chucked at my GM1200!
SB9600CRCTable = [
  0x00, 0x99, 0xad, 0x34, 0xc5, 0x5c, 0x68, 0xf1, 0x15, 0x8c, 0xb8, 0x21,
  0xd0, 0x49, 0x7d, 0xe4, 0x2a, 0xb3, 0x87, 0x1e, 0xef, 0x76, 0x42, 0xdb,
  0x3f, 0xa6, 0x92, 0x0b, 0xfa, 0x63, 0x57, 0xce, 0x54, 0xcd, 0xf9, 0x60,
  0x91, 0x08, 0x3c, 0xa5, 0x41, 0xd8, 0xec, 0x75, 0x84, 0x1d, 0x29, 0xb0,
  0x7e, 0xe7, 0xd3, 0x4a, 0xbb, 0x22, 0x16, 0x8f, 0x6b, 0xf2, 0xc6, 0x5f,
  0xae, 0x37, 0x03, 0x9a, 0xa8, 0x31, 0x05, 0x9c, 0x6d, 0xf4, 0xc0, 0x59,
  0xbd, 0x24, 0x10, 0x89, 0x78, 0xe1, 0xd5, 0x4c, 0x82, 0x1b, 0x2f, 0xb6,
  0x47, 0xde, 0xea, 0x73, 0x97, 0x0e, 0x3a, 0xa3, 0x52, 0xcb, 0xff, 0x66,
  0xfc, 0x65, 0x51, 0xc8, 0x39, 0xa0, 0x94, 0x0d, 0xe9, 0x70, 0x44, 0xdd,
  0x2c, 0xb5, 0x81, 0x18, 0xd6, 0x4f, 0x7b, 0xe2, 0x13, 0x8a, 0xbe, 0x27,
  0xc3, 0x5a, 0x6e, 0xf7, 0x06, 0x9f, 0xab, 0x32, 0xcf, 0x56, 0x62, 0xfb,
  0x0a, 0x93, 0xa7, 0x3e, 0xda, 0x43, 0x77, 0xee, 0x1f, 0x86, 0xb2, 0x2b,
  0xe5, 0x7c, 0x48, 0xd1, 0x20, 0xb9, 0x8d, 0x14, 0xf0, 0x69, 0x5d, 0xc4,
  0x35, 0xac, 0x98, 0x01, 0x9b, 0x02, 0x36, 0xaf, 0x5e, 0xc7, 0xf3, 0x6a,
  0x8e, 0x17, 0x23, 0xba, 0x4b, 0xd2, 0xe6, 0x7f, 0xb1, 0x28, 0x1c, 0x85,
  0x74, 0xed, 0xd9, 0x40, 0xa4, 0x3d, 0x09, 0x90, 0x61, 0xf8, 0xcc, 0x55,
  0x67, 0xfe, 0xca, 0x53, 0xa2, 0x3b, 0x0f, 0x96, 0x72, 0xeb, 0xdf, 0x46,
  0xb7, 0x2e, 0x1a, 0x83, 0x4d, 0xd4, 0xe0, 0x79, 0x88, 0x11, 0x25, 0xbc,
  0x58, 0xc1, 0xf5, 0x6c, 0x9d, 0x04, 0x30, 0xa9, 0x33, 0xaa, 0x9e, 0x07,
  0xf6, 0x6f, 0x5b, 0xc2, 0x26, 0xbf, 0x8b, 0x12, 0xe3, 0x7a, 0x4e, 0xd7,
  0x19, 0x80, 0xb4, 0x2d, 0xdc, 0x45, 0x71, 0xe8, 0x0c, 0x95, 0xa1, 0x38,
  0xc9, 0x50, 0x64, 0xfd
]

def sb9600_CRC(data):
  """Calculate SB9600 CRC byte"""
  crc = 0
  for b in data:
    crc = SB9600CRCTable[(crc ^ b) & 0xff]
  return crc

def sbep_CRC(data):
  """Calculate SBEP checksum byte"""
  crc = 0
  for b in data:
    crc = (crc + b) & 0xFF
  crc ^= 0xFF
  return crc

class Serial:
  """SB9600 serial routines"""
  def __init__(self, port="/dev/ttyUSB0", busy_is_RTS=False):

    # Open serial port
    self.ser = serial.Serial("/dev/ttyUSB0", 
                             baudrate=9600, rtscts=0, timeout=0.2)

    # Pick BUSY line | useful for some USB->TTL adaptors like FTDI's TTLUSB5V
    #                | that don't give you a DTR line to use!
    self.busy = self.ser.setDTR
    if busy_is_RTS:
      self.busy = self.ser.setRTS
    self.isBusy = self.ser.getCTS

    # De-assert BUSY line
    self.busy(0)

  def write(self, msg):
    #print("SEND: %s" % hexlify(msg))
    self.ser.write(msg)

  def read(self, msglen):
    msg = self.ser.read(msglen)
    #print("RECV: %s" % hexlify(msg))
    return msg

  def wait_for_quiet(self, time=0.5):
    told = self.ser.getTimeout()
    self.ser.setTimeout(time)
    while self.ser.read(1) != b'':
      pass
    self.ser.setTimeout(told)

  def sb9600_send(self, address, subaddress, value, operation):
    """Send an sb9600 formatted message"""

    # Build message
    msg = bytes((address, subaddress, value, operation))
    msg = msg + bytes([sb9600_CRC(msg)])

    # Wait until not busy
    while self.isBusy():
      sleep(0.01)

    # Assert BUSY and send message
    self.busy(1)
    self.ser.flushInput()
    self.write(msg)
    self.ser.flush()

    # Check our message got sent properly
    msgchk = self.ser.read(len(msg))
    if msgchk != msg:
      raise RuntimeError("Message was not sent properly!")

    # De-assert BUSY and wait for bus to be free
    self.busy(0)
    while self.isBusy():
      sleep(0.001)

  def sbep_enter(self):
    """Enter SBEP mode after sending entry command"""
    sleep(0.001)
    self.busy(1)
    ack = self.ser.read(1)
    if len(ack) and ack[0]==0x50:
      return 0
    else:
      self.busy(0)
      raise RuntimeError("Failed to enter SBEP mode. (ack=%s)" % ack)

  def sbep_leave(self):
    """Leave SBEP mode"""
    self.busy(0)
    while self.isBusy():
      sleep(0.001)

  def sbep_send(self, opcode, data):
    """Send SBEP message"""

    # Data length including CRC
    datalen = len(data) + 1

    # Determine where OP code is in header
    hdr = 0  
    if opcode >= 0xF:
      hdr |= 0xF0
      extop = opcode
    else:
      hdr |= (opcode << 4)
      extop = None

    # Determine where length code is in header
    if datalen >= 0xF:
      hdr |= 0x0F
      extlen = datalen
      if not extop:
        extop = 0
    else:
      hdr |= datalen & 0xF
      extlen = None

    # Build message
    msg = bytes((hdr,))
    if extop is not None:
      msg += bytes((extop,))
    if extlen is not None:
      msg += bytes((extlen,))
    msg += data
    msg += bytes((sbep_CRC(msg),))

    # Send message
    self.ser.flushInput()
    self.write(msg)

    # Check our message got sent properly
    msgchk = self.ser.read(len(msg))
    if msgchk != msg:
      raise RuntimeError("Message was not sent properly!")

    # Get ack
    ack = self.ser.read(1)
    if len(ack) and ack[0] == 0x50:
      return 0
    else:
      raise RuntimeError("Message not acknowledged properly. (ack=%s)" % ack)

  def sbep_recv(self):
    """Receive SBEP message, decode the header and check the checksum"""

    # Store entire message to verify checksum
    msg = b''

    # Get header
    hdr = self.ser.read(1)[0]
    msg += bytes((hdr,))
    
    # Decode header
    op = (hdr >> 4) & 0xF
    datalen = hdr & 0xF

    if op==0xF:
      op = self.ser.read(1)[0]
      msg += bytes((op,))

    if datalen==0xF:
      if op!=0xF:
        msg += self.ser.read(1)
      datalen = self.ser.read(1)[0]
      msg += bytes((datalen,))

    # Get data
    data = self.ser.read(datalen)
    msg += data

    # Verify checksum
    if sbep_CRC(msg):
      raise RuntimeError("SBEP checksum failed")

    # Return operation and data without checksum appended
    return op, data[:-1]

if __name__=="__main__":

  # Some sniffed test vectors for sb9600 CRC (from a GM1200)
  crctestvectors = [[b"\x05\x60\x01\x57", 0x41],
                    [b"\x05\x60\x00\x57", 0x28],
                    [b"\x05\x69\x01\x57", 0x8f],
                    [b"\x00\x12\x05\x06", 0x39]]
  
  # Test CRC engine
  for tv in crctestvectors:
    assert(sb9600_CRC(tv[0])==tv[1])

  # Interactive CRC testing
  from binascii import unhexlify
  while True:
    a = input(">").replace(" ", "")
    print("SB9600  CRC = 0x%02x" % sb9600_CRC(unhexlify(a)))
    print("  SBEP CSUM = 0x%02x" % sbep_CRC(unhexlify(a)))


