# 🚀 Full DevOps Lifecycle on Kubernetes — FastAPI + GitHub Actions + Helm

A complete, production-grade DevOps project covering every stage from local development
to CI/CD pipelines, Kubernetes deployment, monitoring, and TLS-secured Ingress.

---

## 🗂️ Project Structure

```
k8s-devops-project/
├── app/
│   ├── main.py                  # FastAPI application
│   └── requirements.txt
├── tests/
│   └── test_api.py              # Pytest test suite
├── docker/
│   └── prometheus.yml           # Prometheus config (docker-compose)
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml         # Service + ConfigMap + HPA + ServiceAccount
│   ├── ingress/
│   │   └── ingress.yaml         # Nginx Ingress + cert-manager TLS
│   └── monitoring/
│       └── monitoring.yaml      # Prometheus + Grafana + RBAC
├── helm/
│   └── fastapi-app/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           └── _helpers.tpl
├── .github/
│   └── workflows/
│       └── cicd.yml             # Full CI/CD pipeline
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # Local dev stack
└── pytest.ini
```

---

## 📋 Prerequisites

Install all tools before starting:

```bash
# 1. Docker Desktop
https://www.docker.com/products/docker-desktop/

# 2. Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 3. kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 4. Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 5. Python 3.12+
https://www.python.org/downloads/

# Verify everything
docker --version && minikube version && kubectl version --client && helm version
```

---

## 🐳 PHASE 1 — Containerization (Docker)

### 1.1 Understanding the Multi-Stage Dockerfile

The Dockerfile uses **two stages** to keep the final image lean and secure:

| Stage     | Purpose                                 | Included in final? |
|-----------|-----------------------------------------|--------------------|
| `builder` | Install Python packages, build binaries | ❌ No              |
| `runtime` | Lean image with only what's needed      | ✅ Yes             |

This reduces image size from ~800MB → ~150MB.

### 1.2 Build and run locally

```bash
# Build the image
docker build -t fastapi-k8s-demo:local .

# Run standalone
docker run -p 8000:8000 fastapi-k8s-demo:local

# Or use docker-compose (includes Prometheus + Grafana)
docker-compose up --build

# Test the API
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/info
curl http://localhost:8000/metrics

# Open Grafana
open http://localhost:3000   # admin / admin123
```

### 1.3 Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag and push
docker tag fastapi-k8s-demo:local YOUR_USERNAME/fastapi-k8s-demo:latest
docker push YOUR_USERNAME/fastapi-k8s-demo:latest
```

---

## ☸️ PHASE 2 — Kubernetes Setup (Minikube)

### 2.1 Start Minikube

```bash
# Start with enough resources
minikube start \
  --cpus=4 \
  --memory=4096 \
  --disk-size=20g \
  --driver=docker

# Verify cluster is up
kubectl cluster-info
kubectl get nodes

# Enable essential addons
minikube addons enable ingress          # Nginx Ingress Controller
minikube addons enable metrics-server   # Required for HPA
minikube addons enable dashboard        # K8s Dashboard (optional)

# Point Docker daemon to Minikube's registry (avoids push/pull)
eval $(minikube docker-env)

# Build image directly into Minikube
docker build -t fastapi-k8s-demo:local .
```

### 2.2 Deploy base manifests

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy app (update image name first!)
# Edit k8s/base/deployment.yaml and replace YOUR_DOCKERHUB_USERNAME
kubectl apply -f k8s/base/deployment.yaml
kubectl apply -f k8s/base/service.yaml

# Watch pods come up
kubectl get pods -n fastapi-app -w

# Check logs
kubectl logs -f deployment/fastapi-app -n fastapi-app

# Describe a pod (great for debugging)
kubectl describe pod -l app=fastapi-app -n fastapi-app

# Port-forward to test locally
kubectl port-forward svc/fastapi-app-svc 8080:80 -n fastapi-app
curl http://localhost:8080/health
```

### 2.3 Verify HPA

```bash
# Check HPA status
kubectl get hpa -n fastapi-app

# Simulate load to trigger autoscaling
kubectl run load-test --image=busybox --restart=Never -n fastapi-app -- \
  sh -c "while true; do wget -q -O- http://fastapi-app-svc/; done"

# Watch pods scale up
kubectl get pods -n fastapi-app -w
```

---

## 🔒 PHASE 3 — Ingress & TLS

### 3.1 Install cert-manager

```bash
# Install cert-manager (manages TLS certificates)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml

# Wait for it to be ready
kubectl wait --for=condition=Available deployment \
  --all -n cert-manager --timeout=120s

# Verify pods
kubectl get pods -n cert-manager
```

### 3.2 Apply Ingress manifests

```bash
kubectl apply -f k8s/ingress/ingress.yaml

# Get Minikube IP
minikube ip   # e.g., 192.168.49.2

# Add to /etc/hosts so "fastapi.local" resolves
echo "$(minikube ip)  fastapi.local" | sudo tee -a /etc/hosts

# Test HTTPS (self-signed cert, so use -k to skip verification)
curl -k https://fastapi.local/
curl -k https://fastapi.local/health
```

---

## 📊 PHASE 4 — Monitoring (Prometheus + Grafana)

### 4.1 Deploy monitoring stack

```bash
kubectl apply -f k8s/monitoring/monitoring.yaml

# Wait for pods
kubectl get pods -n monitoring -w

# Get NodePort for Prometheus and Grafana
kubectl get svc -n monitoring
```

### 4.2 Access dashboards

```bash
# Prometheus UI
minikube service prometheus-svc -n monitoring --url

# Grafana UI
minikube service grafana-svc -n monitoring --url
# Login: admin / admin123
```

### 4.3 Set up Grafana dashboard

