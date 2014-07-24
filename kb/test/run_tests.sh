#!/bin/bash
FILES=test_*.py
for f in $FILES
do 
	echo "Running $f...";
	python $f;
done
