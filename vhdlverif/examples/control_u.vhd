--
-- control_u.vhd: Edit engine control unit
-- Copyright (C) 2003 CESNET
-- Author(s): Martinek Tomas martinek@liberouter.org
--
-- Redistribution and use in source and binary forms, with or without
-- modification, are permitted provided that the following conditions
-- are met:
-- 1. Redistributions of source code must retain the above copyright
--    notice, this list of conditions and the following disclaimer.
-- 2. Redistributions in binary form must reproduce the above copyright
--    notice, this list of conditions and the following disclaimer in
--    the documentation and/or other materials provided with the
--    distribution.
-- 3. Neither the name of the Company nor the names of its contributors
--    may be used to endorse or promote products derived from this
--    software without specific prior written permission.
--
-- This software is provided ``as is'', and any express or implied
-- warranties, including, but not limited to, the implied warranties of
-- merchantability and fitness for a particular purpose are disclaimed.
-- In no event shall the company or contributors be liable for any
-- direct, indirect, incidental, special, exemplary, or consequential
-- damages (including, but not limited to, procurement of substitute
-- goods or services; loss of use, data, or profits; or business
-- interruption) however caused and on any theory of liability, whether
-- in contract, strict liability, or tort (including negligence or
-- otherwise) arising in any way out of the use of this software, even
-- if advised of the possibility of such damage.
--
-- $Id: control_u.vhd 5566 2008-09-10 13:37:34Z xrehak5 $
--
-- TODO:
-- - test for chain Edit Parameters
-- - LDOP with adder constant
--
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.std_logic_unsigned.all;
use IEEE.std_logic_arith.all;

-- -------------------- Note only for vericators ------------------------------
-- ASSERT (1)
-- 

-- ----------------------------------------------------------------------------
--                        Entity declaration
-- ----------------------------------------------------------------------------
entity control_u is
   port (
      CLK           : in  std_logic;
      RESET         : in  std_logic;
      EN            : in  std_logic;

      ---------------------- FSM control signals --------------------
      -- fsm memory
      FSM_DI        : in std_logic_vector(18 downto 0);
      FSM_ADDR      : in std_logic_vector(3 downto 0);
      FSM_WE        : in std_logic;

      -- PQ interface
      PQ_REQ        : out std_logic;
      PQ_ACK        : in  std_logic;

      -- DRAM and SSRAM interface
      ADDR_WE       : out std_logic;
      MX_ADDR_LH    : out std_logic;

      DRAM_START    : out std_logic;
      DRAM_PP_READY : in  std_logic;
      DRAM_FINISH   : in  std_logic;

      SSRAM_REQ     : out std_logic;
      SSRAM_ACK     : in  std_logic;

      -- PD Address banks
      WR_BANK       : out std_logic;
      RD_BANK       : out std_logic;

      ------------------ Instruction pipeline signals --------------------
      -- IM, EP, PP interface
      IM_ADDR       : out std_logic_vector(9 downto 0);
      IM_DATA       : in  std_logic_vector(15 downto 0);
      IM_EN         : out std_logic;

      EP_ADDR       : out std_logic_vector(3 downto 0);
      EP_DATAIN     : in  std_logic_vector(15 downto 0);

      PP_ADDR       : out std_logic_vector(3 downto 0);
      PP_DATAIN     : in  std_logic_vector(15 downto 0);

      -- Decoded signals
      OUT_PTR       : out std_logic_vector(15 downto 0);
      END_PTR       : out std_logic_vector(15 downto 0);
      OUT_PTR_WE    : out std_logic;
      END_PTR_WE    : out std_logic;

      SU_STR_PTR    : out std_logic_vector(15 downto 0);
      SU_REF_PTR    : out std_logic_vector(15 downto 0);
      SU_SIZE       : out std_logic_vector(7 downto 0);
      SU_ADD_C      : out std_logic_vector(7 downto 0);
      SU_MARK_DATA  : out std_logic_vector(1 downto 0);

      SU_BUSY       : in std_logic;
      SU_EXE        : out std_logic;

      SU_PD_EP      : out std_logic;
      SU_SIZE_REF   : out std_logic;
      SU_OP_UPDATE  : out std_logic;
      SU_ALU_OPER   : out std_logic;
      SU_ALU_CARRY  : out std_logic;
      SU_MARK       : out std_logic;

      MX_OUT_PTR    : out std_logic;
      MX_EP_PD_DATA : out std_logic;
      MX_EP_ADDR    : out std_logic;
      MX_STR_PTR    : out std_logic
   );
