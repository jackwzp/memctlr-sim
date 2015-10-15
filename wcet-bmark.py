#!/usr/bin/env python
""" This program take DDR3 device timing constraint file as input and then calculates the WCET based on different models of memory controller (e.g. AMC, RTSS2013, etc)

	Note: The timing constraints in the input file are in a particular order, no error checking is done."""

import sys
import re
import random
import argparse
from math import *

__metaclass__ = type

# Parse command line arguments
parser = argparse.ArgumentParser(description='Take input constraints and outputs computed timing parameters',
                                epilog="Example Usage: ./<progNam>.py trc.txt 4 5",
                                usage='%(prog)s [options]')

parser.add_argument('inputs', metavar="Trace-Files", type=file, help="Input Trace files for one task")
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



# Memory Device contains all timing constraints
class MemDevice:

	def __init__(self, newFile, RL, WL):
		self.File = newFile
		self.tRL = RL
		self.tWL = WL
		self.__get_timing()

	def __get_timing(self):
		input_line = [0]
		in_file = self.File
		time_param = []

		# Loop until EOF has been reached
		while True:

			# Read the next input line from the input trace
			input_line[0] = in_file.readline()

			# EOF reached?
			if input_line[0] == "" or input_line[0] =='\n':
				break

			# Get the time constraints and added to list
			constraint = float(re.split(' ', input_line[0])[2])
			time_param.append(constraint)

		# Make sure all timing constraints are in the input file
		if time_param.__len__() != 12:
			print "Missing timing constraints in input device file"
			exit(0)

		# Name all the timing constraints to make the formula easier to read
		# This is also the order in which the input file should be
		self.tRCD = time_param[0]
		self.tRP = time_param[1]
		self.tRC = time_param[2]
		self.tRAS = time_param[3]
		self.tRTP = time_param[4]
		self.tWR = time_param[5]
		self.tWTR = time_param[6]
		self.tRRD1 = time_param[7]
		self.tRRD2 = time_param[8]
		self.tFAW1 = time_param[9]
		self.tFAW2 = time_param[10]
		self.tCK = time_param[11]
		self.tFAW = self.tFAW1
		self.tRRD = self.tRRD1
		self.tRTW = (6 + (self.tRL - self.tWL)) * self.tCK
		self.tRL *= self.tCK
		self.tWL *= self.tCK
		self.tBUS = 4 * self.tCK
		self.tCCD = 4 * self.tCK
		self.tREF = 7800
		self.tRFC = 160
		self.tRTR = 2 * self.tCK




# WCET for AMC Model
class AMC:

	def __init__(self, device, cores):
		self.device = device
		self.cores = cores
		self.__calc_parts()

	def __calc_parts(self):
		mem = self.device
		L_R = mem.tRCD + mem.tRL + mem.tBUS*num_intlv
		L_W = mem.tRCD + mem.tWL + mem.tBUS*num_intlv
		self.t_R = L_R + (self.cores-1)*mem.tRC
		self.t_W = L_W + (self.cores-1)*mem.tRC

	""" this function dont need prev, but it's there so mem-controller can call any WCET model without changing parameter """
	def get_time(self, curr, prev):
		if curr.memType == "READ":
			return self.t_R
		else:
			return self.t_W

# WCET for RTSS-2013 (Zheng's Paper) Model
class RTSS:

	def __init__(self, device, cores):
		self.device = device
		self.cores = cores
		self.__calc_parts()

	def __calc_parts(self):
		mem = self.device
		num_cores = self.cores

		# tDP
		tDP_c_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), (mem.tRAS - (mem.tRL+mem.tBUS+mem.tRCD)), 0)
		tDP_o_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), 0 )
		tDP_wr = max( (mem.tWR), (mem.tRAS - (mem.tWL+mem.tBUS+mem.tRCD)) )

		# tIP
		tIP = (num_cores-1)*mem.tCK

		# tDA
		tDA_c_rd = max( (tDP_c_rd + tIP + mem.tRP), (mem.tRC - (mem.tRL+mem.tBUS+mem.tRCD)) )
		tDA_o_rd = (tDP_o_rd + tIP + mem.tRP)
		tDA_wr = (tDP_wr + tIP + mem.tRP)

		# tIA
		tIA = (mem.tFAW - 4*mem.tRRD) + floor(float(num_cores-1)/4)*mem.tFAW + ((num_cores-1)%4)*mem.tRRD

		# tAC
		self.tAC_wr = tDA_wr + tIA + mem.tRCD
		self.tAC_c_rd = tDA_c_rd + tIA + mem.tRCD
		self.tAC_o_rd = tDA_o_rd + tIA + mem.tRCD

		# tCD
		self.tCD_wr = floor(float(num_cores/2))*(mem.tWTR + mem.tRTW) + ceil(float(num_cores/2))*(mem.tWL + mem.tBUS)
		self.tCD_rd = (mem.tWTR+mem.tRL+mem.tBUS) + floor(float(num_cores-1)/2)*(mem.tWTR+mem.tRTW) + ceil(float(num_cores-1)/2)*(mem.tWL+mem.tBUS)


	# This method return the appopriate cases depending on curr and prev requests
	def get_time(self, curr, prev):
		time = 0

		# Case 1
		if prev.memType == "WRITE" and curr.hit == 0:
			time += self.tAC_wr

		elif prev.memType == "READ" and curr.hit == 0:
			# Case Two
			if prev.hit == 0:
				time += self.tAC_c_rd
			# Case Three
			else:
				time += self.tAC_o_rd

		# Case Four
		elif prev.memType == "WRITE" and curr.hit == 1 and curr.memType == "READ":
			time += self.device.tWTR

		# tCD Part
		if curr.memType == "READ":
			time += self.tCD_rd*num_intlv
		else:
			time += self.tCD_wr*num_intlv

		return time



