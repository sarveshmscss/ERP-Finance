provider "aws" {
  region = "ap-south-1"
}

resource "aws_vpc" "finwave_vpc" {
  cidr_block            = "10.0.0.0/24"
  enable_dns_support    = true
  enable_dns_hostnames  = true

  tags = {
    Name = "finwave_vpc"
  }
}

resource "aws_subnet" "finwave_subnet" {
  vpc_id                  = aws_vpc.finwave_vpc.id
  cidr_block              = "10.0.0.0/26"
  map_public_ip_on_launch = true

  tags = {
    Name = "finwave_subnet"
  }
}

resource "aws_internet_gateway" "finwave_ig" {
  vpc_id = aws_vpc.finwave_vpc.id

  tags = {
    Name = "finwave_ig"
  }
}

resource "aws_route_table" "finwave_route" {
  vpc_id = aws_vpc.finwave_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.finwave_ig.id
  }

  tags = {
    Name = "finwave_route"
  }
}

resource "aws_route_table_association" "finwave_route_association" {
  subnet_id      = aws_subnet.finwave_subnet.id
  route_table_id = aws_route_table.finwave_route.id
}

resource "aws_security_group" "finwave_security_group" {
  vpc_id      = aws_vpc.finwave_vpc.id
  name        = "finwave_security_group"
  description = "Allow Traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

resource "aws_instance" "app_server" {
  ami                    = "ami-0522ab6e1ddcc7055"
  instance_type          = "t2.micro"
  key_name               = "key"
  subnet_id              = aws_subnet.finwave_subnet.id
  vpc_security_group_ids = [aws_security_group.finwave_security_group.id]

  user_data = <<-EOF
    #!/bin/bash
    # Update the system
    sudo apt update -y
    sudo apt upgrade -y
    
    # Install Git
    sudo apt install -y git
    
    # Clone the repository
    git clone https://github.com/sarveshmscss/ERP-Finance.git /home/ubuntu/ERP-Finance
    
    # Install MySQL Server
    sudo apt install -y mysql-server

    # Secure MySQL installation and set root password
    sudo systemctl start mysql
    sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'Sarvesh@123';"
    sudo mysql -u root -pSarvesh@123 -e "FLUSH PRIVILEGES;"
    
    # Create ledger_db and grant all privileges
    sudo mysql -u root -pSarvesh@123 -e "CREATE DATABASE ledger_db;"
    sudo mysql -u root -pSarvesh@123 ledger_db < /home/ubuntu/ERP-Finance/ledger_db_dump.sql
    sudo mysql -u root -pSarvesh@123 -e "GRANT ALL PRIVILEGES ON ledger_db.* TO 'root'@'%' IDENTIFIED BY 'Sarvesh@123';"
    sudo mysql -u root -pSarvesh@123 -e "FLUSH PRIVILEGES;"
    
    # Change MySQL bind address to allow remote access
    sudo sed -i 's/127.0.0.1/0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
    sudo systemctl restart mysql
    
    # Install Python 3 and pip
    sudo apt install -y python3 python3-pip python3-venv

    # Navigate to the project directory
    cd /home/ubuntu/ERP-Finance
    
    # Set up the virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install required Python packages
    pip install --upgrade pip
    pip install Flask mysql-connector-python==9.0.0 Werkzeug==3.0.3
    
    # Ensure that the script is executable
    chmod +x finwave.py
    

    # Print a success message
    echo "Setup is complete. To start the app, activate the venv and run python finwave.py"
    
    EOF

  tags = {
    Name = "finwave_server"
  }
}
