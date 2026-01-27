module btfly_2 #(
    parameter NB_INPUT  = 8,
    parameter NB_OUTPUT = 9
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input  [ NB_INPUT - 1 : 0] i_data0_r,
    input  [ NB_INPUT - 1 : 0] i_data0_i,
    input  [ NB_INPUT - 1 : 0] i_data1_r,
    input  [ NB_INPUT - 1 : 0] i_data1_i,
    //--------------------------------------
    output [NB_OUTPUT - 1 : 0] o_data0_r,
    output [NB_OUTPUT - 1 : 0] o_data0_i,
    output [NB_OUTPUT - 1 : 0] o_data1_r,
    output [NB_OUTPUT - 1 : 0] o_data1_i
);

  /////////////////////////////////////////////////////////////////
  // CL
  /////////////////////////////////////////////////////////////////
  wire [NB_OUTPUT - 1 : 0] w_dataneg_r;
  wire [NB_OUTPUT - 1 : 0] w_dataneg_i;

  assign w_dataneg_r = (~{i_data1_r[NB_INPUT-1], i_data1_r}) + {{NB_OUTPUT - 1{1'b0}}, 1'b1};
  assign w_dataneg_i = (~{i_data1_i[NB_INPUT-1], i_data1_i}) + {{NB_OUTPUT - 1{1'b0}}, 1'b1};


  assign o_data0_r   = {i_data0_r[NB_INPUT-1], i_data0_r} + {i_data1_r[NB_INPUT-1], i_data1_r};
  assign o_data0_i   = {i_data0_i[NB_INPUT-1], i_data0_i} + {i_data1_i[NB_INPUT-1], i_data1_i};

  assign o_data1_r   = {i_data0_r[NB_INPUT-1], i_data0_r} + w_dataneg_r;
  assign o_data1_i   = {i_data0_i[NB_INPUT-1], i_data0_i} + w_dataneg_i;


endmodule
