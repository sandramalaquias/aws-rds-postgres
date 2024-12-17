output "RDS_ENDPOINT" {
  value       = aws_db_instance.postgres.endpoint
  description = "The endpoint of the RDS instance"
  sensitive = true
}

output "RDS_PORT" {
  value       = aws_db_instance.postgres.port
  description = "The port of the RDS instance"
  sensitive = true
}

output "RDS_USER" {
  value       = aws_db_instance.postgres.username
  description = "The username of the RDS instance"
  sensitive = true
}

output "RDS_PASSWORD" {
  value       = aws_db_instance.postgres.password
  description = "The password of the RDS instance"
  sensitive   = true
}

output "RDS_DB_NAME" {
  value       = aws_db_instance.postgres.db_name
  description = "The name of the database in the RDS instance"
  sensitive = true
}
