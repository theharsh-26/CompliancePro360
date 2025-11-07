@echo off
REM CompliancePro360 - Windows Production Deployment Script
REM This script automates the deployment process on Windows

setlocal enabledelayedexpansion

echo ================================================================
echo   CompliancePro360 - Docker SaaS Deployment (Windows)
echo ================================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop for Windows
    pause
    exit /b 1
)
echo [OK] Docker is installed

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed or not in PATH
    pause
    exit /b 1
)
echo [OK] Docker Compose is installed

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found
    if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo.
        echo [IMPORTANT] Please edit .env file with your configuration!
        echo Press any key after you've configured .env file...
        pause
    ) else (
        echo [ERROR] .env.example not found!
        pause
        exit /b 1
    )
)
echo [OK] .env file exists

REM Create necessary directories
echo.
echo Creating necessary directories...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist backups mkdir backups
if not exist nginx\ssl mkdir nginx\ssl
if not exist static mkdir static
echo [OK] Directories created

REM Check SSL certificates
echo.
echo Checking SSL certificates...
if not exist nginx\ssl\cert.pem (
    echo [WARNING] SSL certificates not found
    echo For development, you can generate self-signed certificates
    echo For production, use Let's Encrypt or commercial certificates
    echo.
    echo Creating self-signed certificates for development...
    
    REM Note: This requires OpenSSL to be installed
    where openssl >nul 2>&1
    if %errorlevel% equ 0 (
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 ^
            -keyout nginx\ssl\key.pem ^
            -out nginx\ssl\cert.pem ^
            -subj "/C=IN/ST=State/L=City/O=CompliancePro360/CN=localhost"
        echo [OK] Self-signed certificates generated
    ) else (
        echo [WARNING] OpenSSL not found. Please install OpenSSL or manually create certificates
        echo You can continue, but HTTPS won't work
        pause
    )
) else (
    echo [OK] SSL certificates found
)

REM Ask to proceed
echo.
set /p proceed="Do you want to proceed with deployment? (Y/N): "
if /i not "%proceed%"=="Y" (
    echo Deployment cancelled
    pause
    exit /b 0
)

REM Stop existing containers
echo.
echo ================================================================
echo   Stopping Existing Containers
echo ================================================================
docker-compose down 2>nul
echo [OK] Stopped existing containers

REM Build images
echo.
echo ================================================================
echo   Building Docker Images
echo ================================================================
echo This may take several minutes...
echo.
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build images
    pause
    exit /b 1
)
echo [OK] Images built successfully

REM Start services
echo.
echo ================================================================
echo   Starting Services
echo ================================================================
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)
echo [OK] Services started

REM Wait for services to be ready
echo.
echo Waiting for services to be ready...
timeout /t 15 /nobreak >nul

REM Check service status
echo.
echo ================================================================
echo   Service Status
echo ================================================================
docker-compose ps

REM Run database migrations (if needed)
echo.
echo ================================================================
echo   Running Database Migrations
echo ================================================================
docker-compose exec -T api alembic upgrade head 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Migrations not configured or failed. This is normal for first deployment.
)

REM Display information
echo.
echo ================================================================
echo   DEPLOYMENT COMPLETE!
echo ================================================================
echo.
echo CompliancePro360 is now running!
echo.
echo Access URLs:
echo   Main Application:     https://localhost
echo   API Documentation:    https://localhost/api/docs
echo   Flower Dashboard:     https://localhost/flower/
echo   Direct API:           http://localhost:8000
echo   Direct Frontend:      http://localhost:5000
echo.
echo Credentials:
echo   Check your .env file for Flower dashboard credentials
echo.
echo Useful Commands:
echo   View logs:            docker-compose logs -f
echo   Check status:         docker-compose ps
echo   Stop services:        docker-compose down
echo   Restart services:     docker-compose restart
echo.
echo [NOTE] You may see SSL certificate warnings if using self-signed certificates
echo.

REM Ask to show logs
set /p showlogs="Do you want to view logs? (Y/N): "
if /i "%showlogs%"=="Y" (
    echo.
    echo Press Ctrl+C to exit logs view
    timeout /t 3 /nobreak >nul
    docker-compose logs -f
)

echo.
echo Deployment script completed!
pause
