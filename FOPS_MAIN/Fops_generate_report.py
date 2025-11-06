import sys
import csv
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from datetime import datetime # Import datetime for timestamp
import os
# --- Configuration ---
# The maximum number of results (degenerate patterns) to keep for each unique oligo ID.
TOP_N_RESULTS = 5
# Minimum percentage hit required to keep a pattern (e.g., 80.0 for 80%)
MINIMUM_PERCENT_HIT = 80.0
# Base name for the output report file (timestamp will be appended)
OUTPUT_FILENAME_BASE = "Final_Report"
# ---------------------
def count_fasta_sequences(fasta_file_path):
    """
    Counts the number of sequence headers (lines starting with '>') in a FASTA file.
    Exits with an error if the file is not found.
    """
    count = 0
    try:
        with open(fasta_file_path, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    count += 1
        return count
    except FileNotFoundError:
        print(f"Error: Required FASTA file not found at '{fasta_file_path}'. Cannot calculate percentage hit.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the FASTA file: {e}", file=sys.stderr)
        sys.exit(1)
def calculate_and_cull_report(input_csv_path, TOTAL_COUNT, output_csv_path):
    """
    Reads a CSV file, calculates percentage hit, applies filtering rules (min
    percent, unique percent), culls to the top N, and prints the result to stdout.
    """
    try:
        # Check if total count is valid
        if TOTAL_COUNT <= 0:
            print(f"Error: Sequence count is zero. Cannot proceed.", file=sys.stderr)
            sys.exit(1)
            
        all_processed_rows = []
        
        # 1. READ ALL ROWS AND CALCULATE PERCENTAGES
        with open(input_csv_path, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            
            # Process header
            try:
                header = next(reader)
            except StopIteration:
                # Handle case of an empty file
                print(f"Warning: Input CSV '{input_csv_path}' is empty. No report generated.", file=sys.stderr)
                return
                
            min_percent_decimal = Decimal(MINIMUM_PERCENT_HIT)
            # Set to track unique (Query_ID, Percent_Hit_Value) combinations
            seen_keys = set() 
            
            # Process data rows, calculate percent, and store them
            for row in reader:
                if len(row) < 4:
                    print(f"Skipping malformed row: {row}", file=sys.stderr)
                    continue
                
                # Get the Match_Count from the 4th column (index 3)
                hits_str = row[3].strip()
                try:
                    hits_count = int(hits_str)
                except ValueError:
                    print(f"Warning: Non-numeric 'Match_Count' value '{hits_str}'. Skipping row.", file=sys.stderr)
                    continue
                
                # Calculate the percentage with high precision
                raw_percent = Decimal(hits_count) * Decimal(100) / Decimal(TOTAL_COUNT)
                
                # Format to two decimal places, rounding half up
                percent_hit = raw_percent.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Create a key for uniqueness check (Query_ID and Percent as string)
                query_id = row[0]
                unique_key = (query_id, str(percent_hit))
                
                # --- MINIMUM PERCENTAGE CHECK ---
                if percent_hit >= min_percent_decimal:
                    
                    # --- NEW FILTERING STEP: Check for unique percentage per Query_ID ---
                    if unique_key in seen_keys:
                        continue # Skip this row as a representative for this percentage is already captured
                        
                    # Store the row and the calculated percent
                    # Note: We append the percent_hit object, which will be converted to string on write.
                    all_processed_rows.append(row + [percent_hit])
                    seen_keys.add(unique_key) # Record the unique key
                
        # 2. GROUP AND CULL TO TOP N RESULTS PER QUERY_ID
        grouped_rows = defaultdict(list)
        for row in all_processed_rows:
            query_id = row[0]
            grouped_rows[query_id].append(row)
            
        final_culled_rows = []
        for query_id in grouped_rows:
            # Sort by percentage (last element in the row), descending, then take top N
            # Although the input CSV is often sorted, re-sorting here guarantees
            # we pick the actual top N highest percentage hits.
            sorted_by_percent = sorted(
                grouped_rows[query_id],
                key=lambda x: x[-1], # Sort by the Decimal percent_hit added at the end
                reverse=True
            )
            top_n = sorted_by_percent[:TOP_N_RESULTS]
            final_culled_rows.extend(top_n)
            
        # 3. WRITE HEADER AND CULLED ROWS TO OUTPUT FILE
        
        # Ensure the output file is created in the same directory as the input CSV
        output_dir = os.path.dirname(input_csv_path) or '.'
        output_path_full = os.path.join(output_dir, output_csv_path)
        with open(output_path_full, mode='w', newline='') as outfile:
            writer = csv.writer(outfile)
            
            # Append the new column header
            writer.writerow(header + ['%_Hit_Value'])
            
            # Write the culled data
            # Decimal objects are automatically converted to strings when written by csv.writer
            writer.writerows(final_culled_rows)
            
        print(f"\nReport successfully generated and saved to '{output_path_full}'", file=sys.stderr)
        
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_csv_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
if __name__ == "__main__":
    # Check for correct command-line arguments
    # Expects: <input_csv_file> <fasta_file_for_count>
    if len(sys.argv) != 3:
        print("Usage: python Fops_generate_report.py <input_csv_file> <fasta_file_for_count>", file=sys.stderr)
        print("\nNote: The FASTA file is used to calculate the total sequence count.", file=sys.stderr)
        sys.exit(1)
        
    input_csv_file = sys.argv[1]
    fasta_count_file = sys.argv[2]
    
    # 1. Generate Timestamped Output Filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"{OUTPUT_FILENAME_BASE}_{timestamp}.csv"
    
    # 2. Automatically count sequences from the required FASTA file
    TOTAL_COUNT = count_fasta_sequences(fasta_count_file)
    
    # 3. Run the main processing function, passing the output file path
    # We pass only the name of the output file; the function resolves the path relative to the input CSV.
    calculate_and_cull_report(input_csv_file, TOTAL_COUNT, output_file_name)
