# code/gcp/eval_candidate/lib/CloudEventHandler.py

import re
import os
import logging
import google.auth
import configparser
import json
from datetime import datetime

from cloudevents.http import CloudEvent
from google.events.cloud import firestore as firestoredata
from google.cloud import resourcemanager_v3
from google.cloud import firestore_v1

from .prompts import main_prompt
from .FirestoreDataRetriever import FirestoreDataRetriever
from .FirestoreDataWriter import FirestoreDataWriter
from .eval_criteria import eval_criteria
from .AIClaude import AIClaude
from .Secrets import Secrets

logger = logging.getLogger(__name__)

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
def remove_excess_spaces(text):
    # Use regex to replace 4 or more spaces with 3 spaces
    return re.sub(r' {4,}', '   ', text)



# =================================================================================================
class CloudEventHandler:

    def __init__(self):
        self.defacto_database = os.environ.get('GOOGLE_CLOUD_FS_DATABASE')

        self.bucket_name = os.environ.get('GOOGLE_CLOUD_STORAGE_BUCKET')
        logger.info(f"bucket_name: {self.bucket_name}")

        self.bucket_name_stage = os.environ.get('GOOGLE_CLOUD_STORAGE_BUCKET_STAGE')
        logger.info(f"bucket_name_stage: {self.bucket_name_stage}")

        self.trigger_strings = ['http://', 'https://', 'gs://']
        self.allowed_domains = ['airtableusercontent.com', 'drive.google.com']
        self.project_id = self.get_project_id()

        # Load configuration
        self.config = self.load_config()

    def load_config(self):
        config_parser = configparser.ConfigParser()
        
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go one level up to the parent directory
        parent_dir = os.path.dirname(current_dir)
        # Construct the path to config.ini in the parent directory
        config_path = os.path.join(parent_dir, 'config.ini')
        
        try:
            if not os.path.exists(config_path):
                logger.error(f"Config file not found: {config_path}")
                return None

            config_parser.read(config_path)
            
            if 'FS' not in config_parser:
                logger.error("'FS' section not found in config file")
                return None
            
            return config_parser
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return None

    def get_project_id(self):
        logger.info("Attempting to retrieve project ID")
        credentials, project_id = google.auth.default()
        client = resourcemanager_v3.ProjectsClient()

        try:
            project = client.get_project(name=f"projects/{project_id}")
            logger.info(f"Successfully retrieved project ID: {project.project_id}")
            return project.project_id
        except google.api_core.exceptions.GoogleAPIError as e:
            logger.error(f"An error occurred while retrieving the project ID: {e}")
            return None


    def handle_event(self, cloud_event):
        logger.debug(f"Received cloud event: {cloud_event}")

        # Check if the event is a Firestore event
        if not self.config:
            logger.error("Configuration not loaded. Cannot proceed.")
            return
            
        # Check if the event is a Firestore event
        if not self.bucket_name:
            logger.error("GOOGLE_CLOUD_STORAGE_BUCKET environment variable is not set")
            return

        fs_payload = {}
        subject = cloud_event.get('subject')
        logger.info("subject: %s", subject)

        if not subject:
            logger.error("No subject found in cloud_event")
            return

        # Split the subject to get the document path
        parts = subject.split('/')

        if len(parts) < 6:
            logger.error(f"length: {len(parts)}")
            logger.error(f"Unexpected subject format: {subject}")
            # return

        try:
            # Extract project ID, database ID, collection path, and document ID
            project_id = cloud_event.get('project', self.get_project_id() )
            database_id = cloud_event.get('database', self.defacto_database)
            
            collection = ''
            if fs_payload.get('collection_path'):
                collection_path = fs_payload.get('collection_path')
                collection = collection_path[-2]
            else:
                collection = parts[-2]
            
            collection_path = fs_payload.get('collection_path', '/'.join(parts[5:-1]))
            
            document_from_event = cloud_event.get('document')

            doc_id = ''
            if document_from_event:
                document_from_event_parts =  document_from_event.split('/')
                doc_id = document_from_event_parts[-1]
            else:
                doc_id = parts[-1]

            # Information on the triggering event
            logger.info("==================================================")
            logger.info(f"project_id: {project_id}")
            logger.info(f"database_id: {database_id}")
            logger.info(f"collection: {collection}")
            logger.info(f"doc_id: {doc_id}")
            logger.info("==================================================")

            # todo: this here because of trouble with logging to gcp with info and debug
            #   remove when logging fixed
            # logger.error("==================================================")
            # logger.error(f"project_id: {project_id}")
            # logger.error(f"database_id: {database_id}")
            # logger.error(f"collection: {collection}")
            # # logger.error(f"collection_path: {collection_path}")
            # logger.error(f"doc_id: {doc_id}")
            # logger.error("==================================================")


            # get the current date and time
            now = datetime.now()
            # formatted YYYY-MM-DD HH:MM:SS
            dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
            print("date and time =", dt_string)

            # GET CONFIGURATION INFORMATION ===================================================
            try:
                FS_DATABASE = self.config['FS']['database']
                FS_COLLECTION = self.config['FS']['collection']
            except KeyError as e:
                logger.error(f"Missing key in config: {str(e)}")
                return
            # ===================================================================================

            fs_dr = FirestoreDataRetriever(db_name=FS_DATABASE)

            # doc_id = 'Resume_423bb57f083a9c5d83a2639ff9e35312'
            doc = fs_dr.get_document_data(collection=FS_COLLECTION, doc_id=doc_id, )
            resume = doc.get('parsed_content', None)

            # MAIN PROMPT AND RESUME ============================================================
            main_prompt_and_resume = main_prompt + "\n=============\nCANDIDATE EVALUATION CRITERIA\n==========\n" + eval_criteria +"\n =======\nRESUME\n=========\n"+ resume
            main_prompt_and_resume = remove_excess_spaces(main_prompt_and_resume)
            print(main_prompt_and_resume)

            # EVLAUATION PROMPTS ================================================================
            evaluate_basic = "Evaluate the 'Basic' Type evaluation rules."
            evaluate_technical = "Evaluate the 'Technical' Type evaluation rules."
            evaluate_exp = "Evaluate the 'Experience' Type evaluation rules."
            evaluate_role = "Evaluate the 'Role' Type evaluation rules."
            evaluate_resume_eval = "Evaluate the 'Resume Evaluation' Type evaluation rules."
            evaluate_dark= "Evaluate the 'Dark' Type evaluation rules."
            evaluate_core = "Evaluate the 'Core' Type evaluation rules."
            evaluate_other = "Evaluate the remaining Types."

            # GATHER PROMPTS ====================================================================
            prompts = [evaluate_basic, evaluate_technical, evaluate_exp, evaluate_role, evaluate_resume_eval, evaluate_dark, evaluate_core, evaluate_other, "thanks"] 

            # SET UP CLAUDE ====================================================================
            api_key = Secrets().get_api_key('ANTHROPIC_TOKEN')

            config = {  'model': 'claude-3-5-sonnet-20240620',
                        'api_key': api_key,
                        'temperature': 0.3,
                        'max_tokens': 8000,
                        'system_instructions': main_prompt_and_resume,

            }

            ai = AIClaude(config=config)

            # PERFORM EVALUATION ================================================================
            responses = []
            for prompt in prompts:
                # Get user input
                try:
                    # Generate a response
                    response = ai.generate_response(prompt)
                    responses.append(response)
                except Exception as e:
                    print(f"An error occurred: {str(e)}")

            # Display Evaluation Results ========================================================
            for response in responses:
                print(response )


            responses = responses[:-1]  # Exclude the last response (which is the 'thanks' response)

            # CLEAN UP RESPONSES ================================================================
            cleaned_responses = []
            for response in responses:
                # Remove ```json and ``` from response
                response = response.replace("```json", "").replace("```", "")

                try:
                    # Parse JSON string into native Python data structures
                    stuff = json.loads(response)
                    cleaned_responses.append(stuff)
                    
                    print(stuff)
                except json.JSONDecodeError as e:
                    print(f"An error occurred while parsing JSON: {str(e)}")
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")

            # MERGE CLEANED RESPONSES ===================================================================
            eval_dict = {}
            for response in cleaned_responses:
                eval_dict.update(response)

            candidate_name = eval_dict['preferred_name']['value']

            # CREATE THE STRUCTRURE OF THE DATA WE WILL STORE IN FIRESTORE
            final_dict = {
                'last_updated': firestore_v1.SERVER_TIMESTAMP,  # date-time when the evaluation was done
                'entity_name': candidate_name,  # name of the candidate
                'source_metadata': doc,                          # metadata
                'evaluation': eval_dict  # candidate evaluation
            }

            # WRITE DATA TO FIRESTORE ===================================================================
            fs = FirestoreDataWriter(collection_name="candidate_evaluations", database_id="ff-hr")
            fs.write_data(data=final_dict, doc_id=candidate_name)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise RuntimeError(f"Error processing Evaluation: {str(e)}")
