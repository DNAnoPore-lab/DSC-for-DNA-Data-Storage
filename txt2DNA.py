"""Encode bytes as DNA while rejecting payload homopolymers of four bases."""

import argparse
import math
import random
import sys
import time


# Keep the original mapping and random-number calls for format compatibility.
binary_to_dna = {"00": "A", "01": "T", "10": "C", "11": "G"}
_BYTE_TO_DNA = tuple(
    "".join(binary_to_dna[format(value, "08b")[i:i + 2]] for i in range(0, 8, 2))
    for value in range(256)
)


def byte_to_dna(byte_val):
    """Return the four bases representing one byte."""
    if not 0 <= byte_val <= 255:
        raise ValueError("Byte value must be between 0 and 255")
    return _BYTE_TO_DNA[byte_val]


def check_homopolymers(dna_sequence):
    """Return whether the sequence has no run of four identical bases."""
    return all(base * 4 not in dna_sequence for base in "ATCG")


def seed_to_dna(seed):
    """Encode a 16-bit seed as eight bases, most significant byte first."""
    if not 0 <= seed <= 65535:
        raise ValueError("Seed must be between 0 and 65535")
    return byte_to_dna(seed >> 8) + byte_to_dna(seed & 0xFF)


def _encode_payload(input_data, seed, deadline=None):
    """Return a valid payload, or reject a seed at its first homopolymer."""
    rng = random.Random(seed)
    chunks = []
    tail = ""
    for value in input_data:
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Time limit exceeded while searching for a valid seed")
        chunk = _BYTE_TO_DNA[value ^ rng.randint(0, 255)]
        # Three previous bases cover runs that cross a byte boundary.
        window = tail + chunk
        if not check_homopolymers(window):
            return None
        chunks.append(chunk)
        tail = window[-3:]
    return "".join(chunks)


def encode_data(input_data, start_seed=1024, stop_seed=65536, timeout=6000):
    """Return (seed, DNA) using the first valid seed in [start_seed, stop_seed).

    DNA contains an eight-base seed header followed by the encoded payload.
    As in the original format, only the payload is homopolymer-filtered.
    """
    if not 0 <= start_seed < stop_seed <= 65536:
        raise ValueError("Seed range must satisfy 0 <= start < stop <= 65536")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be finite and positive")
    deadline = time.monotonic() + timeout
    for seed in range(start_seed, stop_seed):
        if time.monotonic() >= deadline:
            raise TimeoutError("Time limit exceeded while searching for a valid seed")
        payload = _encode_payload(input_data, seed, deadline=deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError("Time limit exceeded while searching for a valid seed")
        if payload is not None:
            return seed, seed_to_dna(seed) + payload
    raise ValueError("No valid encoding found in the requested seed range")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="binary or text file to encode")
    parser.add_argument("-o", "--output", default="EncodedToDNA.txt", help="new output DNA file (must not exist)")
    args = parser.parse_args(argv)
    try:
        with open(args.input_file, "rb") as source:
            input_data = source.read()
        print(f"Original file size: {len(input_data)} bytes")
        seed, dna_sequence = encode_data(input_data)
        with open(args.output, "x", encoding="ascii") as output:
            output.write(dna_sequence)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Encoding complete using seed {seed}. Output file: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
