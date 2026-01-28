module twiddle_interface #(
    parameter NB_DATA  = 8,
    parameter NBF_DATA = 7
)(
    `ifdef USE_POWER_PINS
    inout                           VPWR,  // Common digital supply
    inout                           VGND,  // Common digital ground
    `endif
    input                           i_clk,
    input                           i_rst_n,
    input                           i_valid,
    input                           i_inverse,
    input      signed [NB_DATA-1:0] i_data0_re, i_data0_im,
    input      signed [NB_DATA-1:0] i_data1_re, i_data1_im,
    input      signed [NB_DATA-1:0] i_data2_re, i_data2_im,
    input      signed [NB_DATA-1:0] i_data3_re, i_data3_im,
    output reg signed [NB_DATA-1:0] o_data0_re, o_data0_im,
    output reg signed [NB_DATA-1:0] o_data1_re, o_data1_im,
    output reg signed [NB_DATA-1:0] o_data2_re, o_data2_im,
    output reg signed [NB_DATA-1:0] o_data3_re, o_data3_im,
    output reg                      o_valid
);

reg [2:0] cnt_q;
reg       inv_q;
reg       val_q, val_2q;

reg signed [NB_DATA-1:0] data0_re_q, data0_im_q;
reg signed [NB_DATA-1:0] data1_re_q, data1_im_q;
reg signed [NB_DATA-1:0] data2_re_q, data2_im_q;
reg signed [NB_DATA-1:0] data3_re_q, data3_im_q;
reg signed [NB_DATA-1:0] data0_re_2q, data0_im_2q;

wire signed [NB_DATA-1:0] mult1_re, mult1_im;
wire signed [NB_DATA-1:0] mult2_re, mult2_im;
wire signed [NB_DATA-1:0] mult3_re, mult3_im;

wire [2*NB_DATA-1:0] val_w1_fwd, val_w2_fwd, val_w3_fwd;
wire [2*NB_DATA-1:0] val_w1_inv, val_w2_inv, val_w3_inv;

