library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
-- pragma translate_off
--library synplify;
--use synplify.attributes.all;
-- pragma translate_on


entity ADDC is
	generic (
		width : integer
	);
	port(
		opa:		in std_logic_vector(width-1 downto 0);
		opb:		in std_logic_vector(width-1 downto 0);
		ci:		in std_logic;
		sum:	out	std_logic_vector(width-1 downto 0);
		co:		out std_logic
		);
end ADDC;

architecture behavior of ADDC is
begin
process(opa,opb,ci)
variable res:std_logic_vector( width downto 0 ):=(others=>'0');
begin		 
	res:=('0'&opa)+('0'&opb)+ci;
	sum<=res(width-1 downto 0);
	co<=res(width);
end process;
end behavior;
