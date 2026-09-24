terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0, < 7.0.0"
    }
  }

  # Local state for the initial lab stage. Remote (S3) backend comes later.
  # State files are gitignored and must never be committed.
}
