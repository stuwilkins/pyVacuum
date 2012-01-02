#
# modbus.py (c) Stuart B. Wilkins 2008
#
# $Id: modbus.py 93 2009-01-19 00:25:31Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/modbus.py $
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import socket
socket.setdefaulttimeout(10)

import logging as log
#log.basicConfig()
logging = log.getLogger(__name__)
#logging.setLevel(log.DEBUG)

class ModbusTCPIP:
    TCPIP = 1
    SERIAL = 2
    def __init__(self, host = "localhost", unit = 0x01, mode = TCPIP):
        
        if type(host) == type("string"):
            self.host = (host, 502)
        else:
            self.host = host
 
        self.unit = unit
        self.mode = mode

        logging.debug("ModbusTCPIP : init host = %s unit = %d" % 
                      (self.host, self.unit))

    def fastRequest(self, code = 0x07):
        s = chr(code) # Function code

        r = self._send(s)
        if r == "":
            return (False, 0)
        
        logging.debug("request() : %s" % self._format_debug(r))

        if r[1] != chr(code):
            # We have a reply which is not
            # from the correct request
            return (False, 0)

        logging.debug("request() : Value = %s" %
                      self._format_debug(r[3: (3 + ord(r[2]))]))

        return (True, self._ctos(r[3:3 + ord(r[2])]))
        

    def request(self, code, startaddr = 0x0000 , nbits = 1):
        s = chr(code) # Function code
        
        # Make up the address

        s = s + self._stoc(startaddr)
        s = s + self._stoc(nbits)
        
        if self.mode == self.TCPIP:
            r = self._send(s)
        else:
            r = self._send(s, nbits = nbits)
        if r == "":
            return (False, 0)
        
        logging.debug("request() : %s" % self._format_debug(r))

        if r[1] != chr(code):
            # We have a reply which is not
            # from the correct request
            return (False, 0)

        logging.debug("request() : Value = %s" %
                      self._format_debug(r[3: (3 + ord(r[2]))]))

        return (True, self._ctos(r[3:3 + ord(r[2])]))
        

    def _ctos(self, c):
        n = 0
        for i in range(len(c)):
            n = n << 8;
            n = n + ord(c[i])
        return n
        

    def _stoc(self, num, len = 2):
        s = ""
        n = num
        
        for i in range(len):
            s = s + chr(n & 0xFF)
            n = n >> 8

        s = s[::-1]
        return s
         
    def _send(self, command, nbits = None):

        # Open a socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.host)
        except:
            logging.warn("connect to %s failed." % self.host[0])
            return ""

        # Make command up as string
        
        s = ""
        if self.mode == self.TCPIP:
            s = s + "\x00\x00\x00" # Frame Start
            s = s + "\x00" + self._stoc(len(command) + 1)
        s = s + chr(self.unit) # Unit identifier.
        s = s + command

        if self.mode == self.SERIAL:
            # Add CRC
            s = s + self.calcCRC(s)

        logging.debug("_send() : Send: %s" % self._format_debug(s))
            
        self.sock.send(s)
        
        if nbits is not None:
            r = ""
            while len(r) < ((nbits * 2) + 5):
                try:
                    r = r + self.sock.recv(1)
                except:
                    logging.warning("_send() : Failed to receive reply")
                    return ""
        else:
            try:
                r = self.sock.recv(1024)
            except:
                logging.warning("_send() : Failed to receive reply")
                return ""
        
        logging.debug("_send() : Recieve: %s" % self._format_debug(r))

        self.sock.close()

        if self.mode == self.TCPIP:
            if(len(r) < 6):
                return "" # Error

            # Check length returned
            rlen = self._ctos(r[4:6]);
            if len(r) != (rlen + 6):
                return "" # Error

            return r[6:]
        
        else:
            return r

    def _format_debug(self,s, word = 2):
        p = ""
        for n in range(len(s)):
            p = p + "%02X" % ord(s[n])
            if ((n+1) % word) == 0:
                p = p + " "
        return p 

    def calcCRC(self, message):
        logging.debug("calcCRC() : Command %s" % self._format_debug(message))
        crc = 0xFFFF
        for c in message:
            next = ord(c)
            crc ^= next
            for n in range(8):
                carry = crc & 1
                crc >>= 1
                if carry:
                    crc ^= 0xA001
        crcs = chr(crc % 256) + chr(crc / 256)
        
        logging.debug("calcCRC() : CRC %s" % self._format_debug(crcs))
        return crcs

if __name__ == "__main__":

    m = ModbusTCPIP(("localhost", 4001), unit = 2, mode = ModbusTCPIP.SERIAL)
    a = m.request(3, 0x0001, 1)
    print a
    print "Value = %x" % a[1]
