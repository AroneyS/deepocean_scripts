#!/usr/bin/env python3

"""
Author: Samuel Aroney
Extract completed assemblies
"""

import sys
import argparse
import logging
import os
import shutil


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")

    parser.add_argument("--input", help="Assembly results folder")
    parser.add_argument("--output", help="Output folder")

    args = parser.parse_args(arguments)

    # Setup logging
    if args.debug:
        loglevel = logging.DEBUG
    elif args.quiet:
        loglevel = logging.ERROR
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p")

    # Search args.output for files within /assemblies/*done and get the path without the .done extension
    assemblies_folder = os.path.join(args.input, "assemblies")
    assemblies = [os.path.join(assemblies_folder, f.replace(".done", "")) for f in os.listdir(assemblies_folder) if f.endswith(".done")]

    for assembly in assemblies:
        assembly_name = os.path.basename(assembly)
        logging.info(f"Copying {assembly_name} to {args.output}")

        try:
            contigs_path = os.path.join(assembly, f"final_contigs.fa")
            assert os.path.exists(contigs_path)
        except AssertionError:
            logging.error(f"Metaspades output not yet supported: {assembly}")
            continue

        output_path = os.path.join(args.output, assembly_name + ".fa")
        shutil.copyfile(contigs_path, output_path)

    logging.info("Done")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
