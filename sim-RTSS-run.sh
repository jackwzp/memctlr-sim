#!/bin/sh

path=./

run_bmark(){

	outfile=$6
	rank=$7

	echo "trc-CHStone/diff-lbm" > traceFiles
	for (( i=2; i<$5; i++ ))
	do
		echo "trc-CHStone/diff-lbm" >> traceFiles
		#if [ `echo "$i % 2" | bc` -eq 0 ]; then
		#	echo "trc-CHStone/diff-membomb-rdwr" >> traceFiles
		#else
		#	echo "trc-CHStone/diff-membomb-wrrd" >> traceFiles
		#fi
	done
	echo "trc-CHStone/$1" >> traceFiles

	bank=$(echo "$5 / $rank" |bc)
	echo $bank

	./sim-RTSS.py traceFiles $2 $3 $4 -c $5 -b $bank -r $rank >> $outfile


}


run_timing(){

	outfile=$4
	echo "======RL:$2, WL:$3======" >> $outfile

	for core in 4 16
	do
		echo "*****C: $core****" >> $outfile
		for rank in 1 2 4
		do
			echo "--R: $rank--" >> $outfile

			run_bmark diff-adpcm $1 $2 $3 $core $4 $rank
			run_bmark diff-aes $1 $2 $3 $core $4 $rank
			run_bmark diff-bf $1 $2 $3 $core $4 $rank
			run_bmark diff-gsm $1 $2 $3 $core $4 $rank
			run_bmark diff-jpeg $1 $2 $3 $core $4 $rank
			run_bmark diff-mips $1 $2 $3 $core $4 $rank
			run_bmark diff-motion $1 $2 $3 $core $4 $rank
			run_bmark diff-sha $1 $2 $3 $core $4 $rank
			run_bmark diff-dfadd $1 $2 $3 $core $4 $rank
			run_bmark diff-dfdiv $1 $2 $3 $core $4 $rank
			run_bmark diff-dfmul $1 $2 $3 $core $4 $rank
			run_bmark diff-dfsin $1 $2 $3 $core $4 $rank
		done
	done

}
run_timing $path/devices/DDR3-1333H.txt 9 7 $path/results/DDR3-1333H-result-$rank

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