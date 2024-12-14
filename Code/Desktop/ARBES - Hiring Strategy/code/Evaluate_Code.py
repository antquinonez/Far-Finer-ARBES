import logging
from libs.DocumentEvaluator import DocumentEvaluator
import os

# ================================================================================
# SETUP LOGGING
# ================================================================================
from libs.ARBES_Logging import initialize_logging

# --------------------------------------------------------------------------------
script_name = os.path.basename(__file__)
script_name_no_ext = os.path.splitext(script_name)[0]

# Initialize logging for the entire application
logger = initialize_logging(
    log_file=f"logs/{script_name_no_ext}.log",
    max_files=20
)

logger.info("Starting application...")
# ================================================================================
# Initialize evaluator
# ================================================================================

evaluator = DocumentEvaluator(
    evaluation_rules_path="code_evaluation_rules.json",
    evaluation_steps_path="evaluation_steps.json",
    output_dir="evaluation_results"
)

results = evaluator.evaluate_directory("documents_to_evaluate/code")

# Log summary
logger.info(f"Processed {len(results)} documents")


