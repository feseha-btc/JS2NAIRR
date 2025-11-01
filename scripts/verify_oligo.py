# verify_cluster.py


import sys

import itertools

import subprocess

import os

import re


# Define the degenerate bases and their non-degenerate equivalents

DEGENERATE_BASES = {

    'R': ['A', 'G'],    # Purine

    'Y': ['C', 'T'],    # Pyrimidine

    'S': ['G', 'C'],    # Strong

    'W': ['A', 'T'],    # Weak

    'K': ['G', 'T'],    # Keto

    'M': ['A', 'C'],    # Amino

    'B': ['C', 'G', 'T'], # Not A

    'D': ['A', 'G', 'T'], # Not C

    'H': ['A', 'C', 'T'], # Not G

    'V': ['A', 'C', 'G'], # Not T

    'N': ['A', 'C', 'G', 'T'] # Any base

}


def generate_variations(oligo_sequence):

    """

    Generates all non-degenerate variations of an oligo sequence.

    It focuses on the case where 3 positions are 'N' (A,C,G,T).

    """

    # 1. Identify the degenerate positions and their possible substitutions

    substitutions = []

    

    # We assume 'N' for the three degenerate positions as per the prompt (4x4x4)

    # The script can handle any degenerate base from the IUPAC codes

    for base in oligo_sequence:

        if base in DEGENERATE_BASES:

            substitutions.append(DEGENERATE_BASES[base])

        else:

            substitutions.append([base]) # Non-degenerate bases just map to themselves


    # 2. Use itertools.product to get all combinations

    all_combinations = list(itertools.product(*substitutions))


    # 3. Join the characters in each combination to form the new oligo sequences

    variations = [''.join(combo) for combo in all_combinations]

    

    # Filter only variations that contain 'N' bases if the user didn't specify the bases

    # If the user specified a sequence like 'ATNNNTC', this returns the 64 variations.

    return variations



def count_hits_with_grep(fasta_file, oligo_variations, output_file, oligo_name, original_oligo):

    """

    Placeholder for the counting logic. In a single-process environment, this runs serially.

    For a parallel environment, the list of variations would be split and run separately.

    

    NOTE: The prompt asks for the *unique* hit count (union). Grepping directly on a 

    FASTA file for multiple patterns and summing the counts will give the total 

    occurrences, *not* the count of unique sequences (FASTA headers) that contain *at least* one oligo.

    

    To get the union (unique sequences), we must:

    1. Grep for each variant.

    2. Extract the FASTA header (`>...`).

    3. Collect all unique headers.

    4. Count the unique headers.

    

    This implementation performs the unique sequence count (union) using subprocess and temporary files/sets.

    """

    

    print(f"Counting hits for {len(oligo_variations)} variations in {fasta_file}...")

    

    unique_fasta_headers = set()

    

    # The grep command will be:

    # grep -B1 '<oligo_variant>' <fasta_file> | grep '>'

    # -B1: Print the line before the match (the header)

    # The second grep filters for only the headers (' >')


    # --- Counting Unique Hits (Union) ---

    for i, variant in enumerate(oligo_variations):

        try:

            # -F: fixed string search (not regex)

            # -B1: Print 1 line of context before the match (the header)

            # We then pipe the output to grep '>' to only get the headers

            grep_command = f"grep -F -B1 '{variant}' '{fasta_file}' | grep '^>' "

            

            # Execute the command and capture the output

            result = subprocess.run(

                grep_command,

                shell=True,

                capture_output=True,

                text=True,

                check=True

            )

            

            # Add all unique headers found to the set

            # A set automatically handles uniqueness

            for line in result.stdout.splitlines():

                if line.startswith('>'):

                    # The line is the FASTA header, e.g., >Seq1_ID

                    unique_fasta_headers.add(line.strip())

            

        except subprocess.CalledProcessError as e:

            # Grep returns a non-zero exit code (1) if no matches are found. This is normal.

            # print(f"Warning: Grep failed for variant {variant} (no match or error): {e.stderr.strip()}")

            pass

        except Exception as e:

            print(f"An error occurred while processing variant {variant}: {e}")


    unique_hit_count = len(unique_fasta_headers)


    # 4. Write the final result to the output file

    with open(output_file, 'w') as f:

        f.write(f"{oligo_name}\t{original_oligo}\t{unique_hit_count}\n")

    

    print(f"\n--- Analysis Complete ---")

    print(f"Oligo: {original_oligo} ({len(oligo_variations)} variants)")

    print(f"Unique Sequences Found (Union): {unique_hit_count}")

    print(f"Result written to: {output_file}")



def main():

    if len(sys.argv) != 4:

        print("Usage: python verify_cluster.py <oligo_name> <oligo_sequence> <fasta_file>")

        print("Example: python verify_cluster.py Oligo_N ATNNNTC clusters.fasta")

        sys.exit(1)


    oligo_name = sys.argv[1]

    oligo_sequence = sys.argv[2].upper()

    fasta_file = sys.argv[3]

    output_file = f"{oligo_name}_hits.txt"


    # 1. Generate all variations (e.g., 64 variations for a 3-'N' sequence)

    oligo_variations = generate_variations(oligo_sequence)

    

    if len(oligo_variations) != 64:

        # Check if the number of variations is what's expected for 3 degenerate positions (4*4*4=64)

        # This is a good place to add a check for the user's input sequence if needed.

        pass


    # 2. Perform the count and write the result

    # **In a non-parallel environment, this runs the whole task serially.**

    count_hits_with_grep(fasta_file, oligo_variations, output_file, oligo_name, oligo_sequence)



if __name__ == "__main__":

    main()
