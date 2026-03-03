module buffer_tx #(
    parameter NB_DATA = 8,
    parameter N_DATA  = 16
)(
    input                           i_clk,
    input                           i_rst_n,
    input                           i_clk_en,
    input                           i_valid,
    input      signed [NB_DATA-1:0] i_data0_re,
    input      signed [NB_DATA-1:0] i_data0_im,
    input      signed [NB_DATA-1:0] i_data1_re,
    input      signed [NB_DATA-1:0] i_data1_im,
    input      signed [NB_DATA-1:0] i_data2_re,
    input      signed [NB_DATA-1:0] i_data2_im,
    input      signed [NB_DATA-1:0] i_data3_re,
    input      signed [NB_DATA-1:0] i_data3_im,
    input      signed [NB_DATA-1:0] i_data4_re,
    input      signed [NB_DATA-1:0] i_data4_im,
    input      signed [NB_DATA-1:0] i_data5_re,
    input      signed [NB_DATA-1:0] i_data5_im,
    input      signed [NB_DATA-1:0] i_data6_re,
    input      signed [NB_DATA-1:0] i_data6_im,
    input      signed [NB_DATA-1:0] i_data7_re,
    input      signed [NB_DATA-1:0] i_data7_im,
    output                          o_data,
    output                          o_ready
);

wire signed [NB_DATA-1:0] buf_data_re;
wire signed [NB_DATA-1:0] buf_data_im;
wire                       buf_valid;
wire                       tx_ready;

assign o_ready = tx_ready;

buffer_parallel2serial #(
    .NB_DATA (NB_DATA)
) u_buffer (
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_clk_en   (i_clk_en),
    .i_valid    (i_valid),
    .i_tx_ready (tx_ready),
    .i_data0_re (i_data0_re), .i_data0_im (i_data0_im),
    .i_data1_re (i_data1_re), .i_data1_im (i_data1_im),
    .i_data2_re (i_data2_re), .i_data2_im (i_data2_im),
    .i_data3_re (i_data3_re), .i_data3_im (i_data3_im),
    .i_data4_re (i_data4_re), .i_data4_im (i_data4_im),
    .i_data5_re (i_data5_re), .i_data5_im (i_data5_im),
    .i_data6_re (i_data6_re), .i_data6_im (i_data6_im),
    .i_data7_re (i_data7_re), .i_data7_im (i_data7_im),
    .o_data_re  (buf_data_re),
    .o_data_im  (buf_data_im),
    .o_valid    (buf_valid)
);

tx_serializer #(
    .NB_DATA (NB_DATA),
    .N_DATA  (N_DATA)
) u_tx (
    .i_clk     (i_clk),
    .i_rst_n   (i_rst_n),
    .i_valid   (buf_valid),
    .i_data_re (buf_data_re),
    .i_data_im (buf_data_im),
    .o_data    (o_data),
    .o_ready   (tx_ready)
);

endmodule