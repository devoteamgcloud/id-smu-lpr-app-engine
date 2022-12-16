from flask import Flask, request, render_template
from utils.storage import StorageHandler
from config import config as cfg
import os, uuid
from celery import Celery
from google.cloud import vision


def create_celery_app(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

storageHandler = StorageHandler(cfg.PROJECT_ID, cfg.BUCKET_NAME, cfg.FOLDER_PATH_IN_BUCKET)

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://127.0.0.1:6379',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379'
)
celery = create_celery_app(app)

@celery.task
def call_vision_api(binary_image):
    client = vision.ImageAnnotatorClient()

    response = client.document_text_detection(image=binary_image)

    # Process the response and save the results
    print(response)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]

    # Save the file to GCP cloud storage
    storageHandler.upload_binary(file)

    # Call the Celery task to call the Cloud Vision API
    call_vision_api.delay(file)

    return render_template("upload_success.html")




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
