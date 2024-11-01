// Airtable configuration
const AIRTABLE_TABLE_NAME = 'Candidates';
const AIRTABLE_ACCESS_TOKEN = 'XXXXXXX';
const AIRTABLE_BASE_ID = 'XXXXXXX';
const AIRTABLE_CANDIDATE_FIELD_NAME = 'Candidate Name';
const AIRTABLE_SKILL_FIELD_NAME = 'Skill Summary Final';
const AIRTABLE_DESTINATION_TABLE_NAME = 'Candidate Skills';

// Function to fetch all existing skills for a candidate
async function fetchExistingSkillsForCandidate(candidateId) {
  try {
    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_DESTINATION_TABLE_NAME}?filterByFormula={candidate_id}='${candidateId}'`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Error fetching existing skills: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const existingSkills = data.records.map(record => record.fields.Skill);
    console.log(`Found ${existingSkills.length} existing skills for candidate ${candidateId} in the "Candidate Skills" table`);
    console.log('Existing skills:', existingSkills);
    
    return existingSkills;
  } catch (error) {
    console.error('Error fetching existing skills:', error);
    throw error;
  }
}

// Function to check if a skill already exists for a candidate
async function skillExistsForCandidate(candidateId, skill) {
  console.log(`Checking if skill "${skill}" exists for candidate ${candidateId}`);
  try {
    // Encode the skill parameter to ensure special characters are correctly handled
    const encodedSkill = encodeURIComponent(skill);
    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_DESTINATION_TABLE_NAME}?filterByFormula=AND({candidate_id}='${candidateId}',{Skill}='${encodedSkill}')`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Error checking skill existence: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('skillInfo:', data);

    if (data.records.length > 0) {
      console.log(`Skill "${skill}" already exists for candidate ${candidateId}`);
      return true;
    }
    console.log(`Skill "${skill}" does not exist for candidate ${candidateId}`);
  } catch (error) {
    console.error('Error checking skill existence:', error);
    throw error;
  }
}


// Function to create a record in the "Candidate Skills" table
async function createCandidateSkillRecords(candidateId, skills) {
  try {
    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_DESTINATION_TABLE_NAME}`;
    const records = skills.map(skill => ({
      fields: {
        Candidate: [candidateId],
        Skill: skill,
      },
    }));
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ records }),
    });

    if (!response.ok) {
      throw new Error(`Error creating candidate skill records: ${response.status} ${response.statusText}`);
    }
    console.log(`Created ${skills.length} skill records for candidate ${candidateId}`);
  } catch (error) {
    console.error('Error creating candidate skill records:', error);
    throw error;
  }
}

// Function to process skills for a candidate
async function processSkills(candidateId, skillSummary) {
  if (skillSummary) {
    const skills = skillSummary.split(/[,\n]/).map(skill => skill.trim());
    const skillsToCreate = [];

    for (const skill of skills) {
      if (skill !== '') {
        const colonIndex = skill.indexOf(':');
        const processedSkill = colonIndex !== -1 ? skill.slice(colonIndex + 1).trim() : skill;

        const exists = await skillExistsForCandidate(candidateId, processedSkill);
        if (!exists) {
          skillsToCreate.push(processedSkill);
        } else {
          console.log(`Skill already exists for candidate ${candidateId}: ${processedSkill}`);
        }
      }
    }

    // Create records in batches of up to 10 (Airtable's limit per request)
    for (let i = 0; i < skillsToCreate.length; i += 10) {
      const batch = skillsToCreate.slice(i, i + 10);
      await createCandidateSkillRecords(candidateId, batch);
    }
  }
}

// Function to fetch candidate data from Airtable
async function fetchCandidateData(candidateId) {
  try {
    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_TABLE_NAME}/${candidateId}`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${AIRTABLE_ACCESS_TOKEN}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Error fetching candidate data: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.fields[AIRTABLE_SKILL_FIELD_NAME];
  } catch (error) {
    console.error('Error fetching candidate data:', error);
    throw error;
  }
}

// Main function to process a candidate
async function processCandidate(candidateId) {
  try {
    console.log(`Processing candidate: ${candidateId}`);
    const skillSummary = await fetchCandidateData(candidateId);

    const existingSkills = await fetchExistingSkillsForCandidate(candidateId);
    console.log('Existing skills:', existingSkills);
    
    await processSkills(candidateId, skillSummary);
    console.log(`Finished processing candidate: ${candidateId}`);
  } catch (error) {
    console.error(`Error processing candidate: ${candidateId}`, error);
  }
}

// Get the record ID from the automation setup
let inputConfig = input.config();
let recordId = inputConfig['airTableRecordId'];

// Process the candidate
await processCandidate(recordId);

// Output a success message
console.log('Candidate skills processed successfully.');