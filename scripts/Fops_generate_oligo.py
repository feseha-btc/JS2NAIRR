#!/usr/bin/env python3
import sys
import os
def sliding_oligos(fasta_file: str, oligo_length: int = 18, step: int = 1, output_file: str = "oligos.fasta"):
    """
    Create overlapping oligos from a multi-FASTA file using a sliding window.
    
    fasta_file: input FASTA
    oligo_length: length of each oligo
    step: number of bases to slide (1 = maximum overlap)
    output_file: output FASTA
    """
    sequences = {}
    try:
        with open(fasta_file, "r") as f:
            seq_id = None
            seq_list = []
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if seq_id:
                        sequences[seq_id] = "".join(seq_list).upper() # Store sequences as uppercase
                    # Take only the first word as the ID, ignoring any description after a space
                    seq_id = line[1:].split()[0]
                    seq_list = []
                else:
                    seq_list.append(line)
            if seq_id:
                sequences[seq_id] = "".join(seq_list).upper()
    except FileNotFoundError:
        print(f"Error: Input file '{fasta_file}' not found. Please ensure it exists.", file=sys.stderr)
        return False
        
    with open(output_file, "w") as out:
        total_oligos = 0
        for seq_id, seq in sequences.items():
            count = 1
            # The range ensures we stop when there are not enough bases left for a full oligo
            for i in range(0, len(seq) - oligo_length + 1, step):
                oligo_seq = seq[i:i + oligo_length]
                # Format sequence ID as "OriginalID_001"
                out.write(f">{seq_id}_{count:03d}\n{oligo_seq}\n")
                count += 1
                total_oligos += 1
    
    print(f"Oligos successfully written to {output_file}")
    print(f"    Generated {total_oligos} oligos from {len(sequences)} sequences.")
    return True
def main():
    # --- Default Configuration ---
    fasta_file_master = sys.argv[1] # "all_sequences.fasta"
    oligo_length = 18
    step_size = 1
    # --- Argument Parsing and Overrides ---
    
    num_args = len(sys.argv) - 1 # number of arguments provided (excluding script name)
    if num_args > 3:
        print("Usage: python Fops_generate_oligo.py [fasta_file] [oligo_length] [step_size]", file=sys.stderr)
        print(f"Defaults: {fasta_file_master} {oligo_length} {step_size}", file=sys.stderr)
        sys.exit(1)
        
    if num_args >= 1:
        # Argument 1: Master FASTA File Path (overrides default)
        fasta_file_master = sys.argv[1]
    
    if num_args >= 2:
        # Argument 2: Oligo Length (overrides default)
        try:
            oligo_length = int(sys.argv[2])
            if oligo_length < 1:
                raise ValueError
        except ValueError:
            print(f"Error: Oligo length must be a positive integer. Received: {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)
    if num_args >= 3:
        # Argument 3: Step Size (overrides default)
        try:
            step_size = int(sys.argv[3])
            if step_size < 1:
                raise ValueError
        except ValueError:
            print(f"Error: Step size must be a positive integer. Received: {sys.argv[3]}", file=sys.stderr)
            sys.exit(1)
            
    # Report configuration
    print(f"\nConfiguration:")
    print(f"  Master FASTA: {fasta_file_master}")
    print(f"  Oligo Length: {oligo_length}")
    print(f"  Step Size: {step_size}")
    
    # --- Olige Generation ---
    
    # 1. Process the master file (argument 1 or default)
    print(f"\n⚙ Processing Master File: {fasta_file_master}")
    master_output = "master_oligos.fasta"
    # Use the parsed/default values for oligo_length and step
    sliding_oligos(fasta_file_master, oligo_length=oligo_length, step=step_size, output_file=master_output)
    
    # 2. Process the longest sequence file (fixed name: longest_seq.fasta)
    fasta_file_query = "longest_seq.fasta"
    query_output = "query_oligos.fasta"
    
    # Check if the required query file exists before proceeding
    if not os.path.exists(fasta_file_query):
        print(f"\n⚠ Warning: Query file '{fasta_file_query}' not found. Skipping query oligo generation.")
    else:
        print(f"\n⚙ Processing Query File: {fasta_file_query}")
        # Use the same parsed length and step for the query file
        sliding_oligos(fasta_file_query, oligo_length=oligo_length, step=step_size, output_file=query_output)
if __name__ == "__main__":
    main()