end entity control_u;

-- ----------------------------------------------------------------------------
--                      Architecture declaration
-- ----------------------------------------------------------------------------
architecture behavioral of control_u is
   type t_state is (S1, S2);
   signal state : t_state;

   signal addr_cnt     : std_logic_vector(9 downto 0);
   signal addr_cnt_clr : std_logic;
   signal addr_cnt_ld  : std_logic;
   signal nxto_addr    : std_logic_vector(9 downto 0);

   signal fsm_pipe_clr : std_logic;
   signal pipe_ce      : std_logic;
   signal pipe_clr     : std_logic;

   signal ir           : std_logic_vector(15 downto 0);
   signal dc_control   : std_logic_vector(10 downto 0);
   signal ops_dc       : std_logic_vector(9 downto 0);
   signal ops_pp       : std_logic_vector(15 downto 0);
   signal ops_ir       : std_logic_vector(12 downto 0);
   signal mx_size      : std_logic;
   signal mx_start     : std_logic;

   signal mx_nxto      : std_logic;
   signal nxto_cnt     : std_logic_vector(3 downto 0);
   signal nxto_cnt_ce  : std_logic;
   signal nxto_cnt_clr : std_logic;

   signal send_oper    : std_logic;
   signal send_exe     : std_logic;
   signal nxto_exe     : std_logic;
--   signal r_nxto_exe : std_logic;
   signal nxpk_exe : std_logic;
   signal send_finish : std_logic;
   signal spde_exe : std_logic;
   signal addr_cnt_ce : std_logic;

begin

-- ----------------------------------------------------------------------------
--                               FSM
-- ----------------------------------------------------------------------------
CU_FSM : entity work.control_u_fsm
port map(
   CLK           => CLK,
   RESET         => RESET,
   EN            => EN,

   -- fsm memory
   FSM_DI        => FSM_DI,
   FSM_ADDR      => FSM_ADDR,
   FSM_WE        => FSM_WE,

   -- input test signls
   PQ_ACK        => PQ_ACK,
   SSRAM_ACK     => SSRAM_ACK,
   DRAM_PP_READY => DRAM_PP_READY,
   DRAM_FINISH   => send_finish,
   NEXT_PACKET   => nxpk_exe,

      -- output control signals
   PQ_REQ       => PQ_REQ,
   MX_ADDR_LH   => MX_ADDR_LH,
   ADDR_WE      => ADDR_WE,
   DRAM_START   => DRAM_START,
   SSRAM_REQ    => SSRAM_REQ,
   PIPE_CLR     => fsm_pipe_clr,
   WR_BANK      => WR_BANK,
   RD_BANK      => RD_BANK
);

-- ----------------------------------------------------------------------------
--                        Instruction PIPELINE
-- ----------------------------------------------------------------------------

addr_cnt_clr <= fsm_pipe_clr or (not RESET);
addr_cnt_ce <= pipe_ce or nxto_exe;
addr_cnt_ld  <= nxto_exe;
nxto_cnt_clr <= fsm_pipe_clr or (not RESET);

pipe_clr     <= fsm_pipe_clr or nxto_exe;
pipe_ce      <= (not SU_BUSY) and (not send_exe) and (not nxpk_exe);

IM_ADDR      <= "0000000000" when (pipe_clr = '1') else addr_cnt;
IM_EN        <= pipe_ce;

