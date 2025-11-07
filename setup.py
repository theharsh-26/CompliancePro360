"""
CompliancePro360 Setup Script
Automates initial setup and configuration
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def run_command(command, description):
    """Run shell command with error handling"""
    print(f"➤ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required software is installed"""
    print_header("Checking Prerequisites")
    
    prerequisites = {
        "python": "python --version",
        "pip": "pip --version",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version",
        "git": "git --version"
    }
    
    all_installed = True
    for name, command in prerequisites.items():
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            version = result.stdout.strip().split('\n')[0]
            print(f"✓ {name}: {version}")
        except subprocess.CalledProcessError:
            print(f"✗ {name}: Not installed")
            all_installed = False
    
    return all_installed


def create_env_file():
    """Create .env file from .env.example"""
    print_header("Creating Environment File")
    
    if os.path.exists(".env"):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env creation")
            return True
    
    if os.path.exists(".env.example"):
        try:
            with open(".env.example", "r") as source:
                content = source.read()
            
            with open(".env", "w") as target:
                target.write(content)
            
            print("✓ Created .env file from .env.example")
            print("⚠ Please edit .env file with your configuration")
            return True
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")
            return False
    else:
        print("✗ .env.example not found")
        return False


def setup_virtual_environment():
    """Create and activate virtual environment"""
    print_header("Setting Up Virtual Environment")
    
    if os.path.exists("venv"):
        response = input("Virtual environment already exists. Recreate? (y/N): ")
        if response.lower() != 'y':
            print("Using existing virtual environment")
            return True
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    print("✓ Virtual environment created")
    print("⚠ Activate it with:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    return True


def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    # Determine pip command based on OS
    pip_cmd = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
    
    if not run_command(
        f"{pip_cmd} install --upgrade pip",
        "Upgrading pip"
    ):
        return False
    
    if not run_command(
        f"{pip_cmd} install -r requirements.txt",
        "Installing Python packages"
    ):
        return False
    
    return True


def setup_database():
    """Initialize database"""
    print_header("Database Setup")
    
    print("Database setup options:")
    print("1. Use Docker (PostgreSQL + Redis)")
    print("2. Use local PostgreSQL")
    print("3. Skip database setup")
    
    choice = input("Select option (1-3): ")
    
    if choice == "1":
        return run_command(
            "docker-compose up -d postgres redis",
            "Starting PostgreSQL and Redis containers"
        )
    elif choice == "2":
        print("⚠ Make sure PostgreSQL is running locally")
        print("⚠ Update DATABASE_URL in .env file")
        return True
    else:
        print("Skipping database setup")
        return True


def initialize_database():
    """Run database migrations"""
    print_header("Initializing Database")
    
    python_cmd = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
    
    # Create tables
    init_script = """
from app.core.database import init_db
init_db()
print("Database tables created successfully")
"""
    
    try:
        with open("temp_init.py", "w") as f:
            f.write(init_script)
        
        result = run_command(
            f"{python_cmd} temp_init.py",
            "Creating database tables"
        )
        
        os.remove("temp_init.py")
        return result
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def setup_docker():
    """Setup Docker environment"""
    print_header("Docker Setup")
    
    response = input("Start all services with Docker? (y/N): ")
    if response.lower() != 'y':
        print("Skipping Docker setup")
        return True
    
    if not run_command(
        "docker-compose up -d",
        "Starting all Docker services"
    ):
        return False
    
    print("\n✓ All services started!")
    print("\nService URLs:")
    print("  - API: http://localhost:8000")
    print("  - API Docs: http://localhost:8000/api/v1/docs")
    print("  - Flower: http://localhost:5555")
    
    return True


def print_next_steps():
    """Print next steps for user"""
    print_header("Setup Complete!")
    
    print("🎉 CompliancePro360 setup completed successfully!\n")
    print("Next steps:\n")
    print("1. Edit .env file with your configuration:")
    print("   - Database credentials")
    print("   - LLM API keys (OpenAI/Anthropic)")
    print("   - Notification service keys (SendGrid/Twilio)")
    print()
    print("2. Start the application:")
    print("   - With Docker: docker-compose up -d")
    print("   - Without Docker:")
    print("     • Activate venv: source venv/bin/activate")
    print("     • Start API: uvicorn app.main:app --reload")
    print("     • Start Celery: celery -A app.tasks.celery_app worker -l info")
    print()
    print("3. Access the application:")
    print("   - API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/api/v1/docs")
    print()
    print("4. Read the documentation:")
    print("   - README.md - Comprehensive documentation")
    print("   - QUICKSTART.md - Quick start guide")
    print("   - PROJECT_SUMMARY.md - Project overview")
    print()
    print("For help: support@compliancepro360.com")


def main():
    """Main setup function"""
    print("\n" + "=" * 60)
    print("  CompliancePro360 Setup Script")
    print("  Head Developer: Harsh Pandey")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠ Some prerequisites are missing. Please install them first.")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n⚠ Failed to create .env file")
        sys.exit(1)
    
    # Setup choice
    print("\nSetup options:")
    print("1. Full setup (Virtual env + Dependencies + Docker)")
    print("2. Development setup (Virtual env + Dependencies)")
    print("3. Docker only")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == "1":
        # Full setup
        if not setup_virtual_environment():
            sys.exit(1)
        if not install_dependencies():
            sys.exit(1)
        if not setup_docker():
            sys.exit(1)
    
    elif choice == "2":
        # Development setup
        if not setup_virtual_environment():
            sys.exit(1)
        if not install_dependencies():
            sys.exit(1)
        if not setup_database():
            sys.exit(1)
        if not initialize_database():
            sys.exit(1)
    
    elif choice == "3":
        # Docker only
        if not setup_docker():
            sys.exit(1)
    
    else:
        print("Invalid choice")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Setup failed with error: {e}")
        sys.exit(1)
