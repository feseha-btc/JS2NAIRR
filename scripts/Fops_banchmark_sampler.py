import sys
import os
import random
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from typing import List
# List of target sequence counts as specified by the user
TARGET_COUNTS = (
    list(range(10, 101, 10)) + # 10, 20, 30, ..., 100 (10 files)
    list(range(200, 1001, 100)) + # 200, 300, ..., 1000 (9 files)
    [2000, 3000, 4000, 5000] # 2000, 3000, 4000, 5000 (4 files)
)
def create_subsets(input_fasta_path: str):
    """
    Reads a master FASTA file, generates multiple smaller FASTA files 
    based on predefined sequence counts, and saves the list of created 
    filenames to 'sampler.txt'.
    """
    
    # 1. Load all sequences
    try:
        print(f"Reading master FASTA file: {input_fasta_path}")
        all_sequences: List[SeqRecord] = list(SeqIO.parse(input_fasta_path, "fasta"))
    except FileNotFoundError:
        print(f"Error: Input file '{input_fasta_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading FASTA file: {e}", file=sys.stderr)
        sys.exit(1)
        
    total_count = len(all_sequences)
    print(f"Total sequences available in master file: {total_count}")
    
    if total_count == 0:
        print("Error: Master file is empty. Exiting.", file=sys.stderr)
        sys.exit(1)
    # Prepare for output file naming
    base_name = os.path.splitext(os.path.basename(input_fasta_path))[0]
    output_dir = os.path.dirname(input_fasta_path) or '.'
    
    files_created = 0
    created_filenames = [] # List to store names for sampler.txt
    
    # Randomly shuffle the sequences once to ensure subsets are random 
    random.shuffle(all_sequences)
    
    for target_count in TARGET_COUNTS:
        
        # 2. Check if the target count is possible
        if target_count > total_count:
            print(f"Skipping subset for {target_count} sequences (only {total_count} available).")
            continue
            
        # 3. Sample the sequences
        # Taking the first N sequences after shuffling provides a random subset
        subset_sequences = all_sequences[:target_count]
        
        # 4. Construct the output file path
        # Example: 'sequences_master_100.fasta'
        output_filename = f"{base_name}_{target_count}.fasta"
        output_path = os.path.join(output_dir, output_filename)
        
        # 5. Write the subset
        try:
            SeqIO.write(subset_sequences, output_path, "fasta")
            print(f"Created subset file: {output_path} ({target_count} sequences)")
            files_created += 1
            created_filenames.append(output_filename) # Record the file name
        except Exception as e:
            print(f"Warning: Could not write file {output_path}. Error: {e}", file=sys.stderr)
            
    # 6. Write the list of created filenames to sampler.txt
    sampler_path = os.path.join(output_dir, "sampler.txt")
    try:
        with open(sampler_path, 'w') as f:
            f.write('\n'.join(created_filenames) + '\n')
        print(f"\nSuccessfully wrote {files_created} filenames to '{sampler_path}'.")
    except Exception as e:
        print(f"Error writing to sampler.txt: {e}", file=sys.stderr)
    print(f"\nCompleted. Total subset files created: {files_created}")
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_fasta_subsets.py <input_fasta_file>", file=sys.stderr)
        print("\nNote: Requires the 'biopython' package.", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1]
    create_subsets(input_file)
