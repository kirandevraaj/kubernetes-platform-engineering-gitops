provider "aws" {
  region = var.aws_region

  # Credentials come from the standard AWS SDK chain (shared config/env/SSO).
  # Do not hard-code access keys here.

  default_tags {
    tags = local.common_tags
  }
}
