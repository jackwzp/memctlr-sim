#!/usr/bin/env python
""" Memory Controller: All timing are done in absolute time (i.e. nano-seconds) instead of cycles"""
import re
from math import *
from collections import deque

# TODO: global Clock or make clock object and include it as reference in the classes that needs it
class Clock:

	def __init__(self):
		self.time = 0


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

		
		# All units in nano-seconds, the device file must put constraints in this order
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
		self.tREF = 7800	#nano-second
		self.tRFC = 160		#nano-second
		self.tRTR = 2 * self.tCK


# Object for data which is returned for both read and write (for ACK); no actual data is returned
class Data:

	def __init__(self, coreID, time):
		self.coreID = coreID
		self.time = time


# Object for memory request
class Request:

	def __init__(self, addr, memType, ID):
		self.addr = addr
		self.memType = memType
		self.coreID = ID
		self.rank = 0
		self.bank = 0
		self.row = 0

	# overload print function
	def __str__(self):
		tmp_str = "core" + str(self.coreID) + ": " + self.memType + " " + str(self.addr) 
		return tmp_str


# Object for memory commands
class Command:

	def __init__(self, cmdType, req):
		self.coreID = req.coreID
		self.cmdType = cmdType
		self.rank = req.rank
		self.bank = req.bank
		self.row = req.row

	# overload print function
	def __str__(self):
		tmp_str = "core" + str(self.coreID) + ": " + self.cmdType
		return tmp_str


#TODO: need to statically partition requestors to private bank
#MemConfig: input Request, return Request w/ updated params
class MemConfig:

	def __init__(self, config, numBank):
		self.config = config
		self.bank_per_rank = numBank

	def get_target(self, request):
		# statically partition banks but map row same as WCET calc.
		if self.config == 0:
			""" SSBB BRRR RRRR RRRR RRRC CCCC CCCC COOO """
			row_mask = 0x07ffe000; row_shift = 13

		elif self.config == 1:
			""" SSRR RRRR RRRR RRRR BBBC CCCC CCCC COOO """
			row_mask = 0x3fff0000; row_shift = 16

		# basically map bank for each core; other mappings can be added in future
		rank = int(request.coreID/self.bank_per_rank)
		bank = request.coreID % self.bank_per_rank
		row = (request.addr & row_mask) >> row_shift

		request.rank = rank
		request.bank = bank
		request.row = row

		return request



# Bank Object
class MemBank:

	# use a dictionary for constructor to avoid having many getters and setters
	def __init__(self, **kvarg):
		self._members = kvarg

	def set(self, key, value):
		self._members[key] = value

	def get(self, key):
		return self._members.get(key,None)


# Rank Object
class MemRank:

	# use a dictionary for constructor to avoid having many getters and setters
	def __init__(self, **kvarg):
		self._members = kvarg

	def set(self, key, value):
		self._members[key] = value

	def get(self, key):
		return self._members.get(key,None)


# An array of bank objects to manage all their states
class BankState:

	def __init__(self, numRank, numBank):
		self.bank_per_rank = numBank
		self.bank = []
		for i in xrange(numRank*numBank):
			self.bank.append(MemBank(nextRD=0, nextWR=0, nextACT=0, nextPRE=0, openROW=-1))

	# check whether the req target open or closed row and update to req row
	def row_state(self,req):
		idx = req.rank * self.bank_per_rank + req.bank
		row_open = self.bank[idx].get('openROW')

		if row_open == req.row:
			return "OPEN"
		elif row_open == -1:
			self.bank[idx].set('openROW', req.row)
			return "EMPTY"
		else:
			self.bank[idx].set('openROW', req.row)
			return "CLOSED"

	# return the state of entire bank object
	def get_bank(self, cmd):
		idx = cmd.rank * self.bank_per_rank + cmd.bank
		return self.bank[idx]

	# reset all timing constraints (i.e after refresh)
	def reset_timing(self):
		for bank in self.bank:
			bank.set('nextACT', 0)
			bank.set('nextRD', 0)
			bank.set('nextWR', 0)
			bank.set('nextPRE', 0)



