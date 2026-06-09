<div align="center">
  <a href="https://github.com/hitloop-ai/aiprof-frappe-crm">
    <img src=".github/logo.svg" height="80" alt="Frappe CRM Logo">
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

## Installation & Setup

This repository is pre-configured to run inside a Docker environment with automated scripting for local development orchestration.

### Prerequisites
Make sure you have the following installed on your host system:
* **Docker** and **Docker Compose**
* **Node.js** (v18+) and **npm** or **yarn** (for running the frontend dev server on the host)
* **tmux** (required by the automated orchestration script)

---

### Step-by-Step Launch

#### Step 1: Start Backend Services
Run Docker Compose from the root directory to spin up MariaDB, Redis, and the Frappe bench container:
```bash
docker compose up -d
```
> [!NOTE]
> On the first run, the initialization script ([docker/init.sh](file:///home/satheesh/aiprof_crm/docker/init.sh)) will automatically initialize the Frappe bench, symlink the CRM application, and create the development site `crm.localhost`.

* **Backend URL**: `http://localhost:8005` (routes internally to `crm.localhost`)
* **Default Credentials**:
  * **Username**: `Administrator`
  * **Password**: `admin`

#### Step 2: Install Frontend Dependencies
Navigate to the `frontend/` directory and install the packages:
```bash
cd frontend
npm install # or yarn install
```

#### Step 3: Run the Development Environment
Start the unified frontend and tunnel environment from the root directory:
```bash
./start-crm.sh
```
This script automates the full environment setup:
1. Launches the Vite development server on port `8085`.
2. Spins up public tunnels using **localtunnel** and **localhost.run** to expose port `8085`.
3. Updates the container's `site_config.json` with the active public URL.
4. Auto-registers the webhook URL in **CRM Vobiz Settings** so Vobiz voice events route directly back to your local container.
5. Launches a **tmux** session named `crm` containing three windows:
   * **Window 0 (`dev`)**: Vite dev server (`http://localhost:8085`)
   * **Window 1 (`localtunnel`)**: Localtunnel client
   * **Window 2 (`localhost_run`)**: Localhost.run SSH tunnel client

##### tmux Commands:
* `Ctrl+B 0` &rarr; Switch to the dev server console.
* `Ctrl+B 1` &rarr; Switch to the localtunnel client logs.
* `Ctrl+B 2` &rarr; Switch to the localhost.run client logs.
* `Ctrl+B d` &rarr; Detach from the session (keeps everything running in the background).

#### Step 4: Register Telephony Webhook 
If you want to manually update or register your webhook URL with Vobiz (for example, when using a specific localtunnel URL):
```bash
./show-tunnel.sh https://new-tunnel-url.loca.lt
```
This updates the webhook URL in **CRM Vobiz Settings** and registers it with the Vobiz telephony API.

---
