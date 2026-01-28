module complex_multiplier #(
    parameter NB_INPUT   = 10,
    parameter NBF_INPUT  = 7,
    parameter NB_OUTPUT  = 10,
    parameter NBF_OUTPUT = 7
)(
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    output reg signed [NB_OUTPUT-1:0] o_real,
    output reg signed [NB_OUTPUT-1:0] o_imag,
    input  signed [NB_INPUT-1:0]      i_real_A,
    input  signed [NB_INPUT-1:0]      i_imag_A,
    input  signed [NB_INPUT-1:0]      i_real_B,
    input  signed [NB_INPUT-1:0]      i_imag_B,
    input                             i_clk
);

localparam NB_PROD      = NB_INPUT * 2;
localparam NBF_PROD     = NBF_INPUT * 2;
localparam NB_PROD_SUM  = NB_PROD + 1;
localparam NBF_PROD_SUM = NBF_PROD;

wire signed [NB_PROD-1:0] prod_xu; // Real A * Real B
wire signed [NB_PROD-1:0] prod_yv; // Imag A * Imag B
wire signed [NB_PROD-1:0] prod_xv; // Real A * Imag B
wire signed [NB_PROD-1:0] prod_yu; // Imag A * Real B

assign prod_xu = i_real_A * i_real_B;
assign prod_yv = i_imag_A * i_imag_B;
assign prod_xv = i_real_A * i_imag_B;
assign prod_yu = i_imag_A * i_real_B;

wire signed [NB_PROD_SUM-1:0] sum_re;
wire signed [NB_PROD_SUM-1:0] sum_im;

assign sum_re = prod_xu - prod_yv;
assign sum_im = prod_xv + prod_yu;

wire signed [NB_OUTPUT-1:0] w_out_re;
wire signed [NB_OUTPUT-1:0] w_out_im;

clip_round #(
    .NB_INP(NB_PROD_SUM), 
    .NBF_INP(NBF_PROD_SUM), 
    .NB_OUT(NB_OUTPUT), 
    .NBF_OUT(NBF_OUTPUT),
    .RND_MD(0)
) u_clip (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data_re(sum_re),
    .i_data_im(sum_im),
    .o_data_re(w_out_re),
    .o_data_im(w_out_im)
);

always @(posedge i_clk) begin
    o_real <= w_out_re;
    o_imag <= w_out_im;
end
    
endmodule