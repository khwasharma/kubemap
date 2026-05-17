"""
resources.py
------------
Utility functions for parsing and normalising Kubernetes resource strings
(CPU millicores, memory MiB/GiB) and aggregating them across containers.
"""

from __future__ import annotations


# ── CPU ───────────────────────────────────────────────────────────────────────

def parse_cpu_to_millicores(value: str | None) -> int:
    """Return CPU value as an integer number of millicores (0 if missing)."""
    if not value:
        return 0
    if value.endswith("m"):
        try:
            return int(value[:-1])
        except ValueError:
            return 0
    try:
        return int(float(value) * 1000)
    except ValueError:
        return 0


def format_cpu(millicores: int) -> str:
    """Format millicores back to a human-readable string."""
    return f"{millicores}m" if millicores else "—"


# ── Memory ────────────────────────────────────────────────────────────────────

_MEM_SUFFIXES: dict[str, int] = {
    "Ki": 1024,
    "Mi": 1024 ** 2,
    "Gi": 1024 ** 3,
    "Ti": 1024 ** 4,
    "K":  1_000,
    "M":  1_000 ** 2,
    "G":  1_000 ** 3,
    "T":  1_000 ** 4,
}


def parse_mem_to_bytes(value: str | None) -> int:
    """Return memory value as bytes (0 if missing/unparseable)."""
    if not value:
        return 0
    for suffix, multiplier in _MEM_SUFFIXES.items():
        if value.endswith(suffix):
            try:
                return int(float(value[: -len(suffix)]) * multiplier)
            except ValueError:
                return 0
    try:
        return int(value)
    except ValueError:
        return 0


def format_mem(byte_count: int) -> str:
    """Format bytes to a compact MiB or GiB string."""
    if not byte_count:
        return "—"
    mib = byte_count / (1024 ** 2)
    if mib >= 1024:
        return f"{mib / 1024:.2f}Gi"
    return f"{mib:.0f}Mi"


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate_container_resources(containers: list) -> dict[str, str]:
    """
    Sum CPU / memory requests & limits across all containers in a pod spec.

    Returns a dict with keys:
        cpu_requests, cpu_limits, mem_requests, mem_limits
    """
    cpu_req = cpu_lim = mem_req = mem_lim = 0

    for container in containers:
        res = getattr(container, "resources", None)
        if not res:
            continue
        requests = res.requests or {}
        limits   = res.limits   or {}

        cpu_req += parse_cpu_to_millicores(requests.get("cpu"))
        cpu_lim += parse_cpu_to_millicores(limits.get("cpu"))
        mem_req += parse_mem_to_bytes(requests.get("memory"))
        mem_lim += parse_mem_to_bytes(limits.get("memory"))

    return {
        "cpu_requests": format_cpu(cpu_req),
        "cpu_limits":   format_cpu(cpu_lim),
        "mem_requests": format_mem(mem_req),
        "mem_limits":   format_mem(mem_lim),
    }
