#!/usr/bin/env python
"""
Run all scripts in the current directory that match the given string, in
alphabetical order.

        ./rerun.py 'etherpad*'

will run all lines within . that start with "etherpad".
"""

import sys
import glob
from common import *

if len(sys.argv) != 2:
    print "Requires exactly one argument: a glob of scripts to run."
    sys.exit(1)

filenames = glob.glob(os.path.join(os.path.dirname(__file__), sys.argv[1]))
filenames.sort()

for filename in filenames:
    script(filename)
