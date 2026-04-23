# SOAR Bulk Case Closer Integration

This repository contains the source code for a custom Google SecOps (Chronicle) SOAR integration that automates the process of finding and closing stale cases.

## Features
- **Job Scheduler**: Implements a Job that can be scheduled to run periodically.
- **Streaming Processing**: Fetches cases page-by-page and immediately closes them in bulk to avoid timeouts.
- **Smart Retry**: Automatically handles cases that are already closed by removing them from the batch and retrying.
- **No External Dependencies**: Native implementation using SiemplifyJob SDK without requiring `TIPCommon`.

## Repository Structure
- `definition.yaml`: Integration definition.
- `jobs/BulkCaseCloserJob.yaml`: Job definition and parameters.
- `jobs/BulkCaseCloserJob.py`: Python script implementing the job logic.
- `pyproject.toml`: Project configuration and dependencies.
- `resources/`: Images and assets.

## How to Install `mp` Tool

The `mp` (Marketplace CLI) tool is required to build and deploy this integration. You can install it using `uv`:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install mp tool from the official repository
uv tool install mp --from git+https://github.com/chronicle/content-hub.git#subdirectory=packages/mp
```

## How to Build

1.  **Clone this repository** to a machine with internet access.
2.  **Configure the root path** for `mp` if you are running it outside `content-hub`:
    ```bash
    mp config --root-path /path/to/your/workspace
    ```
3.  **Build the integration**:
    ```bash
    mp build integration Bulk-Case-Closer --dst ~/Desktop/output
    ```
    *(This will create a deployable ZIP file in the destination folder).*

## How to Use / Job Configuration

1.  **Deploy to SOAR**: Upload the generated ZIP file to your Chronicle SOAR instance via **Marketplace** -> **Custom Integrations**.
2.  **Enable Integration**: Enable it in the Marketplace (no parameters required).
3.  **Schedule the Job**: Go to **Job Scheduler** and add a new job using the **Bulk Case Closer Job**.
4.  **Configure Parameters**: Provide the following parameters in the job settings:
    - **SOAR URL**: Your SOAR instance API root (e.g., `https://apj-tsc-lab1.siemplify-soar.com/`).
    - **SOAR API key**: A valid API key for authentication.
    - **Days Backwards**: Configure how many days backwards to look for open cases (default is 90).

## Prerequisites
- Python 3.11
- `uv` and `mp` tools.
