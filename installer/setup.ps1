param (
    [string]$InstallDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

function Write-Log($Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

# 1. Check Admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Error: Please run this script as Administrator."
    Exit 1
}

# 2. Check Disk Space (Need at least 5GB on C:)
$drive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
if ($freeSpaceGB -lt 5) {
    Write-Host "Error: Insufficient disk space on C: drive. At least 5GB required. Found $freeSpaceGB GB."
    Exit 1
}

# 3. Check WSL
Write-Log "Checking WSL status..."
$wslStatus = wsl --status 2>&1
if ($wslStatus -match "is not recognized" -or $wslStatus -match "has no installed distributions") {
    Write-Log "WSL is not installed or configured. Installing WSL..."
    wsl --install --no-distribution
    Write-Log "WSL installation initiated."
} else {
    Write-Log "WSL is installed."
}

# 4. Check Docker Desktop
Write-Log "Checking Docker Desktop..."
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Log "Docker is not installed. Downloading Docker Desktop..."
    $dockerInstaller = "$env:TEMP\Docker Desktop Installer.exe"
    Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $dockerInstaller
    Write-Log "Installing Docker Desktop quietly... This may take a few minutes."
    Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet", "--accept-license" -Wait -NoNewWindow
    Write-Log "Docker Desktop installed."
    
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("Docker Desktop has been installed. A system reboot is highly recommended to finalize WSL2 and Hyper-V configuration. Please reboot, then use the desktop shortcuts to start the Self-Healing Engine.", "Reboot Recommended", "OK", "Information")
} else {
    Write-Log "Docker is already installed."
}

# Ensure Docker is running
Write-Log "Ensuring Docker is running..."
$maxRetries = 30
$retryCount = 0
$dockerRunning = $false

# Start Docker Desktop if not running (default installation path)
if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerExe) {
        Write-Log "Launching Docker Desktop..."
        Start-Process -FilePath $dockerExe
    }
}

while (-not $dockerRunning -and $retryCount -lt $maxRetries) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Log "Docker engine is running."
    } else {
        Write-Log "Waiting for Docker engine to start (Attempt $($retryCount + 1)/$maxRetries)..."
        Start-Sleep -Seconds 5
        $retryCount++
    }
}

if (-not $dockerRunning) {
    Write-Host "Error: Docker engine failed to start within the expected time. Please start Docker Desktop manually, wait for it to initialize, and run this script again."
    Exit 1
}

# 5. Check Ports
Write-Log "Checking required ports (5000, 3000, 9090, 3100)..."
$ports = @(5000, 3000, 9090, 3100)
$conflict = $false
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        $pidOwner = $connection.OwningProcess
        $process = Get-Process -Id $pidOwner -ErrorAction SilentlyContinue
        Write-Host "Error: Port $port is in use by process ID $pidOwner ($($process.Name))."
        $conflict = $true
    }
}

if ($conflict) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("One or more required ports (5000, 3000, 9090, 3100) are currently in use. Check the installer console for details to find the PID. Please stop the conflicting services and try starting the engine again.", "Port Conflict", "OK", "Error")
    Exit 1
}

# 6. Setup Environment Variables
Write-Log "Setting up environment variables..."
Set-Location -Path $InstallDir
$envPath = Join-Path -Path $InstallDir -ChildPath ".env"
$envExamplePath = Join-Path -Path $InstallDir -ChildPath ".env.example"

if (-not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
    Copy-Item -Path $envExamplePath -Destination $envPath
    Write-Log "Copied .env.example to .env."
    
    # Generate secrets
    $random = New-Object Random
    $secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
    $jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
    $apiKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
    $adminPass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | % {[char]$_})
    $grafanaPass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | % {[char]$_})

    (Get-Content $envPath) -replace "CHANGE_ME_generate_a_64_char_random_hex_secret", $secretKey `
                           -replace "CHANGE_ME_generate_a_64_char_random_hex_for_jwt", $jwtSecret `
                           -replace "CHANGE_ME_generate_a_strong_random_api_key", $apiKey `
                           -replace "CHANGE_ME_strong_admin_password", $adminPass `
                           -replace "CHANGE_ME_strong_grafana_password", $grafanaPass | Set-Content $envPath
                           
    Write-Log "Injected secure credentials into .env."
    
    # 7. Save Credentials to Desktop
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $credFile = Join-Path -Path $desktopPath -ChildPath "SelfHealing_Credentials.txt"
    $credContent = @"
Self-Healing Monitoring System Credentials
========================================
Generated on: $(Get-Date)

Application Admin:
Username: admin
Password: $adminPass

Grafana Admin:
Username: admin
Password: $grafanaPass

Please keep this file secure! 
You will need these passwords to log into the web interfaces.
"@
    Set-Content -Path $credFile -Value $credContent
    Write-Log "Saved generated credentials to $credFile."
}

# 8. Start Docker Compose
Write-Log "Starting containers using docker-compose.prod.yml..."
docker compose -f docker-compose.prod.yml up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker compose up failed. Please check the Docker Desktop status and logs."
    Exit 1
}

# 9. Wait for Health Checks
Write-Log "Waiting for services to become healthy (this may take a minute)..."

function Wait-ForUrl {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$MaxRetries = 60
    )
    $retry = 0
    while ($retry -lt $MaxRetries) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "$ServiceName is healthy."
                return $true
            }
        } catch {
            # Suppress error output
        }
        $retry++
        Write-Log "Waiting for $ServiceName... ($retry/$MaxRetries)"
        Start-Sleep -Seconds 3
    }
    Write-Log "Timeout waiting for $ServiceName at $Url."
    return $false
}

Wait-ForUrl -Url "http://localhost:5000/health" -ServiceName "Self-Healing App"
Wait-ForUrl -Url "http://localhost:9090/-/ready" -ServiceName "Prometheus"
Wait-ForUrl -Url "http://localhost:3000/api/health" -ServiceName "Grafana"

# 10. Open Browser
Write-Log "Opening applications in default browser..."
Start-Process "http://localhost:5000"
Start-Process "http://localhost:3000"
Start-Process "http://localhost:9090"

Write-Log "Setup complete successfully!"
Start-Sleep -Seconds 3
