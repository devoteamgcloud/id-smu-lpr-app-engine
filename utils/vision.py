import base64
from enum import Enum
from google.cloud import vision
import cv2
import numpy as np
import streamlit as st

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

class VisionHandler:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
        self._image = None
        self._width_threshold = 1.0
        self._height_threshold = 1.0
    
    @property
    def image(self):
        return self._image

    @property
    def width_threshold(self):
        return self._width_threshold

    @property
    def height_threshold(self):
        return self._height_threshold

    @width_threshold.setter
    def width_threshold(self, width_threshold):
        self._width_threshold = width_threshold

    @height_threshold.setter
    def height_threshold(self, height_threshold):
        self._height_threshold = height_threshold

    @image.setter
    def image(self, image):
        self._image = image

    def doc_text_detection(self, base64_image, feature):
        print('Running document text detection...')
        bounds = []
        texts = []
        confidences = []

        # decode image
        image = base64.b64decode(base64_image)
        image = vision.Image(content=image)
        response = self.client.document_text_detection(image=image)
        document = response.full_text_annotation

        def collect_feature_bounds(doc_obj, feature):
            """Helper function to collect specified feature bounds."""
            if feature == FeatureType.PAGE:
                bounds.extend([page.bounding_box for page in doc_obj.pages])
            else:
                for page in doc_obj.pages:
                    for block in page.blocks:
                        if feature == FeatureType.BLOCK:
                            bounds.append(block.bounding_box)
                        else:
                            for paragraph in block.paragraphs:
                                if feature == FeatureType.PARA:
                                    bounds.append(paragraph.bounding_box)
                                else:
                                    for word in paragraph.words:
                                        if feature == FeatureType.WORD:
                                            bounds.append(word.bounding_box)
                                            texts.append(''.join([symbol.text for symbol in word.symbols]))
                                            confidences.append(word.confidence)
                                        else:
                                            for symbol in word.symbols:
                                                tmp_text += symbol.text
                                                if feature == FeatureType.SYMBOL:
                                                    bounds.append(symbol.bounding_box)

        collect_feature_bounds(document, feature)

        # The list `bounds` contains the coordinates of the bounding boxes.
        return bounds, texts, confidences

    def convertBoundsToCoords(self, bounds):
        # Make tuples of coordinates
        coords = []
        for bound in bounds:
            coords.append((bound.vertices[0].x, bound.vertices[0].y))
            coords.append((bound.vertices[1].x, bound.vertices[1].y))
            coords.append((bound.vertices[2].x, bound.vertices[2].y))
            coords.append((bound.vertices[3].x, bound.vertices[3].y))
        return coords

    def draw_bounds(self, bounds, color=(0, 255, 0), thickness=2):
        # Draw bounds as polygons using OpenCV
        # bounds data is in the form of BoundingPoly
        # BoundingPoly is a list of vertices
        # Each vertex is a dict with x and y keys
        for bound in bounds:
            # Get the vertices
            vertices = bound.vertices
            # Convert the vertices to a list of tuples
            vertices = [(vertex.x, vertex.y) for vertex in vertices]
            # Draw the polygon
            cv2.polylines(self.image, [np.array(vertices)], True, color, thickness)

    def define_aoi(self):
        height, width, _ = self.image.shape
        center_x = width // 2
        center_y = height // 2
        width = int(width * self.width_threshold)
        height = int(height * self.height_threshold)
        xmin = center_x - width // 2
        xmax = center_x + width // 2
        ymin = center_y - height // 2
        ymax = center_y + height // 2
        return xmin, xmax, ymin, ymax

    def draw_aoi(self):
        # Draw the rectangle around the center of the image
        xmin, xmax, ymin, ymax = self.define_aoi()
        # Create a black image with the same size as the original image
        mask = np.zeros(self.image.shape, dtype=np.uint8)
        # Draw a white rectangle on the mask image
        cv2.rectangle(mask, (xmin, ymin), (xmax, ymax), (255, 255, 255), -1)
        # Invert the mask image
        mask = cv2.bitwise_not(mask)
        # Blend the original image and the mask using the addWeighted function
        self.image = cv2.addWeighted(self.image, 1.0, mask, 0.4, 0)


    def isBoundWithinAOI(self, bound):
        xmin, xmax, ymin, ymax = self.define_aoi()
        # Check if the bound is within the area
        vertices = bound.vertices
        vertices = [(vertex.x, vertex.y) for vertex in vertices]
        for vertex in vertices:
            if vertex[0] < xmin or vertex[0] > xmax or vertex[1] < ymin or vertex[1] > ymax:
                break
        else:
            return True
        return False

    def filter_bounds(self, bounds, labels, confidences, confidence_threshold):
        # Filter the bounds based on the confidence threshold
        filtered_bounds = []
        filtered_labels = []
        filtered_confidences = []
        for bound, label, confidence in zip(bounds, labels, confidences):
            if confidence >= confidence_threshold:
                if self.isBoundWithinAOI(bound):
                    filtered_bounds.append(bound)
                    filtered_labels.append(label)
                    filtered_confidences.append(confidence)
        return filtered_bounds, filtered_labels, filtered_confidences
