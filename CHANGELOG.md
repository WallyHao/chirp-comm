# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `scipy` and `sounddevice` are now imported lazily, so the package imports and
  the test suite runs without an audio device or PortAudio installed.
- `generate_chirp` uses `numpy.hanning` instead of the SciPy window helper,
  removing SciPy from the core import path.

### Added

- `pyproject.toml` packaging with project metadata, keywords and classifiers.
- MIT `LICENSE`, `CHANGELOG` and `CONTRIBUTING` documentation.
- A `pytest` suite covering the Hamming(7,4) codec, the framing layer, the
  timing constants and the packet container.
- A GitHub Actions workflow running Ruff and Pytest on Python 3.9 to 3.12.
- An English `README.md`; the original Chinese notes are kept as `README.zh.md`.

### Removed

- `setup.py` and `requirements.txt`, superseded by `pyproject.toml`.

## [0.3.0] - 2026-05-02

### Added

- Linear chirp keying at 2-4 kHz with Hann-windowed symbols.
- Hamming(7,4) forward error correction and CRC framing.
- Cross-correlation sync detection and dynamic bit tracking.
- An eleven-category interference sample set and offline analyzer.