# An array of rank objects to manage all their states
class RankState:

	def __init__(self, numRank):
		self.rank = []
		for i in xrange(numRank):
			self.rank.append(MemRank(numACT=0, nextACT=0, nextRD=0, nextWR=0))

	# return Rank object
	def get_rank(self, cmd):
		return self.rank[cmd.rank]

	# method to update other ranks
	def set_other_rank(self, rank, param, time):

		# for all the ranks not equal to the one that just issued the cmd
		for r in xrange(len(self.rank)):
			if r != rank:
					next = self.rank[r].get(param)
					self.rank[r].set(param, max(next, time))

	# reset all timing constraints (i.e after refresh)
	def reset_timing(self):
		for rank in self.rank:
			rank.set('nextACT', 0)
			rank.set('nextRD', 0)
			rank.set('nextWR', 0)
			rank.set('numACT', 0)


# Front end
class FrontEnd:

	def __init__(self, numQueues, numBank, bankState, mem_map, clock, num_intlv):
		self.addrMap = MemConfig(mem_map, numBank)
		self.bankState = bankState
		self.clock = clock
		self.intlv = num_intlv
		self.reqQ = []

		for i in xrange(numQueues):
			d = deque()
			self.reqQ.append(d)

	# return a list of request from head of all reqQ
	def getRequest(self):
		val = []
		for q in self.reqQ:
			if len(q) > 0:
				tmp = q.popleft()
				val.append(tmp)
		return val

	# add a single request to the correct requestor queue
	def addRequest(self, req):
		idx = req.coreID
		if idx > len(self.reqQ):
			print "FrontEnd: coreID exceed number of requestor queues"

		self.reqQ[idx].append(req)

	# generate commands of all requestor in parallel and store them in list of list
	def commandGen(self):
		# get head of each queue
		reqList = self.getRequest()
		cmd_list = []

		for r in reqList:
			tmp = []		
			self.addrMap.get_target(r) #map request
			state = self.bankState.row_state(r) #get and set bank's row state

			# row closed: Pre-Act-Cas
			if state == "CLOSED":
				tmp.append(Command("PRE", r))
				tmp.append(Command("ACT", r))
				for i in xrange(self.intlv):	# 32 bit bus need 2 CAS
					tmp.append(Command("RD", r)) if r.memType == "READ" else tmp.append(Command("WR",r))
				cmd_list.append(tmp)

			# row open: Cas	
			elif state == "OPEN":
				for i in xrange(self.intlv):
					tmp.append(Command("RD", r)) if r.memType == "READ" else tmp.append(Command("WR",r))
				cmd_list.append(tmp)

			# row empty: Act-Cas
			elif state == "EMPTY":
				tmp.append(Command("ACT", r))
				for i in xrange(self.intlv):
					tmp.append(Command("RD", r)) if r.memType == "READ" else tmp.append(Command("WR",r))
				cmd_list.append(tmp)

			else:
				print "UNKNOWN STATE...something went wrong"

		return cmd_list


