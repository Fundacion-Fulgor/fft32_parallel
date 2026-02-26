module fft16_shift_r2 #(
    parameter NB_DATA   = 8
) (
    `ifdef USE_POWER_PINS
    inout                       VPWR,  // Common digital supply
    inout                       VGND,  // Common digital ground
    `endif
    input                       i_clk,
    input                       i_clk_en,
    ///////////////////// INPUTS  /////////////////////
    input                       i_valid,
    input  signed [NB_DATA-1:0] i_data_re,
    input  signed [NB_DATA-1:0] i_data_im,
    ///////////////////// OUTPUTS /////////////////////
    output signed [NB_DATA-1:0] o_data0_re,
    output signed [NB_DATA-1:0] o_data0_im,
    output signed [NB_DATA-1:0] o_data1_re,
    output signed [NB_DATA-1:0] o_data1_im,
    output                      o_valid
);

reg signed [NB_DATA*3-1:0] data_re_q;
reg signed [NB_DATA*3-1:0] data_im_q;
reg        [        3-1:0] valid_q;

always @(posedge i_clk) begin
    if(i_clk_en) begin
        data_re_q[  NB_DATA-1:0      ] <= i_data_re;
        data_re_q[3*NB_DATA-1:NB_DATA] <= data_re_q[2*NB_DATA-1:0];
        data_im_q[  NB_DATA-1:0      ] <= i_data_im;
        data_im_q[3*NB_DATA-1:NB_DATA] <= data_im_q[2*NB_DATA-1:0];
        valid_q[0]     <= i_valid;
        valid_q[2:1]   <= valid_q[1:0];
    end
end

assign o_data1_re = data_re_q[NB_DATA-1:0];
assign o_data1_im = data_im_q[NB_DATA-1:0];
assign o_data0_re = data_re_q[3*NB_DATA-1-:NB_DATA];
assign o_data0_im = data_im_q[3*NB_DATA-1-:NB_DATA];
assign o_valid    = valid_q[2];

endmodule
