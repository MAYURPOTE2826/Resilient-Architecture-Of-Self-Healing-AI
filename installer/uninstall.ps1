param (
    [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

function Write-Log($Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

Write-Log "Starting uninstallation process..."

# Navigate to project directory
Set-Location -Path $InstallDir

# Check if docker is available
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    Write-Log "Stopping and removing Docker containers..."
    
    # Run docker compose down
    if (Test-Path "docker-compose.prod.yml") {
        docker compose -f docker-compose.prod.yml down
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Containers successfully stopped and removed."
        } else {
            Write-Log "Warning: docker compose down encountered an error."
        }
    } else {
        Write-Log "docker-compose.prod.yml not found, skipping container removal."
    }

    # Prompt user about removing volumes
    Add-Type -AssemblyName PresentationFramework
    $result = [System.Windows.MessageBox]::Show("Do you want to completely remove the application data volumes? (This will delete the database, metrics, and logs)", "Remove Data Volumes?", "YesNo", "Question")
    
    if ($result -eq "Yes") {
        Write-Log "Removing volumes..."
        docker compose -f docker-compose.prod.yml down -v
    } else {
        Write-Log "Data volumes preserved."
    }
} else {
    Write-Log "Docker not found, skipping container management."
}

Write-Log "Uninstallation scripts completed."
Start-Sleep -Seconds 2