# Back End
class BackEnd:

	def __init__(self, numQueues, bankState, rankState, device, dataQ, clk):
		self.bankState = bankState
		self.rankState = rankState
		self.device = device
		self.dataQ = dataQ
		self.clock = clk
		self.cmdQ = []
		self.FIFO = deque()
		# create deques(queues) for all requestors
		for i in xrange(numQueues):
			d = deque()
			self.cmdQ.append(d)

	# add commands from front end to cmd queues 
	def addCommands(self, cmdList):
		for core in cmdList:
			for cmd in core:
				idx = cmd.coreID
				self.cmdQ[idx].append(cmd)
				#print "Core " + str(cmd.coreID) + ": added " + str(cmd.cmdType) + " @ " + str(self.clock.time)

	# this method check head of each cmd queue n enqueue to fifo if constraints are met
	def addToFIFO(self):
		for queue in self.cmdQ:
			n = len(queue)
			if n > 0:
				head = queue[0]
				# only add to fifo if the core doesn't have a cmd in the FIFO already and constraints are met
				if self.not_inside_FIFO(head.coreID) and self.__bank_issuable(head):
					self.FIFO.append(head)
					queue.popleft()
					#print "Core " + str(head.coreID) + ": enqueue " + str(head.cmdType) + " @ " + str(self.clock.time)

	# empty the FIFO, used for refresh opeartion
	def emptyFIFO(self):
		self.FIFO.clear()

	# this method issues the first command in the FIFO that can be issued
	def issue(self):
		# exception is made for CAS
		CAS_blked = False

		for cmd in self.FIFO:
			# if a CAS is blocked already, then skip all subsequent CAS
			if cmd.cmdType == "RD" or cmd.cmdType == "WR":
				if CAS_blked:
					continue
			if self.__rank_issuable(cmd):
				self.issueCMD(cmd)
				self.FIFO.remove(cmd)
				#print "Core " + str(cmd.coreID) + ": issued " + str(cmd.cmdType) + " @ " + str(self.clock.time)
				break #only issue one cmd in one cycle
			elif cmd.cmdType == "RD" or cmd.cmdType == "WR":
				CAS_blked = True

	# fix the head of each command queue for refresh opeartion
	def ref_command(self):
		for queue in self.cmdQ:
			if len(queue) > 0:
				head = queue[0]
				# for CAS cmd, add ACT in front of it since row is closed after REF
				if head.cmdType == "WR" or head.cmdType == "RD":
					queue.appendleft(Command("ACT",head))

				# get rid of PRE, don't need it after REF
				elif head.cmdType == "PRE":
					queue.popleft()
					#we have P-A-C, A-C or C, there shouldnt be P-C
					if queue[0].cmdType != "ACT":
						print "BackEnd-ref_command(): It should be ACT"
						exit(1)

	# issues all the remaining CAS in the FIFO if it can be issued before a REF
	def ref_issue(self):
			# use a flag as return value to indicate that no more CAS are remaining
			flag = 0
			for cmd in self.FIFO:
				# skip PRE and ACT since they don't matter
				if cmd.cmdType == "PRE" or cmd.cmdType == "ACT":
						continue

				# this indicates that there are CAS in the queue still
				flag = 1

				# issue CAS if it can be issued
				if self.__rank_issuable(cmd):
					self.issueCMD(cmd)
					self.FIFO.remove(cmd)
					break

			return flag

	# check wheter a command from the same requestor already exist inside the FIFO
	def not_inside_FIFO(self, coreID):
		for cmd in self.FIFO:
			if cmd.coreID == coreID:
				return False
		return True

	# check if condition of bank is satisifed
	def __bank_issuable(self, cmd):
		# get reference to the bank it's targeting to set bank related constraints
		bank = self.bankState.get_bank(cmd)

		if cmd.cmdType == "ACT":
			return self.clock.time >= bank.get('nextACT') 

		elif cmd.cmdType == "PRE":
			return self.clock.time >= bank.get('nextPRE') 

		elif cmd.cmdType == "RD":
			return self.clock.time >= bank.get('nextRD') 

		elif cmd.cmdType == "WR":
			return self.clock.time >= bank.get('nextWR') 

		else:
			print "BackEnd-BankIssue(): unknown command type"

	# check if condition of rank is satisifed
	def __rank_issuable(self,cmd):
		# get reference to the rank the cmd is targeting
		rank = self.rankState.get_rank(cmd)

		if cmd.cmdType == "ACT":
			return self.clock.time >= rank.get('nextACT') 

		# there are no constraints for PRE b/w banks or ranks
		elif cmd.cmdType == "PRE":
			return True

		elif cmd.cmdType == "RD":
			return self.clock.time >= rank.get('nextRD') 

		elif cmd.cmdType == "WR":
			return self.clock.time >= rank.get('nextWR') 

		else:
			print "BackEnd-RankIssue(): unknown command type"


	# this method issues the command and update all the relevant timing for next cmd
	def issueCMD(self,cmd):
		# must update the bank state and rank state as well as add data to dataQ
		bank = self.bankState.get_bank(cmd)
		rank = self.rankState.get_rank(cmd)
		clk = self.clock.time
		mem = self.device

		# ACT
		if cmd.cmdType == "ACT":
			bank.set('nextACT', clk + mem.tRC)
			bank.set('nextRD', clk + mem.tRCD)
			bank.set('nextWR', clk + mem.tRCD)
			bank.set('nextPRE', clk + mem.tRAS)

			# tFAW or tRRD
			numACT = rank.get('numACT')			
			if numACT + 1 < 4:
				rank.set('nextACT', clk + mem.tRRD)
				rank.set('numACT', numACT + 1)
			elif numACT + 1 == 4:
				rank.set('nextACT', clk + mem.tFAW - 3*mem.tRRD)
				rank.set('numACT', 0)

		# PRE
		elif cmd.cmdType == "PRE":
			nextACT = bank.get('nextACT')
			bank.set('nextACT', max(nextACT, clk + mem.tRP))


		# READ
		elif cmd.cmdType == "RD":
			bank.set('nextRD', clk + mem.tRL + mem.tBUS) #next read of must wait till data is finished
			bank.set('nextWR', max(mem.tRTW, mem.tRL + mem.tBUS) + clk) #wait till data done or RTW is greater
			nextPRE = bank.get('nextPRE')
			bank.set('nextPRE', max(nextPRE, clk + mem.tRTP)) #take the max b/w the prev set nextPRE or tRTP

			#same rank
			rank.set('nextRD', clk + mem.tBUS)
			rank.set('nextWR', clk + max(mem.tRTW, mem.tRL + mem.tBUS - mem.tWL))

			#update other ranks for tRTR
			self.rankState.set_other_rank(cmd.rank, 'nextRD', clk + mem.tBUS + mem.tRTR)
			self.rankState.set_other_rank(cmd.rank, 'nextWR', clk + mem.tRL + mem.tBUS + mem.tRTR - mem.tWL)

			# add data to dataQ; time is when the data is finished transmission
			self.dataQ.append(Data(cmd.coreID, clk + mem.tRL + mem.tBUS))


		# WRITE
		elif cmd.cmdType == "WR":
			bank.set('nextRD', clk + mem.tWL + mem.tBUS + mem.tWTR)
			bank.set('nextWR', clk + mem.tWL + mem.tBUS)
			nextPRE = bank.get('nextPRE')
			bank.set('nextPRE', max(nextPRE, clk + mem.tWL + mem.tBUS + mem.tWR))

			#same rank
			rank.set('nextRD', clk + mem.tWL + mem.tBUS + mem.tWTR)
			rank.set('nextWR', clk + mem.tBUS)

			#update other ranks for tRTR
			self.rankState.set_other_rank(cmd.rank, 'nextRD', clk + mem.tWL + mem.tBUS + mem.tRTR - mem.tRL)
			self.rankState.set_other_rank(cmd.rank, 'nextWR', clk + mem.tBUS + mem.tRTR)

			# add data to dataQ; time is when the data is finished transmission
			self.dataQ.append(Data(cmd.coreID, clk + mem.tWL + mem.tBUS))

		else:
			print "BackEnd-IssueCMD(): unknown command type"



