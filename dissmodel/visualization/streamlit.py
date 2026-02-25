




def display_inputs(obj, st):
    annotations = getattr(obj, '__annotations__', {})

    for name, type_ in annotations.items():
        value = getattr(obj, name, None)

        if isinstance(value, int):
            new_value = st.slider(name, 0, 1000, value)
        elif isinstance(value, float):
            new_value = st.slider(name, 0.0, 1.0, value, step=0.01)
        elif isinstance(value, bool):
            new_value = st.checkbox(name, value=value)
        else:
            new_value = st.text_input(name, str(value))

        setattr(obj, name, new_value)



        






