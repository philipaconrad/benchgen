# Testbench Generator for SystemVerilog Modules.
# Copyright (c) Philip Conrad, 2019. All rights reserved.
# Released under the MIT License.
# Description:
#   This script generates a SystemVerilog test bench based upon a module
#   description file (JSON format).
#   Test vectors are expected to be generated separately.
# Limitations:
#   This tool can only generate one test bench at a time.


# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import math
import json

# Command line handling.
import sys
import argparse


# ----------------------------------------------------------------------------
# Template
# ----------------------------------------------------------------------------
template_bench = """// Testbench for module '{module_name}'.
// WARNING: This file is auto-generated. IF EDITING MANUALLY, YOUR CHANGES MAY BE OVERWRITTEN.
// To generate a test bench like this one, see the "Benchgen" project on Github.
//   https://github.com/philipaconrad/benchgen

module testbench_{module_name};

    // Function for displaying a test vector like it appears in the source.
    // Cite: https://www.verificationguide.com/p/systemverilog-functions.html (function syntax)
    function void display_vector(input [{vec_hi_idx}:{vec_lo_idx}] vec);
        begin
            // Print bit slices back with the '_' formatting.
            // Cite: https://electronics.stackexchange.com/a/50828
            $write("{vec_format_str}",
{vec_format_params});
        end
    endfunction

    // Input declarations.
{input_decls}

    // Testbench variables.
    logic [{vec_hi_idx}:{vec_lo_idx}] vectors [999:0]; // 1e3 test vectors
    logic [{vec_hi_idx}:{vec_lo_idx}] current;         // Current test vector
    logic [31:0] i;                // Vector subscript
    logic [3:0] enable;            // Test vector enable
    logic [31:0] error;            // Error counter

    initial begin
{initial_begin_inputs}
        i     = 0;
        error = 0;
    end

    // Instantiate device under test.
    {module_name} dut ({dut_inputs});

    initial begin
        // Load test vectors from disk.
        $readmemh("vectors_{module_name}.dat", vectors);

        for (i = 0; i < 1000; i = i + 1) begin
            current = vectors[i];

            // Pull out enable, ... signals to stimulate the DUT.
{enable_stimulate_block}
{dut_stimulate_block}

            // Check to see if this test vector is used or not.
            // Vectors in-use always start with 1111.
            if (enable === 4'b1111) begin
                // Give the ALU time to respond.
                #10;

                // Check the result.
                if ({output_check_expr}) begin
                    error += 1;
                    $write("Vector failed at index: %4d  ", i);
                    display_vector(current);
                    $display(""); // Newline at the end.
                end
            end
            if (enable === 4'bx) begin
                $display("%4d tests completed with %4d errors", i, error);
                $stop();
            end
        end

        // Tell the simulator we're done.
        $stop();
    end

endmodule"""


# ----------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------

# Cite: https://stackoverflow.com/a/21101086
def round_to_8(x, base=8):
    return int(base * math.ceil(float(x) / base))


def compute_field_bit_width(idx_hi, idx_lo):
    return (idx_hi+1) - idx_lo


def compute_field_bit_width_hex(idx_hi, idx_lo):
    return round_to_8(compute_field_bit_width(idx_hi, idx_lo), base=4) // 4


def generate_vector_format_str(field_lengths_hex):
    # The enable flag is always concatenated to the front.
    out = "%1h"
    for length in field_lengths_hex:
        out += "_%0{}h".format(length)
    return out


# Used to generate the exact slice indices for pulling out test vector parts.
def generate_bit_slice_indices(field_lengths_hex, exact_bit_width_tuples):
    out = []
    field_lengths_hexbits = [x * 4 for x in field_lengths_hex]
    top = sum(field_lengths_hexbits)
    for (hex_length, (idx_hi, idx_lo)) in zip(field_lengths_hexbits,
                                              exact_bit_width_tuples):
        width = compute_field_bit_width(idx_hi, idx_lo)
        out_lo = (top - hex_length)
        out_hi = (out_lo + width) - 1
        out.append((out_hi, out_lo))
        top -= hex_length  # Skip to next field in the vector.
    return out


# ----------------------------------------------------------------------------
# Code generation functions
# ----------------------------------------------------------------------------

def codegen_format_params(slice_index_tuples):
    out = ""
    i = 0
    len_tuples = len(slice_index_tuples)
    for idx_hi, idx_lo in slice_index_tuples:
        if i > 0:
            out += "\n"  # No newline before first line.
        out += (" " * 19) + "vec[{idx_hi}:{idx_lo}]".format(idx_hi=idx_hi,
                                                            idx_lo=idx_lo)
        i += 1
        if i < len_tuples:
            out += ","  # No comma after last line.
    return out


