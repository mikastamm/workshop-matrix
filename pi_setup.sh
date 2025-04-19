#!/usr/bin/env bash
# setup_matrix.sh
#
# 1. (once)  Ensure git, python3‑dev, python3‑pillow are installed
#             and build+install hzeller/rpi‑rgb‑led‑matrix
# 2.         Create/upgrade venv + requirements‑pi.txt
# 3.         Create/enable/start systemd unit "matrix"
# 4.         Follow the service log

set -euo pipefail

SERVICE_NAME="matrix"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="${PROJECT_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LED_REPO_DIR="${HOME}/rpi-rgb-led-matrix"

echo "=== Matrix service setup ==="
echo "Project dir : ${PROJECT_DIR}"
echo "Venv dir    : ${VENV_DIR}"
echo "Service file: ${SERVICE_FILE}"
echo

###############################################################################
# Step 0 – one‑time APT install + rpi‑rgb‑led‑matrix library
###############################################################################
# Check if system packages are present
declare -a DEPS=(git python3-dev python3-pillow)
MISSING=()
for pkg in "${DEPS[@]}"; do
  dpkg -s "${pkg}" &>/dev/null || MISSING+=("${pkg}")
done

if (( ${#MISSING[@]} )); then
  echo "Installing missing system packages: ${MISSING[*]}"
  sudo apt-get update
  sudo apt-get install -y "${MISSING[@]}"
else
  echo "Required system packages already installed – skipping APT step."
fi

# Check if the rgbmatrix Python module is already importable
if python3 - <<'PY' &>/dev/null; then
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec('rgbmatrix') else 1)
PY
then
  echo "rgbmatrix Python module detected – skipping library build."
else
  echo "Building & installing hzeller/rpi-rgb-led-matrix (this can take a while)…"
  # Clone if the directory doesn't exist
  if [[ ! -d "${LED_REPO_DIR}" ]]; then
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git "${LED_REPO_DIR}"
  fi
  pushd "${LED_REPO_DIR}" >/dev/null
    make build-python PYTHON="$(which python3)"
    sudo make install-python PYTHON="$(which python3)"
  popd >/dev/null
fi

###############################################################################
# Step 1 – project update & virtual environment
###############################################################################
echo
git -C "${PROJECT_DIR}" pull || true   # ignore if not a git repo

if [[ -d "${VENV_DIR}" ]]; then
  echo "Virtual‑environment already exists – skipping creation."
else
  echo "Creating virtual‑environment..."
  python3 -m venv "${VENV_DIR}"
fi

echo "Installing Python dependencies into venv…"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/requirements-pi.txt"

###############################################################################
# Step 2 – systemd service
###############################################################################
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

  echo "Reloading systemd daemon and enabling service on boot…"
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}"
fi

###############################################################################
# Step 3 – start / restart the service
###############################################################################
echo "Starting ${SERVICE_NAME} service…"
sudo systemctl restart "${SERVICE_NAME}" || sudo systemctl start "${SERVICE_NAME}"

###############################################################################
# Step 4 – follow the logs
###############################################################################
echo
echo "=== Now following logs (Ctrl+C to exit) ==="
sudo journalctl -u "${SERVICE_NAME}" -f
