#!/bin/sh

path=./trc-CHStone

outfile=$1
bomb=$path/diff-membomb

run_bmark(){

	if [ "$core" -eq 4 ]; then
		./sim-AMC.py $2 $1 $bomb $bomb $bomb >> $outfile
	else
		./sim-AMC.py $2 $1 $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb $bomb>> $outfile
	fi

}


run(){

	for core in 4 16
	do
		echo "--C: $core--" >> $outfile

		run_bmark $path/diff-adpcm $core 
		run_bmark $path/diff-aes $core
		run_bmark $path/diff-bf $core
		run_bmark $path/diff-gsm $core
		run_bmark $path/diff-jpeg $core
		run_bmark $path/diff-mips $core
		run_bmark $path/diff-motion $core
		run_bmark $path/diff-sha $core
		run_bmark $path/diff-dfadd $core
		run_bmark $path/diff-dfdiv $core
		run_bmark $path/diff-dfmul $core
		run_bmark $path/diff-dfsin $core

	done

}

run