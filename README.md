
  <a href="https://github.com/hitloop-ai/aiprof-frappe-crm">
    <img src=".github/logo.png" height="80" alt="Frappe CRM Logo">
  </a>
  <h1>Frappe CRM (Customized)</h1>
  <p><strong>A tailored sales, communication, and event management platform built on Vue 3 and Frappe.</strong></p>
</div>

---

## What It Is & Key Uses

This customized Frappe CRM application supercharges standard sales operations by adding rich communication channels and scheduling capabilities. 

### 1. Unified Lead & Deal Management
* **All-in-One Lead Page**: Track comments, notes, tasks, and history dynamically on a single, responsive layout.
* **Kanban & Custom Views**: Organise leads and deals visually using drag-and-drop Kanban boards or create personalized list views with custom columns, quick sorting, and filters.

### 2. Vobiz Telephony Integration
* **In-App Calling**: Make and receive calls directly from the CRM with active call timers and call log records.
* **Real-time Sync & Automation**: Automatic update of Lead fields upon call creation/update, real-time call log sync via webhook events, and timezone-localized call histories.
* **Integrated Call UI**: Call handling panels built natively into the frontend.

### 3. Calendar & Event Management
* **Event Scheduling**: Plan meetings and invite attendees/users directly from the CRM.
* **Real-time Notifications**: Receive system notifications for scheduled meetings and upcoming events.

### 4. Real-time Frontend Updates
* **Socket Integration**: Real-time interface updates for lead details and call statuses without manual page reloads.

---

## Installation & Setup (Windows / Linux)

> [!IMPORTANT]
> **Linux (specifically Ubuntu)** is the highly recommended and supported environment for running this application on Windows. The orchestration scripts and backend containers run within WSL, bridging seamlessly to the Windows host.

This repository is optimized for development on Windows systems using **Linux** with either **Docker Desktop** or **native Docker Engine** installed inside WSL. Follow these steps to start your environment:

### Prerequisites
1. **Docker**:
   * **Option A (Recommended)**: Docker Desktop running on Windows with Linux integration enabled.
   * **Option B (Native)**: Native Docker Engine installed inside Linux. Ensure the Docker daemon is started:
     ```bash
     sudo service docker start
     ```
2. **MongoDB**: Ensure MongoDB is running on your Windows host (default port `27017`).
3. **Linux Terminal**: Open your WSL terminal (e.g., Ubuntu) to run all backend and orchestration commands.
4. **Node.js**: Install Node.js (v18+) inside WSL for frontend development.

---

### Step-by-Step Launch

You can run the setup commands either directly from your **Linux Terminal** or from **Windows PowerShell** (using the `wsl` prefix).

#### Step 1: Clone the Repository & Navigate
Clone the repository using Git and navigate into the project directory:
* **Linux Terminal / PowerShell**:
  ```bash
  git clone https://github.com/hitloop-ai/aiprof-frappe-crm.git
  cd aiprof-frappe-crm
  ```

#### Step 2: Start Docker Containers
Ensure your Docker service/daemon is running, then spin up the backend containers:
* **Linux Terminal**:
  ```bash
  docker compose -f docker/docker-compose.yml up -d
  ```
* **Windows PowerShell**:
  ```powershell
  wsl docker compose -f docker/docker-compose.yml up -d
  ```
> [!NOTE]
> On the first run, the containers will take a few minutes to download images and initialize. The site will be created automatically inside the container as `crm.localhost`.

#### Step 3: Install Frontend Dependencies (First time only)
* **Linux Terminal**:
  ```bash
  cd frontend && npm install && cd ..
  ```
* **Windows PowerShell**:
  ```powershell
  wsl -e bash -c "cd frontend && npm install"
  ```

#### Step 4: Run the Development Environment

You can start the environment using either the automated script (highly recommended) or run it manually.

##### Option A: Automated Script (Recommended)
* **Linux 2 Terminal**:
  ```bash
  ./start-crm.sh
  ```
* **Windows PowerShell**:
  ```powershell
  wsl ./start-crm.sh
  ```

##### Option B: Manual Execution (Alternative)
If you prefer running the dev server directly in your current terminal window instead of a background tmux session:
* **Linux 2 Terminal**:
  ```bash
  cd frontend && npm run dev -- --host
  ```
* **Windows PowerShell**:
  ```powershell
  wsl -e bash -c "cd frontend && npm run dev -- --host"
  ```
*(Note: If you run manually, you will also need to start the Windows MongoDB proxy and register the tunnel webhook URL manually if you need telephony integration.)*

This script automatically handles:
1. **Linux-Windows Networking**: Resolves your Windows host IP address and writes it to `scratch/wsl_ip.txt`.
2. **MongoDB Proxy**: Launches the background Python proxy on your Windows host on port `27018` to bridge the WSL Docker container to your host's local MongoDB (port `27017`), allowing call logs to sync.
3. **Vite Frontend**: Starts the Vite dev server inside WSL.
4. **Tunnels & Webhooks**: Starts a public tunnel (`localhost.run`) and registers the dynamic tunnel endpoint directly with Vobiz so outgoing/incoming calls work.
5. **tmux Session**: Orchestrates these services inside a tmux session named `crm`.

##### tmux Controls:
* `Ctrl+B 0` &rarr; View the Vite dev server logs.
* `Ctrl+B 1` &rarr; View the localtunnel logs (backup tunnel).
* `Ctrl+B 2` &rarr; View the localhost.run tunnel logs (active tunnel).
* `Ctrl+B d` &rarr; Detach from tmux (everything keeps running in the background!).

To check the active tunnel URL later or re-register it:
* **Linux Terminal**:
  ```bash
  ./show-tunnel.sh
  ```
* **Windows PowerShell**:
  ```powershell
  wsl ./show-tunnel.sh
  ```

#### Step 5: Open in Browser
Open your Windows browser and navigate to:
```
http://localhost:8085
```
> [!TIP]
> If `localhost` fails to connect from Windows (which can happen with native WSL Docker networking), use your WSL IP instead:
> * **Linux Terminal**:
>   ```bash
>   hostname -I | awk '{print $1}'
>   ```
> * **Windows PowerShell**:
>   ```powershell
>   wsl hostname -I
>   ```
> Then open `http://<WSL_IP>:8085` in your Windows browser.

---

### Stopping the Environment

To stop all background processes (tunnels, dev server, proxy) and kill the tmux session:
* **WSL 2 Terminal**:
  ```bash
  tmux kill-session -t crm
  ```
* **Windows PowerShell**:
  ```powershell
  wsl tmux kill-session -t crm
  ```

To stop the Docker containers:
* **Linux Terminal**:
  ```bash
  docker compose -f docker/docker-compose.yml down
  ```
* **Windows PowerShell**:
  ```powershell
  wsl docker compose -f docker/docker-compose.yml down
  ```

---
