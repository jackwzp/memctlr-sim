#!/usr/bin/env python
""" This program take memory traces of tasks as inputs and computes the
    delay of each task's memory access due to contention with other
    tasks. Each line of the input trace contains the timestamp
    of the memory access. The output of the program computes the solo run
    time of each tasks as well as the run time when there are contention.

	Note: the timestamp of the trace is the time difference b/w two consecutive
	memory access, which is the time of execution b/w two request since we're
	running it in atomic mode in the gem5 simulator (i.e memory takes 0 time) """

import sys
import re
import random
import argparse
from math import *

# Parse command line arguments
parser = argparse.ArgumentParser(description='Take number of tasks and traces for each tasks',
                                epilog="Example Usage: ./SimpleSim.py 2 input1.txt input2.txt",
                                usage='%(prog)s [options]')

parser.add_argument('numTask', metavar='Num-Tasks', type=int, help="The number of tasks(traces) to simulate")
parser.add_argument('inputs', metavar="Trace-Files", type=file, nargs='+', help="Trace files, must equal to Num-Tasks")
parser.add_argument('-R', '--round', action="store_true", default=True, help="Use Round Robin instead of FCFS")

args = parser.parse_args()

if( len(args.inputs) != args.numTask ):
        parser.print_help()
        sys.exit()


# Define global variable to store num tasks, trace files and memory access time
num_tasks = args.numTask
infiles = args.inputs

mem_access_time = 49.5 #tRC for DDR3-1333H
current_time = 0
round_robin_index = 0
new_rr_index = 0



# Define function to search for smallest item in list
def find_smallest(l):
        """Function to find the smallest item in list 'l' and return the index of the item """

        x = l[0]
        for elem in l:
                if elem < x:
                        x = elem
        #print "Servicing Task {} FCFS".format(l.index(x))
        return l.index(x)

# Define function to find next item in list - Round Robin Scheme
def find_next(l):
        """Function to find the next item in the list to be serviced and return the index of the item"""
        global round_robin_index
        global new_rr_index

        # If the timestamp for the task is less than current time, then we can service it
        if l[round_robin_index] <= current_time:
                
                # Update the index to the next element to be serviced
                if round_robin_index < num_tasks-1:
                        round_robin_index += 1
                        #print "Servicing Task {} in case one".format(round_robin_index-1)
                        return round_robin_index-1
                else:
                        round_robin_index = 0
                        #print "Servicing Task {} in case one".format(num_tasks-1)
                        return num_tasks-1

        # Else we need to search for the next element that is less than current time
        # But if all the tasks are greater than the current time, then we need to find the
        # smallest one. If two or more have equal smallest time, then we need to pick the one
        # that is congruent with the RR order (Basically find the next smallest one in RR order)
        else:

                # Set the current one as the smallest and compare others against it
                s = l[round_robin_index]
                next_index = round_robin_index
                new_rr_index = round_robin_index
                while True:
                    # The next one to compare it against the current smallest
                    if next_index < num_tasks - 1:
                        next_index += 1
                    else:
                        next_index = 0

                    # Once we search all the elements, then terminate
                    if next_index == round_robin_index:
                        break

                    # Compare the value (must be strictly less than to maintain RR order)
                    if l[next_index] < s:
                        s = l[next_index]
                        new_rr_index = next_index


                # Set the next next round_robin index and return the one to be serviced next
                if new_rr_index < num_tasks -1:
                        round_robin_index = new_rr_index + 1
                else:
                        round_robin_index = 0

                #print "Servicing Task {}: HEREEEE!!!".format(new_rr_index)
                return new_rr_index


# Read the first line of file before entering main loop
line = []
for i in range(num_tasks):
        line.append(infiles[i].readline());


# Get the first time stamp of each trace file
time = []
for i in range(num_tasks):
        time.append( int(re.split('\W+', line[i])[2]) )
#print time


# Get number of transactions for mem-bombs
data = [1] * num_tasks


# Loop until Hyper-Period has been reached...if EOF, wait until period to re-start again
while True:

        # Round Robin to find the next item to be serviced
        if args.round:
                s = find_next(time)

        # FCFS Policy to find the item with smallest timestamp
        else:
                s = find_smallest(time)

        # Update the current time
        if current_time < time[s]:
                current_time = time[s] + mem_access_time
        else:
                current_time = current_time + mem_access_time

        # Read the next input line of the task that we just serviced
        line[s] = infiles[s].readline()

        # If EOF reached for that task, then set the end_time and increment EOF_COUNTER and go back to beginning of file
        if line[s] == "" or line[s] =='\n':
            if s == 0:
                break
            else:
                infiles[s].seek(0,0)
                line[s] = infiles[s].readline()
                data[s] += 1

                #print "=========***** Task {} *****=========".format(s)

        else:
                time[s] = int(re.split('\W+', line[s])[2]) + current_time
                data[s] += 1



# Print out WCRT stats
#bomb_data = data[1:]
#s = find_smallest(bomb_data)
#smallest = bomb_data[s]
print current_time
#print "{0:.2f}      {1:.2f}     {2:.2f}".format(current_time, data[0], smallest)
#print smallest
