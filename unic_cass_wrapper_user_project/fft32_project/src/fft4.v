module fft4 #(
    parameter NB_INPUT  = 8,
    parameter NBF_INPUT = 7,
    parameter NB_OUTPUT = 8,
    parameter NBF_OUTPUT = 7
)(
    `ifdef USE_POWER_PINS
    inout               VPWR,  // Common digital supply
    inout               VGND,  // Common digital ground
    `endif
    output reg signed [NB_OUTPUT-1:0] o_data0_re,
    output reg signed [NB_OUTPUT-1:0] o_data0_im,
    output reg signed [NB_OUTPUT-1:0] o_data1_re,
    output reg signed [NB_OUTPUT-1:0] o_data1_im,
    output reg signed [NB_OUTPUT-1:0] o_data2_re,
    output reg signed [NB_OUTPUT-1:0] o_data2_im,
    output reg signed [NB_OUTPUT-1:0] o_data3_re,
    output reg signed [NB_OUTPUT-1:0] o_data3_im,
    output                            o_valid,
    input      signed [NB_INPUT-1:0]  i_data0_re,
    input      signed [NB_INPUT-1:0]  i_data0_im,
    input      signed [NB_INPUT-1:0]  i_data1_re,
    input      signed [NB_INPUT-1:0]  i_data1_im,
    input      signed [NB_INPUT-1:0]  i_data2_re,
    input      signed [NB_INPUT-1:0]  i_data2_im,
    input      signed [NB_INPUT-1:0]  i_data3_re,
    input      signed [NB_INPUT-1:0]  i_data3_im,
    input                             i_inverse,
    input                             i_enable,
    input                             i_valid,
    input                             i_rst_n,
    input                             i_clk
);

reg valid_q;
reg valid_2q;
reg valid_3q;
reg valid_4q;

reg inv_q;
reg inv_2q;
reg inv_3q;

reg signed [NB_INPUT-1:0] r_x0_re, r_x0_im;
reg signed [NB_INPUT-1:0] r_x1_re, r_x1_im;
reg signed [NB_INPUT-1:0] r_x2_re, r_x2_im;
reg signed [NB_INPUT-1:0] r_x3_re, r_x3_im;

reg signed [NB_INPUT:0] s1_ev_sum_re, s1_ev_sum_im;
reg signed [NB_INPUT:0] s1_ev_sub_re, s1_ev_sub_im;
reg signed [NB_INPUT:0] s1_od_sum_re, s1_od_sum_im;
reg signed [NB_INPUT:0] s1_od_sub_re, s1_od_sub_im;

reg signed [NB_INPUT+1:0] s2_x0_re, s2_x0_im;
reg signed [NB_INPUT+1:0] s2_x1_re, s2_x1_im;
reg signed [NB_INPUT+1:0] s2_x2_re, s2_x2_im;
reg signed [NB_INPUT+1:0] s2_x3_re, s2_x3_im;

wire signed [NB_OUTPUT-1:0] w_out0_re, w_out0_im;
wire signed [NB_OUTPUT-1:0] w_out1_re, w_out1_im;
wire signed [NB_OUTPUT-1:0] w_out2_re, w_out2_im;
wire signed [NB_OUTPUT-1:0] w_out3_re, w_out3_im;

assign o_valid = valid_4q;

always @(posedge i_clk) begin
    if (!i_rst_n) begin
        valid_q  <= 1'b0;
        valid_2q <= 1'b0;
        valid_3q <= 1'b0;
        valid_4q <= 1'b0;
        inv_q    <= 1'b0;
        inv_2q   <= 1'b0;
        inv_3q   <= 1'b0;
    end 
    else if (i_enable) begin
        valid_4q <= valid_3q;
        valid_3q <= valid_2q;
        valid_2q <= valid_q;
        valid_q  <= i_valid;
        inv_3q   <= inv_2q;
        inv_2q   <= inv_q;
        inv_q    <= i_inverse;
    end
end

always @(posedge i_clk) begin
    if (i_enable && i_valid) begin
        r_x0_re <= i_data0_re;
        r_x0_im <= i_data0_im;
        r_x1_re <= i_data1_re;
        r_x1_im <= i_data1_im;
        r_x2_re <= i_data2_re;
        r_x2_im <= i_data2_im;
        r_x3_re <= i_data3_re;
        r_x3_im <= i_data3_im;
    end
end

