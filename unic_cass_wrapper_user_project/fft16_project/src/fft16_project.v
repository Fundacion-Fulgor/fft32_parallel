//=============================================================================
// Updated: 2026-09-01
// Design top for the UNIC CASS user project. The port names on this module
// are fixed by user_project_wrapper.sv and config.json, so they intentionally
// keep the harness naming instead of the i_/o_ convention used below it.
//=============================================================================

module fft16_project (
    `ifdef USE_POWER_PINS
    inout              VPWR,
    inout              VGND,
    `endif
    output wire [1:0]  uo_CORE2PAD,
    input  wire        clk_i,
    input  wire        rst_ni,
    input  wire [3:0]  ui_PAD2CORE
);

top_fft16 u_top_fft16 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .o_data     (uo_CORE2PAD[0]),
    .o_spi_miso (uo_CORE2PAD[1]),
    .i_clk      (clk_i),
    .i_rstn     (rst_ni),
    .i_data     (ui_PAD2CORE[0]),
    .i_spi_ss_n (ui_PAD2CORE[1]),
    .i_spi_sclk (ui_PAD2CORE[2]),
    .i_spi_mosi (ui_PAD2CORE[3])
);

endmodule
