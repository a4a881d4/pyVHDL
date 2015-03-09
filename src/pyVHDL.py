import sys
sys.path.insert(0,"../..")

if sys.version_info[0] >= 3:
	raw_input = input

import vhdllex
import vhdlparse

if len(sys.argv) == 2:
	data = open(sys.argv[1]).read()
	prog = vhdlparse.parse(data,debug=False)
	print prog
	
