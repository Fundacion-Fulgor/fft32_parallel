module ds_switch #(
    parameter NB = 8,
    parameter N  = 4,
    parameter L  = 2
) (
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    input               i_clk,
    input               i_rst_n,
    input               i_valid,
    input  [NB - 1 : 0] i_data_0r,
    input  [NB - 1 : 0] i_data_0i,
    input  [NB - 1 : 0] i_data_1r,
    input  [NB - 1 : 0] i_data_1i,
    //-------------------------------
    output              o_valid,
    output [NB - 1 : 0] o_data_0r,
    output [NB - 1 : 0] o_data_0i,
    output [NB - 1 : 0] o_data_1r,
    output [NB - 1 : 0] o_data_1i
);

  ////////////////////////////////////////////////////////////
  // WIRE AND REGISTER
  ////////////////////////////////////////////////////////////
  localparam STATE_OFF = 1'b0;
  localparam STATE_ON = 1'b1;
  reg               current_state;
  reg               next_state;
  reg               r_sel;
  reg  [ L - 1 : 0] flag;
  wire [L-1:0] Lm1 = (L-1);
  //-----FSM_VALID-------------------------------
  reg               valid_cstate;
  reg               valid_nstate;
  reg  [ N - 1 : 0] valid_count;
  reg               valid;
  //---------------------------------------------
  reg  [NB - 1 : 0] r_idata_r     [L - 1 : 0];
  reg  [NB - 1 : 0] r_idata_i     [L - 1 : 0];
  reg  [NB - 1 : 0] r_odata_r     [L - 1 : 0];
  reg  [NB - 1 : 0] r_odata_i     [L - 1 : 0];
  //---------------------------------------------
  wire              w_sel;
  wire [NB - 1 : 0] w_data_1r;
  wire [NB - 1 : 0] w_data_1i;
  wire [NB - 1 : 0] w_data_2r;
  wire [NB - 1 : 0] w_data_2i;


  ////////////////////////////////////////////////////////////
  // FSM - SEL
  ////////////////////////////////////////////////////////////

  /* verilator lint_off SYNCASYNCNET */
  always @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      flag <= {L{1'b0}};
      current_state <= STATE_OFF;
    end else begin
      current_state <= next_state;
      case (current_state)
        STATE_OFF: begin
          if (i_valid) begin
            /* verilator lint_off UNSIGNED */
            if (flag < Lm1) flag <= flag + 1'b1;
            /* verilator lint_on UNSIGNED */
            else flag <= {L{1'b0}};
          end else flag <= {L{1'b0}};
        end
        STATE_ON: begin
          /* verilator lint_off UNSIGNED */
          if (flag < Lm1) flag <= flag + 1'b1;
          /* verilator lint_on UNSIGNED */
          else flag <= {L{1'b0}};
        end
        default: begin
          flag <= {L{1'b0}};
        end
      endcase
    end
  end
  /* verilator lint_on SYNCASYNCNET */

  always @(*) begin
    case (current_state)
      STATE_OFF: begin
        r_sel = 1'b0;
        if ((flag == Lm1) && i_valid) next_state = STATE_ON;
        else next_state = STATE_OFF;
      end
      STATE_ON: begin
        r_sel = 1'b1;
        if (flag == Lm1) next_state = STATE_OFF;
        else next_state = STATE_ON;
      end
      default: begin
        r_sel = 1'b0;
        next_state = STATE_OFF;
      end
    endcase
  end

  assign w_sel = r_sel;

  ////////////////////////////////////////////////////////////
  // FSM - VALID
  ////////////////////////////////////////////////////////////

  /* verilator lint_off SYNCASYNCNET */
  always @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      valid_count  <= {N{1'b0}};
      valid_cstate <= STATE_OFF;
    end else begin
      valid_cstate <= valid_nstate;
      case (valid_cstate)
        STATE_OFF: begin
          valid_count <= {N{1'b0}};
        end
        STATE_ON: begin
          if (valid_count < (N - 1)) valid_count <= valid_count + {{N - 1{1'b0}}, 1'b1};
          else valid_count <= {N{1'b0}};
        end
        default: begin
          valid_count <= {N{1'b0}};
        end
      endcase
    end
  end
  /* verilator lint_on SYNCASYNCNET */

  always @(*) begin
    case (valid_cstate)
      STATE_OFF: begin
        valid = 1'b0;
        if ((flag == Lm1) && i_valid) valid_nstate = STATE_ON;
        else valid_nstate = STATE_OFF;
      end
      STATE_ON: begin
        valid = 1'b1;
        if ((valid_count < (N - 1))) valid_nstate = STATE_ON;
        else begin
          if (i_valid) valid_nstate = STATE_ON;
          else valid_nstate = STATE_OFF;
        end
      end
      default: begin
        valid = 1'b0;
        valid_nstate = STATE_OFF;
      end
    endcase
  end

  assign o_valid = valid;
  ////////////////////////////////////////////////////////////
  // CL && REG
  ////////////////////////////////////////////////////////////

  integer ptr;
  always @(posedge i_clk) begin
    for (ptr = 0; ptr < L; ptr = ptr + 1) begin
      if (ptr == 0) begin
        r_idata_r[ptr] <= i_data_1r;
        r_idata_i[ptr] <= i_data_1i;
        r_odata_r[ptr] <= w_data_1r;
        r_odata_i[ptr] <= w_data_1i;
      end else begin
        r_idata_r[ptr] <= r_idata_r[ptr-1];
        r_idata_i[ptr] <= r_idata_i[ptr-1];
        r_odata_r[ptr] <= r_odata_r[ptr-1];
        r_odata_i[ptr] <= r_odata_i[ptr-1];
      end
      // r_idata_r[i+1]
    end
  end

  assign w_data_1r = (w_sel) ? r_idata_r[L-1] : i_data_0r;
  assign w_data_1i = (w_sel) ? r_idata_i[L-1] : i_data_0i;
  assign w_data_2r = (w_sel) ? i_data_0r : r_idata_r[L-1];
  assign w_data_2i = (w_sel) ? i_data_0i : r_idata_i[L-1];


  assign o_data_0r = r_odata_r[L-1];
  assign o_data_0i = r_odata_i[L-1];
  assign o_data_1r = w_data_2r;
  assign o_data_1i = w_data_2i;


endmodule
