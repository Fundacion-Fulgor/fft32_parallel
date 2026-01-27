module fft32 #(
    parameter NB_DATA   = 8
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input                       i_clk,
    input                       i_clk_en,
    input                       i_rst_n,
    input                       i_inverse,
    ///////////////////// INPUTS  /////////////////////
    input                       i_valid,
    input                       i_tx_ready,
    input  signed [NB_DATA-1:0] i_data_re,
    input  signed [NB_DATA-1:0] i_data_im,
    ///////////////////// OUTPUTS /////////////////////
    output                      o_valid,
    output signed [NB_DATA-1:0] o_data_re,
    output signed [NB_DATA-1:0] o_data_im,
    output signed [NB_DATA-1:0] o_debug_mid_re
);

wire signed [NB_DATA-1:0] shift_r4_data0_re;
wire signed [NB_DATA-1:0] shift_r4_data0_im;
wire signed [NB_DATA-1:0] shift_r4_data1_re;
wire signed [NB_DATA-1:0] shift_r4_data1_im;
wire signed [NB_DATA-1:0] shift_r4_data2_re;
wire signed [NB_DATA-1:0] shift_r4_data2_im;
wire signed [NB_DATA-1:0] shift_r4_data3_re;
wire signed [NB_DATA-1:0] shift_r4_data3_im;
wire                      shift_r4_valid;
wire signed [NB_DATA-1:0] fft4_data0_re;
wire signed [NB_DATA-1:0] fft4_data0_im;
wire signed [NB_DATA-1:0] fft4_data1_re;
wire signed [NB_DATA-1:0] fft4_data1_im;
wire signed [NB_DATA-1:0] fft4_data2_re;
wire signed [NB_DATA-1:0] fft4_data2_im;
wire signed [NB_DATA-1:0] fft4_data3_re;
wire signed [NB_DATA-1:0] fft4_data3_im;
wire                      fft4_valid;
wire signed [NB_DATA-1:0] twiddle_data0_re;
wire signed [NB_DATA-1:0] twiddle_data0_im;
wire signed [NB_DATA-1:0] twiddle_data1_re;
wire signed [NB_DATA-1:0] twiddle_data1_im;
wire signed [NB_DATA-1:0] twiddle_data2_re;
wire signed [NB_DATA-1:0] twiddle_data2_im;
wire signed [NB_DATA-1:0] twiddle_data3_re;
wire signed [NB_DATA-1:0] twiddle_data3_im;
wire                      twiddle_valid;
wire signed [NB_DATA-1:0] shift_r2_ff0_data0_re;
wire signed [NB_DATA-1:0] shift_r2_ff0_data0_im;
wire signed [NB_DATA-1:0] shift_r2_ff0_data1_re;
wire signed [NB_DATA-1:0] shift_r2_ff0_data1_im;
wire signed [NB_DATA-1:0] shift_r2_ff1_data0_re;
wire signed [NB_DATA-1:0] shift_r2_ff1_data0_im;
wire signed [NB_DATA-1:0] shift_r2_ff1_data1_re;
wire signed [NB_DATA-1:0] shift_r2_ff1_data1_im;
wire signed [NB_DATA-1:0] shift_r2_ff2_data0_re;
wire signed [NB_DATA-1:0] shift_r2_ff2_data0_im;
wire signed [NB_DATA-1:0] shift_r2_ff2_data1_re;
wire signed [NB_DATA-1:0] shift_r2_ff2_data1_im;
wire signed [NB_DATA-1:0] shift_r2_ff3_data0_re;
wire signed [NB_DATA-1:0] shift_r2_ff3_data0_im;
wire signed [NB_DATA-1:0] shift_r2_ff3_data1_re;
wire signed [NB_DATA-1:0] shift_r2_ff3_data1_im;
wire                      shift_r2_ff0_valid;
wire                      shift_r2_ff1_valid;
wire                      shift_r2_ff2_valid;
wire                      shift_r2_ff3_valid;
wire signed [NB_DATA-1:0] mdc_ff0_data0_re;
wire signed [NB_DATA-1:0] mdc_ff0_data0_im;
wire signed [NB_DATA-1:0] mdc_ff0_data1_re;
wire signed [NB_DATA-1:0] mdc_ff0_data1_im;
wire signed [NB_DATA-1:0] mdc_ff1_data0_re;
wire signed [NB_DATA-1:0] mdc_ff1_data0_im;
wire signed [NB_DATA-1:0] mdc_ff1_data1_re;
wire signed [NB_DATA-1:0] mdc_ff1_data1_im;
wire signed [NB_DATA-1:0] mdc_ff2_data0_re;
wire signed [NB_DATA-1:0] mdc_ff2_data0_im;
wire signed [NB_DATA-1:0] mdc_ff2_data1_re;
wire signed [NB_DATA-1:0] mdc_ff2_data1_im;
wire signed [NB_DATA-1:0] mdc_ff3_data0_re;
wire signed [NB_DATA-1:0] mdc_ff3_data0_im;
wire signed [NB_DATA-1:0] mdc_ff3_data1_re;
wire signed [NB_DATA-1:0] mdc_ff3_data1_im;
wire                      mdc_ff0_valid;
wire                      mdc_ff1_valid;
wire                      mdc_ff2_valid;
wire                      mdc_ff3_valid;
wire                      mdc_ffx_valid;

