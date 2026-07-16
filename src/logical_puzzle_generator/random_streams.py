from __future__ import annotations

import hashlib
import random


def derive_seed(base_seed: int, namespace: str) -> int:
    """Derive a stable deterministic child seed for a named random stream."""

    if isinstance(base_seed, bool) or not isinstance(base_seed, int):
        raise TypeError("Base seed must be an integer.")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("Random stream namespace must be a non-empty string.")
    digest = hashlib.sha256(f"{base_seed}:{namespace}".encode("utf-8")).digest()
    # 64 derived bits are sufficient for deterministic random.Random stream separation.
    return int.from_bytes(digest[:8], "big")


def derived_random(base_seed: int, namespace: str) -> random.Random:
    """Create a deterministic random source for one named child stream."""

    return random.Random(derive_seed(base_seed, namespace))
