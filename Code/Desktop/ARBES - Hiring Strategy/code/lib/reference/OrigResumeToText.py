from google.auth.transport.requests import Request
from google.cloud import firestore
from google.cloud import storage
from google.cloud.firestore import WriteBatch
import google.auth
import io
import logging
import os
import pymupdf4llm
import tempfile
import time
import traceback



# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self, gcs_bucket_name, database_name:str, dest_collection:str):
        logger.info(f"Initializing FileProcessor with bucket: {gcs_bucket_name}")
        
        self.dest_collection = dest_collection
        try:
            # Use google.auth to get default credentials and project ID
            self.credentials, self.project_id = google.auth.default()
            logger.info(f"Obtained credentials for project: {self.project_id}")
            
            # Refresh the credentials if necessary
            if self.credentials.expired:
                logger.info("Refreshing expired credentials")
                self.credentials.refresh(Request())
            
            self.gcs_bucket_name = gcs_bucket_name
            self.storage_client = storage.Client(credentials=self.credentials, project=self.project_id)
            self.bucket = self.storage_client.bucket(self.gcs_bucket_name)
            logger.info(f"Successfully connected to bucket: {self.gcs_bucket_name}")
            
            # Initialize Firestore client with the correct project ID and database
            self.db = firestore.Client(project=self.project_id, database=database_name)
            self.collection = self.db.collection(self.dest_collection)
            logger.info(f"Successfully initialized Firestore client for project {self.project_id}, database {database_name}")
        except Exception as e:
            logger.error(f"Error initializing FileProcessor: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def list_unprocessed_files(self):
        logger.info("Listing unprocessed files")
        unprocessed_files = []

        try:
            blobs = self.bucket.list_blobs()
            for blob in blobs:
                logger.debug(f"Found blob: {blob.name}")
                metadata = blob.metadata or {}
                file_id = metadata.get('file_id')
                
                if not file_id:
                    logger.info(f"Adding unprocessed file: {blob.name}")
                    unprocessed_files.append(blob)
                else:
                    doc_ref = self.collection.document(file_id)
                    doc = doc_ref.get()
                    if not doc.exists or doc.to_dict().get('needs_reprocessing', False):
                        logger.info(f"Adding unprocessed file: {blob.name}")
                        unprocessed_files.append(blob)

        except Exception as e:
            logger.error(f"Error listing unprocessed files: {str(e)}")
            logger.error(traceback.format_exc())

        logger.info(f"Found {len(unprocessed_files)} unprocessed files")
        return unprocessed_files

    def process_file(self, blob, batch: WriteBatch):
        logger.info(f"Processing file: {blob.name}")
        file_metadata = blob.metadata or {}  # Define this outside the try block
        file_id = file_metadata.get('file_id') or blob.name.replace('/', '_')
        temp_file_path = None

        # Check if the document already exists
        doc_ref = self.collection.document(file_id)
        doc = doc_ref.get()
        if doc.exists:
            logger.info(f"Document {file_id} already exists. Skipping processing.")
            return False

        try:
            file_content = blob.download_as_bytes()
            file_io = io.BytesIO(file_content)
            
            start_time = time.time()
            file_extension = os.path.splitext(blob.name)[1].lower()
            
            # Save BytesIO to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_io.getvalue())
                temp_file_path = temp_file.name

            # Process the temporary file
            logger.debug(f"Processing file: {blob.name}")
            parsed_content = pymupdf4llm.to_markdown(temp_file_path)
            
            processing_time = time.time() - start_time

            logger.debug(f"Preparing Firestore document for file: {file_id}")
            
            # Prepare the document data
            doc_data = {
                "processed_at": firestore.SERVER_TIMESTAMP,
                "parsed_content": parsed_content,
                "needs_reprocessing": False,
                "file_name": blob.name,
                "file_path": f"gs://{self.gcs_bucket_name}/{blob.name}",
                "processing_status": "processed",
                "processing_time": processing_time,
                "file_type": file_extension,
                "error_message": None,
                "original_metadata": file_metadata
            }
            
            # Add individual metadata fields at the top level for easy querying
            for key, value in file_metadata.items():
                if key != 'file_id':  # avoid duplicating file_id
                    doc_data[f"meta_{key}"] = value

            logger.debug(f"Adding document to Firestore batch for file: {file_id}")
            batch.set(doc_ref, doc_data)  # Use set without merge=True to only create if not exists
            logger.info(f"Successfully processed file: {blob.name}")
            return True

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing file: {blob.name}. Error: {error_message}")
            logger.error(traceback.format_exc())
            
            # Add error information to Firestore
            error_doc_data = {
                "processed_at": firestore.SERVER_TIMESTAMP,
                "needs_reprocessing": True,
                "processing_status": "failed",
                "error_message": error_message,
                "original_metadata": file_metadata,
                "file_name": blob.name
            }
            logger.debug(f"Adding error document to Firestore batch for file: {file_id}")
            batch.set(doc_ref, error_doc_data)  # Use set without merge=True to only create if not exists
            return False

        finally:
            # Clean up the temporary file
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(f"Error deleting temporary file {temp_file_path}: {str(e)}")

    def process_all_unprocessed_files(self):
        logger.info("Starting to process all unprocessed files")
        try:
            unprocessed_files = self.list_unprocessed_files()
            batch = self.db.batch()
            processed_count = 0
            
            for file in unprocessed_files:
                self.process_file(file, batch)
                processed_count += 1
                
                # Commit the batch every 500 files or at the end
                if processed_count % 500 == 0 or processed_count == len(unprocessed_files):
                    logger.info(f"Committing batch of {processed_count} files to Firestore")
                    try:
                        batch.commit()
                        logger.info(f"Successfully committed batch of {processed_count} files to Firestore")
                    except Exception as e:
                        logger.error(f"Error committing batch to Firestore: {str(e)}")
                        logger.error(traceback.format_exc())
                    batch = self.db.batch()  # Start a new batch
            
            logger.info(f"Finished processing all {processed_count} unprocessed files")
        except Exception as e:
            logger.error(f"Error in process_all_unprocessed_files: {str(e)}")
            logger.error(traceback.format_exc())

    def get_processing_status(self, file_id):
        logger.info(f"Getting processing status for file: {file_id}")
        try:
            doc_ref = self.collection.document(file_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error getting processing status for file {file_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def mark_for_reprocessing(self, file_id):
        logger.info(f"Marking file for reprocessing: {file_id}")
        try:
            doc_ref = self.collection.document(file_id)
            doc_ref.set({"needs_reprocessing": True}, merge=True)
            return True
        except Exception as e:
            logger.error(f"Error marking file {file_id} for reprocessing: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def query_processed_files(self, query):
        logger.info(f"Querying processed files with query: {query}")
        try:
            results = self.collection.where(query[0], query[1], query[2]).stream()
            return [doc.to_dict() for doc in results]
        except Exception as e:
            logger.error(f"Error querying processed files: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def print_file_details(self):
        logger.info("Printing details of all files in the bucket")
        try:
            blobs = self.bucket.list_blobs()
            for blob in blobs:
                logger.info(f"File: {blob.name}")
                logger.info(f"  Size: {blob.size} bytes")
                logger.info(f"  Content Type: {blob.content_type}")
                logger.info(f"  Metadata: {blob.metadata}")
                logger.info("---")
        except Exception as e:
            logger.error(f"Error printing file details: {str(e)}")
            logger.error(traceback.format_exc())

# Usage example
if __name__ == "__main__":
    try:
        processor = FileProcessor(
            gcs_bucket_name="hr_candidate_intake_docs",
            database_name="ff-hr"  # Replace with your database name if not using default
        )
        
        # Print details of all files
        processor.print_file_details()
        
        # Process all unprocessed files
        processor.process_all_unprocessed_files()

        # Example of getting processing status for a specific file
        # status = processor.get_processing_status("file-123")
        # logger.info(f"Processing status: {status}")

        # Example of marking a file for reprocessing
        # processor.mark_for_reprocessing("file-123")

        # Example of querying processed files
        # processed_files = processor.query_processed_files(("meta_author", "==", "John Doe"))
        # logger.info(f"Processed files: {processed_files}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        logger.error(traceback.format_exc())