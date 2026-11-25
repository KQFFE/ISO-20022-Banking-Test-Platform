"""Configuration and environment setup.

This module must be imported first, before any other app imports,
to ensure .env variables are loaded into the environment.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Verify key is loaded
api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not api_key:
    raise RuntimeError(
        f"ANTHROPIC_API_KEY not found. "
        f"Make sure backend/.env exists and contains: ANTHROPIC_API_KEY='sk-ant-...'"
    )
