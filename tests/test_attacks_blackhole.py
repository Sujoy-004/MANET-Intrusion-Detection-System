"""Unit tests for BlackholeStrategy and attacks registry."""

import pytest

from attacks.base import AttackStrategy
from attacks.blackhole import BlackholeStrategy
from attacks.registry import create_attack_strategy


def test_blackhole_strategy_inheritance():
    """Verify BlackholeStrategy inherits from AttackStrategy."""
    strategy = BlackholeStrategy()
    assert isinstance(strategy, AttackStrategy)


def test_blackhole_spoofed_rrep_params_default():
    """Verify default spoofed RREP parameter generation."""
    strategy = BlackholeStrategy(seq_offset=1000, spoofed_hops=1)
    
    # Requesting dest seq = 5
    spoofed_seq, spoofed_hops = strategy.get_spoofed_rrep_params(dest=10, rreq_dest_seq=5)
    assert spoofed_seq == 1005
    assert spoofed_hops == 1

    # Requesting dest seq = 0 (unknown)
    spoofed_seq, spoofed_hops = strategy.get_spoofed_rrep_params(dest=10, rreq_dest_seq=0)
    assert spoofed_seq == 1001
    assert spoofed_hops == 1


def test_blackhole_spoofed_rrep_params_custom():
    """Verify custom seq_offset and spoofed_hops."""
    strategy = BlackholeStrategy(seq_offset=500, spoofed_hops=2)
    spoofed_seq, spoofed_hops = strategy.get_spoofed_rrep_params(dest=15, rreq_dest_seq=12)
    assert spoofed_seq == 512
    assert spoofed_hops == 2


def test_blackhole_should_drop_data():
    """Verify BlackholeStrategy drops 100% of data packets."""
    strategy = BlackholeStrategy()
    assert strategy.should_drop_data(pkt_src=1, pkt_dst=2, pkt_id=101) is True
    assert strategy.should_drop_data(pkt_src=5, pkt_dst=20, pkt_id=999) is True


def test_registry_create_blackhole():
    """Verify registry creates BlackholeStrategy with correct parameters."""
    strategy = create_attack_strategy("Blackhole", seq_offset=2000, spoofed_hops=1)
    assert isinstance(strategy, BlackholeStrategy)
    assert strategy.seq_offset == 2000
    assert strategy.spoofed_hops == 1

    # Case-insensitive
    strategy_lower = create_attack_strategy("blackhole")
    assert isinstance(strategy_lower, BlackholeStrategy)
    assert strategy_lower.seq_offset == 1000


def test_registry_unknown_attack_type():
    """Verify registry raises ValueError on unknown attack type."""
    with pytest.raises(ValueError, match="Unknown attack type 'Wormhole'"):
        create_attack_strategy("Wormhole")
