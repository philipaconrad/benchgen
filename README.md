Benchgen
--------

Benchgen is a test bench generator for SystemVerilog modules.

## Design

Benchgen takes in a JSON file describing the inputs and outputs of your SystemVerilog module, and then generates a test bench from that description.
This allows you to skip all the work of writing up custom test benches for each SystemVerilog module in your project, and lets you focus instead on creating solid test vectors.


## Usage

Benchgen can be run with vanilla Python3 like so:

    python3 benchgen.py module.json > testbench_module.sv


## Example with a Flip-Flop module

Let's take a simple resettable flip-flop circuit as an example.

`flopr.sv`:

```
module flopr(input            clk,
             input            reset,
             input      [3:0] d,
             output reg [3:0] q);

  // synchronous reset
  always @ (posedge clk)
    if (reset) q <= 4'b0;
    else       q <= d;

endmodule
```

We'd need to write up a JSON description of its inputs and outputs, like so:

`flopr.json`:

```
{
  "module_name": "flopr",
  "parameters": [
    {
      "name": "clk",
      "io_type": "input",
      "type": "wire",
      "idx_hi": 0,
      "idx_lo": 0
    },
    {
      "name": "reset",
      "io_type": "input",
      "type": "wire",
      "idx_hi": 0,
      "idx_lo": 0
    },
    {
      "name": "d",
      "io_type": "input",
      "type": "wire",
      "idx_hi": 3,
      "idx_lo": 0
    },
    {
      "name": "q",
      "io_type": "output",
      "type": "reg",
      "idx_hi": 3,
      "idx_lo": 0
    }
  ]
}
```

### Generating the test bench

Now we can generate a testbench!

    python3 benchgen.py flopr.json > testbench_flopr.sv


### Creating test vectors

The test vectors file will need at least 1 vector, and can include comments.

Here's the contents of `vectors_flopr.dat`:

```
// Reset the flip-flop.
F_1_1_0_0
F_0_0_0_0
// Store the value 0xA in the flip-flop.
F_1_0_A_A
F_0_0_0_A
F_1_0_0_0
```

The first 4 bits are the `enable` flag, and the fields following are separated by underscores.
This test vector from left-to-right reads:

| Bit width | Padded Hex Width | Field Name |
|-----------|------------------|------------|
| 4 | 1 | `enable` |
| 1 | 1 | `clk` |
| 1 | 1 | `reset` |
| 4 | 1 | `d` |
| 4 | 1 | `q` |

Fields wider than 4 bits are assumed to use `ceil(# of bits / 4)` hex digits (5 bits would take 2 hex digits, 11 bits would take 3 hex digits, etc.).
The test vector internally will correctly handle the bit slicing required to extract the fields, all you have to do is provide the vectors.


### Simulating in ModelSim

To simulate your test bench in ModelSim on the command line:

    vlog -novopt *.sv
    vsim -c -novopt work.testbench_flopr -do "run 5000"


## License

This project is released under the [MIT License][mit-license].

   [mit-license]: https://opensource.org/licenses/MIT
