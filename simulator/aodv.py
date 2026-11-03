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


@dataclass
class DiscoveryState:
    """State of an ongoing route discovery for a destination."""
    dest: int
    retries: int = 0
    timeout: float = 2.0
    timer_token: int = 0
    last_attempt_time: float = 0.0


class AODVNode:
    """AODV routing protocol engine for a single MANET node."""

    DEFAULT_ACTIVE_ROUTE_TIMEOUT = 10.0  # seconds
    DEFAULT_RREQ_TIMEOUT = 2.0  # seconds
    DEFAULT_RREQ_RETRIES = 2
    DEFAULT_DISCOVERY_COOLDOWN = 2.0  # seconds
    DEFAULT_MAX_BUFFER_PER_DEST = 100
    DEFAULT_MAX_BUFFER_TIME = 20.0  # seconds
    DEFAULT_BACKOFF_MULT = 2.0

    def __init__(
        self,
        node_id: int,
        get_time: Callable[[], float],
        send_packet_cb: Callable[[int, Any], None],
        log_event_cb: Callable[..., None],
        active_route_timeout: float = DEFAULT_ACTIVE_ROUTE_TIMEOUT,
        is_blacklisted_cb: Optional[Callable[[int], bool]] = None,
        schedule_timer_cb: Optional[Callable[[float, Callable[[], None]], Any]] = None,
        rreq_timeout: float = DEFAULT_RREQ_TIMEOUT,
        rreq_retries: int = DEFAULT_RREQ_RETRIES,
        discovery_cooldown: float = DEFAULT_DISCOVERY_COOLDOWN,
        max_buffer_per_dest: int = DEFAULT_MAX_BUFFER_PER_DEST,
        max_buffer_time: float = DEFAULT_MAX_BUFFER_TIME,
        backoff_mult: float = DEFAULT_BACKOFF_MULT,
    ):
        self.node_id = node_id
        self.get_time = get_time
        self.send_packet = send_packet_cb
        self.log_event = log_event_cb
        self.active_route_timeout = active_route_timeout
        self.is_blacklisted_cb = is_blacklisted_cb
        self.schedule_timer_cb = schedule_timer_cb
        self.rreq_timeout = rreq_timeout
        self.rreq_retries = rreq_retries
        self.discovery_cooldown = discovery_cooldown
        self.max_buffer_per_dest = max_buffer_per_dest
        self.max_buffer_time = max_buffer_time
        self.backoff_mult = backoff_mult

        self.seq_num: int = 1
        self.rreq_id: int = 0
        self.routing_table: Dict[int, RouteEntry] = {}
        self.seen_rreq: Set[Tuple[int, int]] = set()  # (originator, rreq_id)
        self.packet_buffer: Dict[int, List[Any]] = {}  # dest -> buffered data packets
        self.pending_rreqs: Set[int] = set()

        self.discovery_states: Dict[int, DiscoveryState] = {}
        self.discovery_cooldown_until: Dict[int, float] = {}
        self._timer_token_counter: int = 0

        # Behavioral flags for attack simulation injection
        self.attack_behavior: Optional[Any] = None
        self.is_blackhole: bool = False
        self.is_grayhole: bool = False
        self.grayhole_drop_prob: float = 0.5

    def is_node_blacklisted(self, node_id: int) -> bool:
        """Check whether a node ID is currently in the active quarantine blacklist."""
        return bool(self.is_blacklisted_cb and self.is_blacklisted_cb(node_id))

    def is_discovery_in_cooldown(self, dest: int) -> bool:
        """Check if destination is currently in discovery cooldown."""
        return self.get_time() < self.discovery_cooldown_until.get(dest, 0.0)

    def buffer_packet(self, pkt: Any) -> bool:
        """Buffer data packet at source, enforcing expiration and capacity limits.
        Returns True if packet was successfully buffered, False if dropped."""
        now = self.get_time()
        dest = pkt.dst
        if dest not in self.packet_buffer:
            self.packet_buffer[dest] = []
        buf = self.packet_buffer[dest]

        # 1. Prune expired packets
        unexpired = []
        for p in buf:
            if now - p.timestamp > self.max_buffer_time:
                self.log_event(
                    sim_time=now,
                    src=p.src,
                    dst=p.dst,
                    pkt_id=p.pkt_id,
                    pkt_type="DATA_DROP",
                    hop_count=p.hop_count,
                    dropped_by=self.node_id,
                )
            else:
                unexpired.append(p)
        buf = unexpired

        # 2. Check if packet itself is expired
        if now - pkt.timestamp > self.max_buffer_time:
            self.log_event(
                sim_time=now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=self.node_id,
            )
            self.packet_buffer[dest] = buf
            return False

        # 3. Queue size limit: drop oldest packet if full
        if len(buf) >= self.max_buffer_per_dest:
            old_pkt = buf.pop(0)
            self.log_event(
                sim_time=now,
                src=old_pkt.src,
                dst=old_pkt.dst,
                pkt_id=old_pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=old_pkt.hop_count,
                dropped_by=self.node_id,
            )

        buf.append(pkt)
        self.packet_buffer[dest] = buf
        return True

    def get_buffered_packets(self, dest: int) -> List[Any]:
        """Retrieve and remove eligible (unexpired) buffered packets for dest.
        Expired packets are dropped with DATA_DROP logged."""
        now = self.get_time()
        buffered = self.packet_buffer.pop(dest, [])
        eligible: List[Any] = []
        for pkt in buffered:
            if now - pkt.timestamp > self.max_buffer_time:
                self.log_event(
                    sim_time=now,
                    src=pkt.src,
                    dst=pkt.dst,
                    pkt_id=pkt.pkt_id,
                    pkt_type="DATA_DROP",
                    hop_count=pkt.hop_count,
                    dropped_by=self.node_id,
                )
            else:
                eligible.append(pkt)
        return eligible

    def drop_buffered_packets(self, dest: int) -> List[Any]:
        """Drop all buffered packets for dest, logging DATA_DROP."""
        now = self.get_time()
        dropped = self.packet_buffer.pop(dest, [])
        for pkt in dropped:
            self.log_event(
                sim_time=now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=self.node_id,
            )
        return dropped

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

    def initiate_route_discovery(self, dest: int, force: bool = False) -> bool:
        """Start route discovery by broadcasting RREQ with timeout scheduling."""
        if self.is_node_blacklisted(dest):
            return False
        if dest in self.pending_rreqs:
            return False
        now = self.get_time()
        if not force and self.is_discovery_in_cooldown(dest):
            return False
        if self.get_route(dest) is not None:
            return False

        self._timer_token_counter += 1
        state = DiscoveryState(
            dest=dest,
            retries=0,
            timeout=self.rreq_timeout,
            timer_token=self._timer_token_counter,
            last_attempt_time=now,
        )
        self.discovery_states[dest] = state
        self.pending_rreqs.add(dest)

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

        if self.schedule_timer_cb:
            tok = state.timer_token
            self.schedule_timer_cb(state.timeout, lambda d=dest, t=tok: self.handle_rreq_timeout(d, t))
        return True

    def handle_rreq_timeout(self, dest: int, token: int) -> None:
        """Handle expiration of an RREQ discovery timer."""
        state = self.discovery_states.get(dest)
        if state is None or state.timer_token != token:
            return  # Stale, cancelled, or superseding timer

        # If destination was blacklisted in the meantime, abort discovery
        if self.is_node_blacklisted(dest):
            self.pending_rreqs.discard(dest)
            self.discovery_states.pop(dest, None)
            self.drop_buffered_packets(dest)
            return

        # Check if route already valid
        if self.get_route(dest) is not None:
            self.pending_rreqs.discard(dest)
            self.discovery_states.pop(dest, None)
            return

        now = self.get_time()
        if state.retries < self.rreq_retries:
            # Retransmit RREQ with exponential backoff
            state.retries += 1
            state.timeout = state.timeout * self.backoff_mult
            self._timer_token_counter += 1
            state.timer_token = self._timer_token_counter
            state.last_attempt_time = now

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

            self.log_event(
                sim_time=now,
                src=self.node_id,
                dst=dest,
                pkt_id=self.rreq_id,
                pkt_type="RREQ",
                hop_count=0,
            )
            self.send_packet(-1, rreq)

            if self.schedule_timer_cb:
                tok = state.timer_token
                self.schedule_timer_cb(state.timeout, lambda d=dest, t=tok: self.handle_rreq_timeout(d, t))
        else:
            # Retries exhausted
            self.pending_rreqs.discard(dest)
            self.discovery_states.pop(dest, None)
            self.discovery_cooldown_until[dest] = now + self.discovery_cooldown

            # Drop all buffered packets waiting for dest
            self.drop_buffered_packets(dest)

            # Schedule check upon cooldown expiry: if new packets arrived during cooldown, restart discovery
            if self.schedule_timer_cb:
                def _check_cooldown_restart(d=dest):
                    if d in self.packet_buffer and self.packet_buffer[d]:
                        if d not in self.pending_rreqs and not self.is_node_blacklisted(d):
                            self.initiate_route_discovery(d)
                self.schedule_timer_cb(self.discovery_cooldown, _check_cooldown_restart)

    def handle_rreq(self, rreq: RREQ, prev_hop: int) -> None:
        """Process incoming RREQ packet."""
        if (
            self.is_node_blacklisted(self.node_id)
            or self.is_node_blacklisted(prev_hop)
            or self.is_node_blacklisted(rreq.originator)
        ):
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

    def handle_rrep(self, rrep: RREP, prev_hop: int) -> bool:
        """Process incoming RREP packet. Returns True if accepted and route established/forwarded."""
        if self.is_node_blacklisted(prev_hop) or self.is_node_blacklisted(rrep.dest):
            return False

        now = self.get_time()
        updated = self.update_route(
            dest=rrep.dest,
            next_hop=prev_hop,
            hop_count=rrep.hop_count + 1,
            dest_seq=rrep.dest_seq,
            lifetime=rrep.lifetime,
        )
        if not updated:
            return False

        if self.node_id == rrep.originator:
            self.pending_rreqs.discard(rrep.dest)
            if rrep.dest in self.discovery_states:
                self.discovery_states[rrep.dest].timer_token += 1
                del self.discovery_states[rrep.dest]
            self.discovery_cooldown_until.pop(rrep.dest, None)

            self.log_event(
                sim_time=now,
                src=rrep.dest,
                dst=self.node_id,
                pkt_id=rrep.originator,
                pkt_type="RREP_RECV",
                hop_count=rrep.hop_count + 1,
            )
            return True

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
            return True
        else:
            # Route broken - send RERR
            self.send_rerr(rrep.dest)
            return False

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

        if bad_node in self.discovery_states:
            self.discovery_states[bad_node].timer_token += 1
            del self.discovery_states[bad_node]
            self.pending_rreqs.discard(bad_node)
            self.drop_buffered_packets(bad_node)

        return severed
