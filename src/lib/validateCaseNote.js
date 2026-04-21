function isMissing(value) {
  if (!value) return true;

  const normalized = String(value).trim().toLowerCase();
  if (!normalized) return true;

  return normalized.includes('not yet documented');
}

function validateCaseNote(fields, validationRulesJson) {
  const rules = validationRulesJson.rules || [];

  return rules
    .filter((rule) => isMissing(fields[rule.field]))
    .map((rule) => ({
      id: rule.id,
      field: rule.field,
      severity: rule.severity || 'warning',
      message: rule.message
    }));
}

export { validateCaseNote };
