library ieee;
use ieee.std_logic_1164.all;
ENTITY shiftL IS
	generic (
		width : integer	:= 8
		);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		Ci: In std_logic;
		OP: IN std_logic_vector( 2 downto 0);
		S: OUT std_logic_VECTOR(width-1 downto 0);
		Co: out std_logic
		);
END shiftL;

ARCHITECTURE behavior OF shiftL IS
	
begin
	process( A, OP, Ci )
	begin
		S(width-1 downto 1) <= A(width-2 downto 0);
		Co <= A(width-1);
		case OP is
			when "110" => 			--SLO
			S(0) <= '0';
			when "111" => 			--SL1
			S(0) <= '1';
			when "100" => 			--SLX
			S(0) <= A(0);
			when "000" => 			--SLA
			S(0) <= Ci;
			when "010" => 			--RL
			S(0) <= A(width-1);
			when others =>
			S(0) <= '0';
		end case;
	end process;
end behavior;


