#!/usr/bin/env python3
import sys
def sliding_oligos(fasta_file, oligo_length=18, step=1, output_file="oligos.fasta"):
    """
    Create overlapping oligos from a multi-FASTA file.
    
    fasta_file: input FASTA
    oligo_length: length of each oligo
    step: number of bases to slide (1 = maximum overlap)
    output_file: output FASTA
    """
    sequences = {}
    with open(fasta_file, "r") as f:
        seq_id = None
        seq_list = []
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if seq_id:
                    sequences[seq_id] = "".join(seq_list)
                seq_id = line[1:]
                seq_list = []
            else:
                seq_list.append(line)
        if seq_id:
            sequences[seq_id] = "".join(seq_list)
    with open(output_file, "w") as out:
        for seq_id, seq in sequences.items():
            count = 1
            for i in range(0, len(seq) - oligo_length + 1, step):
                oligo_seq = seq[i:i+oligo_length]
                out.write(f">{seq_id}_{count:03d}\n{oligo_seq}\n")
                count += 1
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_oligos.py <input.fasta> [oligo_length] [step] [output.fasta]")
        sys.exit(1)
    
    fasta_file = sys.argv[1]
    oligo_length = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    output_file = sys.argv[4] if len(sys.argv) > 4 else "oligos.fasta"
    
    sliding_oligos(fasta_file, oligo_length, step, output_file)
    print(f"Oligos written to {output_file}")
