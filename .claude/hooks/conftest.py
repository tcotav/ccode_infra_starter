"""Shared pytest fixtures for hook tests."""

import os
import pytest


@pytest.fixture(autouse=True)
def _suppress_container_warning():
    """Set IN_DEVCONTAINER so container warnings don't interfere with assertions."""
    old = os.environ.get("IN_DEVCONTAINER")
    os.environ["IN_DEVCONTAINER"] = "true"
    yield
    if old is None:
        del os.environ["IN_DEVCONTAINER"]
    else:
        os.environ["IN_DEVCONTAINER"] = old
