; Inno Setup Script for Self-Healing Engine
; This script packages the Python/Docker project into a Windows installer.

[Setup]
AppName=Self-Healing Engine
AppVersion=1.0.0
AppPublisher=Your Company Name
AppPublisherURL=https://yourdomain.com
DefaultDirName={autopf}\Self-Healing Engine
DefaultGroupName=Self-Healing Engine
OutputDir=Output
OutputBaseFilename=SelfHealingEngine_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\unins000.exe
SetupIconFile=compiler:SetupClassicIcon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The installer/ directory itself with PowerShell scripts
Source: "setup.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "uninstall.ps1"; DestDir: "{app}"; Flags: ignoreversion

; Copy project root files
Source: "..\docker-compose.prod.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Dockerfile.prod"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\prometheus.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\gunicorn.conf.py"; DestDir: "{app}"; Flags: ignoreversion

; Copy Folders
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\monitoring\*"; DestDir: "{app}\monitoring"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\grafana\*"; DestDir: "{app}\grafana"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcuts (essentially opening URLs)
Name: "{group}\Open Application"; Filename: "http://localhost:5000"
Name: "{group}\Open Grafana"; Filename: "http://localhost:3000"
Name: "{group}\Open Prometheus"; Filename: "http://localhost:9090"
Name: "{group}\Uninstall Self-Healing Engine"; Filename: "{uninstallexe}"

; Desktop shortcuts
Name: "{autodesktop}\Self-Healing Engine"; Filename: "http://localhost:5000"
Name: "{autodesktop}\Grafana (Monitoring)"; Filename: "http://localhost:3000"

[Run]
; Run the setup.ps1 after extraction completes to handle Docker/WSL, setup env, and start containers.
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Normal -File ""{app}\setup.ps1"""; Description: "Initializing and starting the Self-Healing Engine (This may take a few minutes)"; Flags: waituntilterminated postinstall

[UninstallRun]
; Run the uninstall script BEFORE removing files, to bring down Docker containers
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -File ""{app}\uninstall.ps1"""; Flags: waituntilterminated runascurrentuser

[Code]
// Custom Pascal Scripting can be added here if you want pre-install checks before extraction.
// Right now, the PowerShell script handles WSL, Docker, and ports for robustness.
