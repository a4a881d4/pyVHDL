library IEEE;
use IEEE.STD_LOGIC_1164.all;
--use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
--library synplify;
--use synplify.attributes.all;

entity zHeap is
	port (
	reset	: in std_logic;
	addra: 		in std_logic_vector(4 downto 0);
	dia: 		in std_logic_vector(7 downto 0);
	wea:		in std_logic;
	clk:		in std_logic;
	clk_en:		in std_logic; --
	addrb: 		in std_logic_vector(4 downto 0);
	doa:		out std_logic_vector(7 downto 0);
	dob:		out std_logic_vector(7 downto 0)
	);
end zHeap;

architecture behavior of zHeap is
	type mem is array(0 to 31) of std_logic_vector(7 downto 0);
	signal heap: mem:=(others=>(others=>'0'));  
begin
	doa <= heap(conv_integer(addra));
	dob <= heap(conv_integer(addrb));
wr:
	process(clk)			 
	begin
		if rising_edge(clk) then
			if clk_en='0' then
				if wea='1' then
					heap(conv_integer(addra)) <= dia;
				end if;
			end if;
		end if;
	end process wr;
end behavior;

	
	
	