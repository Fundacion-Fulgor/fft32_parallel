module buffer_serial2parallel #(
    parameter NB_DATA = 8,
    parameter N_DATA  = 16
)(
    `ifdef USE_POWER_PINS
    inout                           VPWR,
    inout                           VGND,
    `endif
    input                           i_clk,
    input                           i_rst_n,
    input                           i_valid,
    input      signed [NB_DATA-1:0] i_data_re,
    input      signed [NB_DATA-1:0] i_data_im,
    output reg                      o_valid,
    output reg signed [NB_DATA-1:0] o_data_re,
    output reg signed [NB_DATA-1:0] o_data_im
);

localparam PTR_W    = $clog2(N_DATA);
localparam S_LOAD   = 1'b0;
localparam S_UNLOAD = 1'b1;

reg signed [NB_DATA-1:0] mem_re [0:N_DATA-1];
reg signed [NB_DATA-1:0] mem_im [0:N_DATA-1];

reg [PTR_W-1:0] ptr;
reg             state;

always @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        ptr       <= 0;
        state     <= S_LOAD;
        o_valid   <= 1'b0;
        o_data_re <= 0;
        o_data_im <= 0;
    end
    else begin
        case (state)
            S_LOAD: begin
                o_valid <= 1'b0;
                if (i_valid) begin
                    mem_re[ptr] <= i_data_re;
                    mem_im[ptr] <= i_data_im;
                    if (ptr == PTR_W'(N_DATA - 1)) begin
                        ptr   <= 0;
                        state <= S_UNLOAD;
                    end else begin
                        ptr   <= ptr + 1'b1;
                    end
                end
            end
            
            S_UNLOAD: begin
                o_valid   <= 1'b1;
                o_data_re <= mem_re[ptr];
                o_data_im <= mem_im[ptr];
                
                if (ptr == PTR_W'(N_DATA - 1)) begin
                    ptr   <= 0;
                    state <= S_LOAD;
                end else begin
                    ptr   <= ptr + 1'b1;
                end
            end
        endcase
    end
end

endmodule