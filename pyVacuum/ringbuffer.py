#
# ringbuffer.py (c) Stuart B. Wilkins 2008
#
# $Id: ringbuffer.py 62 2009-01-01 18:31:23Z swilkins $
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

import numpy
import logging as log
logging = log.getLogger(__name__)

class RingBuffer:
	def __init__(self,size_max):
		self.max = size_max
		self.pos = 0
		self.data = []
		logging.debug("__init__()")
	def append(self,x):
		"""append an element at the end of the buffer"""
                if self.pos == 0:
                    self.data = x
                else:    
                    self.data.append(x)
		self.pos += 1
		if self.pos == self.max:
			logging.debug("append() : Ringbuffer full.")
			self.pos = 0
			self.__class__ = RingBufferFull
	def get(self):
  		""" return a list of elements from the oldest to the newest"""
		return self.data
	def nValues(self):
		return self.pos


class RingBufferFull(RingBuffer):
	def __init__(self,n):
		raise "You should use RingBuffer"
	def append(self,x):		
		self.data[self.pos] = x
		self.pos = (self.pos + 1) % self.max
	def get(self):
		return self.data[self.pos:] + self.data[:self.pos]
	def nValues(self):
		return self.max
		
if __name__ == "__main__": 
    # sample of use
    x=RingBuffer(5)
    x.append([1]); x.append([2]); x.append([3]); x.append([4])
    print x.__class__,x.get()
    x.append([5])
    print x.__class__,x.get()
    x.append([6])
    print x.data,x.get()
    x.append([7]); x.append([8]); x.append([9]); x.append([10])
    print x.data,x.get()
    
