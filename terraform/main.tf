# -----------------------------------------------------------------------------
# FAANG-Level Terraform Architecture for AI Cloud Security Engine
# Deploys the FastAPI WAF to AWS ECS (Elastic Container Service) on Fargate
# -----------------------------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

# 1. Network Infrastructure (VPC, Subnets)
resource "aws_vpc" "sec_vpc" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "Cloud-Security-VPC"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.sec_vpc.id
  cidr_block              = "10.1.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"
}

# 2. Security Groups (Simulating WAF rules at Infrastructure layer)
resource "aws_security_group" "alb_sg" {
  name        = "sec-alb-sg"
  description = "Allow inbound HTTP/HTTPS and WebSockets"
  vpc_id      = aws_vpc.sec_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
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

# 3. Application Load Balancer
resource "aws_lb" "sec_alb" {
  name               = "ai-security-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_subnet.id]
}

resource "aws_lb_target_group" "sec_tg" {
  name        = "ai-security-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.sec_vpc.id
  target_type = "ip"
  
  health_check {
    path = "/docs"
    interval = 30
    timeout = 5
    healthy_threshold = 2
    unhealthy_threshold = 2
  }
}

# 4. ECS Fargate Cluster
resource "aws_ecs_cluster" "sec_cluster" {
  name = "ai-security-cluster"
}

# 5. Task Definition (Docker Container logic with ML Model)
resource "aws_ecs_task_definition" "sec_task" {
  family                   = "ai-security-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"  # Higher CPU required for ML Inference
  memory                   = "1024" # Higher Memory for IsolationForest model

  container_definitions = jsonencode([
    {
      name      = "ai-security-gateway"
      image     = "your-dockerhub-username/ai-security-gateway:latest"
      cpu       = 512
      memory    = 1024
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
    }
  ])
}

# 6. ECS Service (Connects Load Balancer to Task)
resource "aws_ecs_service" "sec_service" {
  name            = "ai-security-service"
  cluster         = aws_ecs_cluster.sec_cluster.id
  task_definition = aws_ecs_task_definition.sec_task.arn
  desired_count   = 2 # High Availability for WAF

  network_configuration {
    subnets          = [aws_subnet.public_subnet.id]
    security_groups  = [aws_security_group.alb_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.sec_tg.arn
    container_name   = "ai-security-gateway"
    container_port   = 8000
  }
}

output "load_balancer_dns" {
  description = "The URL to access the deployed Cloud Security API"
  value       = aws_lb.sec_alb.dns_name
}
