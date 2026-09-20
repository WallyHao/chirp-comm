# Contributing

Thanks for your interest in chirp-comm. This is a small, focused library, so
changes that keep the protocol explicit and well tested are welcome.

## Development Setup

```bash
git clone https://github.com/WallyHao/chirp-comm.git
cd chirp-comm
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

`sounddevice` and `scipy` are only needed for live audio and the bandpass
filter, so the package and its tests run on a machine without an audio device.

## Before Opening A Pull Request

```bash
ruff check .
ruff format --check .
pytest -q
```

CI runs the same checks on Python 3.9 to 3.12.

## Guidelines

- Keep the wire format stable: the sample files under `samples/` depend on the
  framing in `chirp_comm/protocol.py` and the timing constants in
  `chirp_comm/config.py`. If you change either, regenerate the samples.
- Add or update tests for every behavior change. The codec and framing layers
  are pure and easy to test without audio hardware.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