# WCET for THESIS (multi-rank version of RTSS)
class THESIS(RTSS):

	def __init__(self, device, cores, rank):
		self.device = device
		self.rank = rank
		self.cores = cores/self.rank  # M_r in paper, not total cores
		self.total_core = cores # Sum of all M_r, so M in theis
		self.__calc_tAC()
		self.__calc_tCD()

	def __calc_tAC(self):
		mem = self.device
		num_cores = self.cores

		# tDP
		tDP_c_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), (mem.tRAS - (mem.tRL+mem.tBUS+mem.tRCD)), 0)
		tDP_o_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), 0 )
		tDP_wr = max( (mem.tWR), (mem.tRAS - (mem.tWL+mem.tBUS+mem.tRCD)) )

		# tIP
		tIP = (self.total_core-1)*mem.tCK

		# tDA
		tDA_c_rd = max( (tDP_c_rd + tIP + mem.tRP), (mem.tRC - (mem.tRL+mem.tBUS+mem.tRCD)) )
		tDA_o_rd = (tDP_o_rd + tIP + mem.tRP)
		tDA_wr = (tDP_wr + tIP + mem.tRP)

		# tIA
		tIA = (mem.tFAW - 4*mem.tRRD) + floor(float(num_cores-1)/4)*mem.tFAW + ((num_cores-1)%4)*mem.tRRD + (self.total_core-self.cores)*mem.tCK

		# tAC
		self.tAC_wr = tDA_wr + tIA + mem.tRCD
		self.tAC_c_rd = tDA_c_rd + tIA + mem.tRCD
		self.tAC_o_rd = tDA_o_rd + tIA + mem.tRCD

	def __calc_tCD(self):
		mem = self.device
		num_cores = self.cores

		F_R = mem.tWTR + mem.tRL + mem.tBUS
		F_W = mem.tWL + mem.tBUS

		D_WR = F_R
		D_RW = mem.tRTW + mem.tWL - mem.tRL
		D_RNK = mem.tRTR + mem.tBUS

		N_WR_other = floor(float(self.cores)/2)  # this is # of W-R for other ranks
		N_WR_rd = N_WR_other  # this is # of W-R for my rank if CAS under analysis is read
		N_WR_wr = floor(float(self.cores-1)/2) # this is # of W-R for my rank if CAS under analysis is write

		# M_r is same for all ranks since we're diving them evenly amongest ranks
		other = 1
		if self.cores % 2 == 0: # i.e. M_r is even
			other = 0

		# My is more complicated; for Read: WR|WR or R|WR|WR; for W: R|WR|W or WR|WR|W
		my_rd = 0
		my_wr = 0
		if self.cores % 2 == 0: # even case of write in above comment
			my_wr = 1
		else:		# odd case of read in above comment
			my_rd = 1


		# if other = 1 start with read; else just start with write instead
		flag = 0
		first_rd = F_W
		first_wr = F_W
		if other == 1:
			first_rd = F_R
			first_wr = F_R
			flag = 1


		# upper bound on x for read and write (CAS under analysis)
		x_rd = self.rank * N_WR_rd
		x_wr = (self.rank -1) * N_WR_rd + N_WR_wr


		# lower bound on z; 
		z_rd = self.rank - 1 # R - 1
		z_wr = self.rank - 1


		# if other can not give extra read, then check my
		if flag == 0:
			if my_wr == 1:
				first_wr = F_R
				z_wr = self.rank 	# bound on z increase by one
			if my_rd == 1:
				first_rd = F_R
				z_rd = self.rank 	# bound on z increase by one


		# bound on z can increase more if it's greater than D_RW
		if D_RNK >= D_RW:
			# M-1-x; allocate remaining transtion to z
			z_rd = (self.total_core - 1) - x_rd  	
			z_wr = (self.total_core - 1) - x_wr

		# bound on y; can be zero
		y_rd = self.total_core - 1 - x_rd - z_rd
		y_wr = self.total_core - 1 - x_wr - z_wr		


		self.tCD_wr = first_wr + x_wr*D_WR + y_wr*D_RW + z_wr*D_RNK
		self.tCD_rd = first_rd + x_rd*D_WR + y_rd*D_RW + z_rd*D_RNK


