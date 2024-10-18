// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidate Role Options';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';

const AIRTABLE_RESUME_FIELD_NAME = 'Resume (from Candidates)';
const AIRTABLE_JOB_DESCRIPTION_FIELD_NAME = 'JD (from Roles)';

// Destination field
const AIRTABLE_SUMMARY_FIELD_NAME = 'Evaluation';

// Claude API configuration
const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const CLAUDE_API_KEY = 'XXXXXXX';

const CLAUDE_API_VERSION = '2023-06-01';
const CLAUDE_MODEL = 'claude-3-5-sonnet-20240620';
const CLAUDE_MAX_TOKENS = 2000;
const CLAUDE_TEMPERATURE = 0.5;

const SYSTEM_SETUP = `You are an AI assistant that evaluates the fitness of a candidate based on a job description and a resume. You will need to compare the resume to the job description and provide a summary of the candidate's skills. Take it step by step.

Here's an example of the format you should use:
====================================================
Based on the provided resume and job description, Zachary Schumpert appears to be a highly qualified candidate for the Web Architect role in the Knowledge Management project. Here's a summary of how his skills and experience align with the job requirements:

1. Years of Experience:
   - The job requires a minimum of 8 years of experience in web architecture and development.
   - Zachary has over 15 years of professional experience, including roles as a Web Architect, Full Stack Developer, and Frontend Developer.

2. Essential Skills:
   - The job requires expertise in HTML, CSS, JavaScript, responsive design frameworks, web architecture principles, and experience with web development frameworks such as AngularJS, ReactJS, and NodeJS.
   - Zachary's technical skills include proficiency in JavaScript (ES6+), HTML5, CSS3, ReactJS, Vue, Node.js, and experience with responsive design frameworks like Bootstrap and TailwindCSS.

3. Cloud and DevOps Experience:
   - The job requires good knowledge of cloud-based services like AWS, Azure (preferred), or Google Cloud Platform, as well as experience with agile methodologies and DevOps/CICD models.
   - Zachary has experience with Azure, AWS, Docker, Kubernetes, and DevOps practices such as CI/CD pipelines (Jenkins, Azure DevOps), Git, and microservices architecture.

4. Additional Relevant Skills:
   - The job description mentions a passion for keeping up with new trends and developments in the programming community.
   - Zachary has demonstrated expertise in AI & Machine Learning, including NLP, ML Models, Large Language Models (ChatGPT, OpenAI), AI Clustering, Semantic Analysis, Prompt Engineering, and Prompt Crafting.
   - He has experience with web accessibility standards (ARIA, WCAG) and web design tools like Figma and Sketch.
   - Zachary has worked with various databases, including CosmosDB, SQL, MongoDB, and NoSQL.
   - He has experience with agile methodologies like Kanban, SCRUM, and TDD.

Overall, Zachary Schumpert's extensive experience as a Web Architect and Full Stack Developer, coupled with his expertise in modern web technologies, cloud platforms, DevOps practices, and AI/ML integration, make him an excellent fit for the Web Architect role in the Knowledge Management project.`;


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
      content: `Please evaluate this RESUME against the JOB DESCRIPTION. The JOB DESCRIPTION is as follows:\n\n${jobDescriptionText}\n\nThe RESUME is as follows:\n\n${resumeText}`,
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