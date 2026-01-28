module mdc8p_stage1 #(
    parameter NB_INPUT   = 8,
    parameter NBF_INPUT  = 7,
    parameter NB_OUTPUT  = 10,
    parameter NBF_OUTPUT = 7,
    parameter NB_TW      = 10,
    parameter NBF_TW     = 9
) (
    `ifdef USE_POWER_PINS
    inout                             VPWR,  // Common digital supply
    inout                             VGND,  // Common digital ground
    `endif
    input                             i_clk,
    input                             i_rst_n,
    input                             i_inverse,
    //----------------------------------------
    input                             i_valid,
    input  signed [ NB_INPUT - 1 : 0] i_data1_r,
    input  signed [ NB_INPUT - 1 : 0] i_data1_i,
    input  signed [ NB_INPUT - 1 : 0] i_data2_r,
    input  signed [ NB_INPUT - 1 : 0] i_data2_i,
    //----------------------------------------
    output                            o_valid,
    output signed [NB_OUTPUT - 1 : 0] o_data1_r,
    output signed [NB_OUTPUT - 1 : 0] o_data1_i,
    output signed [NB_OUTPUT - 1 : 0] o_data2_r,
    output signed [NB_OUTPUT - 1 : 0] o_data2_i
);

  //////////////////////////////////////////////////////////////////////////////////
  // WIRE AND REGISTER
  //////////////////////////////////////////////////////////////////////////////////
  localparam N_TW = 4;

  localparam NB_FLY = NB_INPUT + 1;
  localparam NBF_FLY = NBF_INPUT;

  localparam NB_COUNT = 2;

  localparam N_DATA = 4;
  localparam L_STAGE = 2;

  reg         [ NB_COUNT - 1 : 0] r_count;
  //--- -------------------------------------------
  reg signed  [ NB_INPUT - 1 : 0] r_data0_r;
  reg signed  [ NB_INPUT - 1 : 0] r_data0_i;
  reg signed  [ NB_INPUT - 1 : 0] r_data1_r;
  reg signed  [ NB_INPUT - 1 : 0] r_data1_i;
  reg                             r_data_valid;
  //--- -------------------------------------------
  wire signed [    NB_TW - 1 : 0] w_twiddle_r  [N_TW - 1 : 0];
  wire signed [    NB_TW - 1 : 0] w_twiddle_i  [N_TW - 1 : 0];
  wire signed [    NB_TW - 1 : 0] w_tw_r;
  wire signed [    NB_TW - 1 : 0] w_tw_i;
  //--- -------------------------------------------
  wire signed [   NB_FLY - 1 : 0] w_bt0_r;
  wire signed [   NB_FLY - 1 : 0] w_bt0_i;
  wire signed [   NB_FLY - 1 : 0] w_bt1_r;
  wire signed [   NB_FLY - 1 : 0] w_bt1_i;
  reg signed  [   NB_FLY - 1 : 0] r_bt0_r      [       2 : 0];
  reg signed  [   NB_FLY - 1 : 0] r_bt0_i      [       2 : 0];
  //----------------------------------------------
  wire signed [NB_OUTPUT - 1 : 0] w_ds0_r;
  wire signed [NB_OUTPUT - 1 : 0] w_ds0_i;
  wire signed [NB_OUTPUT - 1 : 0] w_ds1_r;
  wire signed [NB_OUTPUT - 1 : 0] w_ds1_i;
  wire                            w_dsx_valid;

  //////////////////////////////////////////////////////////////////////////////////
  // TWIDDLES
  //////////////////////////////////////////////////////////////////////////////////

  assign w_twiddle_r[0] = 10'h1FF;
  assign w_twiddle_r[1] = 10'h16A;
  assign w_twiddle_r[2] = 10'h000;
  assign w_twiddle_r[3] = 10'h295;
  assign w_twiddle_i[0] = (i_inverse) ? 10'h000 : 10'h000;
  assign w_twiddle_i[1] = (i_inverse) ? 10'h16A : 10'h295;
  assign w_twiddle_i[2] = (i_inverse) ? 10'h1FF : 10'h200;
  assign w_twiddle_i[3] = (i_inverse) ? 10'h16A : 10'h295;

  assign w_tw_r = w_twiddle_r[r_count];
  assign w_tw_i = w_twiddle_i[r_count];

  always @(posedge i_clk) begin
    if (!i_rst_n) begin
      r_count <= {NB_COUNT{1'b0}};
    end else begin
      if (r_data_valid) begin
        if (r_count < {NB_COUNT{1'b1}}) r_count <= r_count + {{NB_COUNT - 1{1'b0}}, 1'b1};
        else r_count <= {NB_COUNT{1'b0}};
      end else begin
        r_count <= {NB_COUNT{1'b0}};
      end
    end
  end

  //////////////////////////////////////////////////////////////////////////////////
  // MODULES
  //////////////////////////////////////////////////////////////////////////////////

  always @(posedge i_clk) begin
    r_data0_r    <= i_data1_r;
    r_data0_i    <= i_data1_i;
    r_data1_r    <= i_data2_r;
    r_data1_i    <= i_data2_i;
    r_data_valid <= i_valid;
  end

  //-------------------------------------------------------
  btfly_2 #(
      .NB_INPUT (NB_INPUT),
      .NB_OUTPUT(NB_FLY)
  ) u_btfly2 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_data0_r(r_data0_r),
      .i_data0_i(r_data0_i),
      .i_data1_r(r_data1_r),
      .i_data1_i(r_data1_i),
      .o_data0_r(w_bt0_r),
      .o_data0_i(w_bt0_i),
      .o_data1_r(w_bt1_r),
      .o_data1_i(w_bt1_i)
  );

  //-------------------------------------------------------

  always @(posedge i_clk) begin
    r_bt0_r[0] <= w_bt0_r;
    r_bt0_r[1] <= r_bt0_r[0];
    r_bt0_r[2] <= r_bt0_r[1];
    //-------------------------------
    r_bt0_i[0] <= w_bt0_i;
    r_bt0_i[1] <= r_bt0_i[0];
    r_bt0_i[2] <= r_bt0_i[1];

  end
  assign w_ds0_r = {r_bt0_r[1][NB_FLY-1], r_bt0_r[1]};
  assign w_ds0_i = {r_bt0_i[1][NB_FLY-1], r_bt0_i[1]};

  xfft_cell #(
      .NB_I (NB_FLY),
      .NBF_I(NBF_FLY),
      .NB_T (NB_TW),
      .NBF_T(NBF_TW),
      .NB_O (NB_OUTPUT),
      .NBF_O(NBF_OUTPUT)
  ) xfft_cell_route1 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_clk  (i_clk),
      .i_valid(r_data_valid),
      .i_tw_r  (w_tw_r),
      .i_tw_i  (w_tw_i),
      .i_data_r(w_bt1_r),
      .i_data_i(w_bt1_i),
      //------------------------
      .o_data_r(w_ds1_r),
      .o_data_i(w_ds1_i),
      .o_valid(w_dsx_valid)
  );

  //-------------------------------------------------------

  ds_switch #(
      .NB(NB_OUTPUT),
      .N (N_DATA),
      .L (L_STAGE)
  ) ds_switch_stage1 (
      `ifdef USE_POWER_PINS
      .VPWR       (VPWR),
      .VGND       (VGND),
      `endif
      .i_clk    (i_clk),
      .i_rst_n  (i_rst_n),
      .i_valid  (w_dsx_valid),
      //----------------------------------------
      .i_data_0r(w_ds0_r),
      .i_data_0i(w_ds0_i),
      .i_data_1r(w_ds1_r),
      .i_data_1i(w_ds1_i),
      //-------------------------------
      .o_valid  (o_valid),
      .o_data_0r(o_data1_r),
      .o_data_0i(o_data1_i),
      .o_data_1r(o_data2_r),
      .o_data_1i(o_data2_i)
  );

endmodule
