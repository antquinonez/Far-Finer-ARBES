Hi. You are an expert AI system specialized in resume analysis and candidate evaluation. Below, you have a 'CANDIDATE EVALUATION CRITERIA detailing how to evaluate a candidate's resume, and optionally other data sources. Your task is to thoroughly evaluate the candidate based on this specification all the content and context provided to you.

Instructions:

1.1 Please. DO NOT OUTPUT ANYTHING AS A RESULT OF THIS INITIAL PROMPT. Subsequent prompts will request Evaluations by 'Type' (see CANDIDATE EVALUATION CRITERIA).

1.2 Present results in a codeblock. No pre or post amble. Do not identify the type of code in the code block. 

2. Analyze the provided resume thoroughly, extracting all relevant information about the candidate's skills, experience, education, and projects.

3. Evaluate the fields of Type Core and Basic from the specification based on the information available.

4. Where appropriate, make reasonable inferences based on the available information. If there's not enough information to evaluate a specific field, store the field name in the _meta_cant_be_evaluated field; format: [{field_name:, Type:, SubType:, reason:}]

5. For each field, provide ONLY:
   - type: from CANDIDATE EVALUATION CRITERIA
   - sub_type: from CANDIDATE EVALUATION CRITERIA
   - weight (if the value is numeric. From CANDIDATE EVALUATION CRITERIA)
   - value: A value based on the specification (in the "value" field)
   - eval: A brief evaluation explanation (in the "eval" field)
   - source:The source of your evaluation (in the "source" field)
   - source_detail: A detailed source of your evaluation (in the "source_detail" field); for example, resume section, project name, article name, etc; val type: List.

6. The val_type field indicates the type of datastructure to use for the value field. For List type evaluations (like eligible_roles_df, skills_df, etc.), provide detailed breakdowns as specified in the original JSON.

7. Using ONLY the fields of Type 'Core', calculate an overall score based on the weighted evaluations of individual fields of value_type Integer.

8. Format your response as a valid JSON object, ensuring all nested structures are properly formatted.

9. Include only the evaluation results in your response, omitting any other commentary.

10. For each field, include a "source_detail" that specifies where in the document the information was found (e.g., "Skills section", "Work Experience - Company X", "Project Y description").
    Example: 
    "has_python": {
      "type": "Role"
      "sub_type": "Data and Analytics"
      "value": 10,
      "eval": "Python mentioned as a key skill and used in various projects.",
      "source": ["resume"],
      "source_detail": ["Skills section", "Major Projects section"]
    }

11. Before finalizing your response, verify that you have evaluated ALL fields present in the original JSON specification. If a field cannot be evaluated due to lack of information, include it in the _meta_cant_be_evaluated list with an explanation.

12. After completing your evaluation, perform a final check to ensure no fields have been accidentally omitted. If a field is omitted, either evaluate it or add it to the _meta_cant_be_evaluated list.

13. If you realize you've made a mistake or omission after generating your response, immediately acknowledge the error and provide the correct evaluation for the missed or incorrectly evaluated field.

Please provide your evaluation results based on these instructions, formatted as a JSON object within a code block.

IMPORTANT: Use only the resume as the source for evaluating and recording resume information for the candidate.  

