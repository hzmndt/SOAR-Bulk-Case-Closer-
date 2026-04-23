# SOAR Bulk Case Closer Integration

This repository contains the source code for a custom Google SecOps (Chronicle) SOAR integration that automates the process of finding and closing stale cases.

## Features
- **Job Scheduler**: Implements a Job that can be scheduled to run periodically.
- **Streaming Processing**: Fetches cases page-by-page and immediately closes them in bulk to avoid timeouts.
- **Smart Retry**: Automatically handles cases that are already closed by removing them from the batch and retrying.

## Repository Structure
- `definition.yaml`: Integration definition.
- `jobs/BulkCaseCloserJob.yaml`: Job definition and parameters.
- `jobs/BulkCaseCloserJob.py`: Python script implementing the job logic.
- `pyproject.toml`: Project configuration and dependencies.
- `resources/`: Images and assets.

## How to Use

### 1. Clone the Repository
Pull this repository to a machine with internet access.

### 2. Build the Integration
Use the `mp` (Management Plane) CLI tool from `content-hub` to build the integration into a deployable ZIP file:

```bash
uv run mp build integration Bulk-Case-Closer --dst ~/Desktop/output
```
*(Make sure you are in the `packages/mp` directory of `content-hub` or have `mp` installed as a tool).*

### 3. Deploy to SOAR
1. Go to your Chronicle SOAR instance.
2. Navigate to **Marketplace** -> **Custom Integrations**.
3. Upload the generated ZIP file.

### 4. Configure Integration
Enable the integration in the Marketplace (no parameters required here).

### 5. Schedule the Job
1. Go to **Job Scheduler**.
2. Add a new job using the **Bulk Case Closer Job**.
3. Configure the following parameters directly in the job settings:
   - **SOAR URL**: Your SOAR instance API root (e.g., `https://apj-tsc-lab1.siemplify-soar.com/`).
   - **SOAR API key**: A valid API key for authentication.
   - **Days Backwards**: Configure how many days backwards to look for open cases (default is 90).

## Prerequisites
- Python 3.11
- `mp` CLI tool from `content-hub`.
