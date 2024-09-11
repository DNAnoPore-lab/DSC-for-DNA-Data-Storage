import random
import sys

# Reverse translation dictionary, DNA to binary
t = {
    "A": "00",
    "T": "01",
    "C": "10",
    "G": "11"
}

# Function to convert base pairs into bytes
def bp2byte(bp):
    return int(''.join(t[b] for b in bp), 2)

# Function to convert a DNA sequence into a seed value
def dna2seed(dna_sequence):
    # Combine the bytes from the first 8 bases into one seed value
    return (bp2byte(dna_sequence[:4]) << 8) + bp2byte(dna_sequence[4:8])

# Read the input file from command line argument
input_file = sys.argv[1]

# Open and read the DNA sequence from the file
with open(input_file, "r") as f:
    dna_sequence = f.read().strip()

# Extract the seed corresponding to the first 8 bases and convert it into a seed value
seed = dna2seed(dna_sequence[:8])
print(f"Seed extracted: {seed}")

# Set the random seed
random.seed(seed)

# Decode the remaining DNA sequence into binary data
decoded_data = bytearray()
for i in range(8, len(dna_sequence), 4):
    # Convert every 4 bases back into a byte
    byte = bp2byte(dna_sequence[i:i+4])
    # Perform XOR operation with a random number to decode
    decoded_byte = byte ^ random.randint(0, 255)
    decoded_data.append(decoded_byte)

# Write the decoded data to the output file
output_file = "decoded_output"
with open(output_file, "wb") as f:
    f.write(decoded_data)

print(f"Decoding complete. Output file: {output_file}")
