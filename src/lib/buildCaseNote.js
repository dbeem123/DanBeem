function pickSentence(input, matcher) {
  const sentences = input
    .split(/[\n.!?]+/)
    .map((s) => s.trim())
    .filter(Boolean);

  return sentences.find((sentence) => matcher.test(sentence)) || '';
}

function mapScenarioToFields(scenarioText) {
  const clean = (scenarioText || '').trim();

  const problemDescription = pickSentence(clean, /issue|problem|concern|complaint|delayed|cold|pain|unsafe/i) || clean;
  const residentPerspective =
    pickSentence(clean, /resident|they said|she said|he said|feels|wants|requested|reported/i) ||
    'Resident perspective not yet documented (Draft Only).';
  const actionsTaken =
    pickSentence(clean, /ombudsman|called|spoke|interviewed|followed up|observed|reviewed|met with/i) ||
    'Actions taken not yet documented (Draft Only).';

  return {
    complainant_type: 'Resident/Representative (Draft Only)',
    identity_permission: 'pending confirmation (Draft Only)',
    problem_description: problemDescription || 'Problem description not yet documented (Draft Only).',
    complainant_actions_taken: 'Prior steps not yet documented (Draft Only).',
    resident_perspective: residentPerspective,
    resident_desired_outcome: 'Desired outcome not yet documented (Draft Only).',
    initial_plan_of_action: 'Initial plan not yet documented (Draft Only).',
    actions_taken: actionsTaken,
    facility_response: 'Facility response not yet documented (Draft Only).',
    follow_up: 'Follow-up plan not yet documented (Draft Only).',
    case_status: 'open (Draft Only)',
    resident_satisfaction: 'not yet documented (Draft Only)'
  };
}

function renderTemplate(template, fields) {
  return template.replace(/\{(\w+)\}/g, (_, key) => fields[key] ?? `{${key}}`);
}

function buildCaseNote(templatesJson, scenarioText) {
  const fields = mapScenarioToFields(scenarioText);
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

export { buildCaseNote, mapScenarioToFields };
