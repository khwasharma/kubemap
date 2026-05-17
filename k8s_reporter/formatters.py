"""
formatters.py
-------------
Output formatters for the cluster report.

Each formatter receives the raw report list produced by collector.collect_report()
and either prints to stdout (text) or writes a file (json / html).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


# ── Text ──────────────────────────────────────────────────────────────────────

def print_text_report(report: list[dict]) -> None:
    """Pretty-print the report to stdout."""
    wide = "=" * 80
    thin = "-" * 80
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'K8S CLUSTER DEPLOYMENT REPORT':^80}")
    print(f"{'Generated: ' + now:^80}")
    print(wide)

    for ns_data in report:
        deps = ns_data["deployments"]
        print(f"\n  NAMESPACE    : {ns_data['namespace']}")
        print(f"  DEPLOYMENTS  : {ns_data['total_deployments']}")
        print(thin)

        if not deps:
            print("    (no deployments)\n")
            continue

        for dep in deps:
            r = dep["resources"]
            print(f"    ► {dep['name']}")
            print(
                f"      Replicas   : {dep['replicas_ready']}/{dep['replicas_desired']} ready"
                f"  ({dep['replicas_available']} available)"
            )
            print(f"      CPU        : requests={r['cpu_requests']}  limits={r['cpu_limits']}")
            print(f"      Memory     : requests={r['mem_requests']}  limits={r['mem_limits']}")
            print("      Images     :")
            for img in dep["images"]:
                print(f"          [{img['container']}]  {img['image']}")
            print()

        print(thin)

    print(f"\n{'END OF REPORT':^80}\n")


# ── JSON ──────────────────────────────────────────────────────────────────────

def write_json_report(report: list[dict], output_path: str | Path) -> None:
    """Write the report as an indented JSON file."""
    payload = {
        "generated_at": datetime.now().isoformat(),
        "namespaces":   report,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"[✓] JSON report written → {output_path}")


# ── HTML ──────────────────────────────────────────────────────────────────────

def _replica_badge(ready: int, desired: int) -> str:
    if desired == 0:
        colour = "#94a3b8"          # grey  – scaled to zero
    elif ready == desired:
        colour = "#22c55e"          # green – fully healthy
    elif ready > 0:
        colour = "#f59e0b"          # amber – degraded
    else:
        colour = "#ef4444"          # red   – no pods running
    return (
        f'<span style="background:{colour};color:#fff;padding:2px 10px;'
        f'border-radius:9999px;font-size:0.75rem;font-weight:600;">'
        f"{ready}/{desired}</span>"
    )


def write_html_report(report: list[dict], output_path: str | Path) -> None:
    """Write a self-contained, styled HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows: list[str] = []
    for ns_data in report:
        ns    = ns_data["namespace"]
        deps  = ns_data["deployments"]
        count = ns_data["total_deployments"]

        plural = "s" if count != 1 else ""
        rows.append(
            f'<tr class="ns-header"><td colspan="5">'
            f'<strong>📦 {ns}</strong>'
            f'<span class="ns-badge">{count} deployment{plural}</span>'
            f"</td></tr>"
        )

        if not deps:
            rows.append(
                '<tr><td colspan="5" class="empty">No deployments found</td></tr>'
            )
            continue

        for dep in deps:
            r = dep["resources"]
            images_html = "<br>".join(
                f"<code>[{i['container']}] {i['image']}</code>"
                for i in dep["images"]
            ) or "—"

            rows.append(
                f"<tr>"
                f'<td class="dep-name">{dep["name"]}</td>'
                f"<td>{_replica_badge(dep['replicas_ready'], dep['replicas_desired'])}</td>"
                f"<td>req: {r['cpu_requests']}<br>lim: {r['cpu_limits']}</td>"
                f"<td>req: {r['mem_requests']}<br>lim: {r['mem_limits']}</td>"
                f"<td class='images'>{images_html}</td>"
                f"</tr>"
            )

    rows_html = "\n        ".join(rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>K8s Cluster Report – {now}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f1f5f9; color: #1e293b; padding: 2rem; font-size: 14px;
    }}
    header {{ margin-bottom: 1.5rem; }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; }}
    header p  {{ color: #64748b; font-size: 0.82rem; margin-top: 0.25rem; }}
    table {{
      width: 100%; border-collapse: collapse; background: #fff;
      border-radius: 0.75rem; overflow: hidden;
      box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    }}
    thead tr {{ background: #0f172a; color: #fff; }}
    thead th {{ padding: 0.7rem 1rem; text-align: left; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.04em; }}
    tbody tr {{ border-bottom: 1px solid #e2e8f0; }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody td {{ padding: 0.55rem 1rem; vertical-align: top; }}
    tr.ns-header td {{
      background: #e2e8f0; font-size: 0.88rem; color: #0f172a; padding: 0.5rem 1rem;
    }}
    .ns-badge {{
      background: #6366f1; color: #fff; padding: 1px 9px;
      border-radius: 9999px; font-size: 0.7rem; margin-left: 0.6rem; font-weight: 600;
    }}
    td.empty {{ padding-left: 2rem; color: #6b7280; font-style: italic; }}
    td.dep-name {{ padding-left: 2rem; font-weight: 500; }}
    td.images code {{ font-size: 0.72rem; display: block; color: #374151; }}
    tbody tr:not(.ns-header):hover {{ background: #f8fafc; }}
  </style>
</head>
<body>
  <header>
    <h1>☸ Kubernetes Cluster Deployment Report</h1>
    <p>Generated: {now}</p>
  </header>
  <table>
    <thead>
      <tr>
        <th>Deployment</th>
        <th>Replicas (ready/desired)</th>
        <th>CPU</th>
        <th>Memory</th>
        <th>Images</th>
      </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
  </table>
</body>
</html>"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"[✓] HTML report written → {output_path}")
