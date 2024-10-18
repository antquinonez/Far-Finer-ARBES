// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidate Role Options';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';

const AIRTABLE_RESUME_FIELD_NAME = 'Resume (from Candidates)';
const AIRTABLE_JOB_DESCRIPTION_FIELD_NAME = 'JD (from Roles)';

// Destination field
const AIRTABLE_SUMMARY_FIELD_NAME = 'Evaluation - Detailed';

// Claude API configuration
const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const CLAUDE_API_KEY = 'XXXXXXXXXXXXXX';

const CLAUDE_MODEL = 'claude-3-5-sonnet-20240620';
const CLAUDE_API_VERSION = '2023-06-01';
const CLAUDE_MAX_TOKENS = 2000;
const CLAUDE_TEMPERATURE = 0.5;

const SYSTEM_SETUP = `You are an AI assistant that evaluates the fitness of a candidate based on a job description and a resume. You will need to compare the resume to the job description and provide a detailed summary of the candidate's skills. You are to the point, not verbose, and do not prefix your response with a preamble. For each overall section, provide a fitness score between 0 and 5. 0 being not fit at all and 5 being a perfect fit. Finally, provide an overall score between 0 and 5. IMPORTANT: If the candidate lacks a skill the score for that section should be a 0.

Here's an example of the format and style you should use. Headings are subject to change based on the job description. The overall score is calculated based on the scores of the individual sections. The overall score should be rounded to one decimal place. The overall score should be calculated as the average of the individual scores. Here's an example of the format you should use:

Based on the provided resume and job description, here is an evaluation of the candidate's fitness for the role:

HTML/CSS/JavaScript (Must Have):
Score: 5
The candidate has extensive experience with HTML5, CSS3, JavaScript (ES6+), and modern web frameworks like ReactJS and Vue.js. They have demonstrated proficiency in building responsive and accessible web applications.

Web Architecture Principles (Must Have):
Score: 5
The resume highlights the candidate's expertise in architecting scalable, resilient web infrastructures and their contributions in defining technological evolution at companies like Microsoft, REI, and Nintendo.

React/Angular Experience (Must Have):
Score: 5
The candidate has hands-on experience with ReactJS, Vue.js (similar to AngularJS), and Node.js, which aligns with the job requirements.

Cloud Services (Preferred):
Score: 4
The candidate has experience with Azure and AWS cloud platforms and services, which is a preferred qualification.

Accessibility/WCAG Standards (Must Have):
Score: 5
The resume highlights the candidate's expertise in implementing WCAG 2.1 compliant solutions and being recognized as an "Accessibility Champion" at REI.

Agile/DevOps Experience (Must Have):
Score: 5
The candidate has experience with Agile methodologies (Kanban, Scrum), CI/CD pipelines (Jenkins, Azure DevOps), and microservices architecture, demonstrating proficiency in DevOps practices.

Passion for Learning (Must Have):
Score: 5
The candidate's experience with cutting-edge technologies like AI, Machine Learning, and Large Language Models, as well as their involvement in pivotal platform evolutions at companies like Nintendo, showcases their passion for learning and staying up-to-date with new trends.

Overall Score: 4.8
The candidate's extensive experience in web architecture, front-end development, cloud services, accessibility standards, and DevOps practices, combined with their passion for learning and incorporating new technologies, makes them an excellent fit for the Web Architect role in the Knowledge Management project.`;


/**
 * Fetches the resume text from the given URL.
 * @param {string} txtResumeURL - The URL of the txt Resume file.
 * @returns {Promise<string>} The resume text.
 */
async function fetchResumeText(txtResumeURL) {
  const resumeResponse = await fetch(txtResumeURL);
  if (!resumeResponse.ok) {
    throw new Error(`Failed to fetch resume text with status ${resumeResponse.status}`);
  }
  return await resumeResponse.text();
}

/**
 * Fetches the job description text from the given URL.
 * @param {string} jobDescriptionURL - The URL of the job description file.
 * @returns {Promise<string>} The job description text.
 */
async function fetchJobDescriptionText(jobDescriptionURL) {
  const jobDescriptionResponse = await fetch(jobDescriptionURL);
  if (!jobDescriptionResponse.ok) {
    throw new Error(`Failed to fetch job description text with status ${jobDescriptionResponse.status}`);
  }
  return await jobDescriptionResponse.text();
}

/**
 * Generates a summary of a txt resume using the Claude API.
 * @param {string} resumeText - The text of the Resume file to be summarized.
 * @param {string} jobDescriptionText - The text of the Job Description file to be summarized.
 * @returns {Promise<string>} The summary of the Resume file.
 */