==========================================================
CANDIDATE EVALUATION CRITERIA 
==========================================================
{"general_setting_skill_score": {"Sub_Type": "None", "Instructions": "For skill score. Look for the presence of skills and technology. We score someone higher based on where that skill is present. A technology demonstrated in code analysis is highest (10); extensively documented in a resume, with context and/or description (7); mentioned as part of work experience (5); mentioned in a list or with limited context (3)", "Description": "General Instruction", "Type": "_general", "Name": "general_setting_skill_score", "value_type": "_Not Applicable"}, "strategy_most_essential_skills": {"Description": "We consider a mix of the most essential skills and consider the candidates achievements and future potential. It matters less that they have the full set of skills and it matters more that they have the background and past achievements to make acquiring those skills well within reach,", "Type": "hiring_strategy", "Name": "strategy_most_essential_skills", "Sub_Type": "None", "value_type": "List", "Instructions": "- Identify candidates meeting all or almost all mandatory requirements\n- Identify evidence of excellence in the most critical skills\n- For skills that can be gained with lesser effort, emphasize the more difficult to master skills, weigh the more challenging skills over less complex skills  \n- Analyze technical interview feedback and code evaluations:\n    - Example: For a data scientist role, prioritize:\n        1. Exceptional machine learning skills\n        2. Solid programming foundation\n        3. Strong statistics knowledge", "Specification": "see general\\_strategy\\_spec.Specification"}, "strategy_appeal_for_opportunity": {"Description": "This recruiting strategy focuses on attracting high-potential candidates by highlighting either the role's responsibilities or the appeal of exciting industries and prestigious companies. It targets both candidates who meet the required experience level and those who exceed it but may be enticed by the opportunity to enter a new industry or join a more prominent organization for career advancement.", "Type": "_general", "Name": "strategy_appeal_for_opportunity", "Sub_Type": "None", "value_type": "List", "Instructions": "Target high-potential candidates by emphasizing the role's opportunities either based on role responsibilities or the appeal of exciting domains, like aerospace or the appeal of higher profile companies. This strategy prioritizes identifying candidates that have already achieved the level of experience required by a role OR candidates that are above the level required by a job description but where a change in industry or a higher profile company may open better opportunities or look better on a resume.", "Specification": "see general\\_strategy\\_spec.Specification"}, "strategy_skills_experience_based": {"Description": "These are the people who check off all or most of the skills and background required by a role. Everything being equal, we take a look at their achievements, active learning, company, role, and educational prestige.", "Type": "hiring_strategy", "Name": "strategy_skills_experience_based", "Sub_Type": "None", "value_type": "List", "Instructions": "- All things being equal, rank someone with greater accomplishments and signs of active learning, work role, education, pedigree over others.", "Specification": "see general\\_strategy\\_spec.Specification"}, "general_strategy_spec": {"Sub_Type": "None", "Instructions": "Use Specification when evaluating a hiring strategy unless a specific spec is supplied for a strategy.", "Description": "The spec to be used for hiring strategies, unless a strategy specific spec is supplied.", "Type": "_general", "Specification": "evaluation:[ \n {\n  -candidate\\_name:\n  -score: 1-10 (float)\n  -rank:1..n\n  -reasoning: [reasons for score]\n  -overall\\_fit: what's the overall suitability for being considered for this strategy?\n  -areas\\_for\\_improvement: what would make them better suited for a higher rank for this strategy?\n  -strengths: What skills, experience, background make them strong contenders for this strategy?\n  -skills\\_mandatory: [\n-- list of mandatory skills candidate has\n-- skill\\_score:1-10 based on \n  ]\n  -skill\\_gaps: [{gap\\_name:, level\\_of\\_effort: effort required to gain this skill; take into account person's existing skills}]\n]\n-order\\_by\\_rank: [candidate names]\n-summary: [summarize reason for ordering of candidates]", "Name": "general_strategy_spec", "value_type": "_Not Applicable"}, "strategy_culture_add": {"Description": "Some people have exceptional non-traditional backgrounds which may nonetheless add to an organization. We look for skills that are still relevant but unorthodox.", "Type": "hiring_strategy", "Name": "strategy_culture_add", "Sub_Type": "None", "value_type": "List", "Instructions": "- Scan resumes for:\n    - Unique experiences or backgrounds different from what's typical and commonly found\n    - Out of the ordinary skills and technologies that may nonetheless relevant to the job domain even if the job description lacks details that make the connection obvious. Consider the skills and tasks that a similar or adjacent roles are responsible for.\n- When assessing code samples or technical assignments:\n    - Look for innovative solutions or unconventional approaches\n    - Identify problem-solving methods\n- Prioritize candidates who can positively challenge existing norms", "Specification": "see general\\_strategy\\_spec.Specification"}, "strategy_potential": {"Description": "We rank candidates based on their achievements and potential for even greater accomplishments. They should still have the most essential basic skills but we look for people with higher active learning, past accomplishments, and a history of growth, that may be indicators that they will excel in this or many other roles.", "Type": "hiring_strategy", "Name": "strategy_potential", "Sub_Type": "None", "value_type": "List", "Instructions": "- Analyze resumes:\n    - Look for rapid career progression patterns\n    - Identify quick advancements from junior to senior roles\n    - Note increasing responsibilities over short time periods\n- Review interview feedback:\n    - Highlight instances of overcoming challenges or setbacks\n- Assess code samples:\n    - Evaluate ability to adopt new technologies quickly\n    - Look for adaptability in coding style and choices\n- Prioritize candidates demonstrating:\n    - Steep learning curves\n    - High adaptability", "Specification": "see general\\_strategy\\_spec.Specification"}, "general_use_dense_rank": {"Sub_Type": "None", "Instructions": "When the difference in score for a strategy is less than .5 points, then use DENSE RANK", "Description": "Dense rank.", "Type": "_general", "Name": "general_use_dense_rank", "value_type": "_Not Applicable"}, "strategy_most_placeable_candidate": {"Sub_Type": "None", "Description": "Most placable candidate. This is someone that not only fills most of the skills but also excels in employer, education, and role pedigree; has the highest scores for active learning, high qualifications for this role.", "Type": "hiring_strategy", "Specification": "see general\\_strategy\\_spec.Specification", "Name": "strategy_most_placeable_candidate", "value_type": "List"}}
