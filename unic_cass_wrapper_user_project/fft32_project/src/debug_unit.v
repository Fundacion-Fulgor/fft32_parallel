module debug_unit #(
  parameter integer NB_ADDR = 7,
  parameter integer NB_DATA = 8
)(
  `ifdef USE_POWER_PINS
  inout                       VPWR,  // Common digital supply
  inout                       VGND,  // Common digital ground
  `endif
  input  wire                 clk,
  input  wire                 rst_n,
  // SPI Slave Interface
  input  wire [NB_ADDR-1:0]   spi_addr,
  /* verilator lint_off UNUSEDSIGNAL */
  input  wire [NB_DATA-1:0]   spi_wdata,
  /* verilator lint_on UNUSEDSIGNAL */
  input  wire                 spi_wr_en,
  input  wire                 spi_ss_n,
  output reg  [NB_DATA-1:0]   spi_rdata,
  // Probe Inputs
  input  wire [NB_DATA-1:0]   status_flags,
  input  wire [NB_DATA-1:0]   error_flags,
  input  wire [NB_DATA-1:0]   cnt_inputs,
  input  wire [NB_DATA-1:0]   cnt_outputs,
  input  wire [NB_DATA-1:0]   last_out_re,
  input  wire [NB_DATA-1:0]   last_out_im,
  input  wire [NB_DATA-1:0]   mid_data_re,
  // Control Outputs

  output reg  [2:0] sys_config
);

// Address Map
localparam [NB_ADDR-1:0] ADDR_STATUS_FLAGS = 'h00;
localparam [NB_ADDR-1:0] ADDR_ERROR_FLAGS = 'h01;
localparam [NB_ADDR-1:0] ADDR_CNT_INPUTS = 'h02;
localparam [NB_ADDR-1:0] ADDR_CNT_OUTPUTS = 'h03;
localparam [NB_ADDR-1:0] ADDR_LAST_OUT_RE = 'h04;
localparam [NB_ADDR-1:0] ADDR_LAST_OUT_IM = 'h05;
localparam [NB_ADDR-1:0] ADDR_MID_DATA_RE = 'h06;
localparam [NB_ADDR-1:0] ADDR_SYS_CONFIG = 'h10;

// CDC Synchronization (Snapshot)
wire [NB_DATA-1:0] status_flags_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_status_flags (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(status_flags),
  .data_out(status_flags_sync)
);

wire [NB_DATA-1:0] error_flags_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_error_flags (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(error_flags),
  .data_out(error_flags_sync)
);

wire [NB_DATA-1:0] cnt_inputs_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_cnt_inputs (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(cnt_inputs),
  .data_out(cnt_inputs_sync)
);

wire [NB_DATA-1:0] cnt_outputs_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_cnt_outputs (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(cnt_outputs),
  .data_out(cnt_outputs_sync)
);

wire [NB_DATA-1:0] last_out_re_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_last_out_re (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(last_out_re),
  .data_out(last_out_re_sync)
);

wire [NB_DATA-1:0] last_out_im_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_last_out_im (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(last_out_im),
  .data_out(last_out_im_sync)
);

wire [NB_DATA-1:0] mid_data_re_sync;
cdc_snapshot #(.DATA_WIDTH(NB_DATA)) u_cdc_mid_data_re (
  `ifdef USE_POWER_PINS
  .VPWR       (VPWR),
  .VGND       (VGND),
  `endif
  .clk(clk),
  .rst_n(rst_n),
  .trigger_async_n(spi_ss_n),
  .data_in(mid_data_re),
  .data_out(mid_data_re_sync)
);

always @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    sys_config <= 3'b000;
  end
  else begin
    if (spi_wr_en) begin
      /* verilator lint_off UNUSEDSIGNAL */
      case (spi_addr)
        ADDR_SYS_CONFIG: sys_config <= spi_wdata[2:0];
        default:         sys_config <= sys_config;
      endcase
      /* verilator lint_on UNUSEDSIGNAL */
    end
  end
end

always @(*) begin
  case (spi_addr)
    // Probes (Synchronized)
    ADDR_STATUS_FLAGS: spi_rdata = status_flags_sync;
    ADDR_ERROR_FLAGS: spi_rdata = error_flags_sync;
    ADDR_CNT_INPUTS: spi_rdata = cnt_inputs_sync;
    ADDR_CNT_OUTPUTS: spi_rdata = cnt_outputs_sync;
    ADDR_LAST_OUT_RE: spi_rdata = last_out_re_sync;
    ADDR_LAST_OUT_IM: spi_rdata = last_out_im_sync;
    ADDR_MID_DATA_RE: spi_rdata = mid_data_re_sync;
    // Controls (Readback)
    ADDR_SYS_CONFIG: spi_rdata = {{(NB_DATA-3){1'b0}}, sys_config};
    default:      spi_rdata = {NB_DATA{1'b0}};
  endcase
end

endmodule