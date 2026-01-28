module mdc8p_stage3 #(
    parameter NB_INPUT  = 11,
    parameter NB_OUTPUT = 8
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input                       i_clk,
    input                       i_inverse,
    //----------------------------------------
    input                       i_valid,
    input  signed [ NB_INPUT - 1 : 0] i_data1_r,
    input  signed [ NB_INPUT - 1 : 0] i_data1_i,
    input  signed [ NB_INPUT - 1 : 0] i_data2_r,
    input  signed [ NB_INPUT - 1 : 0] i_data2_i,
    //----------------------------------------
    output reg                      o_valid,
    output reg signed [NB_OUTPUT - 1 : 0] o_data1_r,
    output reg signed [NB_OUTPUT - 1 : 0] o_data1_i,
    output reg signed [NB_OUTPUT - 1 : 0] o_data2_r,
    output reg signed [NB_OUTPUT - 1 : 0] o_data2_i
);

localparam NB_FLY = NB_INPUT + 1; // 12 bits
wire signed [NB_FLY - 1 : 0] w_bt0_r;
wire signed [NB_FLY - 1 : 0] w_bt0_i;
wire signed [NB_FLY - 1 : 0] w_bt1_r;
wire signed [NB_FLY - 1 : 0] w_bt1_i;

btfly_2 #(
    .NB_INPUT (NB_INPUT),
    .NB_OUTPUT(NB_FLY)
) u_btfly2 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data0_r(i_data1_r),
    .i_data0_i(i_data1_i),
    .i_data1_r(i_data2_r),
    .i_data1_i(i_data2_i),
    .o_data0_r(w_bt0_r),
    .o_data0_i(w_bt0_i),
    .o_data1_r(w_bt1_r),
    .o_data1_i(w_bt1_i)
);

reg signed [NB_OUTPUT-1:0] next_data0_r, next_data0_i;
reg signed [NB_OUTPUT-1:0] next_data1_r, next_data1_i;

always @(*) begin
    if (i_inverse) begin
        next_data0_r = w_bt0_r[NB_FLY-2 -: NB_OUTPUT]; 
        next_data0_i = w_bt0_i[NB_FLY-2 -: NB_OUTPUT];
        next_data1_r = w_bt1_r[NB_FLY-2 -: NB_OUTPUT];
        next_data1_i = w_bt1_i[NB_FLY-2 -: NB_OUTPUT];
    end 
    else begin
        next_data0_r = w_bt0_r[NB_OUTPUT-1:0]; 
        next_data0_i = w_bt0_i[NB_OUTPUT-1:0];
        next_data1_r = w_bt1_r[NB_OUTPUT-1:0];
        next_data1_i = w_bt1_i[NB_OUTPUT-1:0];
    end
end

always @(posedge i_clk) begin
  o_data1_r <= next_data0_r;
  o_data1_i <= next_data0_i;
  o_data2_r <= next_data1_r;
  o_data2_i <= next_data1_i;
  o_valid   <= i_valid;
end

endmodule