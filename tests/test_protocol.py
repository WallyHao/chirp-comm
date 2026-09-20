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


def test_crc8_matches_reference_check_value():
    data = "".join(format(byte, "08b") for byte in b"123456789")
    assert ChirpProtocol._crc8(data) == format(0xF4, "08b")


def test_single_bit_error_is_corrected():
    bits = list(ChirpProtocol.encode_to_bits("ab"))
    bits[0] = "1" if bits[0] == "0" else "0"
    assert ChirpProtocol.decode_from_bits("".join(bits)) == "ab"


def test_double_bit_error_is_detected():
    bits = list(ChirpProtocol.encode_to_bits("ab"))
    bits[0] = "1" if bits[0] == "0" else "0"
    bits[1] = "1" if bits[1] == "0" else "0"
    assert ChirpProtocol.decode_from_bits("".join(bits)) == "!!!"
