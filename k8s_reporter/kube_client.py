"""
kube_client.py
--------------
Handles loading kubeconfig and returning typed API clients.
"""

import sys

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException  # noqa: F401 (re-exported)
except ImportError:
    print(
        "ERROR: 'kubernetes' package not found.\n"
        "Install it with:  pip install kubernetes\n"
        "Or:               pip install -r requirements.txt"
    )
    sys.exit(1)


def load_kube_config(kubeconfig: str | None = None) -> None:
    """
    Load kubeconfig from *kubeconfig* path, the environment, or fall back to
    in-cluster config when running inside a pod.

    Raises SystemExit on complete failure.
    """
    try:
        if kubeconfig:
            config.load_kube_config(config_file=kubeconfig)
        else:
            config.load_kube_config()   # honours $KUBECONFIG / ~/.kube/config
    except config.ConfigException:
        try:
            config.load_incluster_config()
        except config.ConfigException as exc:
            print(f"ERROR: Could not load any kubeconfig: {exc}")
            sys.exit(1)


def get_apps_v1() -> client.AppsV1Api:
    return client.AppsV1Api()


def get_core_v1() -> client.CoreV1Api:
    return client.CoreV1Api()
