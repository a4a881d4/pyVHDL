-- packet_splitter.vhd: Packet splitter architecture
-- Copyright (C) 2006 CESNET
-- Author(s): Martin Kosek <kosek@liberouter.org>
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
-- $Id: packet_splitter.vhd 3977 2008-07-24 16:42:08Z xrehak5 $
--

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

-- ----------------------------------------------------------------------------
--                            Entity declaration
-- ----------------------------------------------------------------------------
entity PACKET_SPLITTER is
   generic(
      -- should be multiple of 8: only 8,16,32 supported
      DATA_WIDTH     : integer;
      -- number of output interfaces: only 2,4,8,16 supported
      OUTPUT_COUNT   : integer;
      -- determine whether are we connectiong to old HFEs which don't fully 
      -- support command protocol
      OLD_HFE        : boolean := false
   );
   port(
      CLK            : in std_logic;
      RESET          : in std_logic;

      -- input interface
      DATA_IN        : in  std_logic_vector(DATA_WIDTH-1 downto 0);
      CMD_IN         : in  std_logic_vector((DATA_WIDTH/8)-1 downto 0);
      SRC_RDY_IN     : in  std_logic;
      DST_RDY_IN     : out std_logic;
      
      -- output interface
      DATA_OUT       : out std_logic_vector((DATA_WIDTH*OUTPUT_COUNT)-1 
                                                                  downto 0);
      CMD_OUT        : out std_logic_vector(((DATA_WIDTH/8)*OUTPUT_COUNT)-1 
                                                                  downto 0);
      SRC_RDY_OUT    : out std_logic_vector(OUTPUT_COUNT-1 downto 0);
      DST_RDY_OUT    : in  std_logic_vector(OUTPUT_COUNT-1 downto 0)
   );
end entity PACKET_SPLITTER;

-- ----------------------------------------------------------------------------
--                      Architecture declaration
-- ----------------------------------------------------------------------------
architecture full of PACKET_SPLITTER is

   -- ------------------ Constants declaration --------------------------------
   constant STATUS_WIDTH         : integer := 4;
   constant ITEM_COUNT           : integer := 2048 / DATA_WIDTH;
   
   -- ------------------ Components declaration -------------------------------
   component PS_CONTROL_UNIT is
      generic(
         DATA_WIDTH     : integer;
         OUTPUT_COUNT   : integer;
         STATUS_WIDTH   : integer;
         OLD_HFE        : boolean
      );
      port(
         CLK            : in std_logic;
         RESET          : in std_logic;

         -- IBUF interface
         IBUF_RD        : out std_logic;
         IBUF_DV        : in  std_logic;
         IBUF_DO        : in  std_logic_vector(DATA_WIDTH-1 downto 0);
         IBUF_CMD       : in  std_logic_vector((DATA_WIDTH/8)-1 downto 0);
      
         -- SmartFIFOs' interface
         SFIFO_RD       : in  std_logic_vector(OUTPUT_COUNT-1 downto 0);
         SFIFO_DV       : out std_logic_vector(OUTPUT_COUNT-1 downto 0);
         SFIFO_DO       : out std_logic_vector(DATA_WIDTH-1 downto 0);
         SFIFO_CMD      : out std_logic_vector((DATA_WIDTH/8)-1 downto 0);
         SFIFO_STATUS   : in  std_logic_vector((OUTPUT_COUNT*STATUS_WIDTH)-1 
                                                                     downto 0)
      );
   end component PS_CONTROL_UNIT;
   
   component PS_SMART_FIFO is
      generic(
         DATA_WIDTH     : integer;
         STATUS_WIDTH   : integer;
         ITEM_COUNT     : integer
      );
      port(
         CLK            : in  std_logic;
         RESET          : in  std_logic;

         -- IBUF interface
         IBUF_DO        : in  std_logic_vector(DATA_WIDTH-1 downto 0);
         IBUF_CMD       : in  std_logic_vector((DATA_WIDTH/8)-1 downto 0);
         IBUF_DV        : in  std_logic;
         IBUF_RD        : out std_logic;
         IBUF_STATUS    : out std_logic_vector(STATUS_WIDTH-1 downto 0);
      
         -- HFE interface
         HFE_DO         : out std_logic_vector(DATA_WIDTH-1 downto 0);
         HFE_CMD        : out std_logic_vector((DATA_WIDTH/8)-1 downto 0);
         HFE_DV         : out std_logic;
         HFE_RD         : in  std_logic
      );
   end component PS_SMART_FIFO;
   
   -- ------------------ Signals declaration ----------------------------------

   -- Control Unit interface signals
   signal cu_sfifo_rd      : std_logic_vector(OUTPUT_COUNT-1 downto 0);
   signal cu_sfifo_dv      : std_logic_vector(OUTPUT_COUNT-1 downto 0);
   signal cu_sfifo_do      : std_logic_vector(DATA_WIDTH-1 downto 0);
   signal cu_sfifo_cmd     : std_logic_vector((DATA_WIDTH/8)-1 downto 0);
   signal cu_sfifo_status  : std_logic_vector((OUTPUT_COUNT*STATUS_WIDTH)-1 
                                                                     downto 0);

   -- SFIFO output
   signal sfifo_hfe_rd     : std_logic_vector(OUTPUT_COUNT-1 downto 0);
   signal sfifo_hfe_dv     : std_logic_vector(OUTPUT_COUNT-1 downto 0);
   signal sfifo_hfe_do     : std_logic_vector((DATA_WIDTH*OUTPUT_COUNT)-1
                                                                  downto 0);
   signal sfifo_hfe_cmd    : std_logic_vector(((DATA_WIDTH/8)*OUTPUT_COUNT)-1
                                                                  downto 0);

