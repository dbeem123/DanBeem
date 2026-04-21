const ISSUE_MATCHER = /issue|problem|concern|complaint|delayed|cold|pain|unsafe|neglect|abuse/i;
const RESIDENT_MATCHER = /resident|they said|she said|he said|feels|wants|requested|reported/i;
const ACTION_MATCHER = /ombudsman|called|spoke|interviewed|followed up|observed|reviewed|met with|contacted/i;

function splitSentences(input) {
  return (input || '')
    .split(/[\n.!?]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function findFirstMatch(sentences, matcher) {
  return sentences.find((sentence) => matcher.test(sentence)) || '';
}

function extractFieldsFromScenario(scenarioText) {
  const cleanText = (scenarioText || '').trim();
  const sentences = splitSentences(cleanText);

  const problemDescription = findFirstMatch(sentences, ISSUE_MATCHER) || sentences[0] || '';
  const residentPerspective = findFirstMatch(sentences, RESIDENT_MATCHER) || '';
  const actionsTaken = findFirstMatch(sentences, ACTION_MATCHER) || '';

  return {
    problem_description: problemDescription,
    resident_perspective: residentPerspective,
    actions_taken: actionsTaken
  };
}

function buildDraftFieldSet(userFields = {}) {
  return {
    complainant_type: 'Resident/Representative (Draft Only)',
    identity_permission: 'pending confirmation (Draft Only)',
    problem_description: userFields.problem_description || 'Problem description not yet documented (Draft Only).',
    complainant_actions_taken: 'Prior steps not yet documented (Draft Only).',
    resident_perspective: userFields.resident_perspective || 'Resident perspective not yet documented (Draft Only).',
    resident_desired_outcome: 'Desired outcome not yet documented (Draft Only).',
    initial_plan_of_action: 'Initial plan not yet documented (Draft Only).',
    actions_taken: userFields.actions_taken || 'Actions taken not yet documented (Draft Only).',
    facility_response: 'Facility response not yet documented (Draft Only).',
    follow_up: 'Follow-up plan not yet documented (Draft Only).',
    case_status: 'open (Draft Only)',
    case_closed: false,
    resident_satisfaction: 'not yet documented (Draft Only)'
  };
}

function renderTemplate(template, fields) {
  return template.replace(/\{(\w+)\}/g, (_, key) => fields[key] ?? `{${key}}`);
}

function renderCaseNoteFromTemplates(templatesJson, userFields = {}) {
  const fields = buildDraftFieldSet(userFields);
  const sectionOrder = templatesJson.sections || [];
  const templates = templatesJson.templates || {};

  const outputSections = sectionOrder.map((sectionKey) => {
    const section = templates[sectionKey];
    if (!section) return '';

    const lines = (section.sentences || []).map((sentenceDef) => renderTemplate(sentenceDef.template, fields));
    return `${section.header}\n${lines.join('\n')}`;
  });

  return {
    fields,
    draftText: outputSections.filter(Boolean).join('\n\n')
  };
}

function buildCaseNote(templatesJson, scenarioText) {
  const extractedFields = extractFieldsFromScenario(scenarioText);
  return renderCaseNoteFromTemplates(templatesJson, extractedFields);
}

export { extractFieldsFromScenario, renderCaseNoteFromTemplates, buildCaseNote };
