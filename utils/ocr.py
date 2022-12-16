from google.cloud import vision

@celery.task
def call_vision_api(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as image_file:
        image = vision.types.Image(content=image_file.read())

    response = client.document_text_detection(image=image)

    # Process the response and save the results
