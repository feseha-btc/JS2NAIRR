import torch
import itertools
import os
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Dict, Any, Optional
# --- Configuration ---
FLANKING_SIZE = 1 #3   # Bases at the start and end of the oligo to be kept fixed.
NUM_AMBIGUITIES = 3 # Number of positions to replace with '.'
TOP_N_RESULTS = 5   # Number of top matches to report for each query.
# --- High-Performance Computing Configuration ---
# 30 CPU Cores are used for orchestration (reading files, generating patterns)
# 400GB RAM is used for loading the master sequences (10M) into memory before GPU transfer.
NUM_CORES = 30
NUM_GPUS = 4 # Target number of GPUs for splitting the master dataset.
# --- Encoding Map for PyTorch Tensors ---
# We use numerical encoding for fast tensor comparison on the GPU.
# The wildcard '.' is mapped to 0.
BASE_TO_INT = {'A': 1, 'C': 2, 'G': 3, 'T': 4, '.': 0, 'N': 0}
INT_TO_BASE = {v: k for k, v in BASE_TO_INT.items()}
# --- File Parsing Utility (Unchanged) ---
def parse_fasta(file_path: str) -> List[Tuple[str, str]]:
    """
    Parses a FASTA file and returns a list of (header, sequence) tuples.
    """
    sequences = []
    current_header = None
    current_seq = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('>'):
                    # Save the previous sequence if one exists
                    if current_header and current_seq:
                        sequences.append((current_header, "".join(current_seq).upper()))
                    
                    # Start a new sequence
                    current_header = line[1:].split()[0] # Use only the first word of the header
                    current_seq = []
                else:
                    # Append sequence line
                    current_seq.append(line)
            # Save the last sequence
            if current_header and current_seq:
                sequences.append((current_header, "".join(current_seq).upper()))
    
    except FileNotFoundError:
        print(f"Error: Input file '{file_path}' not found.")
        sys.exit(1)
        
    return sequences
