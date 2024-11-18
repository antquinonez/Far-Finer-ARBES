# Copyright (c) 2024 Antonio Quinonez
# Licensed under the MIT License. See LICENSE in the project root for license information.

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..', '..')))

from lib.AI.FFAnthropicCached import FFAnthropicCached
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Anthropic Cached command-line interface")

    config = {
        'max_tokens': 2000,
        'temperature': 0.7,
        'system_instructions': 'Tell the truth.'
    }

    try:
        # Create an instance of the class
        ai = FFAnthropicCached(config, model="claude-3-5-sonnet-20240620")
        logger.info("FFAnthropicCached initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize FFAnthropicCached: %s", str(e))
        return

    logger.info("AI initialized. Type 'exit' to quit.")

    while True:
        # Get user input    
        user_input = input("You: ")

        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            logger.info("User requested to exit")
            print("Goodbye!")
            break

        try:
            # Generate a response
            logger.debug("Generating response for user input: %s", user_input)
            response = ai.generate_response(user_input)
            print("Assistant:", response)
            logger.info("Response generated and displayed to user")
        except Exception as e:
            logger.error("An error occurred while generating response: %s", str(e))

if __name__ == "__main__":
    main()