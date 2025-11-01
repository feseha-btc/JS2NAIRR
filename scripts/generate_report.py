import sys
import csv
from decimal import Decimal, ROUND_HALF_UP
def calculate_percent_hit(input_csv_path, total_sequence_count_str):
    """
    Reads a CSV file, calculates a new percentage hit value based on the 'Hits' 
    column compared to a total sequence count, and prints the updated data.
    """
    try:
        # Convert the total sequence count argument to an integer
        TOTAL_COUNT = int(total_sequence_count_str)
        if TOTAL_COUNT <= 0:
            raise ValueError("Total sequence count must be a positive integer.")
    except ValueError as e:
        print(f"Error: Invalid total sequence count provided: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        # Open the input CSV file
        with open(input_csv_path, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            
            # Use sys.stdout for output, comma-separated (CSV format)
            writer = csv.writer(sys.stdout)
            # Process header
            try:
                header = next(reader)
                # Append the new column header
                writer.writerow(header + ['%_Hit_Value'])
            except StopIteration:
                # Handle case of an empty file
                return
            # Process data rows
            for row in reader:
                # The input lines from the bash script example have 4 or 6 columns.
                # The 'Hits' column is at index 3 (0-indexed).
                
                # Ensure the row has enough columns
                if len(row) < 4:
                    print(f"Skipping malformed row: {row}", file=sys.stderr)
                    continue
                
                # Get the Hits count from the 4th column (index 3)
                hits_str = row[3].strip()
                try:
                    hits_count = int(hits_str)
                except ValueError:
                    print(f"Warning: Non-numeric 'Hits' value '{hits_str}'. Skipping row.", file=sys.stderr)
                    continue
                # Calculate the percentage with high precision
                raw_percent = Decimal(hits_count) * Decimal(100) / Decimal(TOTAL_COUNT)
                
                # Format to two decimal places, rounding half up
                # Note: We don't need the '%' sign as per your request.
                percent_hit = raw_percent.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Append the new percentage to the row and write
                writer.writerow(row + [percent_hit])
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_csv_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
if __name__ == "__main__":
    # Check for correct command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python calculate_hit_percent.py <input_csv_file> <total_sequence_count>", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1]
    total_count = sys.argv[2]
    
    calculate_percent_hit(input_file, total_count)