always @(posedge i_clk) begin
    if (i_enable && valid_q) begin
        // even sums/subs (indices 0 and 2)
        s1_ev_sum_re <= r_x0_re + r_x2_re;
        s1_ev_sum_im <= r_x0_im + r_x2_im;
        s1_ev_sub_re <= r_x0_re - r_x2_re;
        s1_ev_sub_im <= r_x0_im - r_x2_im;
        // odd sums/subs (indices 1 and 3)
        s1_od_sum_re <= r_x1_re + r_x3_re;
        s1_od_sum_im <= r_x1_im + r_x3_im;
        s1_od_sub_re <= r_x1_re - r_x3_re;
        s1_od_sub_im <= r_x1_im - r_x3_im;
    end
end

always @(posedge i_clk) begin
    if (i_enable && valid_2q) begin
        s2_x0_re <= s1_ev_sum_re + s1_od_sum_re;
        s2_x0_im <= s1_ev_sum_im + s1_od_sum_im;
        s2_x2_re <= s1_ev_sum_re - s1_od_sum_re;
        s2_x2_im <= s1_ev_sum_im - s1_od_sum_im;
        if (inv_2q) begin
            s2_x1_re <= s1_ev_sub_re - s1_od_sub_im;
            s2_x1_im <= s1_ev_sub_im + s1_od_sub_re;
            s2_x3_re <= s1_ev_sub_re + s1_od_sub_im;
            s2_x3_im <= s1_ev_sub_im - s1_od_sub_re;
        end 
        else begin
            s2_x1_re <= s1_ev_sub_re + s1_od_sub_im; 
            s2_x1_im <= s1_ev_sub_im - s1_od_sub_re;
            s2_x3_re <= s1_ev_sub_re - s1_od_sub_im;
            s2_x3_im <= s1_ev_sub_im + s1_od_sub_re;
        end
    end
end

clip_round #(
    .NB_INP  (NB_INPUT+2),
    .NBF_INP (NBF_INPUT),
    .NB_OUT  (NB_OUTPUT),
    .NBF_OUT (NBF_OUTPUT),
    .RND_MD  (0)
) u_clip0 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data_re (s2_x0_re),
    .i_data_im (s2_x0_im),
    .o_data_re (w_out0_re),
    .o_data_im (w_out0_im)
);
clip_round #(
    .NB_INP  (NB_INPUT+2),
    .NBF_INP (NBF_INPUT),
    .NB_OUT  (NB_OUTPUT),
    .NBF_OUT (NBF_OUTPUT),
    .RND_MD  (0)
) u_clip1 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data_re (s2_x1_re),
    .i_data_im (s2_x1_im),
    .o_data_re (w_out1_re),
    .o_data_im (w_out1_im)
);
clip_round #(
    .NB_INP  (NB_INPUT + 2),
    .NBF_INP (NBF_INPUT),
    .NB_OUT  (NB_OUTPUT),
    .NBF_OUT (NBF_OUTPUT),
    .RND_MD  (0)
) u_clip2 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data_re (s2_x2_re),
    .i_data_im (s2_x2_im),
    .o_data_re (w_out2_re),
    .o_data_im (w_out2_im)
);
clip_round #(
    .NB_INP  (NB_INPUT+2),
    .NBF_INP (NBF_INPUT),
    .NB_OUT  (NB_OUTPUT),
    .NBF_OUT (NBF_OUTPUT),
    .RND_MD  (0)
) u_clip3 (
    `ifdef USE_POWER_PINS
    .VPWR       (VPWR),
    .VGND       (VGND),
    `endif
    .i_data_re (s2_x3_re),
    .i_data_im (s2_x3_im),
    .o_data_re (w_out3_re),
    .o_data_im (w_out3_im)
);

always @(posedge i_clk) begin
    if (!i_rst_n) begin
        o_data0_re <= 0; o_data0_im <= 0;
        o_data1_re <= 0; o_data1_im <= 0;
        o_data2_re <= 0; o_data2_im <= 0;
        o_data3_re <= 0; o_data3_im <= 0;
    end 
    else if (i_enable && valid_3q) begin
        o_data0_re <= inv_3q ? (w_out0_re >>> 2) : w_out0_re;
        o_data0_im <= inv_3q ? (w_out0_im >>> 2) : w_out0_im;
        o_data1_re <= inv_3q ? (w_out1_re >>> 2) : w_out1_re;
        o_data1_im <= inv_3q ? (w_out1_im >>> 2) : w_out1_im;
        o_data2_re <= inv_3q ? (w_out2_re >>> 2) : w_out2_re;
        o_data2_im <= inv_3q ? (w_out2_im >>> 2) : w_out2_im;
        o_data3_re <= inv_3q ? (w_out3_re >>> 2) : w_out3_re;
        o_data3_im <= inv_3q ? (w_out3_im >>> 2) : w_out3_im;
    end
end

endmodule