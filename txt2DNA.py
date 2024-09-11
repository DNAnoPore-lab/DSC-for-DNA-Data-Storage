import random
import sys
import time

# Reverse translation dictionary, binary to DNA
binary_to_dna = {
    "00": "A",
    "01": "T",
    "10": "C",
    "11": "G"
}

# convert a byte into a binary string
def byte_to_dna(byte_val):
    binary_string = format(byte_val, '08b')
    return ''.join(binary_to_dna[binary_string[i:i+2]] for i in range(0, 8, 2))

# Check if there are more than 3 consecutive identical bases in a DNA sequence
def check_homopolymers(dna_sequence):
    return all(dna_sequence.count(base * 4) == 0 for base in 'ATCG')

# Convert the seed into 4 bases
def seed_to_dna(seed):
    higher_byte = seed >> 8
    lower_byte = seed & 0xFF
    return byte_to_dna(higher_byte) + byte_to_dna(lower_byte)

# Read the input file from the command line
input_file = sys.argv[1]

# Read the contents of the file
with open(input_file, "rb") as f:
    input_data = f.read()

# Print the original file size
original_file_size = len(input_data)
print(f"Original file size: {original_file_size} bytes")

# Start timing
start_time = time.time()

# Print the seed and the corresponding DNA sequence
def print_seed_and_dna(seed):
    seed_dna = seed_to_dna(seed)
    print(f"Seed: {seed} -> Seed DNA: {seed_dna}")
    return seed_dna

# Try different seeds until you find one that does not produce a sequence with consecutive bases
for seed in range(1024, 65536):
    random.seed(seed)
    seed_dna = print_seed_and_dna(seed)
    
    # Perform an XOR operation on each byte, then convert it to DNA.
    xor_data = [b ^ random.randint(0, 255) for b in input_data]
    encoded_dna_sequence = ''.join(byte_to_dna(b) for b in xor_data)

    # Print the encoded DNA sequence and its length
    print(f"Encoded DNA sequence length: {len(encoded_dna_sequence)}")

    # Check if the encoded DNA sequence has repeated bases
    if check_homopolymers(encoded_dna_sequence):
        # Verify if the length of the encoded data is correct
        if len(encoded_dna_sequence) == original_file_size * 4:
            # Write the seed and the encoded DNA sequence to a file
            with open("EncodedToDNA.txt", "w") as outfile:
                outfile.write(seed_dna + encoded_dna_sequence)
            print(f"Encoding complete using seed {seed}.")
            break
        else:
            print(f"Error: Encoded DNA length is {len(encoded_dna_sequence)}, but expected {original_file_size * 4}.")
    else:
        print("Homopolymers detected, trying a new seed...")

    # Check for timeout
    if time.time() - start_time > 6000:
        print("Error: Time limit exceeded.")
        sys.exit(1)