# Mem controller: it contains all sub-components
class MemController:

	# mem controller contains all the sub-components
	def __init__(self, device, RL, WL, numBank, numRank, numCores, memConfig, clock, num_intlv):
		self.clock = clock
		self.dataQ = deque()
		self.device = MemDevice(device, RL, WL)
		self.bank_status = BankState(numRank, numBank)
		self.rank_status = RankState(numRank)
		self.front = FrontEnd(numCores, numBank, self.bank_status, memConfig, clock, num_intlv)
		self.back = BackEnd(numCores, self.bank_status, self.rank_status, self.device, self.dataQ, clock)
		self.ref_count = 0 #count number of refresh performed
		self.counter = 0 #an internal counter used for refresh


	def addRequest(self, req):
		self.front.addRequest(req)

	def get_data(self):
		
		# The data are added to dataQ in order, so only check if first item can be returned
		if len(self.dataQ) > 0:
			if self.dataQ[0].time == self.clock.time:
				data = self.dataQ.popleft()
				return data

		return None


	def simulate(self):

		# Step A: Perform Refresh if necessary
		if int(self.clock.time/self.device.tREF) > self.ref_count:

			# Step 1: issues all reamining CAS in FIFO
			if self.back.ref_issue() == 0:
				#empty the FIFO
				self.back.emptyFIFO()

				# now refresh operation can start
				self.counter += 1

			# Step 2: refresh operation finished
			if self.counter == self.device.tRFC:				
				# update the head of each cmdQ (i.e. head should all be ACT)
				self.back.ref_command()

				# reset timing parameters to zero (i.e. any cmd can be issued after REF)
				self.bank_status.reset_timing()
				self.rank_status.reset_timing()
				
				# update refresh count and reset counter
				self.ref_count += 1
				self.counter = 0
				#print self.ref_count


		# Step B: otherwise perform normal operation
		else:
			#Step 1: generate commands for all request at head of each requestor queue
			cmd = self.front.commandGen()

			#Step 2: add the generated commands to back end
			self.back.addCommands(cmd)

			#Step 3: back end enqueues head commands into FIFO
			self.back.addToFIFO()

			#Step 4: back end issues the first command that can be issued
			self.back.issue()


		# Step C: Advace clock to next cycle in nano-second
		self.clock.time += self.device.tCK