async function generateSummary(resumeText, jobDescriptionText) {
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': CLAUDE_API_KEY,
    'anthropic-version': CLAUDE_API_VERSION,
  };
  const data = {
    system: SYSTEM_SETUP,
    messages: [{
      role: 'user',
      content: `Please evaluate this RESUME against the JOB DESCRIPTION on a technology by technology basis.
      
      RESUME:\n\n${resumeText}
      ------------------------
      JOB DESCRIPTION:\n\n${jobDescriptionText}
      `,
    }],
    model: CLAUDE_MODEL,
    max_tokens: CLAUDE_MAX_TOKENS,
    temperature: CLAUDE_TEMPERATURE,
  };

  const response = await fetch(CLAUDE_API_URL, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const responseBody = await response.text();
    throw new Error(`API request failed with status ${response.status}: ${responseBody}`);
  }

  const result = await response.json();
  console.log('Claude API Result:', result);

  if (result.id && result.content && result.content[0].text) {
    return result.content[0].text.trim();
  } else {
    throw new Error('Unexpected response format from Claude API');
  }
}

/**
 * Fetches the Airtable record with the given ID.
 * @param {string} recordId - The ID of the Airtable record.
 * @returns {Promise<object>} The Airtable record.
 */
async function fetchAirtableRecord(recordId) {
  const headers = {
    'Authorization': `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
    'Content-Type': 'application/json',
  };
  const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${encodeURIComponent(AIRTABLE_TABLE_NAME)}/${recordId}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: headers,
  });

  if (!response.ok) {
    const responseBody = await response.text();
    throw new Error(`Airtable request failed with status ${response.status}: ${responseBody}`);
  }

  return await response.json();
}

/**
 * Updates the Airtable record with the given ID and summary.
 * @param {string} recordId - The ID of the Airtable record.
 * @param {string} summary - The summary to be added to the record.
 */
async function updateAirtableRecord(recordId, summary) {
  const updateUrl = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${encodeURIComponent(AIRTABLE_TABLE_NAME)}`;
  const updateHeaders = {
    'Authorization': `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
    'Content-Type': 'application/json',
  };
  const updateData = {
    'records': [
      {
        'id': recordId,
        'fields': {
          [AIRTABLE_SUMMARY_FIELD_NAME]: summary,
        },
      },
    ],
  };

  const updateResponse = await fetch(updateUrl, {
    method: 'PATCH',
    headers: updateHeaders,
    body: JSON.stringify(updateData),
  });

  if (!updateResponse.ok) {
    const updateResponseBody = await updateResponse.text();
    throw new Error(`Airtable update failed with status ${updateResponse.status}: ${updateResponseBody}`);
  }
}

/**
 * Processes a resume by generating a summary and updating the respective Airtable record.
 * @param {string} recordId - The ID of the Airtable record containing the resume.
 */
async function processResume(recordId) {
  try {
    const record = await fetchAirtableRecord(recordId);
    console.log('Record:', record);

    if (!record.fields || !record.fields[AIRTABLE_RESUME_FIELD_NAME] || record.fields[AIRTABLE_RESUME_FIELD_NAME].length === 0) {
      console.error("The 'resume' field is missing, empty, or does not contain attachments.");
      return;
    }

    // GET RESUME
    const txtResumeURL = record.fields[AIRTABLE_RESUME_FIELD_NAME][0].url;
    console.log(`txtResumeURL found: ${txtResumeURL}`);
    const resumeText = await fetchResumeText(txtResumeURL);

    // GET JOB DESCRIPTION
    const jobDescriptionURL = record.fields[AIRTABLE_JOB_DESCRIPTION_FIELD_NAME][0].url;
    console.log(`Job Description URL found: ${jobDescriptionURL}`);
    const jobDescriptionText = await fetchJobDescriptionText(jobDescriptionURL);

    // GENERATE SUMMARY
    const summary = await generateSummary(resumeText, jobDescriptionText);
    console.log(`Summary: ${summary}`);

    // UPDATE AIRTABLE
    await updateAirtableRecord(recordId, summary);
    console.log('Resume processed successfully.');
  } catch (error) {
    console.error(`Error processing resume: ${error.message}`);
  }
}

// Get the record ID from the automation setup
let inputConfig = input.config();
console.log('inputConfig', inputConfig);

let recordId = inputConfig['airTableRecordId'];

// Execute the script with the provided record ID
processResume(recordId).then(() => console.log('Operation completed.'));