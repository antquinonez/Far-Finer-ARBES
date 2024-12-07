
import logging
from libs.ResumeEvaluator import ResumeEvaluator


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Initialize evaluator
evaluator = ResumeEvaluator(
    evaluation_rules_path="candidate_evaluation_rules.json",

    evaluation_steps_path="candidate_evaluation_steps.json",
    output_dir="evaluation_results"
)

results = evaluator.evaluate_directory("resumes")

# Log summary
logger.info(f"Processed {len(results)} resumes")


