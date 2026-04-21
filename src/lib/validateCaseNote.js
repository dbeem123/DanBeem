function isMissing(value) {
  if (!value) return true;

  const normalized = String(value).trim().toLowerCase();
  if (!normalized) return true;

  return normalized.includes('not yet documented');
}

function parseConditionValue(rawValue) {
  const value = rawValue.trim();

  if (value === 'true') return true;
  if (value === 'false') return false;
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }

  if (!Number.isNaN(Number(value)) && value !== '') {
    return Number(value);
  }

  return value;
}

function shouldRunRule(fields, rule) {
  if (!rule.condition) return true;

  const match = rule.condition.match(/^\s*([a-zA-Z0-9_]+)\s*==\s*(.+)\s*$/);
  if (!match) return true;

  const [, fieldName, expectedRaw] = match;
  const expectedValue = parseConditionValue(expectedRaw);

  return fields[fieldName] === expectedValue;
}

function validateCaseNote(fields, validationRulesJson) {
  const rules = validationRulesJson.rules || [];

  return rules
    .filter((rule) => shouldRunRule(fields, rule))
    .filter((rule) => isMissing(fields[rule.field]))
    .map((rule) => ({
      id: rule.id,
      field: rule.field,
      severity: rule.severity || 'warning',
      message: rule.message
    }));
}

export { validateCaseNote };
