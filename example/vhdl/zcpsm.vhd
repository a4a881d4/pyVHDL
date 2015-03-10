--=============================================================================
-- Project:		ZCPSM 
-- Copyright: 	GPLv2
-- Author: 		Zhao Ming
-- Revision:  	V1.0
-- Last revised:  
-- Workfile: 	zcpsm.vhd
-- Archive: 
-------------------------------------------------------------------------------
-- Description:
-- 
-- 
-------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.std_logic_unsigned.all;


entity zcpsm is
	Port (     
		address 	: 	out std_logic_vector(11 downto 0);
		instruction :	in std_logic_vector(17 downto 0);
		port_id 	:	out std_logic_vector(7 downto 0);
		write_strobe :	out std_logic;
		out_port 	:	out std_logic_vector(7 downto 0);
		read_strobe :	out std_logic;
		in_port 	:	in std_logic_vector(7 downto 0);
		interrupt 	:	in std_logic;
		reset 		:	in std_logic;
		clk 		:	in std_logic);
end zcpsm;


architecture fast of zcpsm is 
----------------------------------------------------------------
--	To inprove preformace, decode instruction two step
--      Heap address is connect direct to instruction 
--	components:
--		Heap:	  	controling s00~s1F's read two(asychronous), write one
--					every time(synchronous)
--		Stack:		program stack, push and pop the addresses of instructions
--		Clk_Gen:	output proper clk signal to control other blocks
----------------------------------------------------------------

   
	component zHeap
		port (	 
			reset	: in std_logic;
			addra: 		in std_logic_vector(4 downto 0);
			dia: 		in std_logic_vector(7 downto 0);
			wea:		in std_logic;
			clk:		in std_logic;
			clk_en:		in std_logic;
			addrb: 		in std_logic_vector(4 downto 0);
			doa:		out std_logic_vector(7 downto 0);
			dob:		out std_logic_vector(7 downto 0)
			);
	end component;

	component pcstack 
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
	end component;

	component addsub 
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
	END component;
	component logical 
	generic (
		width : integer
	);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		B: IN std_logic_VECTOR(width-1 downto 0);
		OP: IN std_logic_vector( 1 downto 0);
		S: OUT std_logic_VECTOR(width-1 downto 0)
	);
	END component;
	
	component shiftL 
	generic (
		width : integer
	);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		Ci: In std_logic;
		OP: IN std_logic_vector( 2 downto 0);
		S: OUT std_logic_VECTOR(width-1 downto 0);
		Co: out std_logic
	);
	END component;
	
	component shiftR 
	generic (
		width : integer
	);
	port (
		A: IN std_logic_VECTOR(width-1 downto 0);
		Ci: In std_logic;
		OP: IN std_logic_vector( 2 downto 0);
		S: OUT std_logic_VECTOR(width-1 downto 0);
		Co: out std_logic
	);
	END component;

	
	--clock signals
	
	--heap signals
	signal heap_dia:	std_logic_vector(7 downto 0);
	signal heap_wea: 	std_logic;
	signal heap_addra: 	std_logic_vector(4 downto 0);
	signal heap_addrb: 	std_logic_vector(4 downto 0);
	signal heap_dob:	std_logic_vector(7 downto 0);
	signal heap_doa:	std_logic_vector(7 downto 0);
	
	
	--ALU signals
	signal alu_A:		std_logic_vector(7 downto 0);
	signal alu_B:		std_logic_vector(7 downto 0);
	signal alu_op: 		std_logic_vector(2 downto 0);
	signal shift_op: 	std_logic_vector(3 downto 0);
	signal alu_out:		std_logic_vector(7 downto 0);
	signal alu_cflag_out:	std_logic;
	signal shift_sel	: std_logic;
	
	
	--addsub signals
	signal sum_out:std_logic_vector(7 downto 0);
	signal sum_cflag_out:std_logic;
	
	--shift l signals
	signal shiftl_out:std_logic_vector(7 downto 0);
	signal shiftl_cflag_out:std_logic;
	
	--shift r signals
	signal shiftr_out:std_logic_vector(7 downto 0);
	signal shiftr_cflag_out:std_logic;
	
	--logic signals
	signal logical_out:std_logic_vector(7 downto 0);
	
	--ZC_Reg signals
	signal cflag:			std_logic;
	signal zflag:			std_logic;
	
	--PC signals	
	signal pc:		std_logic_vector(11 downto 0);
	signal nextPc:	std_logic_vector(11 downto 0);
	signal jumpEn,jumpFlag,jumpSet : std_logic;

	
	--Stack signals
	signal stack_en: 	std_logic;
	signal stack_po_pu: std_logic;
	signal stack_din:	std_logic_vector(11 downto 0);
	signal stack_dout:	std_logic_vector(11 downto 0);
	
		
	--Port_ctrl signals
	signal io_read_strobe_int: 	std_logic;
	signal io_write_strobe_int: 	std_logic;
	
	signal ins : std_logic_vector( 17 downto 0 );
	
	
begin


AHeap: zHeap 
		port map(
			reset		=> reset,
			addra		=> heap_addra, 
			dia		=> heap_dia,
			wea		=> heap_wea,
			clk		=> clk,
			clk_en		=> '0', 	-- why '0' means enable
			addrb		=> heap_addrb,
			doa		=> heap_doa,
			dob		=> heap_dob
			);