////////////////////////////////////////////////////////////////////////////////////////////

shift_r4 #( .NB_DATA(8)) u_shift_r4 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_clk_en   (i_clk_en),
    .i_valid    (i_valid),
    .i_data_re  (i_data_re),
    .i_data_im  (i_data_im),
    .o_data0_re (shift_r4_data0_re),
    .o_data0_im (shift_r4_data0_im),
    .o_data1_re (shift_r4_data1_re),
    .o_data1_im (shift_r4_data1_im),
    .o_data2_re (shift_r4_data2_re),
    .o_data2_im (shift_r4_data2_im),
    .o_data3_re (shift_r4_data3_re),
    .o_data3_im (shift_r4_data3_im),
    .o_valid    (shift_r4_valid)
);

////////////////////////////////////////////////////////////////////////////////////////////

fft4 #( .NB_INPUT(8), .NBF_INPUT(7), .NB_OUTPUT(8), .NBF_OUTPUT(7)) u_fft4 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_enable   (i_clk_en),
    .i_valid    (shift_r4_valid),
    .i_inverse  (i_inverse),
    .i_data0_re (shift_r4_data0_re),
    .i_data0_im (shift_r4_data0_im),
    .i_data1_re (shift_r4_data1_re),
    .i_data1_im (shift_r4_data1_im),
    .i_data2_re (shift_r4_data2_re),
    .i_data2_im (shift_r4_data2_im),
    .i_data3_re (shift_r4_data3_re),
    .i_data3_im (shift_r4_data3_im),
    .o_valid    (fft4_valid),
    .o_data0_re (fft4_data0_re),
    .o_data0_im (fft4_data0_im),
    .o_data1_re (fft4_data1_re),
    .o_data1_im (fft4_data1_im),
    .o_data2_re (fft4_data2_re),
    .o_data2_im (fft4_data2_im),
    .o_data3_re (fft4_data3_re),
    .o_data3_im (fft4_data3_im)
);

////////////////////////////////////////////////////////////////////////////////////////////

