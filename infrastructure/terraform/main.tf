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
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "production"
}

# S3 Bucket for Multi-Document Storage
resource "aws_s3_bucket" "rag_documents" {
  bucket = "multi-document-rag-storage-${var.environment}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encrypt" {
  bucket = aws_s3_bucket.rag_documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# RDS Aurora PostgreSQL with pgvector
resource "aws_db_instance" "rag_postgres" {
  identifier          = "rag-postgres-${var.environment}"
  engine              = "postgres"
  engine_version      = "16.1"
  instance_class      = "db.t4g.medium"
  allocated_storage   = 50
  max_allocated_storage = 200
  storage_encrypted   = true
  username            = "ragadmin"
  password            = "ManagedDbSecret2026!"
  skip_final_snapshot = true
}
