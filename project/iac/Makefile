.PHONY: policy policy-fail plan validate clean help

help:
	@echo "Targets:"
	@echo "  make policy       - run OPA policy against the COMPLIANT plan (expect PASS)"
	@echo "  make policy-fail  - run OPA policy against the BAD plan (expect FAIL, on purpose)"
	@echo "  make plan         - regenerate tfplan.json from real Terraform (needs terraform + AWS creds)"
	@echo "  make validate     - terraform fmt + validate (needs terraform)"
	@echo ""
	@echo "Only conftest is required for the policy targets — they use the bundled plan JSON."

# --- Offline policy checks (only need conftest installed) ---
policy:              ## OPA policy vs the compliant plan — expect "PASS"
	conftest test tfplan.json --policy policy/

policy-fail:         ## OPA policy vs the bad plan — expect failures (demonstrates the guardrail)
	@echo "Expect this to FAIL on purpose — that's the guardrail blocking a bad plan:"
	-conftest test tfplan-bad.json --policy policy/

# --- Real Terraform flow (needs terraform + provider credentials) ---
validate:
	terraform fmt -check
	terraform init -backend=false
	terraform validate

plan:                ## regenerate tfplan.json from s3.tf (needs AWS creds)
	terraform init
	terraform plan -out=tfplan.binary
	terraform show -json tfplan.binary > tfplan.json
	@echo "Regenerated tfplan.json. Now run: make policy"

clean:
	rm -rf .terraform .terraform.lock.hcl tfplan.binary
