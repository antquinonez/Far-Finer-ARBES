# %%
# ! pip install anthropic

# %%
import logging

from lib.ResumeEvaluator import ResumeEvaluator

# %%
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# %%
# Initialize evaluator
evaluator = ResumeEvaluator(
    evaluation_rules_path="candidate_evaluation_rules.json",
    # candidate_evaluation_rules.json",
    evaluation_steps_path="candidate_evaluation_steps.json",
    output_dir="evaluation_results"
)

# Process all resumes in directory
# results = evaluator.evaluate_directory("resumes/to_proc")
results = evaluator.evaluate_directory("resumes")

# Log summary
logger.info(f"Processed {len(results)} resumes")


