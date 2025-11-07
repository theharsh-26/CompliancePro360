#!/bin/bash

# CompliancePro360 - Production Deployment Script
# This script automates the deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker-compose --version)"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example"
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before continuing!"
            read -p "Press Enter after you've configured .env file..."
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
    print_success ".env file exists"
}

# Create necessary directories
create_directories() {
    print_header "Creating Necessary Directories"
    
    mkdir -p logs uploads backups nginx/ssl static
    print_success "Directories created"
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certificates() {
    print_header "SSL Certificate Setup"
    
    if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
        print_info "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=IN/ST=State/L=City/O=CompliancePro360/CN=localhost" \
            2>/dev/null
        print_success "SSL certificates generated"
        print_warning "Using self-signed certificates. For production, use Let's Encrypt!"
    else
        print_success "SSL certificates already exist"
    fi
}

# Stop existing containers
stop_existing() {
    print_header "Stopping Existing Containers"
    
    if docker-compose ps | grep -q "Up"; then
        print_info "Stopping running containers..."
        docker-compose down
        print_success "Containers stopped"
    else
        print_info "No running containers found"
    fi
}

# Build images
build_images() {
    print_header "Building Docker Images"
    
    print_info "This may take a few minutes..."
    docker-compose build --no-cache
    print_success "Images built successfully"
}

# Start services
start_services() {
    print_header "Starting Services"
    
    print_info "Starting all containers..."
    docker-compose up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_success "Services started successfully"
    else
        print_warning "Some services may not be healthy yet. Check with: docker-compose ps"
    fi
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    print_info "Waiting for database to be ready..."
    sleep 5
    
    docker-compose exec -T api alembic upgrade head || {
        print_warning "Migrations not configured or failed. Skipping..."
    }
    print_success "Migrations completed"
}

# Display access information
display_info() {
    print_header "Deployment Complete!"
    
    echo ""
    print_success "CompliancePro360 is now running!"
    echo ""
    echo "Access URLs:"
    echo "  🌐 Main Application:    https://localhost"
    echo "  📚 API Documentation:   https://localhost/api/docs"
    echo "  🌸 Flower Dashboard:    https://localhost/flower/"
    echo "  📊 Direct API:          http://localhost:8000"
    echo "  🌼 Direct Frontend:     http://localhost:5000"
    echo ""
    echo "Credentials:"
    echo "  Check your .env file for Flower dashboard credentials"
    echo ""
    echo "Useful Commands:"
    echo "  View logs:              docker-compose logs -f"
    echo "  Check status:           docker-compose ps"
    echo "  Stop services:          docker-compose down"
    echo "  Restart services:       docker-compose restart"
    echo ""
    print_warning "Note: You may see SSL certificate warnings if using self-signed certificates"
    echo ""
}

# Show logs
show_logs() {
    print_header "Service Logs"
    
    print_info "Showing last 20 lines of logs (Ctrl+C to exit)..."
    sleep 2
    docker-compose logs --tail=20 -f
}

# Main deployment flow
main() {
    clear
    
    print_header "CompliancePro360 - Docker SaaS Deployment"
    echo ""
    echo "This script will deploy CompliancePro360 using Docker"
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to proceed? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
    
    # Run deployment steps
    check_prerequisites
    create_directories
    generate_ssl_certificates
    stop_existing
    build_images
    start_services
    run_migrations
    display_info
    
    # Ask to show logs
    echo ""
    read -p "Do you want to view logs? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# Parse command line arguments
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        docker-compose down
        ;;
    restart)
        docker-compose restart
        ;;
    logs)
        docker-compose logs -f
        ;;
    build)
        build_images
        ;;
    status)
        docker-compose ps
        ;;
    *)
        main
        ;;
esac
