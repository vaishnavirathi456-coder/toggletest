import sys
import os

# Make sure toggletest is importable from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest_plugins = ["toggletest.pytest_plugin"]