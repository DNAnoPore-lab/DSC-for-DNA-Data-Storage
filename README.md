# DSC-for-DNA-Data-Storage

This repository contains a binary-to-DNA codec and an exploratory sequence
selection script.

## Encode and decode a file

The codec uses Python 3 and the standard library only; no packages need to be
installed.

```sh
python txt2DNA.py input.bin
python DNA2txt.py EncodedToDNA.txt
```

The default outputs are `EncodedToDNA.txt` and `decoded_output`. Input may contain
arbitrary bytes, including an empty file. To choose output paths:

```sh
python txt2DNA.py input.bin --output sample.dna
python DNA2txt.py sample.dna --output restored.bin
```

Outputs must not already exist. Both commands return a nonzero exit status rather
than overwrite an existing file, including when the output names the input or a
link to it. Choose a fresh output name for each run. Invalid DNA, input/output
errors, seed exhaustion and encoding timeouts also produce nonzero exit statuses.

Both modules can be imported without reading or writing files:

```python
from txt2DNA import encode_data
from DNA2txt import decode_data

seed, dna = encode_data(b"DNA")
assert decode_data(dna) == b"DNA"
```

## Format and compatibility

- Two-bit values map to bases as `00 -> A`, `01 -> T`, `10 -> C`, `11 -> G`
- The first eight bases encode a 16-bit seed, most significant byte first
- Every remaining four bases encode one source byte XORed with
  `random.Random(seed).randint(0, 255)`
- Seeds are tried in ascending order from 1024 through 65535, inclusive
- A seed is rejected if its encoded **payload** contains four consecutive equal
  bases. This preserves the original rule: the seed header and the
  header/payload boundary are not homopolymer-filtered
- DNA is uppercase. Leading/trailing whitespace is accepted when decoding;
  internal whitespace, invalid bases, incomplete headers and partial bytes are
  rejected

The encoder keeps the original base mapping, random-number calls and first-valid
seed selection. It caches the 256 byte-to-DNA conversions, avoids an intermediate
XOR byte list, and rejects a seed as soon as a disallowed run is found, including
runs across adjacent encoded bytes. It uses local random generators so encoding
and decoding do not alter the caller's global random state.

Search is bounded by the finite seed range and a default 6000-second monotonic
timeout. The Python API accepts `start_seed`, `stop_seed` (exclusive), and
`timeout` overrides. A valid encoding is not guaranteed, particularly as input
length grows. This format does not chunk a large input into independently
encodable strands.

This is a reversible encoding, not cryptographic encryption or an error-correcting
code. The format contains no checksum or original-length field, so valid-base
substitutions and truncation by whole four-base groups cannot reliably be
detected. Keep a separate checksum if integrity verification is required.

## Tests

From the repository root:

```sh
python -m unittest discover -s tests -v
```

Tests cover exact outputs captured from the original encoder, all byte values,
seed representation, round trips, cross-byte homopolymers, early seed rejection,
malformed DNA, timeout/exhaustion errors, safe imports and command-line output
safety. They use synthetic data and only the standard library.

## Exploratory sequence selection

`DSC_location.py` is a separate research script and is unchanged by the codec
improvements. It expects `pandas`, `openpyxl` and local Excel files
`0.xlsx` through `4.xlsx`, which are not supplied in this repository.

It is not currently a validated runnable workflow: it contains malformed
`range` loops, fixed row counts, questionable substring-presence checks, and
workbook output that is not saved. Those issues need a separate review with the
intended datasets and selection criteria. The codec test command above does not
import or execute this script, and passing codec tests does not validate its
scientific selection behavior.
