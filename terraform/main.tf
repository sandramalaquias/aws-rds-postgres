# get VPC default
data "aws_vpc" "default" {
  default = true
}

# Security Group to RDS
resource "aws_security_group" "rds_sg" {
  depends_on = [aws_iam_role_policy_attachment.attach_rds_management_policy]
  name        = "rds-security-group"
  description = "Allow access to RDS PostgreSQL"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  allocated_storage      = var.allocated_storage
  engine                 = "postgres"
  engine_version         = var.engine_version
  instance_class         = var.db_instance_class
  username               = var.db_username
  password               = var.db_password
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  port                   = 5432
  db_name                   = var.db_name

  skip_final_snapshot = true
}

#Create bucket to RDS credentials
# S3 Bucket with ACK = Private (default) and versioning = disable (default)
resource "aws_s3_bucket" "rds_endpoint_bucket" {
  bucket        = var.bucket_name
}

resource "aws_s3_object" "rds_credentials_object" {
  bucket       = aws_s3_bucket.rds_endpoint_bucket.id
  key          = var.object_name
  content      = jsonencode({
    RDS_DB_NAME   = aws_db_instance.postgres.db_name
    RDS_ENDPOINT  = aws_db_instance.postgres.endpoint
    RDS_PASSWORD  = aws_db_instance.postgres.password
    RDS_PORT      = aws_db_instance.postgres.port
    RDS_USER      = aws_db_instance.postgres.username
  })
  content_type = "application/json"

  tags = {
    Name = "RDS Credentials File"
  }
}


# Lambda Function

resource "aws_lambda_layer_version" "pandas_layer" {
  depends_on = [null_resource.prepare_packages]
  layer_name  = "pandas-layer"
  description = "requirements pandas to school lambda"
  compatible_runtimes = ["${var.python_runtime}"]
  # path file to pandas zip
  filename = "${var.build_path}/pandas.zip"
  source_code_hash = base64sha256("${filebase64sha256("${var.build_path}/pandas.zip")}${timestamp()}")
}

# school request except pandas
resource "aws_lambda_layer_version" "request_layer" {
  depends_on = [null_resource.prepare_packages]
  layer_name  = "school-layer"
  description = "requirements to school lambda except pandas"
  compatible_runtimes = ["${var.python_runtime}"]

  # Caminho para o arquivo zip contendo as dependências
  filename = "${var.build_path}/requests.zip"
  source_code_hash = base64sha256("${filebase64sha256("${var.build_path}/requests.zip")}${timestamp()}")

}

# psycopg2 layer
resource "aws_lambda_layer_version" "psycopg2_layer" {
  depends_on = [null_resource.prepare_packages]
  layer_name  = "psycopg2-layer"
  description = "requirements to psycopg2"
  compatible_runtimes = ["${var.python_runtime}"]

  # file path to zip psycopg2
  filename = "${var.build_path}/psycopg2.zip"
  source_code_hash = base64sha256("${filebase64sha256("${var.build_path}/psycopg2.zip")}${timestamp()}")
}

  # Lambda Function
resource "aws_lambda_function" "school_lambda" {
  depends_on = [null_resource.prepare_lambda]
  layers = [aws_lambda_layer_version.pandas_layer.arn,
            aws_lambda_layer_version.request_layer.arn,
            aws_lambda_layer_version.psycopg2_layer.arn,
  ]
  function_name = "school_lambda_function"
  runtime       = "${var.python_runtime}"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "create.handler"

  # Usar o arquivo zip gerado
  filename         = "${var.code_path}/code.zip"
  source_code_hash = base64sha256("${filebase64sha256("${var.code_path}/code.zip")}${timestamp()}")



  # Configure variáveis de ambiente
  environment {
    variables = {
      BUCKET_NAME = var.bucket_name
      RDS_JSON    = var.object_name
    }
  }

  # Timeout e memória
  timeout      = 300
  memory_size  = 512
}


