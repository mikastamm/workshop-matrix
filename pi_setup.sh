#!/usr/bin/env bash
# setup_matrix.sh
#
# Creates a venv (if missing), installs requirements, creates/enables/starts a
# systemd service called "matrix", and then follows the service logs.

set -euo pipefail

SERVICE_NAME="matrix"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="${PROJECT_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== Matrix service setup ==="
echo "Project dir : ${PROJECT_DIR}"
echo "Venv dir    : ${VENV_DIR}"
echo "Service file: ${SERVICE_FILE}"
echo

#
# 1) Create / update virtual environment
#
if [[ -d "${VENV_DIR}" ]]; then
  echo "Virtual‑environment already exists – skipping creation."
else
  echo "Creating virtual‑environment..."
  python3 -m venv "${VENV_DIR}"
fi

echo "Installing Python dependencies into venv..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/requirements-pi.txt"

#
# 2) Create systemd service (only if it does not already exist)
#
if [[ -f "${SERVICE_FILE}" ]]; then
  echo "Systemd unit already present – skipping creation."
else
  echo "Creating systemd unit ${SERVICE_NAME}.service (requires sudo)…"
  sudo tee "${SERVICE_FILE}" >/dev/null <<EOF
[Unit]
Description=Matrix Workshop Display
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/python ${PROJECT_DIR}/run.py
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

  echo "Reloading systemd daemon and enabling service on boot..."
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}"
fi

#
# 3) Start (or restart) the service
#
echo "Starting ${SERVICE_NAME} service..."
sudo systemctl start "${SERVICE_NAME}"

#
# 4) Follow the logs
#
echo
echo "=== Now following logs (Ctrl+C to exit) ==="
sudo journalctl -u "${SERVICE_NAME}" -f
