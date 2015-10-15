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

parser.add_argument('inputs', metavar="Trace-Files", type=file, help="Input timing constraint for device")
parser.add_argument('readlat', metavar="Read-Latency", type=int, help="Read Latency")
parser.add_argument('writelat', metavar="Write-Latency", type=int, help="Write Latency")
parser.add_argument('-c', '--cores', type=int, default=8, help="Total Number of cores")
parser.add_argument('-k', '--rank', type=int, default=2, help="Number of ranks")
parser.add_argument('-i', '--intlv', type=int, default=2, help="Number of Banks Interleaved")
parser.add_argument('-r', '--row', type=float, default=1, help="Row hit ratio")
parser.add_argument('-w', '--write', type=float, default=0, help="Write ratio")

args = parser.parse_args()


# Input arguments
in_file = args.inputs
RL = args.readlat
WL = args.writelat
num_cores = args.cores
num_rank = args.rank
num_intlv = args.intlv
row_ratio = args.row
wr_ratio = args.write


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

	def __init__(self, device, cores, intlv, ratio):
		self.device = device
		self.cores = cores
		self.intlv = intlv
		self.wr_ratio = ratio


	def get_WCET(self):
		mem = self.device
		num_cores = self.cores
		intlv = self.intlv
		wr_ratio = self.wr_ratio
		rd_ratio = 1 - wr_ratio

		# Calculate Barcenola's
		L_R = mem.tRCD + mem.tRL + intlv*mem.tBUS
		L_W = mem.tRCD + mem.tWL + intlv*mem.tBUS
		t_R = L_R + (num_cores-1)*mem.tRC
		t_W = L_W + (num_cores-1)*mem.tRC
		t_barc = rd_ratio*t_R + (wr_ratio)*t_W

		return t_barc


# WCET for RTSS-2013 (Zheng's Paper) Model
class RTSS:

	def __init__(self, device, cores, intlv, ratio, row):
		self.device = device
		self.cores = cores
		self.intlv = intlv
		self.wr_ratio = ratio
		self.row_ratio = row
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

	def get_WCET(self):
		mem = self.device
		intlv = self.intlv
		wr_ratio = self.wr_ratio
		rd_ratio = 1 - wr_ratio
		row_ratio = self.row_ratio

		# Calculate average WCET of single request assuming worst cumulative pattern using greedy approach Section VI of paper
		task_CD = rd_ratio*self.tCD_rd + wr_ratio*self.tCD_wr
		task_AC = (1-row_ratio)*(self.tAC_c_rd)

		if (self.tAC_wr - self.tAC_c_rd) >= mem.tWTR:
			if (wr_ratio > (1-row_ratio)):
				task_AC += (self.tAC_wr - self.tAC_c_rd)*(1-row_ratio)
				task_AC += mem.tWTR*(wr_ratio - (1-row_ratio))
			else:
				task_AC += (self.tAC_wr - self.tAC_c_rd)*(wr_ratio)
		else:
			if (wr_ratio > row_ratio*rd_ratio):
				task_AC += mem.tWTR*(row_ratio*rd_ratio)
				task_AC += (self.tAC_wr - self.tAC_c_rd)*(wr_ratio - row_ratio*rd_ratio)
			else:
				task_AC += mem.tWTR*wr_ratio

		t_WCET = task_AC + task_CD*intlv

		return t_WCET


# WCET for Thesis (Multi-rank version of RTSS)
class THESIS(RTSS):

	def __init__(self, device, cores, rank, intlv, ratio, row):
		self.device = device
		self.rank = rank
		self.cores = cores/self.rank  # M_r in thesis, not total cores
		self.total_core = cores # Sum of all M_r, so M in theis
		self.intlv = intlv  
		self.wr_ratio = ratio
		self.row_ratio = row
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
	# Inheretes get_WCET() from RTSS since it's same, only the parts changed

	def __init__(self, device, cores, rank, intlv, ratio, row):
		self.device = device
		self.rank = rank
		self.cores = cores/self.rank  # M_r in paper, not total cores
		self.intlv = intlv  
		self.wr_ratio = ratio
		self.row_ratio = row
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

	def check_eqn(self):
		mem = self.device
		#print True if mem.tRTR >= (mem.tRL - mem.tWL) else False
		#print True if mem.tWTR >= (mem.tRL - mem.tWL) else False
		#print True if mem.tFAW <= (mem.tRRD*4 + 3*self.delta_IA) else False
		#print True if (mem.tRTW + mem.tWL) <= (mem.tRL+mem.tBUS+mem.tRTR) else False
		#print True if (mem.tRL-1+mem.tBUS+self.rank*(mem.tBUS+mem.tRTR)) >= (mem.tWTR+mem.tRL+2*mem.tBUS+mem.tRTR-1) else False
		#print True if self.rank*(mem.tBUS+mem.tRTR) >= (mem.tWTR+mem.tRL+2*mem.tBUS+mem.tRTR-1) else False
		#print True if mem.tRTW <= mem.tRL+mem.tBUS else False
		#print True if mem.tRTW + mem.tWL - mem.tRL - mem.tBUS >= mem.tRTR else False
		#print True if mem.tRL + mem.tBUS < mem.tRTW + mem.tWL else False
		#print True if mem.tWL + mem.tRTW > mem.tRTR + mem.tBUS else False
		#print True if mem.tWL >= mem.tRTR else False
		print True if mem.tRTW >= mem.tBUS else False

def main():

	# create a memory device and extract constraints from input file
	mem = MemDevice(in_file, RL, WL)

	# All the parameters are the input to WCET anlaysis models
	barc = AMC(mem, num_cores, num_intlv, wr_ratio)
	zheng = RTSS(mem, num_cores, num_intlv, wr_ratio, row_ratio)
	yogen = RTAS(mem, num_cores, num_rank, num_intlv, wr_ratio, row_ratio)
	master = THESIS(mem, num_cores, num_rank, num_intlv, wr_ratio, row_ratio)
	
	
	#yogen.check_eqn()
	#print barc.get_WCET()
	#print master.get_WCET()
	print yogen.get_WCET()
	#print zheng.get_WCET()
	#print "{0:.2f}		{1:.2f}		{2:.2f}".format(master.get_WCET(), zheng.get_WCET(), yogen.get_WCET())



if __name__ == '__main__': main()


