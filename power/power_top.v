//=============================================================================
// Updated: 2026-09-06
// Power analysis harness. Wraps the synthesised fft16_project netlist under the
// RTL port names and starts VCD dumping on i_dump_en, so the recorded window is
// a single contiguous stretch of streaming and never covers the reset or the
// SPI configuration that precede it.
//=============================================================================

module power_top (
    output wire o_data,
    output wire o_spi_miso,
    input  wire i_clk,
    input  wire i_rstn,
    input  wire i_data,
    input  wire i_spi_ss_n,
    input  wire i_spi_sclk,
    input  wire i_spi_mosi,
    input  wire i_dump_en
);

wire [3:0] pad2core;
wire [1:0] core2pad;

assign pad2core   = {i_spi_mosi, i_spi_sclk, i_spi_ss_n, i_data};
assign o_data     = core2pad[0];
assign o_spi_miso = core2pad[1];

fft16_project u_fft16_project (
    .clk_i       (i_clk),
    .rst_ni      (i_rstn),
    .ui_PAD2CORE (pad2core),
    .uo_CORE2PAD (core2pad)
);

reg [4095:0] vcd_file;
reg          dumping;

initial begin
    dumping = 1'b0;
    if (!$value$plusargs("vcd=%s", vcd_file)) begin
        vcd_file = "power.vcd";
    end
end

always @(posedge i_dump_en) begin
    if (!dumping) begin
        dumping = 1'b1;
        $dumpfile(vcd_file);
        $dumpvars(0, u_fft16_project);
    end
end

endmodule