twiddle_interface #( .NB_DATA(8), .NBF_DATA(7)) u_twiddle_interface (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_valid    (fft4_valid),
    .i_inverse  (i_inverse),
    .i_data0_re (fft4_data0_re),
    .i_data0_im (fft4_data0_im),
    .i_data1_re (fft4_data1_re),
    .i_data1_im (fft4_data1_im),
    .i_data2_re (fft4_data2_re),
    .i_data2_im (fft4_data2_im),
    .i_data3_re (fft4_data3_re),
    .i_data3_im (fft4_data3_im),
    .o_data0_re (twiddle_data0_re),
    .o_data0_im (twiddle_data0_im),
    .o_data1_re (twiddle_data1_re),
    .o_data1_im (twiddle_data1_im),
    .o_data2_re (twiddle_data2_re),
    .o_data2_im (twiddle_data2_im),
    .o_data3_re (twiddle_data3_re),
    .o_data3_im (twiddle_data3_im),
    .o_valid    (twiddle_valid)
);

assign o_debug_mid_re = twiddle_data0_re;

////////////////////////////////////////////////////////////////////////////////////////////

shift_r2 #( .NB_DATA(8)) u_shift_r2_fft0 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_clk_en   (i_clk_en),
    .i_valid    (twiddle_valid),
    .i_data_re  (twiddle_data0_re),
    .i_data_im  (twiddle_data0_im),
    .o_data0_re (shift_r2_ff0_data0_re),
    .o_data0_im (shift_r2_ff0_data0_im),
    .o_data1_re (shift_r2_ff0_data1_re),
    .o_data1_im (shift_r2_ff0_data1_im),
    .o_valid    (shift_r2_ff0_valid)
);

shift_r2 #( .NB_DATA(8)) u_shift_r2_fft1 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_clk_en   (i_clk_en),
    .i_valid    (twiddle_valid),
    .i_data_re  (twiddle_data1_re),
    .i_data_im  (twiddle_data1_im),
    .o_data0_re (shift_r2_ff1_data0_re),
    .o_data0_im (shift_r2_ff1_data0_im),
    .o_data1_re (shift_r2_ff1_data1_re),
    .o_data1_im (shift_r2_ff1_data1_im),
    .o_valid    (shift_r2_ff1_valid)
);

shift_r2 #( .NB_DATA(8)) u_shift_r2_fft2 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_clk_en   (i_clk_en),
    .i_valid    (twiddle_valid),
    .i_data_re  (twiddle_data2_re),
    .i_data_im  (twiddle_data2_im),
    .o_data0_re (shift_r2_ff2_data0_re),
    .o_data0_im (shift_r2_ff2_data0_im),
    .o_data1_re (shift_r2_ff2_data1_re),
    .o_data1_im (shift_r2_ff2_data1_im),
    .o_valid    (shift_r2_ff2_valid)
);

shift_r2 #( .NB_DATA(8)) u_shift_r2_fft3 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_clk_en   (i_clk_en),
    .i_valid    (twiddle_valid),
    .i_data_re  (twiddle_data3_re),
    .i_data_im  (twiddle_data3_im),
    .o_data0_re (shift_r2_ff3_data0_re),
    .o_data0_im (shift_r2_ff3_data0_im),
    .o_data1_re (shift_r2_ff3_data1_re),
    .o_data1_im (shift_r2_ff3_data1_im),
    .o_valid    (shift_r2_ff3_valid)
);

////////////////////////////////////////////////////////////////////////////////////////////

fft8 #( .NB_INPUT(8), .NBF_INPUT(7), .NB_OUTPUT(8), .NBF_OUTPUT(7)) u_fft8_mdc0 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_inverse  (i_inverse),
    .i_valid    (shift_r2_ff0_valid),
    .i_data1_r  (shift_r2_ff0_data0_re),
    .i_data1_i  (shift_r2_ff0_data0_im),
    .i_data2_r  (shift_r2_ff0_data1_re),
    .i_data2_i  (shift_r2_ff0_data1_im),
    .o_valid    (mdc_ff0_valid),
    .o_data1_r  (mdc_ff0_data0_re),
    .o_data1_i  (mdc_ff0_data0_im),
    .o_data2_r  (mdc_ff0_data1_re),
    .o_data2_i  (mdc_ff0_data1_im)
);

