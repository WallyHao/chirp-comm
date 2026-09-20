"""Tests for the framing layer: bitstream length, padding and round-trips."""

import pytest

from chirp_comm.config import DATA_LEN_CHARS, TOTAL_EXPECTED_BITS
from chirp_comm.protocol import ChirpProtocol


def test_encoded_length_matches_protocol_constant():
    assert len(ChirpProtocol.encode_to_bits("ab")) == TOTAL_EXPECTED_BITS


def test_encoded_stream_is_binary():
    assert set(ChirpProtocol.encode_to_bits("ab")) <= {"0", "1"}


@pytest.mark.parametrize("text", ["ab", "a", "Z9", "  ", "hello", "1"])
def test_round_trip(text):
    encoded = ChirpProtocol.encode_to_bits(text)
    expected = text[:DATA_LEN_CHARS].ljust(DATA_LEN_CHARS, " ")
    assert ChirpProtocol.decode_from_bits(encoded) == expected


def test_text_is_truncated_to_payload_length():
    assert ChirpProtocol.decode_from_bits(ChirpProtocol.encode_to_bits("abcdef")) == "ab"


def test_short_stream_is_rejected():
    assert ChirpProtocol.decode_from_bits("0101") == "???"
