"""
collector.py
------------
Queries the Kubernetes API and returns a structured report of all deployments,
grouped by namespace.
"""

from __future__ import annotations

from kubernetes import client
from kubernetes.client.rest import ApiException

from .resources import aggregate_container_resources


def _collect_deployments(apps_v1: client.AppsV1Api, namespace: str) -> list[dict]:
    """Return a list of deployment dicts for a single *namespace*."""
    try:
        items = apps_v1.list_namespaced_deployment(namespace=namespace).items
    except ApiException as exc:
        print(f"  WARN: Cannot read deployments in '{namespace}': {exc.reason}")
        return []

    deployments = []
    for dep in items:
        meta       = dep.metadata
        spec       = dep.spec
        status     = dep.status
        containers = spec.template.spec.containers or []

        images = [
            {"container": c.name, "image": c.image or "—"}
            for c in containers
        ]

        deployments.append({
            "name":               meta.name,
            "replicas_desired":   spec.replicas or 0,
            "replicas_ready":     status.ready_replicas or 0,
            "replicas_available": status.available_replicas or 0,
            "resources":          aggregate_container_resources(containers),
            "images":             images,
        })

    return sorted(deployments, key=lambda d: d["name"])


def collect_report(
    apps_v1: client.AppsV1Api,
    namespace: str | None = None,
    exclude_namespaces: list[str] | None = None,
) -> list[dict]:
    """
    Collect deployment data for every namespace (or just *namespace*).

    Parameters
    ----------
    apps_v1:
        Authenticated AppsV1Api client.
    namespace:
        If given, only this namespace is scanned.
    exclude_namespaces:
        Namespaces to skip (only applies when *namespace* is None).

    Returns
    -------
    List of namespace dicts sorted by name, each containing:
        namespace, total_deployments, deployments[]
    """
    exclude = set(exclude_namespaces or [])

    if namespace:
        ns_names = [namespace]
    else:
        core_v1 = client.CoreV1Api()
        try:
            ns_names = [
                ns.metadata.name
                for ns in core_v1.list_namespace().items
                if ns.metadata.name not in exclude
            ]
        except ApiException as exc:
            raise RuntimeError(f"Failed to list namespaces: {exc}") from exc

    report = []
    for ns in sorted(ns_names):
        deps = _collect_deployments(apps_v1, ns)
        report.append({
            "namespace":         ns,
            "total_deployments": len(deps),
            "deployments":       deps,
        })

    return report
