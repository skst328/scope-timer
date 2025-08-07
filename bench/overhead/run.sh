#!/bin/sh

python gen_workload.py

python bench.py --mode on -n 5
python bench.py --mode off -n 5
python bench.py --mode native -n 5

echo ""
echo "---"
echo ""

cat comp_results.txt
