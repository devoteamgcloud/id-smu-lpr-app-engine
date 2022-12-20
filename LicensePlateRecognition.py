import threading, base64
import streamlit as st
from utils.storage import StorageHandler
from utils.vision import VisionHandler, FeatureType
from utils.helper import Canvas, States
from config import config as cfg
import cv2, uuid
import numpy as np
import pandas as pd

storageHandler = StorageHandler(cfg.PROJECT_ID, cfg.BUCKET_NAME, cfg.FOLDER_PATH_IN_BUCKET)
visionHandler = VisionHandler()

def upload_async(file_path, job_id):
    print("Uploading file to GCP cloud storage with job_id: ", job_id)
    # storageHandler.upload_base64_image(file_path, st.session_state['job_id'])

# Cache the function to avoid re-running the OCR
@st.cache(allow_output_mutation=True)
def detect_text_in_image(base64_image):
    # Run the OCR to get data
    bounds, labels, confidences = visionHandler.doc_text_detection(
        base64_image=base64_image, feature=FeatureType.WORD)
    return bounds, labels, confidences

if States.check_password():
    # Set the page title
    st.title("License Plate Recognition")

    # Add text to the page
    st.markdown("A Prototype for License Plate Recognition using Google Cloud Vision API")

    # Initialize the session state
    States.init_state()

    # Add a file uploader widget to allow images
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], on_change=States.reset_state)

    confidence_threshold, area_threshold = Canvas.draw_sidebar(visionHandler)
    if not area_threshold:
        visionHandler.width_threshold = 1.0
        visionHandler.height_threshold = 1.0

    if uploaded_file is not None:
        # Draw a divider
        st.markdown("---")

        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        # Encode the bytes to base64 string
        base64_bytes = base64.b64encode(bytes_data)

        # Run the OCR to get data
        bounds, labels, confidences = detect_text_in_image(base64_bytes)

        # Check if the file has been uploaded
        if st.session_state['uploaded'] == False:
            # Save the file to GCP cloud storage in a separate thread
            thread = threading.Thread(target=upload_async, args=(base64_bytes, st.session_state['job_id']))
            thread.start()
            st.session_state['uploaded'] = True
        
        # Decode the bytes to an image
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        visionHandler.image = img

        # Filter the bounds based
        filtered_bounds, filtered_labels, filtered_confidences = visionHandler.filter_bounds(
            bounds=bounds, labels=labels, confidences=confidences, confidence_threshold=confidence_threshold)
        
        visionHandler.draw_bounds(bounds=filtered_bounds)
        visionHandler.draw_aoi()

        # Convert the image to bytes
        _, buffer = cv2.imencode('.jpg', visionHandler.image)
        bytes_data = buffer.tobytes()

        # Display the image
        st.image(bytes_data, use_column_width=True)

        # Display the data in a dataframe
        data = {
            "Word": filtered_labels,
            "Confidence": filtered_confidences
        }
        df = pd.DataFrame(data)

        # CSS to inject contained in a string
        hide_table_row_index = """
                    <style>
                    thead tr th:first-child {display:none}
                    tbody th {display:none}
                    </style>
                    """

        # Inject CSS with Markdown
        st.markdown(hide_table_row_index, unsafe_allow_html=True)

        # Draw a column
        c1, c2 = st.columns([4, 3], gap="small")
        with st.container():
            c1.markdown("### Detected Labels & Confidences:")
            c2.table(df)
