terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.70.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.6.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.2.3"
    }
  }
}

  provider "aws" {
    alias   = "east"
    region  = "us-east-1"
    profile = "default"

}

provider "archive" {}
# for create a zip file