1. Open Grafana → **Configuration → Data Sources → Add Prometheus**
2. URL: `http://prometheus-svc.monitoring.svc.cluster.local:9090`
3. Import dashboard ID **`12464`** (FastAPI metrics) or **`6417`** (general K8s)
4. Key metrics to watch:
   - `http_requests_total` — request rate
   - `http_request_duration_seconds` — latency p99
   - `container_cpu_usage_seconds_total` — CPU
   - `container_memory_usage_bytes` — memory

---

## 🪄 PHASE 5 — Helm Chart Deployment

### 5.1 Deploy with Helm

```bash
# Dry-run first (renders templates without applying)
helm template fastapi-app ./helm/fastapi-app \
  --set image.repository=YOUR_USERNAME/fastapi-k8s-demo \
  --namespace fastapi-app

# Install
helm install fastapi-app ./helm/fastapi-app \
  --namespace fastapi-app \
  --create-namespace \
  --set image.repository=YOUR_USERNAME/fastapi-k8s-demo \
  --set image.tag=latest

# Check release
helm list -n fastapi-app
helm status fastapi-app -n fastapi-app

# Upgrade (simulates what CI/CD does)
helm upgrade fastapi-app ./helm/fastapi-app \
  --namespace fastapi-app \
  --set image.tag=sha-abc1234 \
  --atomic   # rolls back automatically on failure

# Rollback if needed
helm rollback fastapi-app 1 -n fastapi-app
```

---

## ⚙️ PHASE 6 — GitHub Actions CI/CD

### 6.1 Repository setup

```bash
# Initialize git repo
git init
git add .
git commit -m "feat: initial project setup"

# Create GitHub repo and push
gh repo create k8s-devops-project --public
git remote add origin https://github.com/YOUR_USERNAME/k8s-devops-project.git
git push -u origin main
```

### 6.2 Configure GitHub Secrets

Go to **GitHub → Settings → Secrets and variables → Actions** and add:

| Secret Name          | Value                                      |
|----------------------|--------------------------------------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username                   |
| `DOCKERHUB_TOKEN`    | Docker Hub access token (not password)     |
| `KUBECONFIG`         | Base64-encoded kubeconfig (see below)      |

```bash
# Generate KUBECONFIG secret
cat ~/.kube/config | base64 -w 0
# Copy the output → paste as KUBECONFIG secret
```

### 6.3 Pipeline stages

```
Push to GitHub
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  🧪 Test    │────▶│  🔒 Security │────▶│  🐳 Build &  │────▶│  🚀 Deploy  │
│  pytest     │     │  Trivy scan  │     │  Push image  │     │  Helm       │
│  ruff lint  │     │  SARIF upload│     │  Multi-arch  │     │  upgrade    │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

### 6.4 Test the pipeline

```bash
# Trigger CI on push
git checkout -b feature/my-change
echo "# test" >> README.md
git add . && git commit -m "test: trigger CI"
git push origin feature/my-change

# Open pull request → CI runs tests + security scan
# Merge to main → full pipeline runs including deploy
```

---

## 🔄 Complete DevOps Lifecycle Diagram

```
Developer
   │
   │  git push
   ▼
GitHub
   │
   ├─▶ GitHub Actions
   │       │
   │       ├─▶ 1. Run Tests (pytest)
   │       ├─▶ 2. Security Scan (Trivy)
   │       ├─▶ 3. Build Docker Image (multi-stage)
   │       ├─▶ 4. Push to Docker Hub
   │       └─▶ 5. Helm upgrade → Kubernetes
   │
   ▼
Minikube (local) / Kubernetes (prod)
   │
   ├─▶ Namespace: fastapi-app
   │       ├─▶ Deployment (2 replicas, rolling update)
   │       ├─▶ Service (ClusterIP)
   │       ├─▶ HPA (autoscale 2–10 pods)
   │       └─▶ Ingress (TLS via cert-manager)
   │
   └─▶ Namespace: monitoring
           ├─▶ Prometheus (scrapes /metrics)
           └─▶ Grafana (dashboards)
```

---

## 🛠️ Useful Commands Reference

```bash
# --- Minikube ---
minikube start / stop / delete
minikube status
minikube dashboard           # Open K8s dashboard in browser
eval $(minikube docker-env)  # Use Minikube's Docker

# --- Kubernetes ---
kubectl get all -n fastapi-app
kubectl describe deployment fastapi-app -n fastapi-app
kubectl exec -it <pod-name> -n fastapi-app -- /bin/sh
kubectl logs -f <pod-name> -n fastapi-app
kubectl top pods -n fastapi-app       # Requires metrics-server

# --- Helm ---
helm list --all-namespaces
helm history fastapi-app -n fastapi-app
helm get values fastapi-app -n fastapi-app

# --- Cleanup ---
helm uninstall fastapi-app -n fastapi-app
kubectl delete namespace fastapi-app
kubectl delete namespace monitoring
minikube stop
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ImagePullBackOff` | Check image name in deployment, ensure it's pushed to Docker Hub |
| `CrashLoopBackOff` | Run `kubectl logs <pod>` to see the error |
| `Pending` pods | Run `kubectl describe pod <pod>` — usually insufficient resources |
| Ingress not working | Check `minikube addons enable ingress` and `/etc/hosts` entry |
| HPA shows `<unknown>` | Enable metrics-server: `minikube addons enable metrics-server` |
| CI fails on deploy | Verify `KUBECONFIG` secret is correctly base64 encoded |

---

## 🔐 GitHub Actions Required Secrets

```
Settings → Secrets and variables → Actions → New repository secret

DOCKERHUB_USERNAME   → your Docker Hub username
DOCKERHUB_TOKEN      → Docker Hub access token
KUBECONFIG           → base64-encoded kubeconfig (for remote cluster)
```
