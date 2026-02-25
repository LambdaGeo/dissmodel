from __future__ import annotations

from typing import Any


def display_inputs(obj: Any, st: Any) -> None:
    """
    Render Streamlit input widgets for every annotated attribute on ``obj``.

    The widget type is inferred from the current attribute value:

    - ``int``   → ``st.slider`` (0 – 1000)
    - ``float`` → ``st.slider`` (0.0 – 1.0, step 0.01)
    - ``bool``  → ``st.checkbox``
    - anything else → ``st.text_input``

    The attribute is updated in-place on ``obj`` after each interaction.

    Args:
        obj: Any object with ``__annotations__`` and matching instance
             attributes (e.g. a :class:`~dissmodel.core.Model` subclass).
        st:  The Streamlit module (``import streamlit as st``). Passed as
             an argument to avoid a hard dependency on Streamlit at import
             time.
    """
    annotations: dict[str, Any] = getattr(obj, "__annotations__", {})

    for name in annotations:
        value: Any = getattr(obj, name, None)

        if isinstance(value, bool):
            # bool must come before int — bool is a subclass of int in Python
            new_value = st.checkbox(name, value=value)
        elif isinstance(value, int):
            new_value = st.slider(name, 0, 1000, value)
        elif isinstance(value, float):
            new_value = st.slider(name, 0.0, 1.0, value, step=0.01)
        else:
            new_value = st.text_input(name, str(value))

        setattr(obj, name, new_value)
