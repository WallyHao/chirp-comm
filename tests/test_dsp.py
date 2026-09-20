"""Tests for the DSP primitives: chirp generation and Hamming(7,4)."""

import numpy as np
import pytest

from chirp_comm.config import BIT_DUR, FS
from chirp_comm.dsp import generate_chirp, hamming_74_decode, hamming_74_encode

ALL_NIBBLES = [format(value, "04b") for value in range(16)]


def test_encode_returns_seven_bits():
    assert hamming_74_encode("0000") == "0000000"
    assert len(hamming_74_encode("1011")) == 7
    assert set(hamming_74_encode("1011")) <= {"0", "1"}


@pytest.mark.parametrize("nibble", ALL_NIBBLES)
def test_round_trip_all_nibbles(nibble):
    assert hamming_74_decode(hamming_74_encode(nibble)) == nibble


@pytest.mark.parametrize("nibble", ALL_NIBBLES)
@pytest.mark.parametrize("position", range(7))
def test_single_bit_error_is_corrected(nibble, position):
    encoded = hamming_74_encode(nibble)
    flipped = list(encoded)
    flipped[position] = "1" if flipped[position] == "0" else "0"
    assert hamming_74_decode("".join(flipped)) == nibble


def test_codewords_have_minimum_distance_three():
    codewords = [hamming_74_encode(nibble) for nibble in ALL_NIBBLES]
    for i, left in enumerate(codewords):
        for right in codewords[i + 1 :]:
            distance = sum(a != b for a, b in zip(left, right))
            assert distance >= 3


def test_generate_chirp_length_and_dtype():
    chirp = generate_chirp(2000, 4000, BIT_DUR)
    assert len(chirp) == int(FS * BIT_DUR)
    assert chirp.dtype == np.float32


def test_generate_chirp_is_windowed():
    chirp = generate_chirp(2000, 4000, BIT_DUR)
    assert np.max(np.abs(chirp)) <= 1.0
    # The Hann window drives both ends to zero, limiting spectral splatter.
    assert abs(chirp[0]) < 1e-6
    assert abs(chirp[-1]) < 1e-6
