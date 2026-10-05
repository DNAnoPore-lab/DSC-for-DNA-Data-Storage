"""Decode a seed-prefixed DNA file produced by txt2DNA.py."""

import argparse
import random
import sys


# Preserve the original on-disk mapping.
t = {"A": "00", "T": "01", "C": "10", "G": "11"}


def bp2byte(bp):
    """Decode exactly four uppercase DNA bases into one byte."""
    if len(bp) != 4:
        raise ValueError("Each byte must contain exactly four DNA bases")
    try:
        return int("".join(t[base] for base in bp), 2)
    except KeyError as error:
        raise ValueError(f"Invalid DNA base: {error.args[0]!r}") from None


def dna2seed(dna_sequence):
    """Decode the eight-base seed header."""
    if len(dna_sequence) != 8:
        raise ValueError("The seed header must contain exactly eight DNA bases")
    return (bp2byte(dna_sequence[:4]) << 8) + bp2byte(dna_sequence[4:])


def decode_data(dna_sequence):
    """Decode DNA, rejecting incomplete headers, partial bytes and bad bases."""
    dna_sequence = dna_sequence.strip()
    if len(dna_sequence) < 8:
        raise ValueError("DNA sequence must contain an eight-base seed header")
    if (len(dna_sequence) - 8) % 4:
        raise ValueError("DNA payload length must be a multiple of four bases")
    invalid_bases = set(dna_sequence) - set(t)
    if invalid_bases:
        raise ValueError(f"Invalid DNA bases: {', '.join(repr(base) for base in sorted(invalid_bases))}")
    seed = dna2seed(dna_sequence[:8])
    rng = random.Random(seed)
    return bytes(
        bp2byte(dna_sequence[i:i + 4]) ^ rng.randint(0, 255)
        for i in range(8, len(dna_sequence), 4)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="DNA file to decode")
    parser.add_argument("-o", "--output", default="decoded_output", help="new output binary file (must not exist)")
    args = parser.parse_args(argv)
    try:
        with open(args.input_file, "r", encoding="ascii") as source:
            dna_sequence = source.read()
        decoded_data = decode_data(dna_sequence)
        with open(args.output, "xb") as output:
            output.write(decoded_data)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Decoding complete. Output file: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