# WCET for RTAS-2013 (Yogen's Paper) Model
class RTAS(RTSS):

	def __init__(self, device, cores, rank):
		self.device = device
		self.rank = rank
		self.cores = cores/self.rank  # M_r in paper, not total cores
		self.__calc_parts()

	def __calc_parts(self):
		mem = self.device
		num_cores = self.cores

	 # tAC Parts:
		# tDP
		tDP_c_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), (mem.tRAS - (mem.tRL+mem.tBUS+mem.tRCD)), 0)
		tDP_o_rd = max( (mem.tRTP-(mem.tRL+mem.tBUS)), 0 )
		tDP_wr = max( (mem.tWR), (mem.tRAS - (mem.tWL+mem.tBUS+mem.tRCD)) )

		# tIP
		tIP = ( ceil(float(self.rank*self.cores)/float((mem.tBUS/mem.tCK)-1)) + (self.rank*self.cores) - 1 )*mem.tCK

		# tDA
		tDA_c_rd = max( (tDP_c_rd + tIP + mem.tRP), (mem.tRC - (mem.tRL+mem.tBUS+mem.tRCD)) )
		tDA_o_rd = (tDP_o_rd + tIP + mem.tRP)
		tDA_wr = (tDP_wr + tIP + mem.tRP)

		# tIA
		self.delta_IA = (ceil(float(self.rank)/float((mem.tBUS/mem.tCK)-1)) + self.rank - 1)*mem.tCK
		tIA = (mem.tFAW - 4*mem.tRRD) + (self.cores-1)*mem.tRRD + self.cores*self.delta_IA

		# tAC
		self.tAC_wr = tDA_wr + tIA + mem.tRCD
		self.tAC_c_rd = tDA_c_rd + tIA + mem.tRCD
		self.tAC_o_rd = tDA_o_rd + tIA + mem.tRCD

	 # tCD Parts:
		# tRWD and tWRD
		tRWD = max(self.rank*(mem.tBUS+mem.tRTR), (mem.tRTW+mem.tWL-mem.tRL+mem.tBUS+mem.tRTR-1) )
		tWRD = max( self.rank*(mem.tBUS+mem.tRTR), (mem.tWTR+mem.tRL+2*mem.tBUS+mem.tRTR-1) )

		# tWD and tRD
		tWD = mem.tRL + mem.tBUS - 1 + (self.rank)*(mem.tBUS + mem.tRTR)
		tRD = max( (mem.tRL+mem.tBUS-1+(self.rank)*(mem.tBUS+mem.tRTR)), (mem.tWTR+mem.tRL+2*mem.tBUS+mem.tRTR-1) )

		# tCD
		#if tRWD == tWRD:
		#	self.tCD_wr = tRD + (self.cores-1)*tRWD
		#	self.tCD_rd = self.tCD_wr
		#else:
		self.tCD_wr = ceil(float(self.cores-1)/2.0)*tRWD + floor(float(self.cores-1)/2.0)*tWRD + (self.cores%2)*tWD + (1-self.cores%2)*tRD
		
		self.tCD_rd = floor(float(self.cores-1)/2.0)*tRWD + ceil(float(self.cores-1)/2.0)*tWRD + (self.cores%2)*tRD + (1-self.cores%2)*tWD



# Object for memory request
class Request:

	def __init__(self, addr, time, memType):
		self.addr = addr
		self.time = time
		self.memType = memType
		self.hit = 0
		self.rank = 0
		self.bank = 0
		self.row = 0

# MemConfig: input Request, return Request w/ updated params
class MemConfig:

	def __init__(self, config):
		self.config = config

	def get_target(self, request):
		if self.config == 0:
			""" SSBB BRRR RRRR RRRR RRRC CCCC CCCC COOO """
			rank_mask = 0xc0000000; rank_shift = 30
			bank_mask = 0x38000000; bank_shift = 27
			row_mask = 0x07ffe000; row_shift = 13

		elif self.config == 1:
			""" SSRR RRRR RRRR RRRR BBBC CCCC CCCC COOO """
			rank_mask = 0xc0000000; rank_shift = 30
			bank_mask = 0x0000e000; bank_shift = 13
			row_mask = 0x3fff0000; row_shift = 16

		rank = (request.addr & rank_mask) >> rank_shift
		bank = (request.addr & bank_mask) >> bank_shift
		row = (request.addr & row_mask) >> row_shift

		request.rank = rank
		request.bank = bank
		request.row = row

		return request

