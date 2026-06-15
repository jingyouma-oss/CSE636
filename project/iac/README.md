# IaC + Policy-as-Code starter — Week 7 (Governance)

A tiny, runnable companion to the [Week 7 lab](../../weeks/week-07/week-07-lab.md).
It shows the **agentic IaC guardrail** in action: an agent proposes Terraform, and
an **OPA policy (via conftest)** decides whether the plan is allowed — *before* any
`terraform apply`.

```
iac/
├── s3.tf            # a COMPLIANT S3 bucket (the kind an agent generates)
├── policy/s3.rego   # the OPA guardrails: encryption, public-access block, tags
├── tfplan.json      # bundled COMPLIANT plan output  → conftest PASSES
├── tfplan-bad.json  # bundled NON-COMPLIANT plan      → conftest FAILS (on purpose)
└── Makefile
```

## Run it (only needs `conftest`)

```bash
# macOS:  brew install conftest      Linux: see https://www.conftest.dev/install/
make policy        # OPA vs the compliant plan   → expect PASS
make policy-fail   # OPA vs the bad plan          → expect FAILURES (the guardrail working)
```

`make policy-fail` blocks `tfplan-bad.json` — wrong `Environment` tag, missing
`ManagedBy`, no encryption resource, no public-access block — printing one deny
message per violation. That is exactly what stops a non-compliant (or
prompt-injected) change from reaching `apply`.

## The real Terraform flow (needs terraform + AWS creds)

The bundled `tfplan*.json` let you run the policy offline. To regenerate the plan
from `s3.tf` against real Terraform:

```bash
make validate      # terraform fmt + validate
make plan          # terraform plan → terraform show -json > tfplan.json
make policy        # then re-check the freshly generated plan
```

## How this maps to the lab

| Lab step | Here |
|---|---|
| Agent generates a Terraform resource | `s3.tf` (compliant target the agent should produce) |
| Validate + plan | `make validate` / `make plan` |
| Write & run an OPA policy | `policy/s3.rego` + `make policy` |
| Deliberately break a policy | `make policy-fail` (or edit `s3.tf`'s `Environment` tag) |
| Prompt-injection demo | `tfplan-bad.json` mimics an injected `attacker-controlled-bucket` — OPA still catches it |

The lesson: **the policy gate is independent of the agent.** Even if the agent is
tricked into generating a bad resource, conftest inspects the resulting plan and
blocks it — and an agent with no `terraform_apply` tool can't apply it anyway.
