# JS2NAIRR  -  FOPS
## Fuzzy Oligo Primer Screening (FOPS): A GPU-Accelerated Degenerate Fuzzy Oligo Finder

## Project Overview

This repository hosts the tar.gz  compressed tool which contains the scripts and data folders. The scripts contain all scripts required fro generating the fuzzy oligos where as the data folder contains a demo data from the Fungal 18S sequences.

## Repository Structure 📂 
The project is organized into the following four primary directories:

## 1. FOPS_MAIN
This folder holds all scripts and demo data nedded to test the tool.

A wrapper script - code_runner_FOPS.sh is provided to excute the tool from a single command.

When invoked with a file containing a list of fasta files, for each file in the list it calls the following scripts in the order:
  1. Fops_get_longest_sequence.py  which selects the longest sequence of the input file and create file called longest_seq.fasta
  2. Fops_genetrate_oligos.py which takes both the input fasta file and the longest sequence just saved to file to create oligo nucleotides.
      - from longest_seq.fasta  it creates query_oligos.fasta
      - from the input file it creates master_oligos.fasta
  3. Fops_geminiSimpleCluster_GPU.py which takes query_oligos.fasta and master_oligos.fasta as input and creates the list of query oligos that matched to the master_oligos.file. This will produce a dynamically named file with the results.
  4. Fops_generate_report.py on the resulting dynamically created results file to reduce the matches to those that have 90% or better match scores.

The resulting CSV file can be dowownloaded and opened with EXCEL to manually and visually curate the matching oligo candidates for the desired PCR setup. For each multi fasta file processed, you should see an analysis folder with time stamp inside which the HPV 90% filtered CSV files to analyze using excel.
  
## 2. Documents
   The Documents fiile contains non code documents related to the project.

## 3. Tutorial
This folder is a work in progress and reserved for all code, data and instructions pertaining to a tutorial aimed at introducing the tool to potential users.
• tutorial.md (or similar tutorial files)
• instructions on fetching data (NCBI, SRA)
• parameter tweaking
• parctice data

## 4. miscellanewos
This folder can hold configuration files, license files, environment setup files, or any other items that do not fit into the primary categories.
    • environment.yml or requirements.txt (for dependency management)
    • LICENSE file
    • Any temporary test data or logs.

# Getting Started 🚀 

To use the tool, you will need Python3 and PyTorch with CUDA support configured for your system.
The tool is also optimized for GPU processors.

1. Download the FOPS.tar.gz file to a convenient location.
   
3. Uncompress it:   tar -xvzf FOPS.tar.gz which creates tje FOPS directory with all contents.
   
5. Change directory to FOPS where you will see three things:
     i. the code_runner_FOPS.sh bash script,
    ii. the data folder and
   iii. scripts folders.
   
6. Call the code runner script with a single file argument as follows:
        bash code_runner_FOPS.sh  files_list.txt
    Where files_list.txt is a text file with the name(s) of multifasta file(s) (1 or more) with one file name per line
    for each file that has a collection of fasta sequences from which the user desires to find degenerate (fuzzy) oligos to use as PCR primers.

7. For ease of use
   
    A). explore the data directory to understand the setup and replicate the work as follows:
   
    B). Create a directory like my_data (forexample), put your sequence file(s) in it
   
    C). cd into my_data and call the code runner like this:  bash ../code_runner_FOPS.sh list_of_Files.txt
   
9. Sit back and wait for the program to finish.
10. Read the standard output and follow the file structures to get your oligos.