-- address counter
process(CLK, addr_cnt_clr)
begin
   if (addr_cnt_clr = '1') then
      addr_cnt <= (others => '0');
   elsif (CLK'event AND CLK = '1') then
      if (addr_cnt_ce = '1') then
         if (addr_cnt_ld = '1') then
            addr_cnt <= nxto_addr;
         else
            addr_cnt <= addr_cnt + 1;
         end if;
      end if;
   end if;
end process;

-- ir register
process(RESET, CLK)
begin
   if (RESET = '0') then
      ir <= (others => '0');
   elsif (CLK'event AND CLK = '1') then
      if (pipe_clr = '1') then
         ir <= (others => '0');
      elsif (pipe_ce = '1') then
         ir <= IM_DATA(15 downto 0);
      end if;
   end if;
end process;

-- decoder
process(ir)
begin
   case ir(2 downto 0) is
   when "000" =>
      case ir(14 downto 12) is
      when "100" =>  dc_control <= "10000100000";      -- SPDU PPAddr, OPUp             000PPPPxxxxx001U
      when "010" =>  dc_control <= "10001100000";      -- SPDE OPUp                     000xxxxxxxxx010U
      when "110" =>  dc_control <= "00010000000";      -- LDEN PPAddr                   000PPPPxxxxx011x
      when "001" =>  dc_control <= "00000000010";      -- MARK Const                    000xxxxCCxxx100x
      when "101" =>  dc_control <= "01000000000";      -- NXPK                          000xxxxxxxxx101x
      when others => dc_control <= "00000000000";
      end case;
   when "100" =>  dc_control <= "10000110000";         -- SPDP PPAddr, Size, OPUp       001PPPPSSSSSSSSU
   when "010" =>  dc_control <= "10000010000";         -- SPEP EPAddr, Size, OPUp       010PPPPSSSSSSSSU
   when "110" =>  dc_control <= "10000111000";         -- SAPB PPAddr, Const, OPUp      011PPPPCCCCCCCCU
   when "001" =>  dc_control <= "10000111100";         -- SAPC PPAddr, Const, OPUp      100PPPPCCCCCCCCU
   when "101" =>  dc_control <= "00100000000";         -- LDOP PPAddr, Const            101PPPPCCCCCCCCx
   when "111" =>  dc_control <= "00000000001";         -- NXTO                          111xxxxxxxxxxxxx
   when others => dc_control <= "00000000000";
   end case;
end process;

-- ----------------------------------------------------------------------------
-- Next Options part

-- nxto counter
process(CLK, nxto_cnt_clr)
begin
   if (nxto_cnt_clr = '1') then
      nxto_cnt <= (others => '0');
   elsif (CLK'event AND CLK = '1') then
      if (nxto_cnt_ce = '1') then
         nxto_cnt <= nxto_cnt + 1;
      end if;
   end if;
end process;

mx_nxto <= ir(0) and ir(1) and ir(2); -- opcode == "111"
PP_ADDR <= ir(6 downto 3) when mx_nxto = '0' else "11" & nxto_cnt(3 downto 2);
nxto_addr   <= EP_DATAIN(9 downto 0);
nxto_cnt_ce <= nxto_exe;


-- r_nxto_exe register - save nxto_exe signal for a period
--process(RESET, CLK)
--begin
--   if (RESET = '0') then
--      r_nxto_exe <= '0';
--   elsif (CLK'event AND CLK = '1') then
--      r_nxto_exe <= nxto_exe;
--   end if;
--end process;


-- ep addess multiplexor
with nxto_cnt(1 downto 0) select
   EP_ADDR <= '1' & ops_pp(2 downto 0)   when "00",
              '1' & ops_pp(6 downto 4)   when "01",
              '1' & ops_pp(10 downto 8)  when "10",
              '1' & ops_pp(14 downto 12) when "11",
              "1000"               when others;

-- ----------------------------------------------------------------------------
-- ops_pp registers
process(RESET, CLK)
begin
   if (RESET = '0') then
      ops_pp <= (others => '0');
   elsif (CLK'event AND CLK = '1') then
      if (pipe_clr = '1') then
         ops_pp <= (others => '0');
      elsif (pipe_ce = '1') then
         ops_pp <= PP_DATAIN;
      end if;
   end if;
end process;

-- ops_ir register
process(RESET, CLK)
begin
   if (RESET = '0') then
      ops_ir <= (others => '0');
   elsif (CLK'event AND CLK = '1') then
      if (pipe_clr = '1') then
         ops_ir <= (others => '0');
      elsif (pipe_ce = '1') then
         ops_ir <= ir(15 downto 3);
      end if;
   end if;
end process;

-- ops_dc register
process(RESET, CLK)
begin
   if (RESET = '0') then
      ops_dc <= "1000000000";  -- next packet signal is active
   elsif (CLK'event AND CLK = '1') then
      if (pipe_clr = '1') then
         ops_dc <= (others => '0');
      elsif (pipe_ce = '1') then
         ops_dc <= dc_control(9 downto 0);
      end if;
   end if;
end process;

-- ----------------------------------------------------------------------------
-- send operation FSM

fsm_logic : process(CLK, RESET)
begin
   if (RESET = '0') then
      state <= S1;
      send_exe <= '0';
   elsif (CLK'event and CLK='1') then
      send_exe <= '0';
      case state is
      when S1 =>
         state <= S1;
         send_exe <= send_oper and (not SU_BUSY) and (not nxto_exe);
         if (SU_BUSY='1') then
            state <= S2;
         end if;
      when S2 =>
         state <= S2;
         if (SU_BUSY='0') then
            state <= S1;
         end if;
      when others => state <= S1;
      end case;
   end if;
end process;

-- output_logic : process(state, send_oper, SU_BUSY)
-- begin
--    send_exe <= '0';
--    case state is
--       when S1 =>     send_exe <= send_oper and (not SU_BUSY);
--       when S2 =>     send_exe <= '0';
--       when others => send_exe <= '0';
--    end case;
-- end process;

-- ----------------------------------------------------------------------------
-- mapping of output signals
mx_start      <= ops_dc(5); -- same as SU_PD_EP
mx_size       <= ops_dc(3); -- same as SU_ALU_OPER

MX_OUT_PTR    <= ops_dc(8); -- same as SU_EXE OR ~OUT_PTR_WE
MX_EP_PD_DATA <= ops_dc(5); -- same as SU_PD_EP
MX_EP_ADDR    <= ops_dc(0); -- same as NXTO
MX_STR_PTR    <= ops_dc(4); -- same as SU_SIZE_REF

nxpk_exe      <= ops_dc(9); -- for NXPK
OUT_PTR_WE    <= ops_dc(8); -- for LDOP
END_PTR_WE    <= ops_dc(7); -- for LDEN
spde_exe      <= ops_dc(6); -- for SPDE

SU_PD_EP      <= ops_dc(5); -- for SPEP
SU_SIZE_REF   <= ops_dc(4); -- for SPDU, SPDE
SU_ALU_OPER   <= ops_dc(3); -- for SAPB, SAPC
SU_ALU_CARRY  <= ops_dc(2); -- for SAPC
SU_MARK       <= ops_dc(1); -- for MARK
nxto_exe      <= ops_dc(0); -- for NXTO

send_oper     <= dc_control(10); -- for all send operation
send_finish   <= spde_exe and DRAM_FINISH;
OUT_PTR       <= ops_pp;
END_PTR       <= ops_pp;
SU_EXE        <= send_exe;

SU_STR_PTR    <= ops_pp when mx_start='0' else "000000000000" & ops_ir(3 downto 0);
SU_REF_PTR    <= ops_pp;
SU_SIZE       <= ops_ir(11 downto 4) when mx_size='0' else "00000001";
SU_ADD_C      <= ops_ir(11 downto 4);
SU_MARK_DATA  <= ops_ir(5 downto 4);
SU_OP_UPDATE  <= ops_ir(12);

end architecture behavioral;
-- ----------------------------------------------------------------------------

