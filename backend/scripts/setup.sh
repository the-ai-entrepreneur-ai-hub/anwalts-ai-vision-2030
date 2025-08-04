#!/bin/bash
# AnwaltsAI Backend Setup Script
# Sets up the development environment and initializes the database

set -e

echo "🚀 Setting up AnwaltsAI Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    required_version="3.11"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python $required_version or higher is required. Found: $python_version"
        exit 1
    fi
    
    print_success "Python $python_version found"
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install production dependencies
    pip install -r requirements.txt
    
    # Install development dependencies if available
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    fi
    
    print_success "Dependencies installed"
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your configuration"
    else
        print_warning ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating application directories..."
    
    mkdir -p logs uploads data/postgres data/redis backups
    
    print_success "Directories created"
}

# Check Docker
check_docker() {
    print_status "Checking Docker installation..."
    
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_success "Docker and Docker Compose found"
        return 0
    else
        print_warning "Docker or Docker Compose not found. Some features may not work."
        return 1
    fi
}

# Initialize database schema
init_database() {
    print_status "Initializing database schema..."
    
    if check_docker; then
        print_status "Starting PostgreSQL with Docker..."
        docker-compose up -d postgres
        
        # Wait for PostgreSQL to be ready
        sleep 10
        
        print_success "Database initialized"
    else
        print_warning "Docker not available. Please set up PostgreSQL manually."
        print_warning "Run the SQL script in database/schema.sql"
    fi
}

# Main setup function
main() {
    echo "============================================"
    echo "🏛️  AnwaltsAI Backend Setup"
    echo "============================================"
    echo
    
    # Change to script directory
    cd "$(dirname "$0")/.."
    
    # Run setup steps
    check_python
    create_venv
    activate_venv
    install_dependencies
    create_env_file
    create_directories
    
    # Optional steps
    if check_docker; then
        read -p "Initialize database with Docker? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            init_database
        fi
    fi
    
    echo
    echo "============================================"
    print_success "Setup completed successfully!"
    echo "============================================"
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Start services: docker-compose up -d"
    echo "3. Run migrations: python migration/migrate_client_data.py sample"
    echo "4. Start development server: uvicorn main:app --reload"
    echo
    echo "For production deployment:"
    echo "- docker-compose -f docker-compose.yml up -d"
    echo
}

# Run main function
main "$@"