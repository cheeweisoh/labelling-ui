import streamlit as st


def next_image(image_files):
    if st.session_state.image_index < len(image_files) - 1:
        st.session_state.image_index += 1


def prev_image():
    if st.session_state.image_index > 0:
        st.session_state.image_index -= 1
