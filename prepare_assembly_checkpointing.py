#!/usr/bin/env python3

"""
Author: Samuel Aroney
Prepare coassemblies for Assembly checkpointing
Create yaml file
"""

import sys
import argparse
import logging
import re
import os

def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")

    parser.add_argument("--input", help="Input list of concatenated _1.fastq.gz files")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--assembler", help="Assembler to use", default="megahit")
    parser.add_argument("--threads", help="Number of threads to use", default=32)
    parser.add_argument("--mem_mb", help="Memory to use", default=256000)
    parser.add_argument("--runtime", help="Runtime for each coassembly", default="48h")

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

    with open(args.input, "r") as f:
        forward = [s.strip() for s in f.readlines()]

    logging.info(f"Read {len(forward)} forward reads")

    reverse = [s.replace("_1.fastq.gz", "_2.fastq.gz") for s in forward]
    coassemblies = [re.search(r"(coassembly_\d+)", s).group(0) for s in forward]

    logging.info(f"Processing coassemblies, e.g. {coassemblies[0]}: {forward[0]}, {reverse[0]}")
    for coassembly, r1, r2 in zip(coassemblies, forward, reverse):
        with open(f"{output}/{coassembly}.yaml", "w") as f:
            f.write(f"assembler: {args.assembler}\n")
            f.write(f"output_directory: {output}/{coassembly}\n")
            f.write(f"r1: {r1}\n")
            f.write(f"r2: {r2}\n")
            f.write(f"threads: {args.threads}\n")
            f.write(f"resources:\n")
            f.write(f"  runtime: {args.runtime}\n")
            f.write(f"  mem_mb: {args.mem_mb}\n")

    logging.info("Done")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
