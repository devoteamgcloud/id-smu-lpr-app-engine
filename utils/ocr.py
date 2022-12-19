import base64
from enum import Enum
import io
from google.cloud import vision

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

class OCRHandler:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
    
    def doc_text_detection(self, base64_image, feature):
        """Returns document bounds given an image."""
        print('Running document text detection...')
        bounds = []
        texts = []
        confidences = []

        # decode image
        image = base64.b64decode(base64_image)
        image = vision.Image(content=image)
        response = self.client.document_text_detection(image=image)
        document = response.full_text_annotation

        # print(f'Response: {response}')
        # print(f'Document: {document}')

        # Collect specified feature bounds by enumerating all document features
        for page in document.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        tmp_text = ''
                        for symbol in word.symbols:
                            tmp_text += symbol.text
                            if feature == FeatureType.SYMBOL:
                                bounds.append(symbol.bounding_box)
                                # texts.append(symbol.text)
                                # confidences.append(symbol.confidence)

                        if feature == FeatureType.WORD:
                            bounds.append(word.bounding_box)
                            texts.append(tmp_text)
                            confidences.append(word.confidence)

                    if feature == FeatureType.PARA:
                        bounds.append(paragraph.bounding_box)
                        # texts.append(paragraph.text)
                        confidences.append(paragraph.confidence)

                if feature == FeatureType.BLOCK:
                    bounds.append(block.bounding_box)
                    # texts.append(block.text)
                    confidences.append(block.confidence)

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