begin

   -- ------------------ Directly mapped signals ------------------------------
   sfifo_hfe_rd   <= DST_RDY_OUT;
   SRC_RDY_OUT    <= sfifo_hfe_dv;
   DATA_OUT       <= sfifo_hfe_do;
   CMD_OUT        <= sfifo_hfe_cmd;

   -- mapping Control Unit
   PS_CONTROL_UNIT_I : PS_CONTROL_UNIT
      generic map(
         DATA_WIDTH     => DATA_WIDTH,
         OUTPUT_COUNT   => OUTPUT_COUNT,
         STATUS_WIDTH   => STATUS_WIDTH,
         OLD_HFE        => OLD_HFE
      )
      port map(
         CLK            => CLK,
         RESET          => RESET,

         -- IBUF interface
         IBUF_RD        => DST_RDY_IN,
         IBUF_DV        => SRC_RDY_IN,
         IBUF_DO        => DATA_IN,
         IBUF_CMD       => CMD_IN,
     
         -- SmartFIFOs' interface
         SFIFO_RD       => cu_sfifo_rd,
         SFIFO_DV       => cu_sfifo_dv,
         SFIFO_DO       => cu_sfifo_do,
         SFIFO_CMD      => cu_sfifo_cmd,
         SFIFO_STATUS   => cu_sfifo_status
      );

   -- generate Smart FIFOs ----------------------------------------------------
   GEN_SFIFO: for i in 0 to OUTPUT_COUNT-1 generate

      PS_SMART_FIFO_I : PS_SMART_FIFO
         generic map(
            DATA_WIDTH     => DATA_WIDTH,
            STATUS_WIDTH   => STATUS_WIDTH,
            ITEM_COUNT     => ITEM_COUNT
         )
         port map(
            CLK            => CLK,
            RESET          => RESET,

            -- IBUF interface
            IBUF_DO        => cu_sfifo_do,
            IBUF_CMD       => cu_sfifo_cmd,
            IBUF_DV        => cu_sfifo_dv(i),
            IBUF_RD        => cu_sfifo_rd(i),
            IBUF_STATUS    => 
               cu_sfifo_status((i+1)*STATUS_WIDTH-1 downto i*STATUS_WIDTH),
      
            -- HFE interface
            HFE_DO         => 
               sfifo_hfe_do(((i+1)*DATA_WIDTH)-1 downto i*DATA_WIDTH),
            HFE_CMD        => 
               sfifo_hfe_cmd(((i+1)*(DATA_WIDTH/8))-1 downto i*(DATA_WIDTH/8)),
            HFE_DV         => sfifo_hfe_dv(i),
            HFE_RD         => sfifo_hfe_rd(i)
       );

   end generate;

end architecture full;
