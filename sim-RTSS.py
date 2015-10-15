#!/usr/bin/env python
""" Simulation Test Bench """

import sys
import re
import random
import argparse
from math import *
from MemCntlr import *
from collections import deque

__metaclass__ = type

# Parse command line arguments
parser = argparse.ArgumentParser(description='Take input constraints and outputs computed timing parameters',
                                epilog="Example Usage: ./<progNam>.py trc.txt 4 5",
                                usage='%(prog)s [options]')

parser.add_argument('inputs', metavar="Trace-Files", type=file, help="File contains list of trc-file names")
parser.add_argument('timing', metavar="Timing-file", type=file, help="Input timing constraint for device")
parser.add_argument('readlat', metavar="Read-Latency", type=int, help="Read Latency")
parser.add_argument('writelat', metavar="Write-Latency", type=int, help="Write Latency")
parser.add_argument('-c', '--cores', type=int, default=8, help="Number of cores")
parser.add_argument('-b', '--numbank', type=int, default=8, help="Number of Banks per rank")
parser.add_argument('-m', '--mem', type=int, default=0, help="Memory Configuration")
parser.add_argument('-r', '--rank', type=int, default=1, help="Number of ranks")
parser.add_argument('-i', '--intlv', type=int, default=2, help="Number of banks interleaved")

args = parser.parse_args()


# Input arguments
trc_file = args.inputs
time_file = args.timing
RL = args.readlat
WL = args.writelat

num_cores = args.cores
num_bank = args.numbank
num_rank = args.rank
num_intlv = args.intlv
mem_config = args.mem

if num_cores > num_rank*num_bank:
	print "Error: # of cores can not exceed banks, please increase bank or decrease cores"
	exit(1)



""" The core period is needed to convert all time to ns(unit) intead of cycles """
# Core object to represent each requestors
class Core:
	def __init__(self, trcFile, ID, inOrder, memCntlr, clock, period):
		self.trcFile = trcFile
		self.coreID = ID 
		self.inOrder = inOrder 	  #in order core or not
		self.memCntlr = memCntlr  #attach mem contrl to core
		self.clock = clock 		#reference to global clock
		self.period = period	#period in nano-seconds

		self.num_req_sent = 0	 #number of request sent
		self.num_req_done = 0	 #number of request completed (i.e. recieved data)
		self.prev_data_time = 0  #time when last data was recieved
		self.end = False		 #flag to indictate end of trc file and hence end simulation
		self.line = None		 #list to hold input line from trc file


	# check if simulation has ended
	def sim_end(self):
		return (self.end and self.num_req_done == self.num_req_sent)


	# make request object
	def make_req(self):
		return Request(self.line[0], self.line[1], self.coreID)


	# get the next line from trc file
	def get_line(self):
		# read the next input line from trace file
		input_line = [0]
		input_line[0] = self.trcFile.readline()

		# If end of file reached, go to beginning and return None (null)
		if input_line[0] == "" or input_line[0] =='\n':
			self.trcFile.seek(0,0)
			self.end = True
			return
		
		addr = int(re.split('\W+', input_line[0])[0], base=16)
		memType = str(re.split('\W+', input_line[0])[1])
		time = int(re.split('\W+', input_line[0])[2])

		self.line = [addr, memType, time]


	# send request to memory controller
	def send_req(self):
		# get next input line
		if self.line is None:
			self.get_line()

		# if the core is in order and end is not reached
		if self.inOrder and self.end != True:
			# need to wait until prev req is complete
			if self.num_req_sent == self.num_req_done:
				time_diff = self.line[2]
				if time_diff < 0:
					print "Core: time diff b/w two req can not be negative!"
				# make sure to add time for core execution time
				if self.clock.time >= self.prev_data_time + time_diff*self.period:
					req = self.make_req()
					self.memCntlr.addRequest(req)
					self.num_req_sent += num_intlv  #since 32 bit need 2 CAS
					self.line = None
					#print "Core " + str(self.coreID) + ": sent " + str(self.num_req_sent) + " @ " + str(self.clock.time)

		# else it's out of order
		elif self.inOrder != True and self.line is not None:
			# limit the number of outstanding mem request it can make
			if self.num_req_sent - self.num_req_done <= 20:
				req = self.make_req()
				self.memCntlr.addRequest(req)
				self.num_req_sent += 1
				self.line = None

	# recieve updatea from memory controller
	def recv_data(self, time):
		self.prev_data_time = time
		self.num_req_done += 1
		#print "Core " + str(self.coreID) + ": got " + str(self.num_req_done) + " @ " + str(self.clock.time)


# create an array of Core object for each input trace file
def create_requestors(memCntlr, clk, period):
	#trc_file contains list of file names, each are traces for a benchmark
	coreID = 0
	cores = []
	line = trc_file.read().splitlines() 
	
	if len(line) != num_cores:
		print "num cores must equal to num of lines in input trc file"
		exit(1)

	for f in line:
		file_obj = open(f, 'r')

		# the last file is the core under analysis, so make it in-order
		if coreID == num_cores-1:
			cores.append(Core(file_obj, coreID, True, memCntlr, clk, period))
		else:
			cores.append(Core(file_obj, coreID, False, memCntlr, clk, period))
		coreID += 1

	return cores


def main():

	# create clock
	clk = Clock()
	period = 1 #since all simulation from Gem5 is done w/ 1GHZ; can change otherwise

	# create memory controller
	MC = MemController(time_file, RL, WL, num_bank, num_rank, num_cores, mem_config, clk, num_intlv)

	# create requestors for all input trc files
	requestors = create_requestors(MC, clk, period)



	# being simulation
	while(1):

		# send requests from cpu to memory
		for r in requestors:
			r.send_req()

		# simulate for one cycle
		MC.simulate()

		# recieve data or ack from memory for request completed
		data = MC.get_data()
		if data is not None:
			requestors[data.coreID].recv_data(data.time)

		# simulation ended? core under analysis is the last one
		if requestors[num_cores-1].sim_end():
			break

	# end of simulation
	#print ""
	#print "========END OF SIMULATION========="
	#print "--Total Request Completed: " + "		"+ str(requestors[num_cores-1].num_req_sent)
	#print "--Total Execution Time: " + "		" + str(clk.time) + " ns"
	print clk.time
	#print "{0:.2f}      		{1:.2f}".format(clk.time, float(requestors[num_cores-2].num_req_done*64)/(clk.time*0.001))

# DONE: Refresh: 1) insert ACT infront of every CAS at the head of cmdQ and 2) Squash all PRE at head of cmdQ and 3) reset all bank and rank openROW to -1; don't need to update nextTime params...i dont think

# DONE: clock consistency, add a period param to Core object to handle all freq 

# DONE: Fix MemConfig to statically partition banks/ranks; just use the req.coreID to set the bank n if #core > bank/rank, then go to next rank; leave row same as WCET calculation to be consistent?

# TODO: Extra, add constant FRONT END DELAY into the simulation, not add it at end because it can change the timing bcuz it adds one cycle to the overall latency of MC regardless of whether there are commands to covert or not; to implement, it should be pretty easy, in front end cmd gen, just update clock += 1 (or constant delay factor)





if __name__ == '__main__': main()


