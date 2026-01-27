module shift_r4 #(
    parameter NB_DATA   = 8
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input                       i_clk,
    input                       i_clk_en,
    input                       i_valid,
    input  signed [NB_DATA-1:0] i_data_re,
    input  signed [NB_DATA-1:0] i_data_im,
    output signed [NB_DATA-1:0] o_data0_re,
    output signed [NB_DATA-1:0] o_data0_im,
    output signed [NB_DATA-1:0] o_data1_re,
    output signed [NB_DATA-1:0] o_data1_im,
    output signed [NB_DATA-1:0] o_data2_re,
    output signed [NB_DATA-1:0] o_data2_im,
    output signed [NB_DATA-1:0] o_data3_re,
    output signed [NB_DATA-1:0] o_data3_im,
    output                      o_valid
);

reg [NB_DATA*25-1:0] data_re_q;
reg [NB_DATA*25-1:0] data_im_q;
reg [        25-1:0] valid_q;

integer k;

always @(posedge i_clk) begin
    if(i_clk_en) begin
        data_re_q[   NB_DATA-1:0      ] <= i_data_re;
        // data_re_q[25*NB_DATA-1:NB_DATA] <= data_re_q[24*NB_DATA-1:0];
        data_im_q[   NB_DATA-1:0      ] <= i_data_im;
        // data_im_q[25*NB_DATA-1:NB_DATA] <= data_im_q[24*NB_DATA-1:0];
        valid_q  [   0]                 <= i_valid;
        // valid_q  [24:1]                 <= valid_q[23:0];
        for (k = 1; k < 25; k = k + 1) begin
            data_re_q[k*NB_DATA +: NB_DATA] <= data_re_q[(k-1)*NB_DATA +: NB_DATA];
            data_im_q[k*NB_DATA +: NB_DATA] <= data_im_q[(k-1)*NB_DATA +: NB_DATA];
            valid_q[k]                      <= valid_q[k-1];
        end
    end
end


assign o_data3_re = data_re_q[NB_DATA-1:0];
assign o_data3_im = data_im_q[NB_DATA-1:0];
assign o_data2_re = data_re_q[ 9*NB_DATA-1-:NB_DATA];
assign o_data2_im = data_im_q[ 9*NB_DATA-1-:NB_DATA];
assign o_data1_re = data_re_q[17*NB_DATA-1-:NB_DATA];
assign o_data1_im = data_im_q[17*NB_DATA-1-:NB_DATA];
assign o_data0_re = data_re_q[25*NB_DATA-1-:NB_DATA];
assign o_data0_im = data_im_q[25*NB_DATA-1-:NB_DATA];
assign o_valid    = valid_q[24];


endmodule
