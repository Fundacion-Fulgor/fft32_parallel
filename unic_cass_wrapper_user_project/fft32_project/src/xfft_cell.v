`define PP_1
`define PP_2
// `define PP_3

module xfft_cell #(
    parameter NB_I  = 8,
    parameter NBF_I = 7,
    parameter NB_T  = 10,
    parameter NBF_T = 9,
    parameter NB_O  = 10,
    parameter NBF_O = 7
) (
    `ifdef USE_POWER_PINS
    inout                        VPWR,  // Common digital supply
    inout                        VGND,  // Common digital ground
    `endif
    input                        i_clk,
    input                        i_valid,
    //------------------------
    input  signed [NB_T - 1 : 0] i_tw_r,
    input  signed [NB_T - 1 : 0] i_tw_i,
    input  signed [NB_I - 1 : 0] i_data_r,
    input  signed [NB_I - 1 : 0] i_data_i,
    //------------------------
    output signed [NB_O - 1 : 0] o_data_r,
    output signed [NB_O - 1 : 0] o_data_i,
    output                       o_valid
);

//////////////////////////////////////////////////////////////
// WIRE AND REGISTER
//////////////////////////////////////////////////////////////
//localparam DIF_SIM = NB_O - NB_I;
localparam NB_PROD = NB_I + NB_T;
localparam NBF_PROD = NBF_I + NBF_T;
localparam NB_ADDER = NB_PROD + 1;
localparam NBF_ADDER = NBF_PROD;
localparam SIGNED = (NB_ADDER - NBF_ADDER) - (NB_O - NBF_O) + 1;

 
wire                           w_st1_valid;
wire signed [    NB_I - 1 : 0] w_st1_data_r;
wire signed [    NB_I - 1 : 0] w_st1_data_i;
wire signed [    NB_T - 1 : 0] w_st1_tw_r;
wire signed [    NB_T - 1 : 0] w_st1_tw_i;

wire signed [ NB_PROD - 1 : 0] w_mult_r     [2 - 1 : 0];
wire signed [ NB_PROD - 1 : 0] w_mult_i     [2 - 1 : 0];
wire signed [ NB_PROD - 1 : 0] w_st2_data_r [2 - 1 : 0];
wire signed [ NB_PROD - 1 : 0] w_st2_data_i [2 - 1 : 0];
wire                           w_st2_valid;

wire signed [NB_ADDER - 1 : 0] w_adder_r;
wire signed [NB_ADDER - 1 : 0] w_adder_i;
wire signed [    NB_O - 1 : 0] w_data_r;
wire signed [    NB_O - 1 : 0] w_data_i;
wire signed [    NB_O - 1 : 0] w_st3_data_r;
wire signed [    NB_O - 1 : 0] w_st3_data_i;
wire                           w_st3_valid;
  

//////////////////////////////////////////////////////////////
// LOGIC
//////////////////////////////////////////////////////////////


`ifdef PP_1
    reg signed  [    NB_I - 1 : 0] r_pp1_data_r;
    reg signed  [    NB_I - 1 : 0] r_pp1_data_i;
    reg signed  [    NB_T - 1 : 0] r_pp1_tw_r;
    reg signed  [    NB_T - 1 : 0] r_pp1_tw_i;
   // reg         [           1 : 0] r_pp1_sel;
    reg                            r_pp1_valid;

    always @(posedge i_clk) begin
        r_pp1_data_r <= i_data_r;
        r_pp1_data_i <= i_data_i;
        r_pp1_tw_r   <= i_tw_r;
        r_pp1_tw_i   <= i_tw_i;
        r_pp1_valid  <= i_valid;
    end
    assign w_st1_data_r = r_pp1_data_r; 
    assign w_st1_data_i = r_pp1_data_i;
    assign w_st1_tw_r   = r_pp1_tw_r;
    assign w_st1_tw_i   = r_pp1_tw_i;
    assign w_st1_valid  = r_pp1_valid;
`else
    assign w_st1_data_r = i_data_r; 
    assign w_st1_data_i = i_data_i;
    assign w_st1_tw_r   = i_tw_r;
    assign w_st1_tw_i   = i_tw_i;
    assign w_st1_valid  = i_valid;
