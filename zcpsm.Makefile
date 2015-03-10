
vhdl = example/vhdl/zcpsm.vhd \
	example/vhdl/addsub.vhd \
	example/vhdl/logical.vhd \
	example/vhdl/pcStack.vhd \
	example/vhdl/shiftL.vhd \
	example/vhdl/shiftR.vhd \
	example/vhdl/stackP.vhd \
	example/vhdl/zheap.vhd \
	example/vhdl/addc.vhd
	
dot :
	python vhdl-dot/vhdl-dot.py ${vhdl}

xml : 
	python vhdlverif/vhd2xml.py ${vhdl}