import sys
from pathlib import Path

# Add project root to sys.path for test runners
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
