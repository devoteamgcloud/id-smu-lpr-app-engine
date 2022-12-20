# Define a class of StorageHandler to handle the storage of the data in the cloud storage
import base64
from google.cloud import storage
import uuid, os

class StorageHandler:
    def __init__(self, project_id, bucket_name, folder_path_in_bucket):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.get_bucket(bucket_name)
        self.folder_path_in_bucket = folder_path_in_bucket

    def encode_image(self, image_path):
        """Encodes an image to base64."""
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return encoded_string

    def decode_image(self, base64_image_string):
        """Decodes a base64 encoded image string to a bytes object."""
        decoded_image = base64.b64decode(base64_image_string)
        return decoded_image
    
    def upload_base64_image(self, base64_image_string, job_id):
        """Uploads an encoded image to the bucket."""
        # Decode the image before uploading
        decoded_image = self.decode_image(base64_image_string)
        destination_blob_name = f'{job_id}.jpg'
        blob = self.bucket.blob(f'{self.folder_path_in_bucket}/{destination_blob_name}')
        blob.upload_from_string(decoded_image)
        print(f"File  uploaded to {self.folder_path_in_bucket}/{destination_blob_name}.")