`endif


assign w_mult_r[0] = w_st1_data_r * w_st1_tw_r;
assign w_mult_r[1] = w_st1_data_i * w_st1_tw_i;
assign w_mult_i[0] = w_st1_data_r * w_st1_tw_i;
assign w_mult_i[1] = w_st1_data_i * w_st1_tw_r;

`ifdef PP_2
    reg signed [NB_PROD - 1 : 0] r_pp2_mult_r[2 - 1 : 0];
    reg signed [NB_PROD - 1 : 0] r_pp2_mult_i[2 - 1 : 0];
    reg                          r_pp2_valid;

    always @(posedge i_clk) begin
        r_pp2_mult_r[0] <= w_mult_r[0];
        r_pp2_mult_r[1] <= w_mult_r[1];
        r_pp2_mult_i[0] <= w_mult_i[0];
        r_pp2_mult_i[1] <= w_mult_i[1];
        r_pp2_valid     <= w_st1_valid;
    end
    assign w_st2_data_r[0] = r_pp2_mult_r[0];
    assign w_st2_data_r[1] = r_pp2_mult_r[1];
    assign w_st2_data_i[0] = r_pp2_mult_i[0];
    assign w_st2_data_i[1] = r_pp2_mult_i[1];
    assign w_st2_valid     = r_pp2_valid;
`else
    assign w_st2_data_r[0] = w_mult_r[0];
    assign w_st2_data_r[1] = w_mult_r[1];
    assign w_st2_data_i[0] = w_mult_i[0];
    assign w_st2_data_i[1] = w_mult_i[1];
    assign w_st2_valid     = w_st1_valid;
`endif

assign w_adder_r = w_st2_data_r[0] - w_st2_data_r[1];
assign w_adder_i = w_st2_data_i[0] + w_st2_data_i[1];


assign w_data_r = (~|w_adder_r[NB_ADDER-1 -:SIGNED] || &w_adder_r[NB_ADDER-1 -:SIGNED]) ?
                  w_adder_r[(NB_ADDER-SIGNED)-:NB_O] :
                 (w_adder_r[NB_ADDER-1]) ? {1'b1,{NB_O-1{1'b0}}} : {1'b0,{NB_O-1{1'b1}}};
assign w_data_i = (~|w_adder_i[NB_ADDER-1 -:SIGNED] || &w_adder_i[NB_ADDER-1 -:SIGNED]) ?
                  w_adder_i[(NB_ADDER-SIGNED)-:NB_O] :
                 (w_adder_i[NB_ADDER-1]) ? {1'b1,{NB_O-1{1'b0}}} : {1'b0,{NB_O-1{1'b1}}};

`ifdef PP_3
    reg signed [NB_O - 1 : 0] r_pp3_data_r;
    reg signed [NB_O - 1 : 0] r_pp3_data_i;
    reg                       r_pp3_valid;

    always @(posedge i_clk) begin
        r_pp3_data_r <= w_data_r;
        r_pp3_data_i <= w_data_i;
        r_pp3_valid  <= w_st2_valid;
    end
    assign w_st3_data_r = r_pp3_data_r;
    assign w_st3_data_i = r_pp3_data_i;
    assign w_st3_valid  = r_pp3_valid;
`else
    assign w_st3_data_r = w_data_r;
    assign w_st3_data_i = w_data_i;
    assign w_st3_valid  = w_st2_valid;
`endif


  assign o_data_r = w_st3_data_r;
  assign o_data_i = w_st3_data_i;
  assign o_valid  = w_st3_valid;

endmodule
