from .config import BIT_DUR, BIT_F0, BIT_F1, FS, PAUSE, SYNC_DUR, SYNC_F0, SYNC_F1
from .dsp import generate_chirp, hamming_74_decode, hamming_74_encode
from .engine import Listener, Transmitter
from .packet import AcousticPacket
from .protocol import ChirpProtocol

__version__ = "0.3.0"

__all__ = [
    "Transmitter",
    "Listener",
    "AcousticPacket",
    "ChirpProtocol",
    "generate_chirp",
    "hamming_74_encode",
    "hamming_74_decode",
    "FS",
    "SYNC_F0",
    "SYNC_F1",
    "BIT_F0",
    "BIT_F1",
    "SYNC_DUR",
    "BIT_DUR",
    "PAUSE",
    "__version__",
]
