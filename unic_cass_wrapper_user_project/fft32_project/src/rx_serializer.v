module rx_serializer #(
    parameter NB_DATA = 8
)(
    `ifdef USE_POWER_PINS
    inout                           VPWR,  // Common digital supply
    inout                           VGND,  // Common digital ground
    `endif
    input                           i_clk,
    input                           i_rst_n,
    input                           i_data,
    output reg signed [NB_DATA-1:0] o_data_re,
    output reg signed [NB_DATA-1:0] o_data_im,
    output reg                      o_valid
);

localparam TOTAL_BITS = 2 * NB_DATA; // 16 bits
localparam CNT_W      = 5;

// FSM states
localparam STATE_IDLE  = 0;
localparam STATE_RECV  = 1;
localparam STATE_VALID = 2;

reg [1:0]            current_state, next_state;
reg [CNT_W-1:0]      current_cnt, next_cnt;
reg [TOTAL_BITS-1:0] current_shift, next_shift;

reg data_d;
wire start_detected;

always @(posedge i_clk or negedge i_rst_n) begin
    if(!i_rst_n) data_d <= 1'b0;
    else         data_d <= i_data;
end

assign start_detected = (i_data && !data_d);

always @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        current_state <= STATE_IDLE;
        current_cnt   <= 0;
        current_shift <= 0;
        o_valid       <= 1'b0;
        o_data_re     <= 0;
        o_data_im     <= 0;
    end 
    else begin
        current_state <= next_state;
        current_cnt   <= next_cnt;
        current_shift <= next_shift;
        if (current_state == STATE_VALID) begin
            o_data_re <= current_shift[TOTAL_BITS-1 -: NB_DATA]; // High part -> Real
            o_data_im <= current_shift[NB_DATA-1    -: NB_DATA]; // Low part  -> Imag
            o_valid   <= 1'b1;
        end 
        else begin
            o_valid   <= 1'b0;
        end
    end
end

always @(*) begin
    next_state = current_state;
    next_cnt   = current_cnt;
    next_shift = current_shift;
    case (current_state)
        STATE_IDLE: begin
            next_cnt = 0;
            if (start_detected) begin
                next_state = STATE_RECV;
            end
        end
        STATE_RECV: begin
            next_shift = {current_shift[TOTAL_BITS-2:0], i_data};
            if (current_cnt == TOTAL_BITS - 1) begin
                next_state = STATE_VALID;
            end 
            else begin
                next_cnt = current_cnt + 1;
            end
        end
        STATE_VALID: begin
            next_state = STATE_IDLE;
        end
        default: next_state = STATE_IDLE;
    endcase
end

endmodule