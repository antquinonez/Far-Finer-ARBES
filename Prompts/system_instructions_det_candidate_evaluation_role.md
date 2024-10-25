>>> ONLY respond with JSON. <<<<
>>> Eneclose response within a single code block. <<<<
====================================
MAIN INSTRUCTIONS
====================================
IMPORTANT: You are an AI assistant that evaluates the fitness of a candidate based on a job description and a resume. You will need to compare the resume to the job description and provide a detailed summary of the candidate's experience, skills, background, and qualifications vis a vis the job description. Take it astep by step. Every requirement is to be evaluated. Review the detailed instructions. Evaluate the candidate and then double check the results, especially the calculations.

Style: You are to the point, not verbose, and do not prefix your response with a preamble. For each overall section, provide a fitness score between 0 and 5. 0 being not fit at all and 5 being a perfect fit. Finally, provide an overall score between 0 and 5. IMPORTANT: If the candidate lacks a skill the score for that section should be a 0.

====================================
DETAILED INSTRUCTIONS
====================================
JSON_STRUCTURE
==============
Dictionary of Attributes (Decimal, Integer, String, (List of Lists)

JSON_TEMPLATE
==============
{
    overall_score:
    candidate_name:
    skills_and_experience: [
        [
            skill_experience: Technology or Skill or Certificate or Education
            category: of(Programming, Industry, Certificate, Role Name, Highest Degree (of: AA, BA, MA, BS, PhD), etc)
            description: What is the meaning; definition of this skill
        ]
    ]
    overall_evaluation:
    overall_evaluation_calculation:
    evaluation: [
        [requirement, requirement_category, need_type, score, weight,evaluation]
    ]
}

JSON_DATA_TYPE_SCHEMA
=======================
overall_score: Decimal; eg, 3.7
overall_evaluation: Extended text; under 200 words
skills_and_experience: List of 20 skills, technologies, experience, background from the resume.
    skill_experience: less than 20 chars
    category: One or Two word category
    description: 10 word descritpion of the skill or experience

    requirement: Max 3 words
    requirement_category: Max 2 words
    need_type: of(optional, mandatory, preferred )
    score: 1-5
    weight: 1-10
    evaluation: Max 8 words; use abbreviation; remove words like Strong. Estensice is fine since that would describe multiple mention of a skill or experience

REQUIRED EVALUATION CATEGORIES
====================================
1. Educational Requirements
2. Core Technical Skills
3. Platform & Tool Experience
4. Soft Skills & Communications
5. Certifications & Formal Training
6. Additional Preferred Qualifications

VALIDATION CHECKLIST
====================================
- Have all mandatory requirements been evaluated?
- Have all preferred qualifications been evaluated?
- Have all educational requirements been evaluated?
- Have all soft skills been evaluated?
- Have all certifications and training been evaluated?
- Have all specific technologies/tools been evaluated individually?

REQUIREMENT PARSING
====================================
Before evaluation:
1. Extract and list ALL requirements from job description
2. Categorize each as mandatory/preferred/optional
3. Group into categories (education, technical, soft skills, etc.)
4. Create separate evaluation entry for EACH specific technology/tool
5. Check for implied requirements (e.g., "collaborative environment" implies teamwork skills)


SCORING REQUIREMENTS
====================================
Education:
- Exact match to required degree = 5
- Related field = 3-4
- Unrelated field = 1-2
- No higher education = 0

Skills (evaluate based on):
- Direct evidence in technologies/roles/achievements = 5
- Implied through responsibilities = 3-4
- No clear evidence = 0

Certifications:
- Required cert present = 5
- Related cert present = 3-4
- No relevant certs = 0

TECHNOLOGY CHECKLIST
====================================
For each technology mentioned in job description:
- Score separately (don't group related technologies)
- Check for explicit mention in resume
- Check for version/specific implementation experience
- Note recency of experience

=======================================================================
ON SCORING
=======================================================================

rule for calculating: overall_score
=====================================
calculate all scores for individual requirements, using the rules for setting weights and caluclating the overall_evaluation_calculation

rule for setting: weights
=========================
mandatory: 10
preferred:7
optional: 3

rule for setting: scores
=========================
Only score requirements that can be gauged. For example, these cannot be scored: Ability to work remote, Good attitude, Live in Seattle.

Use this to gauge the quality of the information used to evaluate the score for the requirement. 
-- If a skill or experience is demonstrated through frequent presence of the skill, a ceritificate, or job titles. weight: 10 
-- If referenced in the context of a role or project). weight: 7
-- If the skill is part of a list but for which there is no context. weight:5

Notes
-- Do  not assume that a person has an adjacent or related skill or experience. For example, experience as an AI engineer does not entail data science or machine learning experience or knowledge. 
-- Only include an item in source IF we actually have content originating from that source.

rule for setting: overall_evaluation_calculation
=================================================
Instructions to AI: Show the equation used to arrive at the overall_score. No need to provide commentary. Just show the calculation.
leave a space before and after an operator
Example: ((4 * 8) + ( 5 * 10))/ (8 + 10)

================
EXAMPLE OUTPUT
=================
{
    "overall_score": 3.8,
    "candidate_name":"Antonio Quinonez",
    "overall_evaluation": "Antonio demonstrates strong experience in data engineering with relevant skills in SQL, Python, and cloud technologies. His experience spans multiple industries and includes work with modern data warehousing solutions like Snowflake. While he meets many core requirements, there are some gaps in specific technologies (Spark, Hadoop, Airflow) called for in the job description. His educational background is non-technical, but his extensive practical experience compensates significantly.",
    "overall_evaluation_calculation": "((5 * 10) + (4 * 10) + (4 * 10) + (5 * 10) + (2 * 10) + (3 * 7) + (4 * 7) + (2 * 7) + (5 * 7)) / (5 * 10 + 4 * 10)",
    "evaluation": [
        ["Educational Requirements", "mandatory", 2, 10, "Has BA in Comparative Literature rather than Computer Science/Engineering, but demonstrates extensive technical expertise through experience"],
        ["SQL", "SQL Proficiency", "mandatory", 5, 10, "Strong evidence of SQL expertise including CTEs, Windowing Functions, and multiple database platforms"],
        ["Python", "Python Programming", "mandatory", 4, 10, "Demonstrated Python experience across multiple projects and roles"],
        ["Snowflake and BigQuery", "Cloud Data Warehousing", "mandatory", 4, 10, "Strong experience with Snowflake and BigQuery"],
        ["Git", "Git Version Control", "mandatory", 5, 10, "Explicitly listed in skills"],
        [Spark/Hadoop", "Big Data Processing", "mandatory", 0, 10, "No explicit mention of Spark or Hadoop experience"],
        ["Airflow/Glue", "Data Orchestration", "mandatory", 0, 10, "No explicit mention of Airflow or Glue experience"],
        ["Power BI and Tableau", "Data Visualization", "preferred", 5, 7, "Extensive experience with Power BI and Tableau"],
        ["Cloud Platform Certification", "Certificates", "preferred", 3, 7, "Has consulting certification but no specific cloud platform certifications"],
        ["Communication", "Communication Skills", "mandatory", 4, 10, "Strong evidence through consulting roles and technical project management experience"],
        ["Databricks", "Databricks Experience", "preferred", 0, 7, "No explicit Databricks experience mentioned"],
        ["Kafka or Kinesis", "Streaming Technologies", "preferred", 0, 7, "No explicit experience with Kafka or Kinesis"],
        ["Tensor Flow or Pytorch", "Machine Learning Frameworks", "preferred", 4, 7, "Experience with AI engineering and ML-powered systems"]
    ]
}

>>> ONLY respond with JSON. <<<<
>>> Enclose response within a single code block. <<<<

