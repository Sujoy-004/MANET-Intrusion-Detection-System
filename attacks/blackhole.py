"""RFC 3561 Blackhole attack strategy implementation.

The Blackhole node replies directly to RREQs with an artificially inflated
destination sequence number and a minimal hop count (1), diverting data
traffic through itself and silently dropping 100% of intercepted data packets.
"""

from __future__ import annotations

from typing import Tuple

from attacks.base import AttackStrategy


class BlackholeStrategy(AttackStrategy):
    """Adversarial strategy executing a classic RFC 3561 Blackhole attack."""

    def __init__(self, seq_offset: int = 1000, spoofed_hops: int = 1) -> None:
        self.seq_offset = seq_offset
        self.spoofed_hops = spoofed_hops

    def get_spoofed_rrep_params(self, dest: int, rreq_dest_seq: int) -> Tuple[int, int]:
        """Return artificially inflated destination sequence number and 1-hop distance.

        Args:
            dest: Target destination node ID.
            rreq_dest_seq: Sequence number requested in the incoming RREQ.

        Returns:
            Tuple of (spoofed_dest_seq, spoofed_hop_count).
        """
        spoofed_seq = max(1, rreq_dest_seq) + self.seq_offset
        return (spoofed_seq, self.spoofed_hops)

    def should_drop_data(self, pkt_src: int, pkt_dst: int, pkt_id: int) -> bool:
        """Silently drop 100% of intercepted data packets."""
        return True
