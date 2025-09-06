#!/usr/bin/env python3
"""
VaultRunner - HashiCorp Vault Docker Integration Tool

Main entry point for the VaultRunner application.
Provides seamless integration between HashiCorp Vault and Docker environments.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from vaultrunner.core.cli import main

if __name__ == "__main__":
    main()