port_id	<= ins( 7 downto 0 ) when ins(12)='0' else heap_dob;
ALU_OP <= ins( 14 downto 12 ) when ins(15)='0' else ins( 2 downto 0 );
SHIFT_OP <= ins( 3 downto 0 );
ALU_A <= heap_doa;
ALU_B <= ins( 7 downto 0 ) when ins(15)='0' else heap_dob;

ALUProc:process( ALU_OP, SHIFT_OP,SHIFT_SEL,logical_out,sum_out,sum_cflag_out,shiftl_out,shiftl_cflag_out,shiftr_out,shiftr_cflag_out )
variable alu_res: std_logic_vector( 8 downto 0 );
begin
	if SHIFT_SEL='0' then
		if ALU_OP(2)='0' then
			alu_out<=logical_out;
			alu_cflag_out<='0';
		else
			alu_out<=sum_out;
			alu_cflag_out<=sum_cflag_out;
		end	if;	
	else
		if shift_op(3)='0' then
			alu_out<=shiftl_out;
			alu_cflag_out<=shiftl_cflag_out;
		else
			alu_out<=shiftr_out;
			alu_cflag_out<=shiftr_cflag_out;
		end if;
	end if;		
end process;

	

	
-- Heap address and data define
	heap_addra	<=	ins(17) & ins( 11 downto 8 );
	heap_addrb	<=	ins(16) & ins( 7 downto 4 );
	heap_dia	<=	in_port 	when io_read_strobe_int='1' 	else 
				alu_out;
				
	
--	Lock heap wea
heap_wea<='0' when ins(15 downto 13 )="100" or ins(15 downto 13 )="111"  else '1';
--	Lock Shift sel
SHIFT_SEL<='1' when ins(15 downto 12 )="1101" else '0';
--	Lock in out strobe
io_read_strobe_int<='1' when ins( 15 downto 13 )="101"  else '0';
io_write_strobe_int<='1' when ins( 15 downto 13 )="111"  else '0';
nextPc<=pc+1;	
PcProc:process(reset,clk)
begin
	if reset = '1' then
		pc<=(others=>'0');
		jumpSet<='0';
		ins<="001100000000000000";
	elsif rising_edge(clk) then
		if ins( 15 downto 13 ) ="100" then
			if     (jumpFlag='1' and ins( 12 ) = '1') -- condition jump 
			    or ( ins(12 downto 10) ="000" ) -- uncondition jump
			    or ( ins(12 downto 10) ="011" ) -- call
			    then
				pc<=ins(17 downto 16) & ins(9 downto 0);
				jumpSet<='0';	
				ins <= "001100000000000000";
			elsif ins( 12 downto 10 ) = "010" then --Return
				pc<=stack_dout;
				jumpSet<='0';
				ins <= "001100000000000000";
			else
				pc<=nextpc;
				jumpSet<='1'; 
				if jumpSet='0' then
					ins <= "001100000000000000";
				else
					ins <= instruction;
				end if;
			end if;
		else
			pc<=nextpc;
			jumpSet<='1';
			if jumpSet='0' then
				ins <= "001100000000000000";
			else
				ins <= instruction;
			end if;
		end if;
	end if;
end process;
	
secondHalfProc:process(reset,clk)
begin
	if reset = '1' then
		CFLAG <= '0';
		ZFLAG <= '0';  
		
	elsif rising_edge(clk) then
		if heap_wea='1' then
			if ALU_OP/="0000" then
				CFLAG<=alu_cflag_out;
				if alu_out="00000000" then
					ZFLAG<='1';
				else
					ZFLAG<='0';
				end if;
			end if;
		end if;
	end if;
end process;

	address<=pc;
	write_strobe<=io_write_strobe_int;
	out_port<=alu_A;
	read_strobe<=io_read_strobe_int;
	stack_din<=pc-1;

	Astack: pcstack
		generic map(
			depth => 16,
			awidth => 4,
			width => 12
			)
		port map(
			reset		=> reset,
			clk			=> clk,
			en			=> stack_en,
			pop_push	=> stack_po_pu,
			din			=> stack_din,
			dout		=> stack_dout
			);
	
	jumpFlag <= (cflag xor ins(10)) when ins(11)='1' else (zflag xor ins(10));
	    		
	stack_en <= '1' when  ins( 15 downto 13 ) ="100" and (ins( 12 downto 11 ) = "01" ) else '0';
	stack_po_pu <= '1' when ins( 10 ) = '1' else '0';
	

	 
addsub_a:addsub 
	generic map (
		width => 8
	)
	port map(
		A=>alu_A,
		B=>alu_B,
		C_IN=>cflag,
		C_EN=>ALU_OP(0),
		C_OUT=>sum_cflag_out,
		sub=>ALU_OP(1),
		S=>sum_out
	);
logical_a:logical 
	generic map (
		width => 8
	)
	port map(
		A=>alu_A,
		B=>alu_B,
		OP=>alu_op( 1 downto 0 ),
		S=>logical_out
	);
	
shiftl_a:shiftL
	generic map (
		width => 8
	)
	port map(
		A=>	alu_A,
		Ci=>CFLAG,
		OP=>shift_op( 2 downto 0 ),
		S=> shiftl_out,
		Co=>shiftl_cflag_out
	);	

shiftr_a:shiftR
	generic map (
		width => 8
	)
	port map(
		A=>	alu_A,
		Ci=>CFLAG,
		OP=>shift_op( 2 downto 0 ),
		S=> shiftr_out,
		Co=>shiftr_cflag_out
	);	


end fast;
