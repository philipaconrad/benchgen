Benchgen
--------

Benchgen is a test bench generator for SystemVerilog modules.

## Design

Benchgen takes in a JSON file describing the inputs and outputs of your SystemVerilog module, and then generates a test bench from that description.


## Usage

The following tutorial material is based on the ALU example under the `examples/` directory.

### Generating the test bench

Benchgen can be run with vanilla Python3 like so:

    python3 benchgen.py alu.json > testbench_alu.sv


### Creating test vectors

The test vectors file will need at least 1 vector, and can include comments.

Here's the contents of `vectors_alu.dat`:

    // test bitwise AND with non-zero output
    F_0F0F0F0F_FFFFFFFF_00_0_00000000_0F0F0F0F_0

Usually, the first 4 bits are the `enable` flag, and the fields following are separated by underscores.


### Simulating in ModelSim

To simulate your test bench in ModelSim on the command line:

    vlog -novopt *.sv
    vsim -c -novopt work.testbench_alu -do "run 5000"


## License

This project is released under the [MIT License][mit-license].

   [mit-license]: https://opensource.org/licenses/MIT
