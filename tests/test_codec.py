"""Compatibility and safety tests for the byte/DNA codec, using only stdlib."""

import contextlib
import io
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import DNA2txt
import txt2DNA


ROOT = Path(__file__).resolve().parents[1]
# Captured from the original encoder at d5a15038869b6ae778a1b0c5988a98a66117af28.
GOLDEN_ENCODINGS = (
    (b"", "AATAAAAA"),
    (b"DNA", "AATAAAAATAGTCGCTCATC"),
    (b"hello", "AATAAAATAAAGTGCATGCCAATTGTGG"),
    (
        bytes(range(16)),
        "AATAAAAAAACTGGTCGATTCCTCAGTGGCTCCGGTCGCGGAGCAGCATAGTGAGAAGCAGTGATAATGTAA",
    ),
    (bytes([0, 255, 128, 1]), "AATAAAAAAACTAACATATGCCTA"),
)


def legacy_byte_to_dna(value):
    binary = format(value, "08b")
    mapping = {"00": "A", "01": "T", "10": "C", "11": "G"}
    return "".join(mapping[binary[i:i + 2]] for i in range(0, 8, 2))


def legacy_payload(data, seed):
    rng = random.Random(seed)
    return "".join(legacy_byte_to_dna(value ^ rng.randint(0, 255)) for value in data)


