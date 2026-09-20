"""Tests for the AcousticPacket container."""

from datetime import datetime

from chirp_comm.packet import AcousticPacket


def test_defaults():
    packet = AcousticPacket(payload="ab")
    assert packet.payload == "ab"
    assert packet.rssi == 0.0
    assert packet.is_valid is True
    assert isinstance(packet.timestamp, datetime)


def test_repr_includes_payload():
    assert "ab" in repr(AcousticPacket(payload="ab", rssi=12.5))
