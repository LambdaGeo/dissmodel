from __future__ import annotations

import matplotlib


def is_notebook() -> bool:
    """Return True if the code is running inside a Jupyter notebook."""
    try:
        from IPython import get_ipython
        return get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


def is_interactive_backend() -> bool:
    """Return True if the current matplotlib backend supports interactive display."""
    return matplotlib.get_backend().lower() not in {"agg", "pdf", "ps", "svg", "cairo"}