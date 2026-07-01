NS := k8s-demo
BACKEND_IMG := k8s-demo-backend:local
FRONTEND_IMG := k8s-demo-frontend:local

# Prefer python3.12 (the runtime the backend pins + has a psycopg2 wheel).
# Fall back to python3 if it isn't installed. Override with `make test PYTHON=...`.
PYTHON := $(shell command -v python3.12 || command -v python3)

.PHONY: check images deploy status open logs test clean

check:                ## verify Docker Desktop Kubernetes is the active context
	@kubectl config current-context | grep -qx docker-desktop || { \
	  echo "kubectl context is '$$(kubectl config current-context)', not docker-desktop."; \
	  echo "Enable Kubernetes in Docker Desktop, then: kubectl config use-context docker-desktop"; \
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
