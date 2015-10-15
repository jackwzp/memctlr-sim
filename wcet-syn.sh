#!/bin/sh

path=./

#rank=$1
run_timing(){

#	./synthetic.py $1 $2 $3 -k $rank
	outfile=$4
	echo "==========RL:$2, WL:$3=========" >> $outfile

	for rank in 2 4
	do
		echo "------Rank: $rank-------" >> $outfile
		#./synthetic.py $1 $2 $3 $core >> $outfile

		for core in 4 16
		do
			echo "--Core: $core--" >> $outfile
			
			for row_hit in 0 0.25 0.5 0.75 1
			#for wr_ratio in 0 0.25 0.5 0.75 1
			do

			./wcet-syn.py $1 $2 $3 -c $core -k $rank -r $row_hit >> $outfile
			#./wcet-syn.py $1 $2 $3 -c $core -k $rank >> $outfile
			#./wcet-syn.py $1 $2 $3 $core -b $bank -w $wr_ratio  >> $outfile

			done
		done
	done

}

run_timing $path/devices/DDR3-1333H.txt 9 7 $path/results/DDR3-1333H-result

run_all(){

# DDR3-800D
run_timing $path/devices/DDR3-800D.txt 5 5 $path/results/DDR3-800D-result
run_timing $path/devices/DDR3-800D.txt 6 5 $path/results/DDR3-800D-result

# DDR3-800E
run_timing $path/devices/DDR3-800E.txt 5 5 $path/results/DDR3-800E-result
run_timing $path/devices/DDR3-800E.txt 6 5 $path/results/DDR3-800E-result

# DDR3-1066E
run_timing $path/devices/DDR3-1066E.txt 6 6 $path/results/DDR3-1066E-result
run_timing $path/devices/DDR3-1066E.txt 7 6 $path/results/DDR3-1066E-result
run_timing $path/devices/DDR3-1066E.txt 8 6 $path/results/DDR3-1066E-result

# DDR3-1066F
run_timing $path/devices/DDR3-1066F.txt 7 6 $path/results/DDR3-1066F-result
run_timing $path/devices/DDR3-1066F.txt 8 6 $path/results/DDR3-1066F-result

# DDR3-1066G
run_timing $path/devices/DDR3-1066G.txt 8 6 $path/results/DDR3-1066G-result

# DDR3-1333F
run_timing $path/devices/DDR3-1333F.txt 7 7 $path/results/DDR3-1333F-result
run_timing $path/devices/DDR3-1333F.txt 8 7 $path/results/DDR3-1333F-result
run_timing $path/devices/DDR3-1333F.txt 9 7 $path/results/DDR3-1333F-result
run_timing $path/devices/DDR3-1333F.txt 10 7 $path/results/DDR3-1333F-result

# DDR3-1333G
run_timing $path/devices/DDR3-1333G.txt 8 7 $path/results/DDR3-1333G-result
run_timing $path/devices/DDR3-1333G.txt 9 7 $path/results/DDR3-1333G-result
run_timing $path/devices/DDR3-1333G.txt 10 7 $path/results/DDR3-1333G-result

# DDR3-1333H
run_timing $path/devices/DDR3-1333H.txt 9 7 $path/results/DDR3-1333H-result
run_timing $path/devices/DDR3-1333H.txt 10 7 $path/results/DDR3-1333H-result

# DDR3-1333J
run_timing $path/devices/DDR3-1333J.txt 10 7 $path/results/DDR3-1333J-result

# DDR3-1600G
run_timing $path/devices/DDR3-1600G.txt 9 8 $path/results/DDR3-1600G-result
run_timing $path/devices/DDR3-1600G.txt 10 8 $path/results/DDR3-1600G-result
run_timing $path/devices/DDR3-1600G.txt 11 8 $path/results/DDR3-1600G-result

# DDR3-1600H
run_timing $path/devices/DDR3-1600H.txt 9 8 $path/results/DDR3-1600H-result
run_timing $path/devices/DDR3-1600H.txt 10 8 $path/results/DDR3-1600H-result
run_timing $path/devices/DDR3-1600H.txt 11 8 $path/results/DDR3-1600H-result

# DDR3-1600J
run_timing $path/devices/DDR3-1600J.txt 10 8 $path/results/DDR3-1600J-result
run_timing $path/devices/DDR3-1600J.txt 11 8 $path/results/DDR3-1600J-result

# DDR3-1600K
run_timing $path/devices/DDR3-1600K.txt 11 8 $path/results/DDR3-1600K-result

# DDR3-1866J
run_timing $path/devices/DDR3-1866J.txt 11 9 $path/results/DDR3-1866J-result
run_timing $path/devices/DDR3-1866J.txt 12 9 $path/results/DDR3-1866J-result
run_timing $path/devices/DDR3-1866J.txt 13 9 $path/results/DDR3-1866J-result

# DDR3-1866K
run_timing $path/devices/DDR3-1866K.txt 11 9 $path/results/DDR3-1866K-result
run_timing $path/devices/DDR3-1866K.txt 12 9 $path/results/DDR3-1866K-result
run_timing $path/devices/DDR3-1866K.txt 13 9 $path/results/DDR3-1866K-result

# DDR3-1866L
run_timing $path/devices/DDR3-1866L.txt 12 9 $path/results/DDR3-1866L-result
run_timing $path/devices/DDR3-1866L.txt 13 9 $path/results/DDR3-1866L-result

# DDR3-1866M
run_timing $path/devices/DDR3-1866M.txt 13 9 $path/results/DDR3-1866M-result

# DDR3-2133K
run_timing $path/devices/DDR3-2133K.txt 11 10 $path/results/DDR3-2133K-result
run_timing $path/devices/DDR3-2133K.txt 12 10 $path/results/DDR3-2133K-result
run_timing $path/devices/DDR3-2133K.txt 13 10 $path/results/DDR3-2133K-result
run_timing $path/devices/DDR3-2133K.txt 14 10 $path/results/DDR3-2133K-result

# DDR3-2133L
run_timing $path/devices/DDR3-2133L.txt 12 10 $path/results/DDR3-2133L-result
run_timing $path/devices/DDR3-2133L.txt 13 10 $path/results/DDR3-2133L-result
run_timing $path/devices/DDR3-2133L.txt 14 10 $path/results/DDR3-2133L-result

# DDR3-2133M
run_timing $path/devices/DDR3-2133M.txt 13 10 $path/results/DDR3-2133M-result
run_timing $path/devices/DDR3-2133M.txt 14 10 $path/results/DDR3-2133M-result

# DDR3-2133N
run_timing $path/devices/DDR3-2133N.txt 14 10 $path/results/DDR3-2133N-result

}

#run_all