class CodecTests(unittest.TestCase):
    def test_all_byte_values_match_original_mapping(self):
        for value in range(256):
            with self.subTest(value=value):
                dna = txt2DNA.byte_to_dna(value)
                self.assertEqual(dna, legacy_byte_to_dna(value))
                self.assertEqual(DNA2txt.bp2byte(dna), value)

    def test_seed_header_is_big_endian(self):
        for seed in (0, 1, 255, 256, 1024, 32768, 65535):
            with self.subTest(seed=seed):
                expected = legacy_byte_to_dna(seed >> 8) + legacy_byte_to_dna(seed & 255)
                self.assertEqual(txt2DNA.seed_to_dna(seed), expected)
                self.assertEqual(DNA2txt.dna2seed(expected), seed)

    def test_exact_legacy_encodings_and_roundtrips(self):
        for data, expected in GOLDEN_ENCODINGS:
            with self.subTest(data=data):
                seed, encoded = txt2DNA.encode_data(data)
                self.assertEqual(encoded, expected)
                self.assertEqual(seed, DNA2txt.dna2seed(expected[:8]))
                self.assertEqual(DNA2txt.decode_data(expected), data)

    def test_all_byte_values_decode_with_legacy_rng(self):
        data = bytes(range(256))
        for seed in (0, 1024, 65535):
            encoded = txt2DNA.seed_to_dna(seed) + legacy_payload(data, seed)
            self.assertEqual(DNA2txt.decode_data(encoded), data)

    def test_seed_rejection_matches_full_legacy_payload(self):
        rng = random.Random(12345)
        for length in (0, 1, 2, 16, 128):
            data = bytes(rng.randrange(256) for _ in range(length))
            for seed in range(1024, 1044):
                with self.subTest(length=length, seed=seed):
                    payload = legacy_payload(data, seed)
                    valid = all(payload.count(base * 4) == 0 for base in "ATCG")
                    self.assertEqual(
                        txt2DNA._encode_payload(data, seed),
                        payload if valid else None,
                    )

    def test_cross_byte_homopolymers_are_rejected(self):
        # These encoded bytes are CAAA and ATCG, with AAAA across the boundary.
        with patch("txt2DNA.random.Random") as random_type:
            random_type.return_value.randint.return_value = 0
            self.assertIsNone(txt2DNA._encode_payload(bytes([128, 27]), 1024))

    def test_rejection_stops_before_remaining_bytes(self):
        with patch("txt2DNA.random.Random") as random_type:
            random_type.return_value.randint.return_value = 0
            self.assertIsNone(txt2DNA._encode_payload(bytes(10000), 1024))
            self.assertEqual(random_type.return_value.randint.call_count, 1)

    def test_homopolymer_filter_keeps_original_payload_only_scope(self):
        # The legacy header contains five As; header/junction filtering would
        # change the first selected seed and break exact output compatibility.
        seed, encoded = txt2DNA.encode_data(b"")
        self.assertEqual(seed, 1024)
        self.assertEqual(encoded, "AATAAAAA")
        self.assertFalse(txt2DNA.check_homopolymers(encoded))

    def test_homopolymer_threshold_is_four(self):
        for base in "ATCG":
            self.assertTrue(txt2DNA.check_homopolymers(base * 3))
            self.assertFalse(txt2DNA.check_homopolymers(base * 4))

    def test_global_random_state_is_unchanged(self):
        before = random.getstate()
        _, dna = txt2DNA.encode_data(b"DNA")
        DNA2txt.decode_data(dna)
        self.assertEqual(random.getstate(), before)

    def test_exhaustion_reports_failure(self):
        # XOR with the first random byte produces AAAA for this sole seed.
        data = bytes([random.Random(1024).randint(0, 255)])
        with self.assertRaisesRegex(ValueError, "No valid encoding"):
            txt2DNA.encode_data(data, start_seed=1024, stop_seed=1025)

    def test_upper_seed_endpoint_is_supported(self):
        seed, dna = txt2DNA.encode_data(b"", start_seed=65535)
        self.assertEqual(seed, 65535)
        self.assertEqual(dna, "GGGGGGGG")

    def test_timeout_uses_monotonic_clock(self):
        with patch("txt2DNA.time.monotonic", side_effect=[10, 11]):
            with self.assertRaises(TimeoutError):
                txt2DNA.encode_data(b"DNA", timeout=1)

    def test_invalid_seed_ranges(self):
        for start, stop in ((-1, 1024), (1024, 1024), (1025, 1024), (0, 65537)):
            with self.subTest(start=start, stop=stop):
                with self.assertRaises(ValueError):
                    txt2DNA.encode_data(b"", start_seed=start, stop_seed=stop)

    def test_invalid_timeouts(self):
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                txt2DNA.encode_data(b"", timeout=timeout)

    def test_timeout_interrupts_a_payload_attempt(self):
        # Deadline expires before the second byte, not just between seeds.
        with patch("txt2DNA.time.monotonic", side_effect=[0, 0, 0, 2]):
            with self.assertRaises(TimeoutError):
                txt2DNA.encode_data(b"DNA", timeout=1)

    def test_timeout_is_checked_after_a_successful_attempt(self):
        with patch("txt2DNA.time.monotonic", side_effect=[0, 0, 0, 2]):
            with self.assertRaises(TimeoutError):
                txt2DNA.encode_data(b"D", timeout=1)

    def test_invalid_byte_and_seed_values(self):
        for value in (-1, 256):
            with self.assertRaises(ValueError):
                txt2DNA.byte_to_dna(value)
        for seed in (-1, 65536):
            with self.assertRaises(ValueError):
                txt2DNA.seed_to_dna(seed)

    def test_missing_or_incomplete_seed_header(self):
        for sequence in ("", "A", "ATCGATC"):
            with self.subTest(sequence=sequence):
                with self.assertRaisesRegex(ValueError, "seed header"):
                    DNA2txt.decode_data(sequence)

    def test_partial_payload_bytes_are_rejected(self):
        for suffix in ("A", "AT", "ATC"):
            with self.assertRaisesRegex(ValueError, "multiple of four"):
                DNA2txt.decode_data("AATAAAAA" + suffix)

    def test_invalid_bases_are_rejected(self):
        for sequence in ("AATAAAAN", "AATAAAAAatcg", "AATAAAAAAT N"):
            with self.subTest(sequence=sequence):
                with self.assertRaisesRegex(ValueError, "Invalid DNA"):
                    DNA2txt.decode_data(sequence)

    def test_byte_and_seed_helpers_reject_partial_groups(self):
        for group in ("", "ATC", "ATCGA"):
            with self.assertRaises(ValueError):
                DNA2txt.bp2byte(group)
        for header in ("ATCG", "ATCGATCGA"):
            with self.assertRaises(ValueError):
                DNA2txt.dna2seed(header)
        with self.assertRaisesRegex(ValueError, "Invalid DNA"):
            DNA2txt.bp2byte("ATCN")

    def test_outer_whitespace_remains_supported(self):
        self.assertEqual(DNA2txt.decode_data(" \nAATAAAAATAGTCGCTCATC\n"), b"DNA")


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)

    def run_cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / script), *map(str, args)],
            cwd=self.folder,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_default_output_names_and_binary_roundtrip(self):
        data = bytes([0, 255, 128, 1])
        (self.folder / "input.bin").write_bytes(data)
        encoded = self.run_cli("txt2DNA.py", "input.bin")
        self.assertEqual(encoded.returncode, 0, encoded.stderr)
        self.assertTrue((self.folder / "EncodedToDNA.txt").is_file())
        decoded = self.run_cli("DNA2txt.py", "EncodedToDNA.txt")
        self.assertEqual(decoded.returncode, 0, decoded.stderr)
        self.assertEqual((self.folder / "decoded_output").read_bytes(), data)

    def test_custom_output_names(self):
        (self.folder / "input").write_bytes(b"hello")
        encoded = self.run_cli("txt2DNA.py", "input", "--output", "custom.dna")
        self.assertEqual(encoded.returncode, 0, encoded.stderr)
        decoded = self.run_cli("DNA2txt.py", "custom.dna", "-o", "custom.bin")
        self.assertEqual(decoded.returncode, 0, decoded.stderr)
        self.assertEqual((self.folder / "custom.bin").read_bytes(), b"hello")

    def test_existing_outputs_are_never_overwritten(self):
        for script, data in (("txt2DNA.py", b"DNA"), ("DNA2txt.py", b"AATAAAAATAGTCGCTCATC")):
            with self.subTest(script=script):
                (self.folder / "input").write_bytes(data)
                (self.folder / "output").write_bytes(b"keep this")
                result = self.run_cli(script, "input", "-o", "output")
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual((self.folder / "output").read_bytes(), b"keep this")

    def test_input_path_cannot_be_used_as_output(self):
        for script, data in (("txt2DNA.py", b"DNA"), ("DNA2txt.py", b"AATAAAAATAGTCGCTCATC")):
            with self.subTest(script=script):
                (self.folder / "input").write_bytes(data)
                result = self.run_cli(script, "input", "-o", "input")
                self.assertEqual(result.returncode, 1)
                self.assertEqual((self.folder / "input").read_bytes(), data)

    def test_hardlink_to_input_cannot_be_used_as_output(self):
        for script, data in (("txt2DNA.py", b"DNA"), ("DNA2txt.py", b"AATAAAAATAGTCGCTCATC")):
            with self.subTest(script=script):
                source = self.folder / script
                source.write_bytes(data)
                link = self.folder / (script + ".link")
                try:
                    os.link(source, link)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"Hard links unavailable: {error}")
                result = self.run_cli(script, source, "-o", link)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(source.read_bytes(), data)

    def test_symlink_to_input_cannot_be_used_as_output(self):
        for script, data in (("txt2DNA.py", b"DNA"), ("DNA2txt.py", b"AATAAAAATAGTCGCTCATC")):
            with self.subTest(script=script):
                source = self.folder / script
                source.write_bytes(data)
                link = self.folder / (script + ".link")
                try:
                    link.symlink_to(source)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"Symbolic links unavailable: {error}")
                result = self.run_cli(script, source, "-o", link)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(source.read_bytes(), data)

    def test_no_arguments_show_usage(self):
        for script in ("txt2DNA.py", "DNA2txt.py"):
            result = self.run_cli(script)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("usage:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_missing_input_is_reported_cleanly(self):
        for script in ("txt2DNA.py", "DNA2txt.py"):
            result = self.run_cli(script, "missing")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_dna_does_not_create_or_overwrite_output(self):
        invalid = self.folder / "invalid.dna"
        invalid.write_text("AATAAAAAATC", encoding="ascii")
        result = self.run_cli("DNA2txt.py", invalid)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.folder / "decoded_output").exists())
        (self.folder / "decoded_output").write_bytes(b"keep this")
        result = self.run_cli("DNA2txt.py", invalid)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.folder / "decoded_output").read_bytes(), b"keep this")

    def test_non_ascii_input_is_reported_cleanly(self):
        (self.folder / "invalid.dna").write_bytes(b"AATAAAAA\xff")
        result = self.run_cli("DNA2txt.py", "invalid.dna")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_encoder_failure_does_not_overwrite_output(self):
        source = self.folder / "input"
        output = self.folder / "output"
        source.write_bytes(b"DNA")
        output.write_bytes(b"keep this")
        with patch("txt2DNA.encode_data", side_effect=ValueError("No valid encoding")):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(txt2DNA.main([str(source), "-o", str(output)]), 1)
        self.assertEqual(output.read_bytes(), b"keep this")

    def test_importing_modules_has_no_io_side_effects(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        result = subprocess.run(
            [sys.executable, "-c", "import txt2DNA; import DNA2txt"],
            cwd=self.folder,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(list(self.folder.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
