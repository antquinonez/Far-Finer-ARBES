>>> ONLY respond with JSON. <<<<
>>> Eneclose response within a single code block. <<<<

JSON_STRUCTURE
==============
Dictionary of Attributes Decimal, String, (List of Lists)

JSON_TEMPLATE
==============
{
    overall_score:
    overall_evaluation:
    overall_evaluation_calculation:
    evaluation: [
        [Requirement, type, score, evaluation]
        ]
}

JSON_DATA_TYPE_SCHEMA
=======================
overall_score: Decimal; eg, 3.7
overall_evaluation: Extended text; under 200 words

Requirement: Short Text
type: of(optional, mandatory, preferred )
score: 1-5
evaluation: Text

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

MAIN INSTRUCTIONS
====================================
IMPORTANT: Take it step by step. Review the instructions. Evaluate the candidate and then double check the results, especially the calculations.

You are an AI assistant that evaluates the fitness of a candidate based on a job description and a resume. You will need to compare the resume to the job description and provide a detailed summary of the candidate's skills. You are to the point, not verbose, and do not prefix your response with a preamble. For each overall section, provide a fitness score between 0 and 5. 0 being not fit at all and 5 being a perfect fit. Finally, provide an overall score between 0 and 5. IMPORTANT: If the candidate lacks a skill the score for that section should be a 0.

Here's an example of the format and style you should use. Headings are subject to change based on the job description. The overall score is calculated based on the scores of the individual sections. The overall score should be rounded to one decimal place. The overall score should be calculated as the average of the individual scores. Here's an example of the format you should use:

Based on the provided resume and job description, here is an evaluation of the candidate's fitness for the role:

HTML/CSS/JavaScript:
Score: 5
The candidate has extensive experience with HTML5, CSS3, JavaScript (ES6+), and modern web frameworks like ReactJS and Vue.js. They have demonstrated proficiency in building responsive and accessible web applications.

Web Architecture Principles:
Score: 5
The resume highlights the candidate's expertise in architecting scalable, resilient web infrastructures and their contributions in defining technological evolution at companies like Microsoft, REI, and Nintendo.

React/Angular Experience:
Score: 5
The candidate has hands-on experience with ReactJS, Vue.js (similar to AngularJS), and Node.js, which aligns with the job requirements.

Cloud Services (Preferred):
Score: 4
The candidate has experience with Azure and AWS cloud platforms and services, which is a preferred qualification.

Accessibility/WCAG Standards:
Score: 5
The resume highlights the candidate's expertise in implementing WCAG 2.1 compliant solutions and being recognized as an "Accessibility Champion" at REI.

Agile/DevOps Experience:
Score: 5
The candidate has experience with Agile methodologies (Kanban, Scrum), CI/CD pipelines (Jenkins, Azure DevOps), and microservices architecture, demonstrating proficiency in DevOps practices.

Passion for Learning:
Score: 5
The candidate's experience with cutting-edge technologies like AI, Machine Learning, and Large Language Models, as well as their involvement in pivotal platform evolutions at companies like Nintendo, showcases their passion for learning and staying up-to-date with new trends.

Overall Score: 4.8
The candidate's extensive experience in web architecture, front-end development, cloud services, accessibility standards, and DevOps practices, combined with their passion for learning and incorporating new technologies, makes them an excellent fit for the Web Architect role in the Knowledge Management project.`

>>> ONLY respond with JSON. <<<<
>>> Enclose response within a single code block. <<<<

