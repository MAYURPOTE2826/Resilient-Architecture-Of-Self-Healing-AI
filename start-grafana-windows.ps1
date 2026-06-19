$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host " Starting Fresh Grafana Setup for Windows "
Write-Host "=========================================="

$GrafanaUrl = "https://dl.grafana.com/oss/release/grafana-11.1.0.windows-amd64.zip"
$GrafanaZip = "$PSScriptRoot\grafana.zip"
$GrafanaDir = "$PSScriptRoot\grafana-bin"

# 1. Kill any running grafana
Write-Host "Stopping any running Grafana instances..."
Stop-Process -Name "grafana-server" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Delete old installation to make it "completely new"
if (Test-Path $GrafanaDir) {
    Write-Host "Removing old Grafana installation..."
    Remove-Item -Path $GrafanaDir -Recurse -Force
}

# 3. Download Grafana if we don't have it (or if it's incomplete)
if (-not (Test-Path $GrafanaZip) -or (Get-Item $GrafanaZip).Length -lt 100000000) {
    Write-Host "Downloading Grafana using curl (this should be much faster)..."
    curl.exe -L -o $GrafanaZip $GrafanaUrl
}

# 4. Extract
Write-Host "Extracting Grafana (Fast Mode)..."
mkdir $GrafanaDir -Force | Out-Null
tar.exe -xf $GrafanaZip -C $GrafanaDir

# We need to find the extracted folder (e.g. grafana-v11.1.0)
$ExtractedSubDir = Get-ChildItem -Path $GrafanaDir -Directory | Select-Object -First 1
$GrafanaBinPath = "$($ExtractedSubDir.FullName)\bin\grafana-server.exe"

# 5. Provisioning Setup
Write-Host "Setting up project dashboards and datasources..."
$ProvisioningDir = "$($ExtractedSubDir.FullName)\conf\provisioning"

# Copy datasources
Copy-Item -Path "$PSScriptRoot\grafana\provisioning\datasources\*" -Destination "$ProvisioningDir\datasources\" -Recurse -Force

# Create custom dashboard provider that points to the local Windows path
$ProviderConfig = @"
apiVersion: 1
providers:
  - name: self-healing-engine
    orgId: 1
    folder: "Self-Healing Engine"
    folderUid: self-healing
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: $PSScriptRoot\grafana
      foldersFromFilesStructure: false
"@

$ProviderConfig | Out-File -FilePath "$ProvisioningDir\dashboards\provider.yml" -Encoding UTF8

# 6. Start Grafana
Write-Host "Starting Grafana Server..."
Write-Host "The default credentials will be admin / admin"
Write-Host "=========================================="

cd $ExtractedSubDir.FullName
Start-Process -FilePath $GrafanaBinPath -WindowStyle Normal

Write-Host "Done! Grafana is starting up in a new window."
Write-Host "Open your browser to: http://localhost:3000"
