# Self-Healing Monitoring System - Installer Guide

This guide covers how to build the Windows Installer (`.exe`) and how an end-user installs the software.

---

## 🛠️ 1. Building the Installer (For Developers)

The installer is built using [Inno Setup](https://jrsoftware.org/isinfo.php). It packages the entire Python/Docker stack, sets up Start Menu shortcuts, and bootstraps necessary dependencies via PowerShell.

### Prerequisites to Build
1. Download and install **Inno Setup Compiler** from [jrsoftware.org](https://jrsoftware.org/isinfo.php).
2. Ensure your project repository is clean and ready. 

### How to Compile
1. Navigate to the `installer` folder in your project root.
2. Double-click the `installer.iss` file to open it in Inno Setup Studio.
3. Click the **"Compile"** button (or press `Ctrl+F9`).
4. Wait for the compiler to package your files.
5. Once complete, you will find `SelfHealingEngine_Setup.exe` in the `installer/Output` folder.

You can now distribute this `.exe` file to your end users!

---

## 🚀 2. Installing the Software (For End Users)

The installer is designed to be "zero-configuration". It will automatically check your system, install prerequisites, and configure the Self-Healing Engine.

### System Requirements
* **OS:** Windows 10 or Windows 11 (64-bit)
* **Disk Space:** At least 5GB free on the `C:\` drive
* **Virtualization:** Hardware Virtualization must be enabled in your BIOS/UEFI.

### Installation Steps
1. Double-click `SelfHealingEngine_Setup.exe`.
2. Accept the administrator prompt.
3. Follow the wizard to choose an installation directory.
4. The installer will extract the files and automatically launch a setup console. **Do not close this console window.**
5. **Prerequisites Check:**
   - If **WSL** (Windows Subsystem for Linux) is missing, it will install it.
   - If **Docker Desktop** is missing, it will download and install it silently.
6. **Important Note on Reboots:**
   - If Docker Desktop was installed for the first time, you will receive a prompt recommending a system reboot. 
   - **You must reboot** for WSL2 and Hyper-V to finalize. After rebooting, allow Docker Desktop a moment to start, then use the desktop shortcuts to access the application.
7. Once the containers are running and healthy, your default web browser will automatically open the applications.

---

## 🔑 3. Accessing the System

During installation, secure random passwords are automatically generated for your local deployment. 

A file named **`SelfHealing_Credentials.txt`** will be placed on your **Desktop**. It contains the credentials for both the Application and Grafana.

### Default URLs
You can use the desktop shortcuts or navigate directly in your browser:
* **Self-Healing Application:** [http://localhost:5000](http://localhost:5000)
* **Grafana Dashboards:** [http://localhost:3000](http://localhost:3000)
* **Prometheus Metrics:** [http://localhost:9090](http://localhost:9090)

---

## 🛑 4. Uninstalling

To cleanly remove the software and stop the background containers:
1. Open the Start Menu and search for **"Uninstall Self-Healing Engine"**.
2. Run the uninstaller.
3. The uninstaller will safely stop and remove the Docker containers.
4. You will be prompted asking if you want to keep or delete the persistent application data (database, logs, and metrics).

---

## ❓ Troubleshooting

**Q: The installer says a port (5000, 3000, or 9090) is in use.**
A: Another application is using the network port required by the engine. Check the installer console output—it will give you the Process ID (PID). Open Task Manager, go to the Details tab, find that PID, and end the task.

**Q: Docker fails to start.**
A: Ensure you have rebooted your computer after the initial installation. Also, check that Hardware Virtualization is enabled in your computer's BIOS/UEFI settings.

**Q: The web page doesn't load immediately.**
A: Give it a moment! Docker might take 30-60 seconds to pull the latest images and start the services completely. Check the Docker Desktop dashboard to see the container status.
