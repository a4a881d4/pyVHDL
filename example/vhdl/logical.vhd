library ieee;
use ieee.std_logic_1164.all;
ENTITY logical IS
	generic (
		width : integer
	);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		B: IN std_logic_VECTOR(width-1 downto 0);
		OP: IN std_logic_vector( 1 downto 0);
		S: OUT std_logic_VECTOR(width-1 downto 0)
	);
END logical;

ARCHITECTURE behavior OF logical IS

begin
	process( A, B, OP )
	begin
		case OP is
			when "00" =>
				S<=B;
			when "01" =>
				S<=A and B;
			when "10" =>
				S<=A or B;
			when "11" =>
				S<=A xor B;
			when others =>
				null;
		end case;
	end process;
end behavior;


