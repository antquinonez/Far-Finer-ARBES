# Far Finer Candidate Evaluation System

## Overview

The Far Finer Candidate Evaluation System is a toolkit for evaluating candidates against job descriptions using multiple hiring strategies. This repository contains tools and rule sets that will allow everyone in the hiring process to:
- Evaluate candidate resumes
- Assess role fit
- Summarize resume and extract skill information.

## Goal

To create a set of AI-powered tools, evaluation methods, and hiring strategy rules to evaluate candidates to roles using multiple hiring strategies.

## Features

- Tools for analyzing job descriptions and candidate profiles
- Multiple evaluation strategies to consider different hiring perspectives
- Resources for both hiring professionals and job seekers

## Use Cases

### Basic Use Cases

1. **Candidate Evaluation**: 
   - Assess how a person matches a job description
   - Aid in interview preparation

2. **Self Evaluation**: 
   - Allow job seekers to compare their skills to job requirements
   - Identify potential areas for professional development

3. **Resume Summary**: 
   - Summarize resumes with a focus on key skills
   - List relevant certifications and competencies

### Advanced Use Cases

- **Multi-Strategy Hiring Evaluation**: 
  - Evaluate candidates using different hiring approaches
  - Consider various aspects of a candidate's potential fit

## Tools

### Candidate Evaluation Tool - Desktop
This tool runs on your compputer. 
See the `Code/Desktop/dpg` directory for instructions.

### Candidate Evaluation Tool - Airtable

This tool, built on the Airtable platform, addresses all Basic Use Cases.

#### Prerequisites
- Airtable account with Teams license (required for Automations)

#### Setup
Unfortunately, an Airtable tool is not downloadable, and there's a lot of manual setup/configuration. These are just the automation scripts. If you have some experience, you can take a look at these scripts and get an idea. 

## Rules
Published in the form of rulesets in various formats (JSON, CSV, etc)
See `Rules`

### Candidate Evaluation Rules
A very large set of evaluation rules. Will provide scores, roles a candidate may be qualified for, suggestions for improvements.

#### Usage

##### Chatbot
1) Attach the CSV or JSON ruleset to the prompt
2) Attach a resume.
3) Ask for an evaluation.
4) Optionally: See the prompts folder for a comprehensive prompt that outputs data as JSON.

##### API
1) Include the rule set in the system instructions, preferrably using an AI API that uses caching. See the FFAnthropicCached class in my [Far Finer AI Clients Library](https://github.com/antquinonez/Far-Finer-AI-Clients), 

### Hiring Strategy Rules
A set of hiring strategies. Lesson: There's more than one way to hire someone.

##### Chatbot
1) Attach the CSV or JSON ruleset to the prompt
2) Attach one more more resumes.
3) Ask for an evaluation using one, more, or all strategies

##### API
1) Include the rule set in the system instructions, preferrably using an AI API that uses caching. See the FFAnthropicCached class in my [Far Finer AI Clients Library](https://github.com/antquinonez/Far-Finer-AI-Clients).
2) See the `Prompt Templates` folder for prompts. I reccomend you run the strategies one at a time. So, for example, create the AI client with the system instructions and strategies. Include the candidate data (preferrably the resulting JSON from the FF Candidate Evaluation Rules) as JSONL strings for efficient prompt space utilization. Then ask for an evaluation of Strategy X. Repeat with the other strategies that you need. or ask for all of them at once. You get longer responses from doing one at a time though.  

## Future Development

Additional tools are in development and will be added to this repository as they become available.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
