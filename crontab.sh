#!/bin/bash
# chmod 755
# Every 24 hours - 0 6 * * * /path/to/script.sh
ulimit -n 10256
cd supplyshark
python supplyshark.py --app