import os
from pathlib import Path

# Path to the runtime artifacts directory
RUNTIME_ARTIFACTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime_artifacts")

# Ensure the runtime artifacts directory exists
Path(RUNTIME_ARTIFACTS_PATH).mkdir(parents=True, exist_ok=True)
