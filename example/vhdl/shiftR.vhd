library ieee;
use ieee.std_logic_1164.all;
ENTITY shiftR IS
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
END shiftR;

ARCHITECTURE behavior OF shiftR IS
	
begin
	process( A, OP, Ci )
	begin
		S(width-2 downto 0) <= A(width-1 downto 1);
		Co <= A(0);
		case OP is
			when "110" => 			--SR0
			S(width-1) <= '0';
			when "111" => 			--SR1
			S(width-1) <= '1';
			when "010" => 			--SRX
			S(width-1) <= A(width-1);
			when "000" => 			--SRA
			S(width-1) <= Ci;
			when "100" => 			--RR
			S(width-1) <= A(0);
			when others =>
			S(width-1) <= '0';
		end case;
	end process;
end behavior;


