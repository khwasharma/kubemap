# ☸ k8s-deployment-reporter

A Python CLI tool that scans a Kubernetes cluster and generates a **namespace-segregated deployment report** — available as a terminal summary, a JSON file, and a styled HTML page.

---

## Report contents

For every namespace the tool collects:

| Field | Detail |
|---|---|
| **Namespace** | Name |
| **Total deployments** | Count of `Deployment` objects |
| **Per deployment** | Name, replicas ready / desired / available |
| **Resources** | CPU & Memory — both `requests` and `limits`, summed across all containers |
| **Images** | Container name + full `image:tag` for every container |

---

## Output formats

| Format | Description |
|---|---|
| `text` | Formatted report printed to stdout |
| `json` | Machine-readable JSON file (timestamped) |
| `html` | Self-contained styled page with colour-coded replica badges |
| `all` *(default)* | All three at once |

---

## Project structure

```
k8s-deployment-reporter/
├── k8s_reporter/               # Main package
│   ├── __init__.py             # Version / metadata
│   ├── cli.py                  # Argument parsing & entry point
│   ├── config.py               # ReporterConfig dataclass
│   ├── kube_client.py          # kubeconfig loading & API clients
│   ├── collector.py            # Kubernetes API queries
│   ├── resources.py            # CPU / memory parsing & formatting
│   └── formatters.py           # Text, JSON, and HTML output
├── tests/
│   └── test_resources.py       # Unit tests (no cluster required)
├── reports/                    # Default output directory (gitignored)
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

---

## Requirements

- Python **3.10+**
- Access to a Kubernetes cluster via `kubeconfig` or in-cluster config
- RBAC: `list` on `namespaces` (ClusterRole) and `list` on `deployments` per namespace


---

## Usage

```
k8s-reporter [OPTIONS]

Options:
  --kubeconfig PATH     Path to kubeconfig file
                        (default: $KUBECONFIG or ~/.kube/config)
  -n, --namespace NS    Limit scan to a single namespace
                        (default: all namespaces)
  --exclude NS [NS …]   Namespaces to skip when scanning all
  -o, --output FORMAT   text | json | html | all  (default: all)
  --out-dir DIR         Directory for JSON / HTML files (default: ./reports)
  --version             Show version and exit
  -h, --help            Show this message and exit
```

### Examples

```bash
# Scan everything, produce all output formats
k8s-reporter

# Production namespace only, HTML output
k8s-reporter -n production --output html

# All namespaces except system ones
k8s-reporter --exclude kube-system kube-public cert-manager

# Custom kubeconfig, save reports to ./out/
k8s-reporter --kubeconfig ~/clusters/staging.yaml --out-dir ./out

# JSON only (useful for piping into jq or further processing)
k8s-reporter --output json --out-dir /tmp
```

---

## Running from inside a pod

The tool automatically falls back to **in-cluster config** when no kubeconfig is found, so you can run it as a Kubernetes `Job`.

Minimal RBAC for the service account:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8s-reporter
rules:
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["list"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: k8s-reporter
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: k8s-reporter
subjects:
  - kind: ServiceAccount
    name: k8s-reporter
    namespace: default
```

---

## Running the tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# With coverage
pytest --cov=k8s_reporter --cov-report=term-missing
```

The test suite covers CPU/memory parsing and aggregation logic; **no cluster connection is required**.

---

## Sample text output

```
                       K8S CLUSTER DEPLOYMENT REPORT
                    Generated: 2025-04-01 14:32:10
================================================================================

  NAMESPACE    : production
  DEPLOYMENTS  : 3
--------------------------------------------------------------------------------
    ► api-server
      Replicas   : 3/3 ready  (3 available)
      CPU        : requests=300m  limits=1000m
      Memory     : requests=256Mi  limits=512Mi
      Images     :
          [api]  my-registry.io/api-server:v2.4.1

    ► frontend
      Replicas   : 2/2 ready  (2 available)
      CPU        : requests=100m  limits=500m
      Memory     : requests=128Mi  limits=256Mi
      Images     :
          [nginx]  nginx:1.25-alpine

    ► worker
      Replicas   : 0/1 ready  (0 available)
      CPU        : requests=500m  limits=2000m
      Memory     : requests=512Mi  limits=1Gi
      Images     :
          [worker]  my-registry.io/worker:latest
--------------------------------------------------------------------------------
```

---
