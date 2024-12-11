import os
import sys
import logging
from libs.ARBES_Logging import initialize_logging

# ================================================================================
# SETUP LOGGING
# ================================================================================
script_name = os.path.basename(__file__)
script_name_no_ext = os.path.splitext(script_name)[0]

# Initialize logging for the entire application
logger = initialize_logging(
    log_file=f"logs/{script_name_no_ext}.log",
    max_files=20
)

logger.info("Starting application...")
# ================================================================================

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..', '..')))

from lib.AI.FFAI_AzureOpenAI import FFAI_AzureOpenAI as AI
from lib.AI.FFAzureOpenAI import FFAzureOpenAI

# Create the Azure client
azure_client = FFAzureOpenAI()
logger.info("Azure client created")

# Create the wrapper
ffai = AI(azure_client)
logger.info("AI wrapper created")

# Generate responses and track history
logger.info("Generating responses...")

response = ffai.generate_response("How do I use AI?")
logger.info(f"Response to 'How do I use AI?': {response}")

response = ffai.generate_response("how are you?", prompt_name="greeting")
logger.info(f"Response to greeting: {response}")

response = ffai.generate_response("what is 2 +2?", prompt_name="math")
logger.info(f"Response to math question: {response}")

response = ffai.generate_response("concatenate these words: cat, dog ", prompt_name="pet")
logger.info(f"Response to concatenation: {response}")

ffai.clear_conversation()
logger.info("Conversation cleared")

response = ffai.generate_response("what did you say to the math problem?", prompt_name='final query', history=["pet", "math", "greeting"])
logger.info("RESPONSE:")
logger.info(response)
logger.info("============================")

response = ffai.generate_response("concatenate these words again: cat, dog,shrimp ")
logger.info(f"Response to second concatenation: {response}")

ffai.clear_conversation()
logger.info("Conversation cleared")

# The history will now include both the 'final query' and its associated history
response = ffai.generate_response("what did you say to the question?", prompt_name='really final query', history=["final query"])
logger.info(f"Final response: {response}")


response = ffai.generate_response("what did you say to the question? Respond with a JSON dict.", prompt_name='really final query', history=["final query"])
logger.info(f"Final response: {response}")


# Access history using any of the interface methods
history = ffai.get_interaction_history()
clean_history = ffai.get_clean_interaction_history()

latest = ffai.get_latest_interaction()
stats = ffai.get_model_usage_stats()
prompt_dict = ffai.get_prompt_dict()
formatted_responses = ffai.get_formatted_responses(['math'])

logger.info("Interaction History:")
logger.info(history)
logger.info("Clean Interaction History:")
logger.info(clean_history)

logger.info("----------")
logger.info("Latest Interaction:")
logger.info(latest)
logger.info("----------")
logger.info("Model Usage Stats:")
logger.info(stats)
logger.info("----------")
logger.info("Prompt Dictionary:")
logger.info(prompt_dict)
logger.info("----------")
logger.info("Formatted Responses:")
logger.info(formatted_responses)

logger.info("Script execution completed")