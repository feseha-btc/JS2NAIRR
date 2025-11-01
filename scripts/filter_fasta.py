#!/usr/bin/env python3

import sys


def deduplicate_fasta(input_fasta, output_fasta="deduplicated.fasta"):

    """

    Removes identical sequences from a multi-FASTA file.

    Keeps the first occurrence of each unique sequence.

    """

    seen = {}

    with open(input_fasta, "r") as infile:

        seq_id = None

        seq_list = []

        for line in infile:

            line = line.strip()

            if line.startswith(">"):

                if seq_id:

                    seq = "".join(seq_list)

                    if seq not in seen:

                        seen[seq] = seq_id

                seq_id = line[1:]

                seq_list = []

            else:

                seq_list.append(line)

        # add the last sequence

        if seq_id:

            seq = "".join(seq_list)

            if seq not in seen:

                seen[seq] = seq_id


    with open(output_fasta, "w") as outfile:

        for seq, seq_id in seen.items():

            outfile.write(f">{seq_id}\n{seq}\n")


    print(f"✅ Deduplicated FASTA written to {output_fasta}")

    print(f"Unique sequences retained: {len(seen)}")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Usage: python dedup_fasta.py <input.fasta> [output.fasta]")

        sys.exit(1)

    

    input_fasta = sys.argv[1]

    output_fasta = sys.argv[2] if len(sys.argv) > 2 else "deduplicated.fasta"

    deduplicate_fasta(input_fasta, output_fasta)

