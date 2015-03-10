library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
-- pragma translate_off
--library synplify;
--use synplify.attributes.all;
-- pragma translate_on

entity pcstack is
	generic(
		depth:integer:=16;
		awidth:integer:=4;
		width:integer:=8
		);
	port (	
		reset	: in std_logic;
		clk:		in std_logic;
		en: 		in std_logic;
		pop_push:	in std_logic;
		din:		in std_logic_vector(width-1 downto 0);
		dout:		out std_logic_vector(width-1 downto 0)
		);
end pcstack;

architecture behavior of pcstack is
	type mem is array(0 to depth-1) of std_logic_vector(width-1 downto 0);
	signal ram: mem:=(others=>(others=>'0'));
	signal addr:std_logic_vector( awidth-1 downto 0 ):=(others=>'0');
	
	component StackP is
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
	end component;
begin

astackP:stackP
	generic map(
		width => awidth
	)
	port map(
		reset => reset,
		en => en,
		clk => clk,
		pop_push => pop_push,
		addr => addr
	);
	dout <= ram(conv_integer(addr));
	process(clk)
	begin 
		if rising_edge(clk) then
			if en='1' and pop_push='1' then
			--push stack
				ram(conv_integer(addr))<=din;
			end if;
		end if;
	end process;
end behavior;
			

	