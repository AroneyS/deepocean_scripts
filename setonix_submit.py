#!/usr/bin/env python3
import os
import sys

from snakemake.utils import read_job_properties

# Adapted from https://ulhpc-tutorials.readthedocs.io/en/latest/bio/snakemake/#immediate_submit

# last command-line argument is the job script
jobscript = sys.argv[-1]

# all other command-line arguments are the dependencies
dependencies = set(sys.argv[1:-1])

# parse the job script for the job properties that are encoded by snakemake within
job_properties = read_job_properties(jobscript)

ncpus = ""
mem = ""
time = ""
account = ""
ntasks = ""

if "threads" in job_properties:
    ncpus = "-c " + str(job_properties["threads"])

if "resources" in job_properties:
    resources = job_properties["resources"]
    if "mem_mb" in resources:
        provided_mem = resources["mem_mb"]
        if provided_mem == "<TBD>":
            mem = ""
        else:
            mem = "--mem=" + str(resources["mem_mb"]) + "M"
    if "runtime" in resources:
        hours = resources["runtime"] // 60
        minutes = resources["runtime"] - (hours * 60)
        runtime = "{hours}:{minutes:02d}:{seconds:02d}".format(hours=hours, minutes=minutes, seconds=0)
        time = "-t " + str(resources["runtime"])
    else:
        time = "-t " + "6:00:00"
    if "account" in resources:
        account = "-A " + resources["account"]
    if "ntasks" in resources:
        ntasks = "-n " + str(resources["ntasks"])


# collect all command-line options in an array
cmdline = ["sbatch"]

# set all the slurm submit options as before
slurm_args = " {ncpus} {mem} {time} {account} {ntasks} ".format(
    ncpus=ncpus,
    mem=mem,
    time=time,
    account=account,
    ntasks=ntasks,
    )

cmdline.append(slurm_args)

if dependencies:
    # only keep numbers in dependencies list
    dependencies = [ x for x in dependencies if x.isdigit() ]
    cmdline.append("--dependency=afterok:" + ",".join(dependencies))

cmdline.append(jobscript)

os.system(" ".join(cmdline))
