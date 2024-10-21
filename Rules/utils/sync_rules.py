# %%
import os
import sys
from dotenv import load_dotenv
import logging
import json

from google.cloud import firestore

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '.')))

from lib.utils import exclude_keys, write_dict_to_csv
from lib.Secrets import Secrets

from lib.AirtablePipelineConfigs import PipelineConfig, AirtableConfig, DatastoreConfig, UpdateType
from lib.AirtableToDatastore import AirtableToDatastore
from lib.AirtableToDatastoreBuilder import AirtableToDatastoreBuilder
from lib.FirestoreDataRetriever import FirestoreDataRetriever

# %%
_= Secrets.get_api_key('AIRTABLE_API_KEY')

# %%
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# %%
api_key  = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
database_id = os.getenv('FS_DATABASE_ID')
datastore_collection = os.getenv('FS_CONFIGS')

# %% [markdown]
# # Process Hiring Strategy Rules

# %%
source_table = os.getenv('AT_STRATEGY_SPEC_TABLE_NAME')
source_view = os.getenv('AT_STRATEGY_SPEC_VIEW_NAME')
primary_key = os.getenv('AT_STRATEGY_SPEC_PK')

update_type = UpdateType.UPSERT_TABLE_CHECKSUM

# Create configuration
airtable_config = AirtableConfig(base_id=base_id, table_name=source_table, view_name=source_view, api_key=api_key)
datastore_config = DatastoreConfig(project_id=project_id, database_id=database_id, kind=datastore_collection)

pipeline_config = PipelineConfig(
    airtable=airtable_config,
    datastore=datastore_config,
    primary_key=primary_key,
    update_type=update_type,
)

# Create and run the pipeline
pipeline = AirtableToDatastore(pipeline_config)
pipeline.run_pipeline()

# %% [markdown]
# ## Publish Hiring Strategy Files

# %%
dr = FirestoreDataRetriever(db_name=database_id)
rules = dr.get_document_data(collection=datastore_collection, doc_id=source_table)
rules = rules['table_data']

fields_to_exclude = ['id', 'Created', 'Created By', 'Last Modified', 'Last Modified By', 'Approved By', 'Notes (not for AI)', 'NTD', 'Use?','Status']

rules = exclude_keys(rules, fields_to_exclude)

rules_json = json.dumps(rules, indent=4)
rules_json_noindent = json.dumps(rules)

folder_path = '../hiring_strategy'
rule_name = 'hiring_strategy_rules'

# write result_json to a file
with open(f'{folder_path}/{rule_name}.json', 'w') as f:
    f.write(rules_json)

# write rules_json_noindent to a file
with open(f'{folder_path}/{rule_name}_noindent.json', 'w') as f:
    f.write(rules_json_noindent)    

# write to csv
priority_fields = ['Name', 'Type', 'Sub_Type', 'Attribute Description', 'Specification', 'embedded_schema', 'Weight', 'value_type']
write_dict_to_csv(rules_json, f'{folder_path}/{rule_name}.csv', priority_fields=priority_fields)

# %% [markdown]
# # Process Candidate Evaluation Rules -- with builder for more extensive checks/setup

# %%
source_table = os.getenv('AT_CANDIDATE_EVAL_TABLE_NAME')
source_view = os.getenv('AT_CANDIDATE_EVAL_VIEW_NAME')
primary_key = os.getenv('AT_CANDIDATE_EVAL_PK')

update_type = UpdateType.UPSERT_TABLE_CHECKSUM

pipeline_config = (AirtableToDatastoreBuilder()
    .with_airtable_config(base_id=base_id, table_name=source_table, view_name=source_view, api_key=api_key)
    .with_datastore_config(project_id=project_id, database_id=database_id, kind=datastore_collection)
    .with_primary_key(primary_key)
    .with_update_type(update_type)
    .build())

# Create and run the pipeline
pipeline = AirtableToDatastore(pipeline_config)
pipeline.run_pipeline()

# %% [markdown]
# ## Publish Candidate Evaluation Files

# %%
dr = FirestoreDataRetriever(db_name=database_id)
rules = dr.get_document_data(collection=datastore_collection, doc_id=source_table)
rules = rules['table_data']

fields_to_exclude = ['id', 'Created', 'Created By', 'Last Modified', 'Last Modified By', 'Approved By', 'Notes (not for AI)', 'NTD', 'Use?','Status']

rules = exclude_keys(rules, fields_to_exclude)

rules_json = json.dumps(rules, indent=4)
rules_json_noindent = json.dumps(rules)

folder_path = '../candidate_evaluation'
rule_name = 'candidate_evaulation_rules'

# write result_json to a file
with open(f'{folder_path}/{rule_name}.json', 'w') as f:
    f.write(rules_json)

# write rules_json_noindent to a file
with open(f'{folder_path}/{rule_name}_noindent.json', 'w') as f:
    f.write(rules_json_noindent)    

# write to csv
priority_fields = ['Name', 'Type', 'Sub_Type', 'Attribute Description', 'Specification', 'embedded_schema', 'Weight', 'value_type']
write_dict_to_csv(rules_json, f'{folder_path}/{rule_name}.csv', priority_fields=priority_fields)

# %%



