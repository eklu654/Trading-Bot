#!/usr/bin/env python3
"""Shared 0DTESPX authentication helpers.

Credentials are read from environment variables when available. Interactive
prompts remain available for local use, but CI never needs to prompt.

Environment variables:
  ODTESPX_EMAIL
  ODTESPX_PASSWORD
"""

from __future__ import annotations

import getpass
import os

def get_credentials() -> tuple[str, str]:
    email = os.environ.get("ODTESPX_EMAIL", "").strip()
    password = os.environ.get("ODTESPX_PASSWORD", "")

    if not email:
        email = input("0DTESPX email: ").strip()
    if not password:
        password = getpass.getpass("0DTESPX password (hidden): ")

    if not email or not password:
        raise RuntimeError(
            "0DTESPX credentials are required. Set ODTESPX_EMAIL and "
            "ODTESPX_PASSWORD or provide them at the local prompts."
        )

    return email, password
