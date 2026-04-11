variable "aws_region" {
  description = "AWS Region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.medium" # k3s runs better on t2.medium than t2.micro
}

variable "key_name" {
  description = "Name of the existing AWS key pair for SSH access"
  type        = string
  default     = "healthguard-key"
}