# Takes a list of dictionaries.
def codegen_input_decls(variables_list):
    out = ""
    # Put inputs together.
    out += "\n    // Inputs.\n"
    for v in variables_list:
        if v["io_type"] == "input":
            out += (" " * 4)  # Indentation level.
            out += "logic [{idx_hi}:{idx_lo}] {name};".format(idx_hi=v["idx_hi"], idx_lo=v["idx_lo"], name=v["name"])
            out += "\n"
    # Put outputs together.
    out += "\n    // Outputs.\n"
    for v in variables_list:
        if v["io_type"] == "output":
            out += (" " * 4)  # Indentation level.
            out += "logic [{idx_hi}:{idx_lo}] {name};".format(idx_hi=v["idx_hi"], idx_lo=v["idx_lo"], name=v["name"])
            out += "\n"
    # Put expected outputs together.
    out += "\n    // Expected Outputs.\n"
    for v in variables_list:
        if v["io_type"] == "output":
            out += (" " * 4)  # Indentation level.
            out += "logic [{idx_hi}:{idx_lo}] {name}_e;".format(idx_hi=v["idx_hi"], idx_lo=v["idx_lo"], name=v["name"])
            out += "\n"
    return out


def codegen_initial_begin_decls(variables_list):
    out = ""
    max_name_length = max([len(v["name"]) for v in variables_list])
    for v in variables_list:
        if v["io_type"] == "input":
            out += (" " * 8)
            out += ("{:" + str(max_name_length) + "} = 0;").format(v["name"])
            out += "\n"
    return out


def codegen_dut_stimulate_block(variables_list, bit_slices_list):
    out = ""
    max_name_length = max([len(v["name"]) for v in variables_list]) + 2
    for (v, (idx_hi, idx_lo)) in zip(variables_list, bit_slices_list):
        out += (" " * 12)  # Indentation level.
        if v["io_type"] == "input":
            out += "{:{width}} = current[{idx_hi}:{idx_lo}];".format(v["name"], width=max_name_length, idx_hi=idx_hi, idx_lo=idx_lo)
        elif v["io_type"] == "output":
            out += "{:{width}} = current[{idx_hi}:{idx_lo}];".format(v["name"] + "_e", width=max_name_length, idx_hi=idx_hi, idx_lo=idx_lo)
        out += "\n"
    return out


def codegen_output_check_expr(variables_list):
    out = ""
    i = 0
    for v in variables_list:
        if i > 0:
            out += " || "
        if v["io_type"] == "output":
            out += "{name} != {name}_e".format(name=v["name"])
            i += 1
    return out


# ----------------------------------------------------------------------------
# Application code
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Command-line interface.
    # Cite: https://stackoverflow.com/a/11038508
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)

    # Parse command line args.
    args = parser.parse_args()

    text = args.infile.read()
    j = json.loads(text)

    # Build useful variables for later use in the template.
    module_name = j["module_name"]

    parameters = j["parameters"]
    parameter_names = [x["name"] for x in j["parameters"]]
    parameter_widths = [(x["idx_hi"], x["idx_lo"]) for x in j["parameters"]]
    parameter_hex_widths = [compute_field_bit_width_hex(idx_hi, idx_lo)
                            for (idx_hi, idx_lo) in parameter_widths]
    parameter_hex_bit_widths = [x * 4 for x in parameter_hex_widths]

    vec_hi_idx = (sum(parameter_hex_bit_widths) + 4) - 1  # 4 bits for enable flag.
    vec_lo_idx = 0
    vec_format_str = generate_vector_format_str(parameter_hex_widths)
    vec_bit_slices = generate_bit_slice_indices(parameter_hex_widths, parameter_widths)

    inputs = [x for x in j["parameters"] if x["type"] == "input"]
    input_names = [x["name"] for x in inputs]

    outputs = [x for x in j["parameters"] if x["type"] == "output"]
    output_names = [x["name"] for x in outputs]

    # Print the filled-in template to the specified file.
    # Default: sys.stdout
    print(template_bench.format(
              module_name=module_name,
              vec_format_str=vec_format_str,
              vec_format_params=codegen_format_params([(vec_hi_idx, vec_hi_idx - 3)] + vec_bit_slices),
              vec_hi_idx=vec_hi_idx,
              vec_lo_idx=vec_lo_idx,
              input_decls=codegen_input_decls(parameters),
              initial_begin_inputs=codegen_initial_begin_decls(parameters),
              dut_inputs=", ".join([v["name"] for v in parameters]),
              enable_stimulate_block="            enable = current[{}:{}];\n".format(vec_hi_idx, vec_hi_idx-3),
              dut_stimulate_block=codegen_dut_stimulate_block(parameters, vec_bit_slices),
              output_check_expr=codegen_output_check_expr(parameters),
          ), file=args.outfile)