# --- GPU Manager Class ---
class GpuManager:
    """Manages the master sequence data and dispatches matching jobs to multiple GPUs."""
    def __init__(self, master_sequences: List[str], target_gpus: int):
        self.master_sequences = master_sequences
        self.target_gpus = min(target_gpus, torch.cuda.device_count())
        self.gpu_data: List[Tuple[torch.Tensor, torch.device]] = []
        
        if self.target_gpus == 0:
            print(" No GPUs detected or PyTorch misconfigured. Cannot run GPU-accelerated job.")
            sys.exit(1)
        print(f"Initializing {self.target_gpus} GPU(s) for acceleration...")
        self.split_and_load_data()
    def _encode_sequences(self, sequences: List[str]) -> torch.Tensor:
        """Converts list of DNA strings to a single integer tensor."""
        if not sequences:
            return torch.empty(0, 0, dtype=torch.int8)
        seq_len = len(sequences[0])
        num_seqs = len(sequences)
        
        # Create an empty tensor and populate it with encoded values
        encoded_tensor = torch.zeros((num_seqs, seq_len), dtype=torch.int8)
        
        for i, seq in enumerate(sequences):
            for j, base in enumerate(seq):
                # Use BASE_TO_INT to convert character to integer
                encoded_tensor[i, j] = BASE_TO_INT.get(base, BASE_TO_INT['N'])
                
        return encoded_tensor
    def split_and_load_data(self):
        """Encodes master sequences and splits the tensor across target GPUs."""
        if not self.master_sequences:
            return
        # 1. Encode all data on CPU
        print("Encoding master sequences to tensor (CPU)...")
        master_tensor_cpu = self._encode_sequences(self.master_sequences)
        total_seqs = master_tensor_cpu.shape[0]
        
        # 2. Split the tensor into chunks
        chunk_size = total_seqs // self.target_gpus
        chunks = []
        for i in range(self.target_gpus):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < self.target_gpus - 1 else total_seqs
            chunks.append(master_tensor_cpu[start:end])
        # 3. Move each chunk to a dedicated GPU device
        for i, chunk in enumerate(chunks):
            device = torch.device(f"cuda:{i}")
            chunk_gpu = chunk.to(device)
            self.gpu_data.append((chunk_gpu, device))
            print(f"  > Loaded {chunk_gpu.shape[0]} sequences onto {device} (GPU {i})")
    @torch.no_grad()
    def match_on_gpu(self, pattern_tensor: torch.Tensor, device_id: int) -> int:
        """
        Performs the highly parallel pattern matching on a single GPU.
        The pattern tensor is of shape (1, oligo_length).
        The master tensor is of shape (N, oligo_length), where N is the chunk size.
        """
        master_chunk, device = self.gpu_data[device_id]
        
        if master_chunk.numel() == 0:
            return 0
        # Move the pattern to the specific GPU
        pattern_tensor = pattern_tensor.to(device)
        
        # 1. Identify which positions in the pattern are NOT wildcards ('.', encoded as 0)
        #    This creates a mask of shape (1, oligo_length).
        fixed_base_mask = (pattern_tensor != BASE_TO_INT['.'])
        # 2. Compare the master chunk only at the fixed base positions.
        #    We use `torch.masked_select` (or broadcasting) to only consider fixed bases.
        #    This comparison checks: Is the master base EQUAL to the pattern's fixed base?
        
        # A. Comparison tensor: True where master sequence matches the pattern's fixed base.
        #    Shape (N_seqs, oligo_length)
        match_comparison = (master_chunk == pattern_tensor)
        
        # B. Apply the fixed_base_mask: Only keep the results for non-wildcard positions.
        #    For wildcard positions, the mask is False, and the result is True (a match is assumed).
        #    A non-match at a fixed position results in False.
        #    We can use the `torch.where` trick:
        #    Where the pattern is a fixed base (mask is True), use the match_comparison result.
        #    Where the pattern is a wildcard (mask is False), assume a match (use True).
        #    Shape (N_seqs, oligo_length)
        positional_match = torch.where(fixed_base_mask, match_comparison, torch.tensor(True, device=device))
        
        # 3. Reduce across the sequence length dimension (dim=1)
        #    A sequence matches ONLY IF all positions match (i.e., the product is 1 or sum equals length)
        #    Using `all(dim=1)`: True if ALL positions in the sequence are True (match).
        sequence_matches = positional_match.all(dim=1) # Shape (N_seqs,)
        
        # 4. Sum the matches to get the total count
        match_count = sequence_matches.sum().item()
        
        return match_count
# --- Worker Function (CPU/Orchestration) ---
def analyze_single_query_oligo(
    query_id: str,
    query_seq: str,
    gpu_manager: GpuManager, # Takes the GPU manager instance now
    flanking_size: int,
    num_ambiguities: int
) -> List[Tuple[str, str, str, int]]:
    """
    Orchestrates: Generates all degenerate patterns for a single query sequence
    and dispatches matching to the 4 GPUs. Returns the top N results.
    """
    actual_length = len(query_seq)
    
    # 1. Check length constraints
    search_indices = list(range(flanking_size, actual_length - flanking_size))
    if len(search_indices) < num_ambiguities:
        print(f"Warning: Query {query_id} (Length {actual_length}) is too short. Skipping.")
        return []
        
    # 2. Generate all combinations of ambiguous positions (indices)
    ambiguity_combinations = list(itertools.combinations(search_indices, num_ambiguities))
    
    # 3. Process all combinations and store results
    results: Dict[Tuple[str, Tuple[int, ...]], int] = {}
    
    for amb_indices in ambiguity_combinations:
        # Build the degenerate pattern (string representation)
        pattern_list = list(query_seq)
        for i in amb_indices:
            pattern_list[i] = '.'
        degenerate_pattern = "".join(pattern_list)
        
        # Encode the pattern for the GPU (1, oligo_length)
        encoded_pattern = [BASE_TO_INT.get(base, BASE_TO_INT['N']) for base in degenerate_pattern]
        pattern_tensor = torch.tensor([encoded_pattern], dtype=torch.int8)
        
        total_match_count = 0
        
        # Dispatch the pattern matching to all 4 GPUs and sum the results
        for i in range(gpu_manager.target_gpus):
            count = gpu_manager.match_on_gpu(pattern_tensor, i)
            total_match_count += count
            
        # Store the result
        results[(degenerate_pattern, amb_indices)] = total_match_count
        
    # 4. Sort and format the top results (CPU operation)
    sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)
    
    final_output = []
    for (pattern, amb_indices), count in sorted_results[:TOP_N_RESULTS]:
        # Convert indices (0-based) to positions (1-based)
        amb_positions = tuple(i + 1 for i in amb_indices)
        positions_str = "-".join(map(str, amb_positions))
        
        # Output format: (Query_ID, Pattern, Positions_Str, Count)
        final_output.append((query_id, pattern, positions_str, count))
        
    return final_output