assign val_w1_fwd = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0111110111100111 :
        (cnt_q == 3'd2) ? 16'b0111011011001111 :
        (cnt_q == 3'd3) ? 16'b0110101010111000 :
        (cnt_q == 3'd4) ? 16'b0101101010100101 :
        (cnt_q == 3'd5) ? 16'b0100011110010101 :
        (cnt_q == 3'd6) ? 16'b0011000010001001 :
        (cnt_q == 3'd7) ? 16'b0001100010000010 :
        16'd0;
assign val_w2_fwd = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0111011011001111 :
        (cnt_q == 3'd2) ? 16'b0101101010100101 :
        (cnt_q == 3'd3) ? 16'b0011000010001001 :
        (cnt_q == 3'd4) ? 16'b0000000010000000 :
        (cnt_q == 3'd5) ? 16'b1100111110001001 :
        (cnt_q == 3'd6) ? 16'b1010010110100101 :
        (cnt_q == 3'd7) ? 16'b1000100111001111 :
        16'd0;
assign val_w3_fwd = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0110101010111000 :
        (cnt_q == 3'd2) ? 16'b0011000010001001 :
        (cnt_q == 3'd3) ? 16'b1110011110000010 :
        (cnt_q == 3'd4) ? 16'b1010010110100101 :
        (cnt_q == 3'd5) ? 16'b1000001011100111 :
        (cnt_q == 3'd6) ? 16'b1000100100110000 :
        (cnt_q == 3'd7) ? 16'b1011100001101010 :
        16'd0;

assign val_w1_inv = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0111110100011000 :
        (cnt_q == 3'd2) ? 16'b0111011000110000 :
        (cnt_q == 3'd3) ? 16'b0110101001000111 :
        (cnt_q == 3'd4) ? 16'b0101101001011010 :
        (cnt_q == 3'd5) ? 16'b0100011101101010 :
        (cnt_q == 3'd6) ? 16'b0011000001110110 :
        (cnt_q == 3'd7) ? 16'b0001100001111101 :
        16'd0;
assign val_w2_inv = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0111011000110000 :
        (cnt_q == 3'd2) ? 16'b0101101001011010 :
        (cnt_q == 3'd3) ? 16'b0011000001110110 :
        (cnt_q == 3'd4) ? 16'b0000000001111111 :
        (cnt_q == 3'd5) ? 16'b1100111101110110 :
        (cnt_q == 3'd6) ? 16'b1010010101011010 :
        (cnt_q == 3'd7) ? 16'b1000100100110000 :
        16'd0;
assign val_w3_inv = 
        (cnt_q == 3'd0) ? 16'b0111111100000000 :
        (cnt_q == 3'd1) ? 16'b0110101001000111 :
        (cnt_q == 3'd2) ? 16'b0011000001110110 :
        (cnt_q == 3'd3) ? 16'b1110011101111101 :
        (cnt_q == 3'd4) ? 16'b1010010101011010 :
        (cnt_q == 3'd5) ? 16'b1000001000011000 :
        (cnt_q == 3'd6) ? 16'b1000100111001111 :
        (cnt_q == 3'd7) ? 16'b1011100010010101 :
        16'd0;

wire [2*NB_DATA-1:0] w1_selected, w2_selected, w3_selected;

assign w1_selected = inv_q ? val_w1_inv : val_w1_fwd;
assign w2_selected = inv_q ? val_w2_inv : val_w2_fwd;
assign w3_selected = inv_q ? val_w3_inv : val_w3_fwd;


always @(posedge i_clk) begin
    if (!i_rst_n) begin
        cnt_q  <= 3'd0;
        val_q  <= 1'b0;
        val_2q <= 1'b0;
        inv_q  <= 1'b0;
    end 
    else begin
        val_q  <= i_valid;
        val_2q <= val_q;
        if (i_valid) inv_q <= i_inverse;
        if (i_valid) begin
            if (cnt_q == 3'd7) cnt_q <= 3'd0;
            else               cnt_q <= cnt_q + 1'd1;
        end
    end
end

always @(posedge i_clk) begin
    if (i_valid) begin
        data0_re_q <= i_data0_re; data0_im_q <= i_data0_im;
        data1_re_q <= i_data1_re; data1_im_q <= i_data1_im;
        data2_re_q <= i_data2_re; data2_im_q <= i_data2_im;
        data3_re_q <= i_data3_re; data3_im_q <= i_data3_im;
    end
end

always @(posedge i_clk) begin
    data0_re_2q <= data0_re_q;
    data0_im_2q <= data0_im_q;
end

complex_multiplier #(
    .NB_INPUT(NB_DATA), .NBF_INPUT(NBF_DATA),
    .NB_OUTPUT(NB_DATA), .NBF_OUTPUT(NBF_DATA)
) u_mult_1 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk    (i_clk), 
    .i_real_A (data1_re_q), 
    .i_imag_A (data1_im_q),
    .i_real_B (w1_selected[2*NB_DATA-1 : NB_DATA]), 
    .i_imag_B (w1_selected[NB_DATA-1 : 0]),
    .o_real   (mult1_re), 
    .o_imag   (mult1_im)
);
complex_multiplier #(
    .NB_INPUT(NB_DATA), .NBF_INPUT(NBF_DATA),
    .NB_OUTPUT(NB_DATA), .NBF_OUTPUT(NBF_DATA)
) u_mult_2 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk    (i_clk), 
    .i_real_A (data2_re_q), 
    .i_imag_A (data2_im_q),
    .i_real_B (w2_selected[2*NB_DATA-1 : NB_DATA]), 
    .i_imag_B (w2_selected[NB_DATA-1 : 0]),
    .o_real   (mult2_re), 
    .o_imag   (mult2_im)
);
complex_multiplier #(
    .NB_INPUT(NB_DATA), .NBF_INPUT(NBF_DATA),
    .NB_OUTPUT(NB_DATA), .NBF_OUTPUT(NBF_DATA)
) u_mult_3 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_clk    (i_clk), 
    .i_real_A (data3_re_q), 
    .i_imag_A (data3_im_q),
    .i_real_B (w3_selected[2*NB_DATA-1 : NB_DATA]), 
    .i_imag_B (w3_selected[NB_DATA-1 : 0]),
    .o_real   (mult3_re), 
    .o_imag   (mult3_im)
);

always @(posedge i_clk) begin
    if (!i_rst_n) begin
        o_data0_re <= 0; o_data0_im <= 0;
        o_data1_re <= 0; o_data1_im <= 0;
        o_data2_re <= 0; o_data2_im <= 0;
        o_data3_re <= 0; o_data3_im <= 0;
        o_valid    <= 0;
    end 
    else begin
        o_valid <= val_2q; 
        if (val_2q) begin
            o_data0_re <= data0_re_2q;
            o_data0_im <= data0_im_2q;
            o_data1_re <= mult1_re;
            o_data1_im <= mult1_im;
            o_data2_re <= mult2_re;
            o_data2_im <= mult2_im;
            o_data3_re <= mult3_re;
            o_data3_im <= mult3_im;
        end
    end
end

endmodule
