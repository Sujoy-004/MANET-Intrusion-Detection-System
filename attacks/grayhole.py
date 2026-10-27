"""RFC 3561 Grayhole attack strategy implementation.

The Grayhole node participates honestly in AODV route discovery—it forwards
RREQs, emits honest RREPs (accurate sequence numbers and actual hop counts),
and handles RERRs compliantly. This ensures the node is legitimately selected
along forwarding paths. Once traffic flows, it selectively or probabilistically
drops data packets according to its configured drop probability and targets.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from attacks.base import AttackStrategy


class GrayholeStrategy(AttackStrategy):
    """Adversarial strategy executing a selective/probabilistic Grayhole attack."""

    def __init__(
        self,
        drop_prob: float = 0.5,
        target_flows: Optional[List[Tuple[int, int]]] = None,
        target_dests: Optional[List[int]] = None,
        seed: Optional[int] = None,
        rng: Optional[random.Random] = None,
        **kwargs: object,
    ) -> None:
        """Initialize Grayhole attack behavior.

        Args:
            drop_prob: Probability of dropping an intercepted data packet in (0.0, 1.0].
            target_flows: Optional list of (src, dst) pairs to target. If None, all flows considered.
            target_dests: Optional list of destination node IDs to target. If None, all dests considered.
            seed: Optional integer seed for reproducible drop decisions.
            rng: Optional external random.Random instance.
            **kwargs: Ignored additional keyword arguments for factory compatibility.
        """
        self.drop_prob = float(drop_prob)
        self.target_flows = set(target_flows) if target_flows is not None else None
        self.target_dests = set(target_dests) if target_dests is not None else None

        if rng is not None:
            self.rng = rng
        elif seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random(42)

    def get_spoofed_rrep_params(self, dest: int, rreq_dest_seq: int) -> Optional[Tuple[int, int]]:
        """Return None to indicate honest participation in AODV route discovery.

        Unlike Blackhole, Grayhole does not fabricate sequence numbers or minimal
        hop counts; it complies with normal RFC 3561 control packet routing.
        """
        return None

    def should_drop_data(self, pkt_src: int, pkt_dst: int, pkt_id: int) -> bool:
        """Determine whether to drop an intercepted application data packet.

        Evaluates target flow/destination filters first, then rolls against drop_prob.
        """
        if self.target_flows is not None and (pkt_src, pkt_dst) not in self.target_flows:
            return False

        if self.target_dests is not None and pkt_dst not in self.target_dests:
            return False

        return self.rng.random() < self.drop_prob
