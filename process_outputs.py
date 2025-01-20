#!/usr/bin/env python3

"""
Author: Samuel Aroney
Process Assembly checkpointing outputs
- Folder for renamed coassemblies (megahit/assembly_output/final.contigs.fa)
- Folder for megahit/assembly_output/log and coassembly_*.log
- Folder for megahit/assembly_output/options.json
- Combined benchmarking file
"""

import sys
import argparse
import logging
import os
import polars as pl
import extern

def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")

    parser.add_argument("--input", nargs="+", help="List of output directories")
    parser.add_argument("--output", help="Output directory")

    args = parser.parse_args(arguments)

    # Setup logging
    if args.debug:
        loglevel = logging.DEBUG
    elif args.quiet:
        loglevel = logging.ERROR
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p")

    output = os.path.abspath(args.output)
    logging.info(f"Output directory: {output}")

    output_contigs = os.path.join(output, "contigs")
    os.makedirs(output_contigs, exist_ok=True)
    output_logs = os.path.join(output, "logs")
    os.makedirs(output_logs, exist_ok=True)

    benchmarks_list = []
    coassembly_contig_files = {
        "name": [],
        "assembly": [],
    }
    for coassembly in args.input:
        coassembly_name = coassembly.replace("./", "")
        logging.info(f"Processing {coassembly_name}")

        main_log = coassembly + ".log"
        # List folders in coassembly
        assembler_dir = os.listdir(coassembly)
        if len(assembler_dir) == 0:
            logging.error(f"No assembler directories found in {coassembly}")
            raise FileNotFoundError
        elif len(assembler_dir) > 1:
            logging.error(f"Multiple assembler directories found in {coassembly}: {assembler_dir}")
            raise FileNotFoundError
        assembler = assembler_dir[0]

        if assembler == "megahit":
            contigs = os.path.join(coassembly, assembler, "assembly_output", "final.contigs.fa")
            options = os.path.join(coassembly, assembler, "assembly_output", "options.json")
            log = os.path.join(coassembly, assembler, "assembly_output", "log")

            benchmark_dir = os.path.join(coassembly, assembler, "benchmark")
            benchmarks = {f.replace(".tsv", ""): os.path.join(benchmark_dir, f) for f in os.listdir(benchmark_dir)}
        elif assembler == "metaspades":
            raise NotImplementedError
        else:
            logging.error(f"Unknown assembler: {assembler}")
            raise ValueError

        # Copy contigs and rename
        coassembly_contig_files["name"].append(coassembly_name)
        coassembly_contig_files["assembly"].append(os.path.abspath(contigs))
        contigs_output = os.path.join(output_contigs, f"{coassembly_name}.contigs.fasta")
        extern.run(f"cp {contigs} {contigs_output}")

        # Copy logs and options and rename
        extern.run(f"cp {main_log} {output_logs}")
        extern.run(f"cp {log} {output_logs}/{coassembly_name}_assembler.log")
        extern.run(f"cp {options} {output_logs}/{coassembly_name}.options.json")

        # Load benchmarks into DataFrame
        for benchmark_name, benchmark_file in benchmarks.items():
            benchmarks_list.append(
                pl.scan_csv(benchmark_file, separator="\t")
                .with_columns(
                    benchmark=pl.lit(benchmark_name),
                    coassembly=pl.lit(coassembly_name),
                    )
            )

    benchmarks_df = pl.concat(benchmarks_list).collect()
    benchmarks_df.write_csv(os.path.join(output, "benchmarks.tsv"), separator="\t")

    coassembly_contig_df = pl.DataFrame(coassembly_contig_files)
    coassembly_contig_df.write_csv(os.path.join(output, "coassembly_contigs.tsv"), separator="\t")

    logging.info("Done")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
