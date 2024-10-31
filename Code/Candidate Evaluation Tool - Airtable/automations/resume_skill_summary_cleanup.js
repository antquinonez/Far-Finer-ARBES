// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidates';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';
const AIRTABLE_INPUT_FIELD_NAME = 'Skill Summary';
const AIRTABLE_OUTPUT_FIELD_NAME = 'Skill Summary Final';

/**
 * Cleans up and organizes lists of category items.
 * @param {string} input - The input text containing category items.
 * @returns {string} The cleaned up and organized text.
 */
function cleanUpCategoryItems(input) {
  const lines = input.split('\n');
  const cleanedLines = lines.filter(line => line.trim() !== '' && line.includes(':') && line.split(':')[1].trim() !== '');
  return cleanedLines.join('\n\n');
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
          [AIRTABLE_OUTPUT_FIELD_NAME]: summary,
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

    if (!record.fields || !record.fields[AIRTABLE_INPUT_FIELD_NAME]) {
      console.error(`The '${AIRTABLE_INPUT_FIELD_NAME}' field is missing or empty.`);
      return;
    }

    const resumeText = record.fields[AIRTABLE_INPUT_FIELD_NAME];
    console.log(`Resume text found: ${resumeText}`);

    const summary = cleanUpCategoryItems(resumeText);
    console.log(`Cleaned up summary: ${summary}`);

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