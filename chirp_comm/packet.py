from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AcousticPacket:
    payload: str
    timestamp: datetime = field(default_factory=datetime.now)
    rssi: float = 0.0
    is_valid: bool = True

    def __repr__(self):
        return (
            f"<AcousticPacket payload='{self.payload}' rssi={self.rssi:.2f} valid={self.is_valid}>"
        )
