#!/usr/bin/env bash

set -e

echo "🔧 Instalando PostgreSQL 16..."

sudo apt-get update
sudo apt-get install -y wget gnupg lsb-release

# Repositorio oficial de PostgreSQL
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt-get update
sudo apt-get install -y postgresql-16 postgresql-client-16

echo "🔧 Configurando PostgreSQL..."

sudo systemctl enable postgresql
sudo systemctl start postgresql

# Crear usuario y base
sudo -u postgres psql <<EOF
ALTER USER postgres WITH PASSWORD 'postgres';
CREATE USER dev WITH PASSWORD 'dev';
CREATE DATABASE appdb OWNER dev;
EOF

echo "🎉 PostgreSQL instalado y configurado"
