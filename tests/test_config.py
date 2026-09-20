"""Tests for the shared timing and framing constants."""

from chirp_comm import config


def test_frame_is_46_bits():
    assert config.TOTAL_EXPECTED_BITS == 46


def test_frame_composition():
    assert config.DATA_BITS == 28
    assert config.PARITY_BITS == 4
    assert config.CRC_BITS == 14
    assert config.DATA_BITS + config.PARITY_BITS + config.CRC_BITS == config.TOTAL_EXPECTED_BITS


def test_bit_slot_includes_pause():
    assert config.BIT_TOTAL_SAMPLES == int(config.FS * (config.BIT_DUR + config.PAUSE))


def test_sync_and_bit_bands_match():
    assert (config.SYNC_F0, config.SYNC_F1) == (config.BIT_F0, config.BIT_F1)
