// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidates';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';
const AIRTABLE_RESUME_FIELD_NAME = 'Resume';
const AIRTABLE_SUMMARY_FIELD_NAME = 'Resume Feedback';

// Claude API configuration
const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const CLAUDE_API_KEY = 'XXXXXXX';

const CLAUDE_MODEL = 'claude-3-5-sonnet-20240620';
const CLAUDE_API_VERSION = '2023-06-01';
const CLAUDE_MAX_TOKENS = 4000;
const CLAUDE_TEMPERATURE = 0.6;

const SYSTEM_SETUP = 'You are an AI assistant that is deliberate and approaches requests step by step. Before presenting a response, you always double check your work when you provide feedback on resume content. You do not include any extra preamble and immediately address requests.';
const MESSAGE = 'I am an HR professional evaluating the quality of resumes. Please suggest improvements based on this resume text. Do not provide feedback on formatting, but do address overall structure and placement of information. In your evaluation, add a section for grammar and spelling mistakes.';

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