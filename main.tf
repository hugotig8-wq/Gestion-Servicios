terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Usa la versión 5 o superior
    }
  }
}

provider "aws" {
  region = "us-east-1" # La región que elijas (N. Virginia es la más barata)
  # Nota: Es mejor configurar tus credenciales en la consola de AWS CLI 
  # con 'aws configure' para no poner tus llaves aquí.
}

# --- 1. BASE: VPC Y NETWORKING --- 
resource "aws_vpc" "main_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "vpc-seguros-ia" }
}

resource "aws_internet_gateway" "main_igw" {
  vpc_id = aws_vpc.main_vpc.id
  tags   = { Name = "igw-seguros-ia" }
}

# --- 2. RUTAS Y SUBREDES --- 
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main_igw.id
  }
}

# --- 3. PERSISTENCIA: DYNAMODB --- 
# --- 1. TABLA DYNAMODB PARA METADATOS (Audios y Scrapper) ---
resource "aws_dynamodb_table" "servicios_metadata" {
  name           = "ServiciosMetadata"
  billing_mode   = "PAY_PER_REQUEST" # Ideal para Free Tier: solo pagas si la usas
  hash_key       = "id_metadata"

  attribute {
    name = "id_metadata"
    type = "S" # String (el UUID que generamos en el backend)
  }

  tags = {
    Name = "metadata-servicios-ia"
  }
}

# --- 2. PERMISOS: ACTUALIZACIÓN DEL ROL ---
# Añadimos este bloque a tu política de IAM para que el backend pueda escribir en Dynamo
resource "aws_iam_role_policy" "lambda_dynamo_extra" {
  name = "lambda_dynamo_extra_policy"
  role = aws_iam_role.lambda_role.id # Usando el rol unificado que definimos antes

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.servicios_metadata.arn
      }
    ]
  })
}

# --- 4. OBSERVABILIDAD: CLOUDWATCH --- 
resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/api-gw/api-seguros-expert"
  retention_in_days = 7
}

# --- 5. IAM Y SEGURIDAD (Sin duplicados) --- 
resource "aws_iam_role" "lambda_role" {
  name = "lambda_proxy_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy" "lambda_master_policy" {
  name = "lambda_master_policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"], Resource = "*" },
      { Effect = "Allow", Action = ["dynamodb:*"], Resource = aws_dynamodb_table.servicios_metadata.arn },
      { Effect = "Allow", Action = ["logs:*"], Resource = "*" }
    ]
  })
}

# --- 6. API GATEWAY V2 (HTTP API) --- 
resource "aws_apigatewayv2_api" "api_seguros" {
  name          = "api-seguros-expert"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

# --- 4. ALMACENAMIENTO DE OBJETOS: S3 ---
resource "aws_s3_bucket" "servicios_assets" {
  bucket = "gestseguros-assets-${random_id.suffix.hex}" # Nombre único global
  force_destroy = true # Permite borrar el bucket aunque tenga archivos (útil en pruebas)
}

# Bloqueamos el acceso público por seguridad profesional
resource "aws_s3_bucket_public_access_block" "assets_access" {
  bucket                  = aws_s3_bucket.servicios_assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Necesitamos un ID aleatorio porque los nombres de S3 son únicos en TODO el mundo
resource "random_id" "suffix" {
  byte_length = 4
}

# --- 7. GRUPO DE SEGURIDAD PARA RDS ---
# Esto es el "escudo" de la base de datos. 
# Solo permite tráfico por el puerto 5432.
resource "aws_security_group" "rds_sg" {
  name        = "rds-sg-seguros"
  description = "Permitir acceso a Postgres"
  vpc_id      = aws_vpc.main_vpc.id

  # Entrada: Permitimos que tú entres desde tu casa (IP pública)
  # y que la futura Lambda/App también entre.
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # En producción, usa solo tu IP por seguridad
  }

  # Salida: Permitir que la DB responda
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- 8. SUBREDES PARA LA BASE DE DATOS ---
# RDS requiere al menos dos subredes en zonas distintas para existir
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "main-rds-subnet-group"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = { Name = "RDS Subnet Group" }
}

# --- 9. INSTANCIA DE BASE DE DATOS RDS (POSTGRES) ---
resource "aws_db_instance" "postgres_db" {
  identifier           = "gestseguros-db"
  allocated_storage    = 20            # 20GB es el máximo gratuito
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "15"        # Versión recomendada
  instance_class       = "db.t3.micro" # Esta es la única clase GRATIS
  
  db_name              = "gestseguros" # Nombre de la base de datos inicial
  username             = "postgres"    # Usuario maestro
  password             = "TuPasswordSeguro123" # ¡Cámbiala después!

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  
  publicly_accessible    = true        # Para que puedas conectar DBeaver desde tu PC
  skip_final_snapshot    = true        # Para que borre rápido si haces terraform destroy
  
  tags = {
    Name = "DB-GestSeguros-V1"
  }
}

# --- OUTPUT: El punto de conexión ---
# Cuando termine el 'apply', Terraform te dará la dirección web (Endpoint)
output "rds_endpoint" {
  value = aws_db_instance.postgres_db.endpoint
}

# --- 10. SUBREDES PÚBLICAS (Donde vivirá el RDS y la API) ---

# Subred A (Zona de disponibilidad 1)
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a" # Asegúrate que coincida con tu región
  map_public_ip_on_launch = true
  tags                    = { Name = "subnet-seguros-a" }
}

# Subred B (Zona de disponibilidad 2 - Requisito de RDS)
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
  tags                    = { Name = "subnet-seguros-b" }
}

# --- 11. TABLA DE RUTAS (Para que las subredes tengan internet) ---

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public_rt.id
}