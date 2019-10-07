module alu (input [31:0] a,b, input[3:0] op,
                       input [4:0] shamt,
                       output reg [31:0] hi,lo,
                       output zero);

wire [32:0] diff = {1'b0,a}+{1'b0,~b+32'b1};

assign zero = lo==32'd0 ? 1'b1 : 1'b0;

always @(*) begin
	hi = 32'b0;
	lo = 32'b0;

	casez (op)

	// arithmetic operations
	4'b01_00: lo = a+b; // add
	4'b01_01: lo = a-b; // sub

	// mult signed
	4'b01_10: {hi,lo} = $signed(a)*$signed(b);

	// mult unsigned
	4'b01_11: {hi,lo} = a*b;

	// shifter operations
	4'b10_00: lo = b << shamt; // sll
	4'b10_01: lo = b >> shamt; // srl
	4'b10_1?: lo = $signed(b) >>> shamt; //sra

	// comparison operations
	4'b11_00:  // A < B signed
	if (a[31] & ~b[31])
		lo = 32'b1; // a neg, b pos
	else
		if (a[31] == b[31] & diff[31]) // same sign, diff is neg
			lo = 32'b1;
		else lo = 32'b0;

	4'b11_??:
		if (~diff[32]) lo = 32'b1; // sltu
		else lo = 32'b0;

	// logical operations
	4'b00_00: lo = a & b; // and
	4'b00_01: lo = a | b; // or
	4'b00_10: lo = ~(a | b); // nor
	4'b00_11: lo = a ^ b; // xor

	endcase // casez(op)

	end // always
endmodule
