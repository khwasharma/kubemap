"""
config.py
---------
Centralised defaults and constants for k8s_reporter.
"""

from dataclasses import dataclass, field


@dataclass
class ReporterConfig:
    """Runtime configuration passed through the application."""

    # kubeconfig path; None → use $KUBECONFIG / ~/.kube/config / in-cluster
    kubeconfig: str | None = None

    # None → scan all namespaces
    namespace: str | None = None

    # One of: "text", "json", "html", "all"
    output_format: str = "all"

    # Directory where JSON / HTML files are written
    out_dir: str = "reports"

    # Namespaces to skip even when scanning all
    exclude_namespaces: list[str] = field(default_factory=lambda: [])
