#!/bin/bash
# For generating data for free_check table
# Usage: ./scripts/parse.sh
cat results/* | tr '[:upper:]' '[:lower:]' | sort | uniq > combined.txt
cat combined.txt | cut -d'[' -f3 | cut -d"'" -f2 | cut -d'/' -f4 | tr '[:upper:]' '[:lower:]' | sort | uniq > ghusers.txt
echo "id,created_at,organization,count" > ~/Downloads/data.csv
for i in `cat ghusers.txt`; do echo ",,$i,$(grep -i "github.com/$i" combined.txt| cut -d'[' -f4 | sed "s/'https:\/\/github.com/\n/g" | grep -v '^$' | wc -l | tr -d ' ' )"; done >> ~/Downloads/data.csv
rm ghusers.txt combined.txt