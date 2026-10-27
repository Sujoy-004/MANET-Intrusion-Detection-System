"""RFC 3561 Ad hoc On-Demand Distance Vector (AODV) Routing Protocol.

Implements route discovery (RREQ broadcast), reverse route establishment,
route reply (RREP unicast), route error (RERR), sequence numbers,
and route expiration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class RouteEntry:
    """Entry in an AODV node's routing table."""
    dest: int
    next_hop: int
    hop_count: int
    dest_seq: int
    lifetime: float
    is_valid: bool = True
    precursors: Set[int] = field(default_factory=set)


@dataclass
class RREQ:
    """Route Request message."""
    rreq_id: int
    originator: int
    originator_seq: int
    dest: int
    dest_seq: int
    hop_count: int = 0


@dataclass
class RREP:
    """Route Reply message."""
    originator: int
    dest: int
    dest_seq: int
    hop_count: int
    lifetime: float


@dataclass
class RERR:
    """Route Error message."""
    unreachable_dest: int
    unreachable_seq: int


class AODVNode:
    """AODV routing protocol engine for a single MANET node."""

    DEFAULT_ACTIVE_ROUTE_TIMEOUT = 10.0  # seconds
    DEFAULT_RREQ_TIMEOUT = 2.0  # seconds

    def __init__(
        self,
        node_id: int,
        get_time: Callable[[], float],
        send_packet_cb: Callable[[int, Any], None],
        log_event_cb: Callable[..., None],
        active_route_timeout: float = DEFAULT_ACTIVE_ROUTE_TIMEOUT,
        is_blacklisted_cb: Optional[Callable[[int], bool]] = None,
    ):
        self.node_id = node_id
        self.get_time = get_time
        self.send_packet = send_packet_cb
        self.log_event = log_event_cb
        self.active_route_timeout = active_route_timeout
        self.is_blacklisted_cb = is_blacklisted_cb

        self.seq_num: int = 1
        self.rreq_id: int = 0
        self.routing_table: Dict[int, RouteEntry] = {}
        self.seen_rreq: Set[Tuple[int, int]] = set()  # (originator, rreq_id)
        self.packet_buffer: Dict[int, List[Any]] = {}  # dest -> buffered data packets
        self.pending_rreqs: Set[int] = set()

        # Behavioral flags for attack simulation injection
        self.attack_behavior: Optional[Any] = None
        self.is_blackhole: bool = False
        self.is_grayhole: bool = False
        self.grayhole_drop_prob: float = 0.5

    def is_node_blacklisted(self, node_id: int) -> bool:
        """Check whether a node ID is currently in the active quarantine blacklist."""
        return bool(self.is_blacklisted_cb and self.is_blacklisted_cb(node_id))

    def get_route(self, dest: int) -> Optional[RouteEntry]:
        """Look up valid, unexpired route to destination."""
        now = self.get_time()
        entry = self.routing_table.get(dest)
        if entry is not None:
            if self.is_node_blacklisted(entry.next_hop) or self.is_node_blacklisted(dest):
                entry.is_valid = False
                return None
            if entry.is_valid and entry.lifetime > now:
                return entry
            else:
                entry.is_valid = False
        return None

    def update_route(
        self,
        dest: int,
        next_hop: int,
        hop_count: int,
        dest_seq: int,
        lifetime: float,
    ) -> bool:
        """Update or insert route entry if more recent or shorter."""
        if self.is_node_blacklisted(next_hop) or self.is_node_blacklisted(dest):
            return False

        now = self.get_time()
        existing = self.routing_table.get(dest)

        should_update = False
        if existing is None or not existing.is_valid:
            should_update = True
        elif dest_seq > existing.dest_seq:
            should_update = True
        elif dest_seq == existing.dest_seq and hop_count < existing.hop_count:
            should_update = True
        elif existing.lifetime <= now:
            should_update = True

        if should_update:
            self.routing_table[dest] = RouteEntry(
                dest=dest,
                next_hop=next_hop,
                hop_count=hop_count,
                dest_seq=dest_seq,
                lifetime=now + lifetime,
                is_valid=True,
            )
            return True
        return False

    def initiate_route_discovery(self, dest: int) -> None:
        """Start route discovery by broadcasting RREQ."""
        now = self.get_time()
        self.seq_num += 1
        self.rreq_id += 1

        existing = self.routing_table.get(dest)
        dest_seq = existing.dest_seq if existing else 0

        rreq = RREQ(
            rreq_id=self.rreq_id,
            originator=self.node_id,
            originator_seq=self.seq_num,
            dest=dest,
            dest_seq=dest_seq,
            hop_count=0,
        )
        self.seen_rreq.add((self.node_id, self.rreq_id))
        self.pending_rreqs.add(dest)

        self.log_event(
            sim_time=now,
            src=self.node_id,
            dst=dest,
            pkt_id=self.rreq_id,
            pkt_type="RREQ",
            hop_count=0,
        )

        # Broadcast to 1-hop neighbors (indicated by dst=-1)
        self.send_packet(-1, rreq)

    def handle_rreq(self, rreq: RREQ, prev_hop: int) -> None:
        """Process incoming RREQ packet."""
        if self.is_node_blacklisted(prev_hop) or self.is_node_blacklisted(rreq.originator):
            return

        now = self.get_time()
        key = (rreq.originator, rreq.rreq_id)
        if key in self.seen_rreq:
            return  # Drop duplicate RREQ flood
        self.seen_rreq.add(key)

        # Update reverse route to originator
        self.update_route(
            dest=rreq.originator,
            next_hop=prev_hop,
            hop_count=rreq.hop_count + 1,
            dest_seq=rreq.originator_seq,
            lifetime=self.active_route_timeout,
        )

        # Check if attack behavior intercepts RREQ with spoofed RREP
        if (
            self.attack_behavior is not None
            and hasattr(self.attack_behavior, "get_spoofed_rrep_params")
            and self.node_id != rreq.dest
            and rreq.originator != self.node_id
        ):
            spoofed_params = self.attack_behavior.get_spoofed_rrep_params(
                rreq.dest, rreq.dest_seq
            )
            if spoofed_params is not None:
                spoofed_seq, spoofed_hops = spoofed_params
                rrep = RREP(
                    originator=rreq.originator,
                    dest=rreq.dest,
                    dest_seq=spoofed_seq,
                    hop_count=spoofed_hops,
                    lifetime=self.active_route_timeout,
                )
                self.log_event(
                    sim_time=now,
                    src=self.node_id,
                    dst=rreq.originator,
                    pkt_id=rreq.rreq_id,
                    pkt_type="RREP",
                    hop_count=spoofed_hops,
                )
                reverse_route = self.get_route(rreq.originator)
                if reverse_route:
                    self.send_packet(reverse_route.next_hop, rrep)
                return

        # Check if this node is the destination
        if self.node_id == rreq.dest:
            self.seq_num = max(self.seq_num, rreq.dest_seq) + 1
            rrep = RREP(
                originator=rreq.originator,
                dest=self.node_id,
                dest_seq=self.seq_num,
                hop_count=0,
                lifetime=self.active_route_timeout,
            )
            self.log_event(
                sim_time=now,
                src=self.node_id,
                dst=rreq.originator,
                pkt_id=rreq.rreq_id,
                pkt_type="RREP",
                hop_count=0,
            )
            reverse_route = self.get_route(rreq.originator)
            if reverse_route:
                self.send_packet(reverse_route.next_hop, rrep)
            return

        # Check intermediate node valid route to destination
        route_to_dest = self.get_route(rreq.dest)
        if route_to_dest and route_to_dest.dest_seq >= rreq.dest_seq:
            rrep = RREP(
                originator=rreq.originator,
                dest=rreq.dest,
                dest_seq=route_to_dest.dest_seq,
                hop_count=route_to_dest.hop_count,
                lifetime=self.active_route_timeout,
            )
            reverse_route = self.get_route(rreq.originator)
            if reverse_route:
                self.send_packet(reverse_route.next_hop, rrep)
            return

        # Otherwise forward broadcast RREQ
        forward_rreq = RREQ(
            rreq_id=rreq.rreq_id,
            originator=rreq.originator,
            originator_seq=rreq.originator_seq,
            dest=rreq.dest,
            dest_seq=max(rreq.dest_seq, route_to_dest.dest_seq if route_to_dest else 0),
            hop_count=rreq.hop_count + 1,
        )
        self.send_packet(-1, forward_rreq)

    def handle_rrep(self, rrep: RREP, prev_hop: int) -> None:
        """Process incoming RREP packet."""
        if self.is_node_blacklisted(prev_hop) or self.is_node_blacklisted(rrep.dest):
            return

        now = self.get_time()
        self.update_route(
            dest=rrep.dest,
            next_hop=prev_hop,
            hop_count=rrep.hop_count + 1,
            dest_seq=rrep.dest_seq,
            lifetime=rrep.lifetime,
        )

        if self.node_id == rrep.originator:
            self.pending_rreqs.discard(rrep.dest)
            self.log_event(
                sim_time=now,
                src=rrep.dest,
                dst=self.node_id,
                pkt_id=rrep.originator,
                pkt_type="RREP_RECV",
                hop_count=rrep.hop_count + 1,
            )
            return

        # Unicast forward towards originator
        reverse_route = self.get_route(rrep.originator)
        if reverse_route:
            forward_rrep = RREP(
                originator=rrep.originator,
                dest=rrep.dest,
                dest_seq=rrep.dest_seq,
                hop_count=rrep.hop_count + 1,
                lifetime=rrep.lifetime,
            )
            self.send_packet(reverse_route.next_hop, forward_rrep)
        else:
            # Route broken - send RERR
            self.send_rerr(rrep.dest)

    def send_rerr(self, unreachable_dest: int) -> None:
        """Broadcast Route Error for broken link."""
        now = self.get_time()
        entry = self.routing_table.get(unreachable_dest)
        seq = (entry.dest_seq + 1) if entry else 1
        if entry:
            entry.is_valid = False

        rerr = RERR(unreachable_dest=unreachable_dest, unreachable_seq=seq)
        self.log_event(
            sim_time=now,
            src=self.node_id,
            dst=unreachable_dest,
            pkt_id=seq,
            pkt_type="RERR",
            hop_count=0,
        )
        self.send_packet(-1, rerr)

    def handle_rerr(self, rerr: RERR, prev_hop: int) -> None:
        """Process received RERR."""
        entry = self.routing_table.get(rerr.unreachable_dest)
        if entry and entry.next_hop == prev_hop:
            entry.is_valid = False
            entry.dest_seq = rerr.unreachable_seq

    def invalidate_routes_through(self, bad_node: int) -> List[int]:
        """Invalidate all route entries that traverse or terminate at bad_node.
        Returns list of unreachable destinations."""
        severed: List[int] = []
        for dest, entry in list(self.routing_table.items()):
            if entry.is_valid and (entry.next_hop == bad_node or dest == bad_node):
                entry.is_valid = False
                severed.append(dest)
        return severed
