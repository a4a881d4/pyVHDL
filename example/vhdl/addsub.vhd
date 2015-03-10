library ieee;
use ieee.std_logic_1164.all;
ENTITY addsub IS
	generic (
		width : integer
	);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		B: IN std_logic_VECTOR(width-1 downto 0);
		C_IN: IN std_logic;
		C_EN: IN std_logic;
		C_OUT: OUT std_logic;
		sub: IN std_logic;
		S: OUT std_logic_VECTOR(width-1 downto 0)
	);
END addsub;

ARCHITECTURE behavior OF addsub IS
component ADDC is
	generic (
		width : integer
	);
	port(
		opa:		in std_logic_vector(width-1 downto 0);
		opb:		in std_logic_vector(width-1 downto 0);
		ci:		in std_logic;
		sum:		out std_logic_vector(width-1 downto 0);
		co:		out std_logic
		);
end component;

signal B_int : std_logic_vector( width-1 downto 0 ):=(others=>'0');
signal ci,co : std_logic:='0';
begin
	B_int<=B when sub='0' else (not B);
	ci<=(C_In and C_EN) xor sub;
	C_out<=co xor sub;
	
ADDC_a : ADDC
	generic map (
		width => width )
	port map (
		opa => A,
		opb => B_int,
		Ci => ci,
		co => co,
		sum => S
		);
end behavior;


