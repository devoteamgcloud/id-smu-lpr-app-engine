# Define a class of StorageHandler to handle the storage of the data in the cloud storage
from google.cloud import storage
import uuid, os

class StorageHandler:
    def __init__(self, project_id, bucket_name, folder_path_in_bucket):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.get_bucket(bucket_name)
        self.folder_path_in_bucket = folder_path_in_bucket

    def upload_binary(self, source_file):
        """Uploads a file to the bucket."""
        # Get file extension
        file_extension = os.path.splitext(source_file.filename)[1]
        destination_blob_name = f'{str(uuid.uuid4())}.{file_extension}'
        blob = self.bucket.blob(f'{self.folder_path_in_bucket}/{destination_blob_name}')
        blob.upload_from_file(source_file)
        print(f"File {source_file.filename} uploaded to {self.folder_path_in_bucket}/{destination_blob_name}.")
    
    def upload_blob(self, source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
    
    def download_blob(self, source_blob_name, destination_file_name):
        """Downloads a blob from the bucket."""
        blob = self.bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
    
    def list_blobs(self):
        """Lists all the blobs in the bucket."""
        blobs = self.bucket.list_blobs()
        for blob in blobs:
            print(blob.name)