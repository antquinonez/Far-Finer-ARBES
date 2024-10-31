// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidates';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';
const AIRTABLE_RESUME_FIELD_NAME = 'Resume';
const AIRTABLE_SUMMARY_FIELD_NAME = 'Skill Summary';

// Claude API configuration
const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const CLAUDE_API_KEY = 'XXXXXXX';

const CLAUDE_MODEL = 'claude-3-5-sonnet-20240620';
const CLAUDE_API_VERSION = '2023-06-01';
const CLAUDE_MAX_TOKENS = 2000;
const CLAUDE_TEMPERATURE = 0.1;

const SYSTEM_SETUP = 'You are an AI assistant that is deliberate and approaches requests step by step. Before presenting a response, you always double check your work in identifying technologies, tools, skills, programming languages, and certificates, and then categorizing these. You do not include any extra preamble and immedoately address requests. You comma separate items in the list.';
const MESSAGE = `Please extract and categorize the information, such as i have in the FORMAT and EXAMPLE below. Be careful not to invent content not in the resume. Only use the resume as the source for the technologies, tools, skills, programming languages, and certificates.

Additional instructions:
-- Do not invent experience or skills not listed in the resume.
-- Only include skills without a date or with a date within the last 5 years.
-- Consider the context of the technology or tool to determine the category.
-- Do not list a programming language in any section other than Programming Language
-- Do not list a database name in in any section other than Databases.
-- Order the items based on main technology, followed by secondary dependent technologies.
-- Please check the output so that databases and programming languages are not repeated in other items; for example, Python should not be mentioned in 'Front end' or 'Back end'.
-- Additional categories can be added for categories not listed in the EXAMPLE. Name the categories based on the content in the resume.
-- All skills must be categorized.  Use 'Other' as a last resort.
-- For Professional Skills, only include major skills with a broad professional application.
-- Separate categories with an empty line.
-- Order the categories alphabetically but
  -- if it exists, keep the 'Programming Languages' first
  -- if it exists, follow with the 'Databases' category
  -- if they  exist, keep the front end and backend next
  -- keep the 'Certificates', 'Professional Skills', and 'Roles' sections at the end.

FORMAT:
=======
[category1]: [item1], [item2], [item3]

[category2]: [item1], [item2], [item3]
--
Certificates: [certificate1], [certificate2]

Professional Skills: [professional skill1], [professional skill2]

Roles: [role1], [role2]

EXAMPLE
=======
Programming Languages:

Front end:

Back end:

Databases:

Containers and Orchestration:

Dev Tools:

Cloud:

----
Certificates: 

Industries: 

Professional Skills: 

Roles: 
=======
`;

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
 * Generates a summary of a txt resume using the Claude API.
 * @param {string} resumeText - The text of the Resume file to be summarized.
 * @returns {Promise<string>} The summary of the Resume file.
 */
async function generateSummary(resumeText) {
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': CLAUDE_API_KEY,
    'anthropic-version': CLAUDE_API_VERSION,
  };
  const data = {
    system: SYSTEM_SETUP,
    messages: [{
      role: 'user',
      content: `${MESSAGE}:\n\n${resumeText}`,
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

    if (!record.fields || !record.fields[AIRTABLE_RESUME_FIELD_NAME] || record.fields[AIRTABLE_RESUME_FIELD_NAME].length === 0) {
      console.error("The 'resume' field is missing, empty, or does not contain attachments.");
      return;
    }

    const txtResumeURL = record.fields[AIRTABLE_RESUME_FIELD_NAME][0].url;
    console.log(`Txt URL found: ${txtResumeURL}`);

    const resumeText = await fetchResumeText(txtResumeURL);
    const summary = await generateSummary(resumeText);
    console.log(`ResumeSummary: ${summary}`);

    await updateAirtableRecord(recordId, summary);
    console.log('Resume processed successfully.');
  } catch (error) {
    console.error(`Error processing resume: ${error.message}`);
  }
}

// Get the record ID from the automation setup
let inputConfig = input.config();
let recordId = inputConfig['airTableRecordId'];

// Execute the script with the provided record ID
processResume(recordId).then(() => console.log('Operation completed.'));