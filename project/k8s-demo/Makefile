NS := k8s-demo
BACKEND_IMG := k8s-demo-backend:local
FRONTEND_IMG := k8s-demo-frontend:local

# Prefer python3.12 (the runtime the backend pins + has a psycopg2 wheel).
# Fall back to python3 if it isn't installed. Override with `make test PYTHON=...`.
PYTHON := $(shell command -v python3.12 || command -v python3)

.PHONY: check certs images deploy status open logs test clean

certs:                ## (macOS) export the host CA bundle into the build contexts — run if builds fail with CERTIFICATE_VERIFY_FAILED behind a TLS-inspecting proxy (e.g. Zscaler)
	@security find-certificate -a -p /Library/Keychains/System.keychain > backend/certs/corp-ca.pem
	@security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain >> backend/certs/corp-ca.pem
	@cp backend/certs/corp-ca.pem frontend/certs/corp-ca.pem
	@echo "Wrote backend/certs/corp-ca.pem and frontend/certs/corp-ca.pem ($$(grep -c 'BEGIN CERT' backend/certs/corp-ca.pem) certs). Now: make images"

check:                ## verify a local single-node cluster (Docker Desktop or Rancher Desktop) is active
	@kubectl config current-context | grep -qxE 'docker-desktop|rancher-desktop' || { \
	  echo "kubectl context is '$$(kubectl config current-context)', not a supported local cluster."; \
	  echo "Enable Kubernetes in Docker Desktop or Rancher Desktop, then select its context:"; \
	  echo "  kubectl config use-context docker-desktop    # Docker Desktop"; \
	  echo "  kubectl config use-context rancher-desktop    # Rancher Desktop"; \
	  exit 1; }
	@kubectl get nodes

images:               ## build the backend and frontend images (tagged :local)
	docker build -t $(BACKEND_IMG) ./backend
	docker build -t $(FRONTEND_IMG) ./frontend

deploy:               ## apply the namespace first, then all manifests
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/

status:               ## show pods, services, and the PVC
	kubectl get pods,svc,pvc -n $(NS)

open:                 ## open the app in your browser
	open http://localhost:30080

logs:                 ## tail the backend logs across both replicas
	kubectl logs -n $(NS) -l app=backend --tail=100 -f

test:                 ## run the backend unit tests (no cluster needed)
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -q -r backend/requirements.txt pytest httpx
	cd backend && ../.venv/bin/pytest -q

clean:                ## delete everything (the namespace removes all resources)
	kubectl delete namespace $(NS) --ignore-not-found
