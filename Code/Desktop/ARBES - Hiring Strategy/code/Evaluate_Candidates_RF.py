
import logging
from libs.ResumeEvaluator import ResumeEvaluator
from libs.ARBES_Logging import setup_logging
import os


# Configure logging
logging.basicConfig(level=logging.DEBUG)
# ================================================================================
# SETUP LOGGING
# ================================================================================
script_name = os.path.basename(__file__)
script_name_no_ext = os.path.splitext(script_name)[0]

logger = setup_logging(
    log_file=f"logs/{script_name_no_ext}.log",
    max_files=20
)

logger.info("Starting application...")
# ================================================================================


# Initialize evaluator
evaluator = ResumeEvaluator(
    evaluation_rules_path="candidate_evaluation_rules.json",

    evaluation_steps_path="candidate_evaluation_steps.json",
    output_dir="evaluation_results"
)

results = evaluator.evaluate_directory("resumes")

# Log summary
logger.info(f"Processed {len(results)} resumes")


