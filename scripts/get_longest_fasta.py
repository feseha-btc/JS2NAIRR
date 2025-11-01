#!/usr/bin/env python3

"""

get_longest_fasta.py

---------------------

Reads a FASTA file and writes the longest sequence entry to a new FASTA file.


Usage:

    python get_longest_fasta.py input.fasta output.fasta


Author: F. Abebe-Akele

Version: 1.0

Date: October 2025

"""


import sys


def read_fasta(file_path):

    """Generator to read FASTA sequences from a file."""

    header, seq = None, []

    with open(file_path, 'r') as f:

        for line in f:

            line = line.strip()

            if not line:

                continue

            if line.startswith('>'):

                if header:

                    yield header, ''.join(seq)

                header = line

                seq = []

            else:

                seq.append(line)

        if header:

            yield header, ''.join(seq)


def find_longest_fasta(input_file, output_file):

    """Finds and writes the longest sequence in the FASTA file."""

    longest_header = None

    longest_seq = ""

    max_len = 0


    for header, seq in read_fasta(input_file):

        seq_len = len(seq)

        if seq_len > max_len:

            longest_header = header

            longest_seq = seq

            max_len = seq_len


    if longest_header:

        with open(output_file, 'w') as out:

            out.write(f"{longest_header}\n")

            # wrap sequence lines to 80 characters per FASTA convention

            for i in range(0, len(longest_seq), 80):

                out.write(longest_seq[i:i+80] + '\n')


        print(f"✅ Longest sequence written to '{output_file}'")

        print(f"Header: {longest_header}")

        print(f"Length: {max_len:,} bases")

    else:

        print("⚠️ No sequences found in the input file.")


if __name__ == "__main__":

    if len(sys.argv) != 3:

        print("Usage: python get_longest_fasta.py input.fasta output.fasta")

        sys.exit(1)


    find_longest_fasta(sys.argv[1], sys.argv[2])

