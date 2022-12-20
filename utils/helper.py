import streamlit as st
import uuid

class Canvas:
    def __init__(self):
        pass

    @staticmethod
    def draw_sidebar(visionHandler):
        # Define sidebar
        st.sidebar.image("assets/devoteam_logo.png")
        st.sidebar.title("Detection Settings")
        confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.01, 0.01)
        area_threshold = st.sidebar.checkbox(label="Apply Area Filter", value=True)
        if area_threshold:
            visionHandler.width_threshold, visionHandler.height_threshold = 0.8, 0.5
            c1, c2 = st.sidebar.columns([1, 10], gap="small")
            with st.container():
                visionHandler.width_threshold = c2.slider("Width Threshold", 0.0, 1.0, 0.8, 0.01)
                visionHandler.height_threshold = c2.slider("Height Threshold", 0.0, 1.0, 0.5, 0.01)
        with st.sidebar.expander("See explanation"):
            st.write("Confidence Threshold: The minimum confidence score for the OCR to detect the text")
            st.write("Area Filter: The OCR will only detect text within the area defined by the width and height threshold")
            st.write("Width Threshold: It's a ratio of the width of the image, measured from the center of the image")
            st.write("Height Threshold: It's a ratio of the height of the image, measured from the center of the image")
        return confidence_threshold, area_threshold

class States:
    @staticmethod
    def check_password():
        """Returns `True` if the user had the correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if st.session_state["password"] == st.secrets["password"]:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # don't store password
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show input for password.
            st.text_input(
                label="Password", type="password", on_change=password_entered, key="password"
            )
            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error.
            st.text_input(
                label="Password", type="password", on_change=password_entered, key="password"
            )
            st.error("😕 Password incorrect, try again")
            return False
        else:
            # Password correct.
            return True

    @staticmethod
    def reset_state():
        st.session_state['uploaded'] = False
        st.session_state['job_id'] = str(uuid.uuid4())

    @staticmethod
    def init_state():
        if 'uploaded' not in st.session_state:
            st.session_state['uploaded'] = False
        if 'job_id' not in st.session_state:
            st.session_state['job_id'] = str(uuid.uuid4())