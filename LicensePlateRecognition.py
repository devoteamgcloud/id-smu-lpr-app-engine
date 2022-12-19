import threading, base64
import streamlit as st
from utils.storage import StorageHandler
from utils.ocr import OCRHandler, FeatureType
from config import config as cfg
import cv2
import numpy as np
import pandas as pd

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

storageHandler = StorageHandler(cfg.PROJECT_ID, cfg.BUCKET_NAME, cfg.FOLDER_PATH_IN_BUCKET)
ocrHandler = OCRHandler()

def upload_async(file_path):
    storageHandler.upload_base64_image(file_path)

def calculate_center_of_image(image, width_ratio=0.8, height_ratio=0.5):
    height, width, _ = image.shape
    center_x = width // 2
    center_y = height // 2
    width = int(width * width_ratio)
    height = int(height * height_ratio)
    xmin = center_x - width // 2
    xmax = center_x + width // 2
    ymin = center_y - height // 2
    ymax = center_y + height // 2
    return xmin, xmax, ymin, ymax

def isBoundWithinArea(bound, image, width_threshold=0.8, height_threshold=0.5):
    xmin, xmax, ymin, ymax = calculate_center_of_image(image, width_threshold, height_threshold)
    # Check if the bound is within the area
    vertices = bound.vertices
    vertices = [(vertex.x, vertex.y) for vertex in vertices]
    for vertex in vertices:
        if vertex[0] < xmin or vertex[0] > xmax or vertex[1] < ymin or vertex[1] > ymax:
            break
    else:
        return True
    return False

# Cache the function to avoid re-running the OCR
@st.cache(allow_output_mutation=True)
def detect_text_in_image(base64_image):
    # Run the OCR to get data
    bounds, labels, confidences = ocrHandler.doc_text_detection(
        base64_image=base64_image, feature=FeatureType.WORD)
    return bounds, labels, confidences
    

@st.cache(allow_output_mutation=True)
def filter_bounds(bounds, labels, confidences, threshold, isAreaFilter, image, width_threshold, height_threshold):
    # Filter the bounds based on the confidence threshold
    filtered_bounds = []
    filtered_labels = []
    filtered_confidences = []
    for bound, label, confidence in zip(bounds, labels, confidences):
        if confidence >= threshold:
            if isAreaFilter:
                if isBoundWithinArea(bound, image, width_threshold, height_threshold):
                    filtered_bounds.append(bound)
                    filtered_labels.append(label)
                    filtered_confidences.append(confidence)
            else:
                filtered_bounds.append(bound)
                filtered_labels.append(label)
                filtered_confidences.append(confidence)
    return filtered_bounds, filtered_labels, filtered_confidences


if check_password():
    st.title("License Plate Recognition")

    # Add text to the page
    st.markdown("A Prototype for License Plate Recognition using Google Cloud Vision API")

    # Add a file uploader widget to allow images
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

    # Define sidebar
    st.sidebar.image("assets/devoteam_logo.png")
    st.sidebar.title("Detection Settings")
    confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.01, 0.01)
    area_threshold = st.sidebar.checkbox(label="Apply Area Filter", value=True)
    width_threshold, height_threshold = 1.0, 1.0
    if area_threshold:
        width_threshold, height_threshold = 0.8, 0.5
        c1, c2 = st.sidebar.columns([1, 10], gap="small")
        with st.container():
            width_threshold = c2.slider("Width Threshold", 0.0, 1.0, 0.8, 0.01)
            height_threshold = c2.slider("Height Threshold", 0.0, 1.0, 0.5, 0.01)
    with st.sidebar.expander("See explanation"):
        st.write("Confidence Threshold: The minimum confidence score for the OCR to detect the text")
        st.write("Area Filter: The OCR will only detect text within the area defined by the width and height threshold")
        st.write("Width Threshold: It's a ratio of the width of the image, measured from the center of the image")
        st.write("Height Threshold: It's a ratio of the height of the image, measured from the center of the image")


    # Make the button to run the OCR only visible when the file is uploaded
    if uploaded_file is not None:
        # Draw a divider
        st.markdown("---")

        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        # Encode the bytes to base64 string
        base64_bytes = base64.b64encode(bytes_data)

        # Run the OCR to get data
        # bounds, labels, confidences = ocrHandler.doc_text_detection(
        #     base64_image=base64_bytes, feature=FeatureType.WORD)
        bounds, labels, confidences = detect_text_in_image(base64_bytes)

        # Save the file to GCP cloud storage in a separate thread
        thread = threading.Thread(target=upload_async, args=(base64_bytes,))
        thread.start()
        
        # Draw bounds as polygons using OpenCV
        # bounds data is in the form of BoundingPoly
        # BoundingPoly is a list of vertices
        # Each vertex is a dict with x and y keys
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        # Filter the bounds based
        bounds, labels, confidences = filter_bounds(
            bounds=bounds, labels=labels, confidences=confidences, 
            threshold=confidence_threshold, 
            width_threshold=width_threshold, height_threshold=height_threshold,
            isAreaFilter=True, image=img)
        for bound in bounds:
            # Get the vertices
            vertices = bound.vertices
            # Convert the vertices to a list of tuples
            vertices = [(vertex.x, vertex.y) for vertex in vertices]
            # Draw the polygon
            cv2.polylines(img, [np.array(vertices)], True, (0, 255, 0), 2)

        # DEBUG: Draw the rectangle around the center of the image
        xmin, xmax, ymin, ymax = calculate_center_of_image(img, width_threshold, height_threshold)
        # Create a black image with the same size as the original image
        mask = np.zeros(img.shape, dtype=np.uint8)
        # Draw a white rectangle on the mask image
        cv2.rectangle(mask, (xmin, ymin), (xmax, ymax), (255, 255, 255), -1)
        # Invert the mask image
        mask = cv2.bitwise_not(mask)
        # Blend the original image and the mask using the addWeighted function
        blended = cv2.addWeighted(img, 1.0, mask, 0.4, 0)
        img = blended

        # Convert the image to bytes
        _, buffer = cv2.imencode('.jpg', img)
        bytes_data = buffer.tobytes()

        # Display the image
        st.image(bytes_data, use_column_width=True)

        # Format labels and confidences into a dataframe
        df = pd.DataFrame(confidences, index=labels, columns=["Confidence"])

        # Draw a column
        c1, c2 = st.columns([4, 3], gap="small")
        with st.container():
            c1.markdown("### Detected Labels & Confidences:")
            c2.table(df)