# --- Main Execution ---
def main():
    """Main execution function to handle file I/O and parallel execution."""
    
#    if len(sys.argv) != 3:
 #       print("Usage: python geminiSimpleCluster_GPU.py <query_oligo.fasta> <master_oligo.fasta>")
  #      sys.exit(1)
        
    # Check for GPU availability first
    if not torch.cuda.is_available():
        print("FATAL ERROR: CUDA is not available. Please install the necessary drivers and CUDA Toolkit.")
        sys.exit(1)
        
    QUERY_FILE = sys.argv[1]
    MASTER_FILE = sys.argv[2]
    
    # Set output file name based on query file
    base_name, _ = os.path.splitext(QUERY_FILE)
    OUTPUT_FILE = base_name + "_GPU_results.csv"
    # 1. Load Data (Leveraging 400GB RAM)
    print(f"Loading master sequences from: {MASTER_FILE} (400GB RAM available)...")
    master_sequences_w_id = parse_fasta(MASTER_FILE)
    master_sequences = [seq for _, seq in master_sequences_w_id]
    
    if not master_sequences:
        print("Error: No sequences found in the master file.")
        sys.exit(1)
        
    print(f"Master file loaded: {len(master_sequences)} sequences.")
    
    # 2. Initialize GPU Manager and Transfer Data to GPUs
    gpu_manager = GpuManager(master_sequences, NUM_GPUS)
    
    print(f"\nLoading query sequences from: {QUERY_FILE}...")
    query_oligos = parse_fasta(QUERY_FILE)
    
    if not query_oligos:
        print("Error: No sequences found in the query file.")
        sys.exit(1)
        
    print(f"Query file loaded: {len(query_oligos)} queries.")
    print(f"Starting parallel analysis of {len(query_oligos)} queries using {NUM_CORES} CPU cores for orchestration.")
    
    all_results = []
    
    # 3. Parallel Execution using CPU pool for query orchestration
    # The CPU cores manage the job submission (generating patterns)
    with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
        futures = {
            executor.submit(
                analyze_single_query_oligo, 
                query_id, 
                query_seq, 
                gpu_manager, # Pass the initialized GPU manager
                FLANKING_SIZE, 
                NUM_AMBIGUITIES
            ): query_id
            for query_id, query_seq in query_oligos
        }
        # Monitor and collect results
        for i, future in enumerate(as_completed(futures)):
            query_id = futures[future]
            try:
                results_for_query = future.result()
                all_results.extend(results_for_query)
                
                if (i + 1) % 100 == 0 or (i + 1) == len(query_oligos):
                    print(f"Completed {i + 1}/{len(query_oligos)} queries. Total results collected: {len(all_results)}")
            except Exception as exc:
                print(f'Query {query_id} generated an exception: {exc}')
    # 4. Write the aggregated results to a CSV file
    print(f"\nAnalysis complete. Writing {len(all_results)} total result rows to '{OUTPUT_FILE}'...")
    try:
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Query_ID", "Degenerate_Pattern", "Ambiguous_Positions", "Match_Count"])
            writer.writerows(all_results)
                
        print(f"\nSuccessfully wrote results to '{OUTPUT_FILE}'.")
        
    except IOError as e:
        print(f"Error writing to file '{OUTPUT_FILE}': {e}")
if __name__ == "__main__":
    # Ensure correct start method for multiprocessing compatibility with CUDA
    # 'spawn' is generally safer for GPU contexts
    try:
        torch.multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # Method already set
        pass 
        
    main()
