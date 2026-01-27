module fft8 #(
    parameter NB_INPUT   = 8,
    parameter NBF_INPUT  = 7,
    parameter NB_OUTPUT  = 8,
    /* verilator lint_off UNUSEDPARAM */
    parameter NBF_OUTPUT = 7
    /* verilator lint_on UNUSEDPARAM */
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input                             i_clk,
    input                             i_rst_n,
    input                             i_inverse,
    ///////////////////// INPUTS  /////////////////////
    input                             i_valid,
    input  signed [ NB_INPUT - 1 : 0] i_data1_r,
    input  signed [ NB_INPUT - 1 : 0] i_data1_i,
    input  signed [ NB_INPUT - 1 : 0] i_data2_r,
    input  signed [ NB_INPUT - 1 : 0] i_data2_i,
    ///////////////////// OUTPUTS /////////////////////
    output                            o_valid,
    output signed [NB_OUTPUT - 1 : 0] o_data1_r,
    output signed [NB_OUTPUT - 1 : 0] o_data1_i,
    output signed [NB_OUTPUT - 1 : 0] o_data2_r,
    output signed [NB_OUTPUT - 1 : 0] o_data2_i
);


  ///////////////////////////////////////////////////////////////////////////////
  // WIRE AND REGISTER
  ///////////////////////////////////////////////////////////////////////////////

  localparam NB_TW = 10;
  localparam NBF_TW = 9;
  //-----------------------------------------
  localparam NB_STAGE1  = NB_INPUT + 2;
  localparam NBF_STAGE1 = NBF_INPUT;
  localparam NB_STAGE2  = NB_STAGE1 + 1;
  //localparam NBF_STAGE2 = NBF_STAGE1;
  //localparam NB_STAGE3  = NB_STAGE2 + 1;
  //localparam NBF_STAGE3 = NBF_STAGE2;


 // wire [ NB_INPUT - 1 : 0] w_data0_r;
 // wire [ NB_INPUT - 1 : 0] w_data0_i;
 // wire [ NB_INPUT - 1 : 0] w_data1_r;
 // wire [ NB_INPUT - 1 : 0] w_data1_i;
 // wire                     w_valid;
  //------------------------------------------------
  wire [NB_STAGE1 - 1 : 0] w_st1_1r;
  wire [NB_STAGE1 - 1 : 0] w_st1_1i;
  wire [NB_STAGE1 - 1 : 0] w_st1_2r;
  wire [NB_STAGE1 - 1 : 0] w_st1_2i;
  wire                     w_st1_valid;
  //------------------------------------------------
  wire [NB_STAGE2 - 1 : 0] w_st2_1r;
  wire [NB_STAGE2 - 1 : 0] w_st2_1i;
  wire [NB_STAGE2 - 1 : 0] w_st2_2r;
  wire [NB_STAGE2 - 1 : 0] w_st2_2i;
  wire                     w_st2_valid;
  //------------------------------------------------
//  wire [NB_STAGE3 - 1 : 0] w_st3_1r;
//  wire [NB_STAGE3 - 1 : 0] w_st3_1i;
//  wire [NB_STAGE3 - 1 : 0] w_st3_2r;
//  wire [NB_STAGE3 - 1 : 0] w_st3_2i;


  ///////////////////////////////////////////////////////////////////////////////
  // MODULES
  ///////////////////////////////////////////////////////////////////////////////

  mdc8p_stage1 #(
      .NB_INPUT  (NB_INPUT),
      .NBF_INPUT (NBF_INPUT),
      .NB_OUTPUT (NB_STAGE1),
      .NBF_OUTPUT(NBF_STAGE1),
      .NB_TW     (NB_TW),
      .NBF_TW    (NBF_TW)
  ) u_mdc8p_stage1 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_clk    (i_clk),
      .i_rst_n    (i_rst_n),
      .i_inverse(i_inverse),
      //----------------------------------------
      .i_valid  (i_valid),
      .i_data1_r(i_data1_r),
      .i_data1_i(i_data1_i),
      .i_data2_r(i_data2_r),
      .i_data2_i(i_data2_i),
      //----------------------------------------
      .o_valid  (w_st1_valid),
      .o_data1_r(w_st1_1r),
      .o_data1_i(w_st1_1i),
      .o_data2_r(w_st1_2r),
      .o_data2_i(w_st1_2i)
  );

  ////////////////////////////////////////////////////////////////
  // STAGE 2

  mdc8p_stage2 #(
      .NB_INPUT (NB_STAGE1),
      .NB_OUTPUT(NB_STAGE2)
  ) u_mdc8p_stage2 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_clk    (i_clk),
      .i_rst_n    (i_rst_n),
      .i_inverse(i_inverse),
      //----------------------------------------
      .i_valid  (w_st1_valid),
      .i_data1_r(w_st1_1r),
      .i_data1_i(w_st1_1i),
      .i_data2_r(w_st1_2r),
      .i_data2_i(w_st1_2i),
      //----------------------------------------
      .o_valid  (w_st2_valid),
      .o_data1_r(w_st2_1r),
      .o_data1_i(w_st2_1i),
      .o_data2_r(w_st2_2r),
      .o_data2_i(w_st2_2i)
  );

  ////////////////////////////////////////////////////////////////
  // STAGE 3
  mdc8p_stage3 #(
      .NB_INPUT (NB_STAGE2),
      .NB_OUTPUT(NB_OUTPUT)
  ) u_mdc8p_stage3 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_clk    (i_clk),
      .i_inverse(i_inverse),
      //----------------------------------------
      .i_valid  (w_st2_valid),
      .i_data1_r(w_st2_1r),
      .i_data1_i(w_st2_1i),
      .i_data2_r(w_st2_2r),
      .i_data2_i(w_st2_2i),
      //----------------------------------------
      .o_valid  (o_valid),
      .o_data1_r(o_data1_r),
      .o_data1_i(o_data1_i),
      .o_data2_r(o_data2_r),
      .o_data2_i(o_data2_i)
  );

endmodule
