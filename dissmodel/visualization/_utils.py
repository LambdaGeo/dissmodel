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
    """
    Checks if the current matplotlib backend supports interactive windows.
    Converts to lowercase to support Matplotlib 3.x backend name changes.
    """
    backend = matplotlib.get_backend().lower()
    
    interactive_backends = {
        'qt5agg', 'qtagg', 'qt4agg', 'tkagg','agg',
        'macosx', 'gtk3agg', 'gtk4agg', 'wxagg'
    }
    
    return backend in interactive_backends
