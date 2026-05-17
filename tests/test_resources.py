"""
tests/test_resources.py
-----------------------
Unit tests for CPU / memory parsing and aggregation logic.
No Kubernetes cluster required.
"""

import pytest
from k8s_reporter.resources import (
    parse_cpu_to_millicores,
    parse_mem_to_bytes,
    format_cpu,
    format_mem,
    aggregate_container_resources,
)


# ── CPU parsing ───────────────────────────────────────────────────────────────

class TestParseCpu:
    def test_millicores(self):
        assert parse_cpu_to_millicores("500m") == 500

    def test_full_cores(self):
        assert parse_cpu_to_millicores("2") == 2000

    def test_fractional_cores(self):
        assert parse_cpu_to_millicores("0.5") == 500

    def test_none(self):
        assert parse_cpu_to_millicores(None) == 0

    def test_empty(self):
        assert parse_cpu_to_millicores("") == 0

    def test_invalid(self):
        assert parse_cpu_to_millicores("abc") == 0


class TestFormatCpu:
    def test_nonzero(self):
        assert format_cpu(250) == "250m"

    def test_zero(self):
        assert format_cpu(0) == "—"


# ── Memory parsing ────────────────────────────────────────────────────────────

class TestParseMem:
    def test_mebibytes(self):
        assert parse_mem_to_bytes("128Mi") == 128 * 1024 ** 2

    def test_gibibytes(self):
        assert parse_mem_to_bytes("2Gi") == 2 * 1024 ** 3

    def test_kibibytes(self):
        assert parse_mem_to_bytes("512Ki") == 512 * 1024

    def test_plain_bytes(self):
        assert parse_mem_to_bytes("1048576") == 1_048_576

    def test_none(self):
        assert parse_mem_to_bytes(None) == 0

    def test_megabytes_si(self):
        assert parse_mem_to_bytes("100M") == 100 * 1_000 ** 2


class TestFormatMem:
    def test_mib(self):
        assert format_mem(256 * 1024 ** 2) == "256Mi"

    def test_gib(self):
        result = format_mem(2 * 1024 ** 3)
        assert "Gi" in result

    def test_zero(self):
        assert format_mem(0) == "—"


# ── Aggregation ───────────────────────────────────────────────────────────────

class _FakeResources:
    def __init__(self, requests=None, limits=None):
        self.requests = requests or {}
        self.limits   = limits   or {}


class _FakeContainer:
    def __init__(self, name, requests=None, limits=None):
        self.name      = name
        self.resources = _FakeResources(requests, limits)


class TestAggregateResources:
    def test_single_container(self):
        containers = [
            _FakeContainer("app", requests={"cpu": "200m", "memory": "256Mi"},
                                  limits={"cpu": "500m", "memory": "512Mi"}),
        ]
        result = aggregate_container_resources(containers)
        assert result["cpu_requests"]  == "200m"
        assert result["cpu_limits"]    == "500m"
        assert result["mem_requests"]  == "256Mi"
        assert result["mem_limits"]    == "512Mi"

    def test_multiple_containers_summed(self):
        containers = [
            _FakeContainer("app",     requests={"cpu": "100m", "memory": "128Mi"}),
            _FakeContainer("sidecar", requests={"cpu": "50m",  "memory": "64Mi"}),
        ]
        result = aggregate_container_resources(containers)
        assert result["cpu_requests"] == "150m"
        assert result["mem_requests"] == "192Mi"

    def test_no_resources(self):
        class _Bare:
            name = "bare"
            resources = None
        result = aggregate_container_resources([_Bare()])
        assert result["cpu_requests"] == "—"
        assert result["mem_limits"]   == "—"

    def test_empty_list(self):
        result = aggregate_container_resources([])
        assert all(v == "—" for v in result.values())
