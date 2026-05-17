"""
cli.py
------
Command-line interface for k8s_reporter.
Parses arguments, wires up the pipeline, and dispatches to formatters.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .config import ReporterConfig
from .kube_client import get_apps_v1, load_kube_config
from .collector import collect_report
from .formatters import print_text_report, write_json_report, write_html_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="k8s-reporter",
        description=(
            "Scan a Kubernetes cluster and generate a namespace-segregated "
            "deployment report (text / JSON / HTML)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Scan all namespaces, produce all output formats
  k8s-reporter

  # Scan a single namespace, HTML report only
  k8s-reporter -n production --output html

  # Use a custom kubeconfig and save reports to ./out/
  k8s-reporter --kubeconfig ~/clusters/staging.yaml --out-dir ./out

  # Exclude system namespaces
  k8s-reporter --exclude kube-system kube-public
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "--kubeconfig",
        metavar="PATH",
        default=None,
        help="Path to kubeconfig file (default: $KUBECONFIG or ~/.kube/config)",
    )
    parser.add_argument(
        "--namespace", "-n",
        metavar="NS",
        default=None,
        help="Limit scan to a single namespace (default: all namespaces)",
    )
    parser.add_argument(
        "--exclude",
        metavar="NS",
        nargs="+",
        default=[],
        help="Namespaces to exclude when scanning all (e.g. kube-system kube-public)",
    )
    parser.add_argument(
        "--output", "-o",
        choices=["text", "json", "html", "all"],
        default="all",
        help="Output format (default: all)",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        default="reports",
        help="Directory for JSON / HTML output files (default: ./reports)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args   = parser.parse_args(argv)

    cfg = ReporterConfig(
        kubeconfig=args.kubeconfig,
        namespace=args.namespace,
        output_format=args.output,
        out_dir=args.out_dir,
        exclude_namespaces=args.exclude,
    )

    # ── Connect ────────────────────────────────────────────────────────────────
    print("⏳  Connecting to cluster …")
    load_kube_config(cfg.kubeconfig)
    apps_v1 = get_apps_v1()

    # ── Collect ────────────────────────────────────────────────────────────────
    scope = f"namespace '{cfg.namespace}'" if cfg.namespace else "all namespaces"
    print(f"⏳  Collecting deployment data ({scope}) …")

    try:
        report = collect_report(
            apps_v1,
            namespace=cfg.namespace,
            exclude_namespaces=cfg.exclude_namespaces,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    total_ns   = len(report)
    total_deps = sum(ns["total_deployments"] for ns in report)
    print(f"✅  Found {total_deps} deployment(s) across {total_ns} namespace(s).\n")

    # ── Output ─────────────────────────────────────────────────────────────────
    out_dir   = Path(cfg.out_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if cfg.output_format in ("text", "all"):
        print_text_report(report)

    if cfg.output_format in ("json", "all"):
        write_json_report(report, out_dir / f"k8s_report_{timestamp}.json")

    if cfg.output_format in ("html", "all"):
        write_html_report(report, out_dir / f"k8s_report_{timestamp}.html")

    return 0


if __name__ == "__main__":
    sys.exit(main())
