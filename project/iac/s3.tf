# Week 7 IaC starter — a COMPLIANT S3 bucket.
# This is the kind of resource an agent generates from a natural-language
# request; the OPA policy in policy/s3.rego is the guardrail that checks it
# before any `terraform apply`.
#
# It satisfies every rule in policy/s3.rego:
#   - server-side encryption enabled
#   - public access blocked
#   - versioning enabled
#   - Environment + ManagedBy tags present, Environment == "capstone"

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  # For `terraform plan` without real credentials, see the Makefile note.
}

resource "aws_s3_bucket" "capstone_artifacts" {
  bucket = "cse636-capstone-artifacts"

  tags = {
    Environment = "capstone"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "capstone_artifacts" {
  bucket = aws_s3_bucket.capstone_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "capstone_artifacts" {
  bucket = aws_s3_bucket.capstone_artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "capstone_artifacts" {
  bucket                  = aws_s3_bucket.capstone_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