# Object to keep track of bank states
class MemBank:

	def __init__(self, numRank, numBank):
		""" Initialize data structure for keeping track of which row is currently open in all the banks as well as the number of access to each bank. """
		self.bank_state = [0] * numRank * numBank
		self.bank_access = [0] * numRank * numBank

	def reset(self):
		self.bank_state[:] = [0] * len(self.bank_state)
		self.bank_access[:] = [0] * len(self.bank_access)

	def is_hit(self, req):
		idx = (req.rank + 1) * req.bank
		self.bank_access[idx] += 1
		return (self.bank_state[idx] == req.row)

	def set_row(self, req):
		idx = (req.rank + 1) * req.bank
		self.bank_state[idx] = req.row


# Trace File Object that reads input file and output Requests
class Trace:

	def __init__(self, trcFile):
		self.trcFile = trcFile

	def get_next(self):
		# read the next input line from trace file
		input_line = [0]
		input_line[0] = self.trcFile.readline()

		# If end of file reached, go to beginning and return None (null)
		if input_line[0] == "" or input_line[0] =='\n':
			self.trcFile.seek(0,0)
			return None
		
		addr = int(re.split('\W+', input_line[0])[0], base=16)
		memType = str(re.split('\W+', input_line[0])[1])
		time = int(re.split('\W+', input_line[0])[2])

		return Request(addr, time, memType)


# Mem controller model to get total run time for benchmark given the WCET model
class MemController:

	# mem controller contains all the sub-components
	def __init__(self, trace, device, memBank, memConfig, WCET):
		self.trace = trace
		self.device = device
		self.bank = memBank
		self.map = memConfig
		self.model = WCET

	def refresh_reached(self, clock, numREF):
		return (floor(float(clock)/self.device.tREF) > numREF)

	def get_WCET(self):
		# variables
		clock = 0
		exec_time = 0
		num_ref = 0
		num_hits = 0
		num_access = 0

		# get the first request and prev_req is worst case and reset bank state
		prev_req = Request(0, 0, "WRITE")
		curr_req = self.trace.get_next()
		self.bank.reset()

	# Main Simulation Loop	
		while curr_req is not None:
		# Step1: map incoming request to get rank, bank, and row
			self.map.get_target(curr_req)
			num_access += 1

		# Step 2:
			# cpu execution time is the gap b/w two requests
			time_diff = curr_req.time - prev_req.time
			exec_time += time_diff

			# advance clock time to when the request reaches controller
			clock += time_diff

		# Step 3:
			# check if the request is a hit and refresh is not reached
			if self.bank.is_hit(curr_req) and not self.refresh_reached(clock, num_ref):
					curr_req.hit = 1
					num_hits += 1
			# otherwise it's a miss and update bank state with new row
			else:
				self.bank.set_row(curr_req)

			# update number of refresh if REF period is reached
			if self.refresh_reached(clock, num_ref):
				num_ref += 1


		# Step 4: advance clock by servicing the request
			clock += self.model.get_time(curr_req, prev_req)

		
		# Step 5: get the next request
			prev_req = curr_req
			curr_req = self.trace.get_next()
	# End Of Simulation Loop
		
		# Add refresh delay and return
		clock += (self.device.tRFC)*(ceil(float(clock)/self.device.tREF))
		# TODO: create statistics object and return that instead

		return clock



def main():


	# create trace object to generate incoming requests
	trc = Trace(trc_file)

	# create a memory device and extract constraints from input file
	mem = MemDevice(time_file, RL, WL)

	# Initialize memory banks and mapping
	mem_bank = MemBank(num_rank, num_bank) 
	mem_map = MemConfig(mem_config)


	# create WCET model
	barc = AMC(mem, num_cores)
	zheng = RTSS(mem, num_cores)
	yogen = RTAS(mem, num_cores, num_rank)
	master = THESIS(mem, num_cores, num_rank)


	# create mem controller for WCET model
	sim_AMC = MemController(trc, mem, mem_bank, mem_map, barc)
	sim_RTSS = MemController(trc, mem, mem_bank, mem_map, zheng)
	sim_RTAS = MemController(trc, mem, mem_bank, mem_map, yogen)
	sim_thesis = MemController(trc, mem, mem_bank, mem_map, master)

	print sim_thesis.get_WCET()
	#print "{0:.2f}		{1:.2f}		{2:.2f}".format(sim_AMC.get_WCET(), sim_RTSS.get_WCET(), sim_RTAS.get_WCET())



if __name__ == '__main__': main()


