variable "db_username" {
  description = "The username for the RDS database"
  type        = string
  sensitive   = false
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = false
}

variable "db_name" {
  description = "The name of the RDS database"
  type        = string
  default     = "schools"
}

variable "db_instance_class" {
  description = "The instance class for the RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "The allocated storage in GB"
  type        = number
  default     = 20
}

variable "engine_version" {
  description = "The version of the PostgreSQL engine"
  type        = string
  default     = "16.5"
}

# Bucket RDS configuration
variable "bucket_name" {
  description = "S3 Bucket RDS endpoint "
  type        = string
  default     = "techschools"
}

variable "object_name" {
  description = "S3 Bucket RDS endpoint "
  type        = string
  default     = "schools.json"
}

#code path
variable "code_path" {
  description = "Path to the code file"
  type        = string
  default     = "/home/sandra/Documents/code/schools/code"
}

#build path
variable "build_path" {
  description = "Path to the build file"
  type        = string
  default     = "/home/sandra/Documents/code/schools/layer"
}

#lambda name
variable "function_name" {
  description = "lambda function name"
  type        = string
  default     = "school_lambda_function"
}

# python runtime
variable "python_runtime" {
  description = "python run time to use"
  type        = string
  default     = "python3.12"
}



