package main

# Policy-as-Code guardrails for S3 buckets, evaluated by conftest against
# `terraform show -json` plan output. Each `deny` rule that matches produces a
# failure message and blocks the pipeline before `terraform apply` runs.
#
# Run:  conftest test tfplan.json --policy policy/
#
# These mirror the rules described in weeks/week-07/week-07-notes.md.

# --- Rule 1: every S3 bucket must carry an Environment tag ---
deny[msg] {
	r := input.resource_changes[_]
	r.type == "aws_s3_bucket"
	not r.change.after.tags.Environment
	msg := sprintf("S3 bucket '%s' is missing the required 'Environment' tag.", [r.address])
}

# --- Rule 2: every S3 bucket must carry a ManagedBy tag ---
deny[msg] {
	r := input.resource_changes[_]
	r.type == "aws_s3_bucket"
	not r.change.after.tags.ManagedBy
	msg := sprintf("S3 bucket '%s' is missing the required 'ManagedBy' tag.", [r.address])
}

# --- Rule 3: Environment must be 'capstone' for this exercise ---
deny[msg] {
	r := input.resource_changes[_]
	r.type == "aws_s3_bucket"
	r.change.after.tags.Environment
	r.change.after.tags.Environment != "capstone"
	msg := sprintf(
		"S3 bucket '%s' has Environment='%s', expected 'capstone'.",
		[r.address, r.change.after.tags.Environment],
	)
}

# --- Rule 4: server-side encryption must be configured ---
# A dedicated aws_s3_bucket_server_side_encryption_configuration resource must
# exist for the bucket (the modern Terraform pattern).
deny[msg] {
	some i
	bucket := input.resource_changes[i]
	bucket.type == "aws_s3_bucket"
	not encryption_configured
	msg := sprintf("S3 bucket '%s' must have server-side encryption configured.", [bucket.address])
}

encryption_configured {
	enc := input.resource_changes[_]
	enc.type == "aws_s3_bucket_server_side_encryption_configuration"
}

# --- Rule 5: a public-access block must be present ---
deny[msg] {
	some i
	bucket := input.resource_changes[i]
	bucket.type == "aws_s3_bucket"
	not public_access_blocked
	msg := sprintf("S3 bucket '%s' must have a public access block.", [bucket.address])
}

public_access_blocked {
	pab := input.resource_changes[_]
	pab.type == "aws_s3_bucket_public_access_block"
}
