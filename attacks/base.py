"""Abstract base class and protocols for attack strategies.

All attack strategies must inherit from AttackStrategy and implement
the required hooks. Attacks must be self-contained and depend only on
the Python standard library.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class AttackStrategy(ABC):
    """Abstract base class for adversarial routing behavior strategies."""

    @abstractmethod
    def get_spoofed_rrep_params(self, dest: int, rreq_dest_seq: int) -> Optional[Tuple[int, int]]:
        """Return spoofed (dest_seq, hop_count) for an intercepted RREQ, or None if honest."""
        pass

    @abstractmethod
    def should_drop_data(self, pkt_src: int, pkt_dst: int, pkt_id: int) -> bool:
        """Determine whether to drop an intercepted application data packet."""
        pass