fft8 #( .NB_INPUT(8), .NBF_INPUT(7), .NB_OUTPUT(8), .NBF_OUTPUT(7)) u_fft8_mdc1 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_inverse  (i_inverse),
    .i_valid    (shift_r2_ff1_valid),
    .i_data1_r  (shift_r2_ff1_data0_re),
    .i_data1_i  (shift_r2_ff1_data0_im),
    .i_data2_r  (shift_r2_ff1_data1_re),
    .i_data2_i  (shift_r2_ff1_data1_im),
    .o_valid    (mdc_ff1_valid),
    .o_data1_r  (mdc_ff1_data0_re),
    .o_data1_i  (mdc_ff1_data0_im),
    .o_data2_r  (mdc_ff1_data1_re),
    .o_data2_i  (mdc_ff1_data1_im)
);

fft8 #( .NB_INPUT(8), .NBF_INPUT(7), .NB_OUTPUT(8), .NBF_OUTPUT(7)) u_fft8_mdc2 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_inverse  (i_inverse),
    .i_valid    (shift_r2_ff2_valid),
    .i_data1_r  (shift_r2_ff2_data0_re),
    .i_data1_i  (shift_r2_ff2_data0_im),
    .i_data2_r  (shift_r2_ff2_data1_re),
    .i_data2_i  (shift_r2_ff2_data1_im),
    .o_valid    (mdc_ff2_valid),
    .o_data1_r  (mdc_ff2_data0_re),
    .o_data1_i  (mdc_ff2_data0_im),
    .o_data2_r  (mdc_ff2_data1_re),
    .o_data2_i  (mdc_ff2_data1_im)
);

fft8 #( .NB_INPUT(8), .NBF_INPUT(7), .NB_OUTPUT(8), .NBF_OUTPUT(7)) u_fft8_mdc3 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_inverse  (i_inverse),
    .i_valid    (shift_r2_ff3_valid),
    .i_data1_r  (shift_r2_ff3_data0_re),
    .i_data1_i  (shift_r2_ff3_data0_im),
    .i_data2_r  (shift_r2_ff3_data1_re),
    .i_data2_i  (shift_r2_ff3_data1_im),
    .o_valid    (mdc_ff3_valid),
    .o_data1_r  (mdc_ff3_data0_re),
    .o_data1_i  (mdc_ff3_data0_im),
    .o_data2_r  (mdc_ff3_data1_re),
    .o_data2_i  (mdc_ff3_data1_im)
);

assign mdc_ffx_valid = mdc_ff0_valid & mdc_ff1_valid & mdc_ff2_valid & mdc_ff3_valid;

////////////////////////////////////////////////////////////////////////////////////////////

buffer_parallel2serial #( .NB_DATA(8)) u_buffer_parallel2serial (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_clk_en   (i_clk_en),
    .i_valid    (mdc_ffx_valid),
    .i_tx_ready (i_tx_ready),
    .i_data0_re (mdc_ff0_data0_re),
    .i_data0_im (mdc_ff0_data0_im),
    .i_data1_re (mdc_ff0_data1_re),
    .i_data1_im (mdc_ff0_data1_im),
    .i_data2_re (mdc_ff1_data0_re),
    .i_data2_im (mdc_ff1_data0_im),
    .i_data3_re (mdc_ff1_data1_re),
    .i_data3_im (mdc_ff1_data1_im),
    .i_data4_re (mdc_ff2_data0_re),
    .i_data4_im (mdc_ff2_data0_im),
    .i_data5_re (mdc_ff2_data1_re),
    .i_data5_im (mdc_ff2_data1_im),
    .i_data6_re (mdc_ff3_data0_re),
    .i_data6_im (mdc_ff3_data0_im),
    .i_data7_re (mdc_ff3_data1_re),
    .i_data7_im (mdc_ff3_data1_im),
    .o_data_re  (o_data_re),
    .o_data_im  (o_data_im),
    .o_valid    (o_valid)
);

endmodule