"""
Snakemake script to submit assembly jobs to the cluster.

snakemake \
    --snakefile submit_assembly.smk --configfile config.yaml \
    --profile mqsub --retries 2 --use-conda \
    --rerun-incomplete --keep-going --nolock \
    --cores 64 --local-cores 4 --directory results
"""

#############
### Setup ###
#############
reads_1 = config["reads_1"]
reads_2 = config["reads_2"]
coassemblies = reads_1.keys()

#################
### Functions ###
#################
def get_assemble_assembler(wildcards, attempt):
    # Attempt 1+2 with Metaspades, then Megahit
    match attempt:
        case 1:
            assembler = "spades.py --meta"
        case 2:
            assembler = "megahit"
        case 3:
            assembler = "megahit"

    return assembler

def get_assemble_threads(wildcards, attempt):
    # Attempt 1 with 32, 2 with 64, then 32 with Megahit
    match attempt:
        case 1:
            threads = 48
        case 2:
            threads = 48
        case 3:
            threads = 32

    return threads

def get_assemble_memory(wildcards, attempt, unit=None):
    # Attempt 1 with 250GB, 2 with 500GB, then 250GB with Megahit
    match attempt:
        case 1:
            mem = 354
        case 2:
            mem = 354
            if not unit: unit = "B"
        case 3:
            mem = 250
            if not unit:
                # Megahit needs memory in bytes
                unit = "B"

    match unit:
        case "MB":
            mult = 1_000
        case "B":
            mult = 1_000_000
        case _:
            mult = 1

    return mem * mult

#############
### Rules ###
#############
rule all:
    input:
        expand("assemblies/{coassembly}.done", coassembly=coassemblies)

rule assembly:
    output:
        touch("assemblies/{coassembly}.done")
    params:
        reads_1 = lambda wildcards: reads_1[wildcards.coassembly],
        reads_2 = lambda wildcards: reads_2[wildcards.coassembly],
        dir = directory("assemblies/{coassembly}"),
    threads: lambda wildcards, attempt: get_assemble_threads(wildcards, attempt)
    resources:
        mem_mb = lambda wildcards, attempt: get_assemble_memory(wildcards, attempt, unit="MB"),
        mem_assembler = get_assemble_memory,
        runtime = "48h",
        assembler = get_assemble_assembler,
    log:
        "logs/{coassembly}.log"
    benchmark:
        "benchmarks/{coassembly}.tsv"
    conda:
        "assembly.yaml"
    shell:
        "rm -rf {params.dir} && "
        "{resources.assembler} "
        "-m {resources.mem_assembler} "
        "-1 {params.reads_1} "
        "-2 {params.reads_2} "
        "-t {threads} "
        "-o {params.dir} "
        "&> {log} "
