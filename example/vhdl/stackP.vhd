library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
-- pragma translate_off
--library synplify;
--use synplify.attributes.all;
-- pragma translate_on


entity StackP is
	generic (
		width : integer
	);
	port(
		reset:		in std_logic;
		en:		in std_logic;
		clk:		in std_logic;
		pop_push:	in std_logic;
		addr:		out std_logic_vector(width-1 downto 0)
	);
end StackP;

architecture behavior of StackP is
signal count : std_logic_vector( width-1 downto 0 ):=(others=>'0');
signal updown : std_logic_vector( width-1 downto 0 ):=(others=>'0');
begin
updown<=count+1 when pop_push='1' else count-1;
addr<=updown when pop_push='1' else count;

process(clk,reset)
begin		 
	if reset = '1' then
		count <= (others=>'0');
	elsif rising_edge(clk) then
		if en='1' then
			count<=updown;
		end if;
	end if;
end process;
end behavior;
