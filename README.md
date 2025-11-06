# JS2NAIRR  -  FOPS
## Fuzzy Oligo Primer Screening (FOPS): A GPU-Accelerated Degenerate Fuzzy Oligo Finder

## Project Overview

This repository hosts the tar.gz  compressed tool which contains the scripts and data folders. The scripts contain all scripts required fro generating the fuzzy oligos where as the data folder contains a demo data from the Fungal 18S sequences.

📂 ## Repository Structure
The project is organized into the following four primary directories:

## 1. FOPS_MAIN
This folder holds all scripts and demo data nedded to test the tool.

A wrapper script - code_runner_FOPS.sh is provided to excute the tool from a single command.

When invoked with a file containing a list of fasta files, for each file in the list it calls the following scripts in the order:
  - Fops_get_longest_sequence.py  which selects the longest sequence of the input file and create file called longest_seq.fasta
  - Fops_genetrate_oligos.py which takes both the input fasta file and the longest sequence just saved to file to create oligo nucleotides.
  -     from longest_seq.fasta  it creates query_oligos.fasta
  -     from the input file it creates master_oligos.fasta
  - Fops_geminiSimpleCluster_GPU.py which takes query_oligos.fasta and master_oligos.fasta as input and creates the list of query oligos that matched to the master_oligos.file. This will produce a dynamically named file with the results.
  - Fops_generate_report.py on the resulting dynamically created results file to reduce the matches to those that have 90% or better match scores.

The resulting CSV file can be dowownloaded and opened with EXCEL to manually and visually curate the matching oligo candidates for the desired PCR setup.
  
2. Documents

3. Tutorial
This folder is reserved for all code, data and instructions pertaining to a tutorial aimed at introducing the tool to potential users.
• tutorial.md (or similar tutorial files)
• instructions on fetching data (NCBI, SRA)
• parameter tweaking
• parctice data

5. miscellanewos
This folder can hold configuration files, license files, environment setup files, or any other items that do not fit into the primary categories.
    • environment.yml or requirements.txt (for dependency management)
    • LICENSE file
    • Any temporary test data or logs.

🚀 Getting Started
To run the pipeline, you will need Python 3 and PyTorch with CUDA support configured for your system.
1. Place your source sequences (all_sequences.fasta)
2. Create a query oligo set by running first find_longest_fasta.py and then the generate oligo script on it
3. Alternately, provide your own query sequences named as (query_oligos.fasta) into the Data folder.
4. Execute the main workflow script from the project root
5. bash Scripts/run_workflow.sh
6. The final results will be available in the Data/final_cluster_report.csv.
7. The project is best used after attending the tutorial.

