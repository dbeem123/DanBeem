    let assistantData = null;

    const dataFiles = {
      templates: ['../narrative_templates.json', '../data/case_note_templates.json'],
      validationRules: ['../narrative_validation_rules.json', '../data/case_note_validation_rules.json']
    };

    const crosswalkPaths = {
      norsHierarchy: ['../nors_hierarchy.json', '../data/nors_hierarchy.json'],
      keywordMap: ['../keyword_map.json', '../data/keyword_map.json'],
      norsToTopic: ['../nors_to_topic.json', '../data/nors_to_topic.json'],
      topicToAuthority: ['../topic_to_authority.json', '../data/topic_to_authority.json'],
      authorityIndex: ['../authority_index.json', '../data/reference_source_index.json'],
      retrievalRules: ['../retrieval_rules.json', '../data/retrieval_rules.json']
    };

    const fieldIds = {
      complainant_type: 'complainant-type',
      identity_permission: 'identity-permission',
      problem_description: 'problem-description',
      complainant_actions_taken: 'complainant-actions-taken',
      authorization_note: 'authorization-note',
      resident_perspective: 'resident-perspective',
      resident_desired_outcome: 'resident-desired-outcome',
      initial_plan_of_action: 'initial-plan-of-action',
      actions_taken: 'actions-taken',
      facility_response: 'facility-response',
      follow_up: 'follow-up',
      case_status: 'case-status',
      resident_satisfaction: 'resident-satisfaction',
      concern_area: 'concern-area',
      resident_right: 'resident-right',
      status_or_outcome: 'status-or-outcome'
    };

    async function loadJsonFile(paths, keyName) {
      const candidates = Array.isArray(paths) ? paths : [paths];
      const errors = [];

      for (const path of candidates) {
        try {
          const response = await fetch(path);
          if (!response.ok) {
            console.warn(`[drafting-assistant] Failed to load ${keyName || 'data'} from ${path} (HTTP ${response.status})`);
            errors.push(`${path} returned HTTP ${response.status}`);
            continue;
          }
          const payload = await response.json();
          console.info(`[drafting-assistant] Loaded ${keyName || 'data'} from ${path}`);
          return payload;
        } catch (err) {
          console.warn(`[drafting-assistant] Failed to load ${keyName || 'data'} from ${path}: ${err.message}`);
          errors.push(`${path}: ${err.message}`);
        }
      }

      console.error(`[drafting-assistant] Could not load ${keyName || 'data'} from any path`, candidates);
      throw new Error(errors.join('; '));
    }

    async function loadData() {
      const status = document.getElementById('load-status');
      const generateButton = document.getElementById('generate-button');
      status.style.display = 'block';
      status.className = 'notice';
      status.textContent = 'Loading assistant data...';

      try {
        if (!window.Crosswalk) throw new Error('Shared crosswalk logic did not load.');
        const [entries, crosswalkData] = await Promise.all([
          Promise.all(Object.entries(dataFiles).map(async ([key, path]) => {
            return [key, await loadJsonFile(path, key)];
          })),
          Crosswalk.loadCrosswalkData(crosswalkPaths)
        ]);

        assistantData = { ...Object.fromEntries(entries), ...crosswalkData };
        status.style.display = 'none';
        generateButton.disabled = false;
        populateMainNorsOptions();
        populateCrosswalkOptions();
        bindNorsGuidanceHandlers();
        bindCrosswalkHandler();
        bindPhase0Controls();
        await loadSyntheticScenarios();
      } catch (err) {
        assistantData = null;
        status.style.display = 'block';
        status.className = 'notice error';
        status.textContent = `Assistant data could not be loaded. Please run this page from a local web server and confirm the JSON files are present. Details: ${err.message}`;
        generateButton.disabled = true;
      }
    }

    function getFormData() {
      const formData = {};
      Object.entries(fieldIds).forEach(([field, id]) => {
        formData[field] = document.getElementById(id).value.trim();
      });
      formData.nors_code = document.getElementById('nors-code').value.trim();
      formData.case_closed = formData.case_status.toLowerCase() === 'closed';
      return formData;
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function getNorsOptionHtml(emptyLabel) {
      const groups = Crosswalk.getNorsCodeOptions(assistantData);
      if (!groups.length) {
        return `<option value="">${escapeHtml(emptyLabel)}</option>`;
      }

      return `<option value="">${escapeHtml(emptyLabel)}</option>` + groups.map(group => {
        const groupLabel = `${group.code} - ${group.label}`;
        return `
          <optgroup label="${escapeHtml(groupLabel)}">
            ${group.minorCodes.map(minor => {
              const label = `${minor.code} - ${minor.label}`;
              return `<option value="${escapeHtml(minor.code)}" title="${escapeHtml(minor.description || label)}">${escapeHtml(label)}</option>`;
            }).join('')}
          </optgroup>
        `;
      }).join('');
    }

    function populateMainNorsOptions() {
      const select = document.getElementById('nors-code');
      if (!select) return;
      select.innerHTML = getNorsOptionHtml('No NORS code selected');
    }

    function populateCrosswalkOptions() {
      const select = document.getElementById('norsCodeSelect');
      if (!select) return;

      select.innerHTML = getNorsOptionHtml('Select NORS code');
    }

    function renderNorsCodeGuidance(selectId, outputId) {
      const select = document.getElementById(selectId);
      const output = document.getElementById(outputId);
      const detail = select && assistantData ? Crosswalk.getNorsCodeDetail(select.value, assistantData) : null;

      if (!output) return;
      if (!detail) {
        output.style.display = 'none';
        output.innerHTML = '';
        return;
      }

      const examples = Array.isArray(detail.examples) ? detail.examples : [];
      output.style.display = 'block';
      output.innerHTML = `
        <strong>${escapeHtml(detail.code)} - ${escapeHtml(detail.label)}</strong>
        <div class="subtle">${escapeHtml(detail.majorCode)} - ${escapeHtml(detail.majorLabel)}</div>
        ${detail.definition ? `<p><strong>Definition, Examples &amp; Reporting Tips:</strong><br>${escapeHtml(detail.definition)}</p>` : ''}
        ${detail.useWhen ? `<p><strong>Use when:</strong><br>${escapeHtml(detail.useWhen)}</p>` : ''}
        ${detail.likelyPhrases && detail.likelyPhrases.length ? `<p><strong>Likely phrases:</strong><br>${detail.likelyPhrases.map(escapeHtml).join(', ')}</p>` : ''}
        ${detail.doNotUseWhen ? `<p><strong>Do not use when:</strong><br>${escapeHtml(detail.doNotUseWhen)}</p>` : ''}
        ${detail.humanReview ? `<p><strong>Human review note:</strong><br>${escapeHtml(detail.humanReview)}</p>` : ''}
        ${examples.length ? `<p><strong>Examples:</strong><br>${examples.map(escapeHtml).join('<br>')}</p>` : ''}
        ${detail.reportingTips ? `<p><strong>Examples and Reporting Tips:</strong><br>${escapeHtml(detail.reportingTips)}</p>` : ''}
        <div class="subtle">Source: ${escapeHtml(detail.source || 'NORS Table 2 complaint code guidance')}. Informational only.</div>
      `;
    }

    function bindNorsGuidanceHandlers() {
      const mainSelect = document.getElementById('nors-code');
      const crosswalkSelect = document.getElementById('norsCodeSelect');

      if (mainSelect && mainSelect.dataset.guidanceBound !== 'true') {
        mainSelect.addEventListener('change', () => renderNorsCodeGuidance('nors-code', 'nors-code-guidance'));
        mainSelect.dataset.guidanceBound = 'true';
      }
      if (crosswalkSelect && crosswalkSelect.dataset.guidanceBound !== 'true') {
        crosswalkSelect.addEventListener('change', () => renderNorsCodeGuidance('norsCodeSelect', 'crosswalk-code-guidance'));
        crosswalkSelect.dataset.guidanceBound = 'true';
      }
    }

    function bindCrosswalkHandler() {
      const button = document.getElementById('runCrosswalkBtn');
      const keywordButton = document.getElementById('runKeywordCrosswalkBtn');
      if (button && button.dataset.bound !== 'true') {
        button.addEventListener('click', runCrosswalk);
        button.dataset.bound = 'true';
      }
      if (keywordButton && keywordButton.dataset.bound !== 'true') {
        keywordButton.addEventListener('click', runKeywordCrosswalk);
        keywordButton.dataset.bound = 'true';
      }
    }

    function showCrosswalkInputWarning(message) {
      const output = document.getElementById('crosswalk-input-warning');
      if (!output) return;
      if (!message) {
        output.style.display = 'none';
        output.textContent = '';
        return;
      }
      output.style.display = 'block';
      output.textContent = message;
    }

    function renderCrosswalkTestResult(result, selectedLabel) {
      const output = document.getElementById('crosswalkResult');
      const topics = result.topicMatches.map(match => match.topic);
      const authorityRows = result.authorityGroups.flatMap(group => group.authorities);
      const authorityIds = authorityRows.map(authority => authority.id);

      if (!topics.length) {
        output.innerHTML = `
          <div class="notice">Informational Only: no mapped topics were found for ${escapeHtml(selectedLabel)}.</div>
          <p><strong>Crosswalk Trace:</strong></p>
          <ul class="result-list">${result.trace.map(item => `<li>${renderTraceItem(item)}</li>`).join('')}</ul>
        `;
        return;
      }

      output.innerHTML = `
        <div class="notice">Informational Only: this crosswalk surfaces possible references only. It does not make findings or make legal conclusions.</div>
        <p>These references are informational only and were surfaced through the shared topic mapping.</p>
        <p><strong>Lookup:</strong> ${escapeHtml(selectedLabel)}</p>
        <p><strong>Mapped Topic(s):</strong> ${topics.map(escapeHtml).join(', ')}</p>
        <p><strong>Matched Authority ID(s):</strong> ${authorityIds.length ? authorityIds.map(escapeHtml).join(', ') : 'None found'}</p>
        <p><strong>Matched Citations / Authorities:</strong></p>
        <ul class="result-list">
          ${authorityRows.length ? authorityRows.map(row => `
            <li>
              <strong>${renderAuthorityLink(row)}</strong>
              <br><span>${escapeHtml(row.title)}</span>
              <br><span class="subtle">Authority ID: ${escapeHtml(row.id)}</span>
              <br><span class="subtle">Category / Type: ${escapeHtml(row.category || row.label)}</span>
              <br><span class="subtle">Why selected: ${escapeHtml(row.reason)}</span>
            </li>
          `).join('') : '<li>No authorities found for mapped topic(s).</li>'}
        </ul>
        <p><strong>Crosswalk Trace:</strong></p>
        <ul class="result-list">
          ${result.trace.map(item => `<li>${renderTraceItem(item)}</li>`).join('')}
        </ul>
      `;
    }

    function runCrosswalk() {
      const output = document.getElementById('crosswalkResult');
      const code = document.getElementById('norsCodeSelect').value;

      if (!assistantData) {
        output.innerHTML = '<div class="notice error">Assistant data is not loaded yet, so the crosswalk cannot run.</div>';
        return;
      }

      if (!code) {
        showCrosswalkInputWarning('Select a NORS code before running NORS code lookup.');
        return;
      }

      showCrosswalkInputWarning('');
      const result = Crosswalk.runCrosswalk({ norsCode: code, keywordText: '' }, assistantData);
      renderCrosswalkTestResult(result, `NORS code ${code}`);
    }

    function runKeywordCrosswalk() {
      const output = document.getElementById('crosswalkResult');
      const keywordText = document.getElementById('crosswalkKeywordText').value.trim();

      if (!assistantData) {
        output.innerHTML = '<div class="notice error">Assistant data is not loaded yet, so the crosswalk cannot run.</div>';
        return;
      }

      if (!keywordText) {
        showCrosswalkInputWarning('Enter a keyword or concern before running keyword lookup.');
        return;
      }

      showCrosswalkInputWarning('');
      const result = Crosswalk.runCrosswalk({ norsCode: '', keywordText }, assistantData);
      renderCrosswalkTestResult(result, `keyword / concern "${keywordText}"`);
    }

    function normalizeScenarioText(text) {
      return text
        .replace(/\r/g, '\n')
        .split(/\n+|(?<=[.!?])\s+|;|\s+-\s+|\s+\|\s+/)
        .map(sentence => sentence.trim())
        .filter(Boolean);
    }

    function scoreSentence(sentence, rules) {
      return rules.reduce((score, rule) => {
        return rule.pattern.test(sentence) ? score + rule.weight : score;
      }, 0);
    }

    function choosePrimaryField(sentence, classifiers, fieldPriority) {
      const scores = fieldPriority.map(field => ({
        field,
        score: scoreSentence(sentence, classifiers[field])
      }));
      const best = scores.sort((a, b) => b.score - a.score)[0];
      return best && best.score >= 3 ? best.field : '';
    }

    function appendUnique(target, sentence) {
      if (!sentence) return;
      if (!target.includes(sentence)) target.push(sentence);
    }

    function extractFieldsFromScenario(text) {
      const sentences = normalizeScenarioText(text);
      const extracted = {
        problem_description: [],
        resident_perspective: [],
        resident_desired_outcome: [],
        complainant_actions_taken: [],
        actions_taken: [],
        facility_response: [],
        follow_up: [],
        authorization_note: [],
        status_or_outcome: []
      };

      const classifiers = {
        resident_desired_outcome: [
          { pattern: /\b(resident|she|he|they|caller|complainant)\b.*\b(would like|wants|prefers|does not want|doesn't want|would prefer|is requesting|requested|goal is|desired outcome)\b/i, weight: 7 },
          { pattern: /\b(would like|wants|prefers|does not want|doesn't want|would prefer|is requesting|requested|goal is|desired outcome)\b/i, weight: 5 }
        ],
        authorization_note: [
          { pattern: /\b(authori[sz]ed|authori[sz]es|authorization|gave permission|permission to|consent(?:ed)?|okay to share|may disclose|may discuss)\b/i, weight: 8 },
          { pattern: /\b(asked|wants|requested)\s+(the\s+)?ombudsman\s+to\b/i, weight: 7 }
        ],
        follow_up: [
          { pattern: /\b(ombudsman|program|staff|worker)\b.*\b(plans to follow up|will follow up|will contact|will call|next step|next steps|check back|revisit|monitor)\b/i, weight: 8 },
          { pattern: /\b(plans to follow up|will follow up|will contact|will call|next step|next steps|check back|revisit|monitor)\b/i, weight: 6 },
          { pattern: /\b(tomorrow|next week|within \d+|in \d+ days|by friday|by monday)\b/i, weight: 2 }
        ],
        status_or_outcome: [
          { pattern: /\b(resolved|partially resolved|unresolved|closed|remains open|case remains open|outcome|status|resident satisfied|resident not satisfied|satisfied with)\b/i, weight: 7 }
        ],
        facility_response: [
          { pattern: /\b(facility|administrator|director of nursing|don|staff)\b.*\b(stated|said|reported|responded|agreed|denied|explained|indicated)\b/i, weight: 7 },
          { pattern: /\bfacility response\b/i, weight: 7 }
        ],
        complainant_actions_taken: [
          { pattern: /\b(resident|complainant|family|daughter|son|caller|she|he|they)\b.*\b(has not yet raised|has not raised|have not raised|not yet raised|already told|previously told|spoke with|spoke to|reported to|told the nurse|called the facility|filed a grievance|asked staff)\b/i, weight: 8 },
          { pattern: /\b(has not yet raised|has not raised|have not raised|not yet raised|already told|previously told|spoke with|spoke to|reported to|told the nurse|called the facility|filed a grievance|asked staff)\b/i, weight: 7 },
          { pattern: /\b(before calling|prior to|earlier|already|previously)\b/i, weight: 2 }
        ],
        resident_perspective: [
          { pattern: /\b(resident reports|resident states|resident stated|resident said|resident says|resident feels|resident described|according to the resident|according to resident)\b/i, weight: 6 },
          { pattern: /\b(feels|felt|embarrassed|uncomfortable|worried|afraid|upset|frustrated|concerned|typically|usually)\b/i, weight: 5 }
        ],
        actions_taken: [
          { pattern: /\b(ombudsman interviewed|ombudsman observed|ombudsman reviewed|ombudsman contacted|ombudsman called|ombudsman visited|interviewed resident|observed|reviewed records|contacted staff|documented|visited resident|spoke with resident|spoke with facility)\b/i, weight: 5 }
        ],
        problem_description: [
          { pattern: /\b(did not assist|didn't assist|not answered|was not answered|were not answered|not provided|was not provided|were not provided|missed|delayed|late|ignored|refused|unanswered)\b/i, weight: 7 },
          { pattern: /\b(call light|medication|food|meal|staffing|pain|toileting|hygiene|fall|injury|discharge notice|transfer notice)\b/i, weight: 3 },
          { pattern: /\b(problem|concern|complaint|issue|alleges)\b/i, weight: 2 }
        ]
      };

      const fieldPriority = [
        'resident_desired_outcome',
        'authorization_note',
        'follow_up',
        'status_or_outcome',
        'facility_response',
        'complainant_actions_taken',
        'resident_perspective',
        'actions_taken',
        'problem_description'
      ];

      sentences.forEach(sentence => {
        const field = choosePrimaryField(sentence, classifiers, fieldPriority);
        if (field) {
          appendUnique(extracted[field], sentence);
        }
      });

      return {
        problem_description: extracted.problem_description.join('\n'),
        resident_perspective: extracted.resident_perspective.join('\n'),
        resident_desired_outcome: extracted.resident_desired_outcome.join('\n'),
        complainant_actions_taken: extracted.complainant_actions_taken.join('\n'),
        actions_taken: extracted.actions_taken.join('\n'),
        facility_response: extracted.facility_response.join('\n'),
        follow_up: extracted.follow_up.join('\n'),
        authorization_note: extracted.authorization_note.join('\n'),
        status_or_outcome: extracted.status_or_outcome.join('\n')
      };
    }

    function setFieldIfEmpty(fieldName, value) {
      const id = fieldIds[fieldName];
      const element = id ? document.getElementById(id) : null;
      if (!element || element.value.trim() || !value) return false;
      element.value = value;
      return true;
    }

    function extractScenarioFields() {
      const scenarioText = document.getElementById('scenario-notes').value.trim();
      const notice = document.getElementById('scenario-extract-notice');

      if (!scenarioText) {
        notice.style.display = 'block';
        notice.className = 'notice warning';
        notice.textContent = 'Enter invented example notes before extracting fields.';
        return;
      }

      const extracted = extractFieldsFromScenario(scenarioText);
      const changed = [
        setFieldIfEmpty('problem_description', extracted.problem_description),
        setFieldIfEmpty('complainant_actions_taken', extracted.complainant_actions_taken),
        setFieldIfEmpty('actions_taken', extracted.actions_taken),
        setFieldIfEmpty('facility_response', extracted.facility_response),
        setFieldIfEmpty('follow_up', extracted.follow_up),
      ].some(Boolean);

      notice.style.display = 'block';
      notice.className = 'notice';
      notice.textContent = changed
        ? 'Draft fields were populated from your invented text. Check each field before use.'
        : 'No empty target fields were updated. Existing field values were preserved.';

      if (assistantData) {
        const formData = getFormData();
        const crosswalkResult = runDraftCrosswalk(formData);
        renderInlineCrosswalk(crosswalkResult);
        renderOrganizedSections(formData);
        renderChecklistReview(formData);
        renderTopics(crosswalkResult.topicMatches);
        renderTopicReasons(crosswalkResult.topicMatches);
        renderReferences(retrieveReferences(crosswalkResult), crosswalkResult.topicMatches);
      }
    }

    function buildCrosswalkKeywordText(formData) {
      return [
        document.getElementById('scenario-notes').value.trim(),
        formData.problem_description,
        formData.initial_plan_of_action,
        formData.complainant_actions_taken,
        formData.resident_perspective,
        formData.resident_desired_outcome,
        formData.actions_taken,
        formData.facility_response,
        formData.follow_up,
        formData.authorization_note,
        formData.concern_area,
        formData.resident_right,
        formData.status_or_outcome
      ].join(' ');
    }

    function runDraftCrosswalk(formData) {
      return Crosswalk.runCrosswalk({
        norsCode: formData.nors_code,
        keywordText: buildCrosswalkKeywordText(formData)
      }, assistantData);
    }

    function renderInlineCrosswalk(crosswalkResult) {
      const topicsOutput = document.getElementById('inline-topics-output');
      const norsOutput = document.getElementById('inline-nors-output');
      const referencesOutput = document.getElementById('inline-references-output');
      const traceOutput = document.getElementById('inline-trace-output');
      const topicMatches = crosswalkResult.topicMatches || [];
      const authorityGroups = crosswalkResult.authorityGroups || [];
      const trace = crosswalkResult.trace || [];
      const warnings = crosswalkResult.warnings || [];
      const contextTips = crosswalkResult.contextTips || [];

      if (!topicMatches.length) {
        topicsOutput.textContent = 'No likely topics identified yet. Add note details or a NORS code and run Extract Fields.';
        norsOutput.textContent = 'No likely NORS codes identified yet.';
      } else {
        topicsOutput.innerHTML = topicMatches.map(match => `
          <div class="topic-summary">
            <strong>${escapeHtml(formatTopicName(match.topic))}</strong>
            <div class="subtle summary-line">${escapeHtml(getTopicSourceText(match))}</div>
            <span class="match-count">${escapeHtml(getKeywordMatchText(match))}</span>
            ${getLikelyNorsCodeText(match) ? `<div class="subtle summary-line">${escapeHtml(getLikelyNorsCodeText(match))}</div>` : ''}
          </div>
        `).join('');
        renderInlineLikelyNorsCodes(norsOutput, topicMatches);
      }

      if (!authorityGroups.length) {
        referencesOutput.textContent = topicMatches.length
          ? 'No authority mappings found for matched topics.'
          : 'No references to display yet.';
      } else {
        referencesOutput.innerHTML = authorityGroups.map(group => `
          <div class="reference-summary">
            <strong>${escapeHtml(formatTopicName(group.topic))}</strong>
            <ul class="result-list">
              ${getReferenceList(group).map(authority => `
                <li>
                  <strong>${renderAuthorityLink(authority)}</strong>
                  ${authority.title ? `<br><span>${escapeHtml(authority.title)}</span>` : ''}
                  <br><span class="subtle reference-meta">${escapeHtml(getReferenceCategory(authority))}</span>
                  ${authority.authorityLevel ? `<br><span class="subtle">Authority layer: ${escapeHtml(authority.authorityLevel.replace(/_/g, ' '))}</span>` : ''}
                  ${authority.guidanceNote ? `<br><span class="subtle">Guidance note: ${escapeHtml(authority.guidanceNote)}</span>` : ''}
                  ${renderAuthoritySourceLine(authority)}
                  <br><span class="subtle">Why shown: ${escapeHtml(getReferenceReason(authority, group))}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        `).join('');
      }

      const traceHtml = trace.length
        ? `<ul class="result-list">${trace.map(item => `<li>${renderTraceItem(item)}</li>`).join('')}</ul>`
        : 'No trace generated yet.';
      const warningHtml = warnings.length
        ? `<div class="notice warning" style="margin-top:12px;"><strong>Review caveats</strong><ul class="result-list">${warnings.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`
        : '';
      const tipHtml = contextTips.length
        ? `<div class="notice" style="margin-top:12px;"><strong>Context tips</strong><ul class="result-list">${contextTips.map(item => `<li><strong>${escapeHtml(item.term || item.id || 'Tip')}</strong>${item.short_help ? `<br>${escapeHtml(item.short_help)}` : ''}${item.details ? `<br><span class="subtle">${escapeHtml(item.details)}</span>` : ''}</li>`).join('')}</ul></div>`
        : '';
      traceOutput.innerHTML = `${traceHtml}${tipHtml}${warningHtml}`;
    }

    function fillTemplate(template, formData) {
      return template.replace(/\{([^}]+)\}/g, (match, field) => {
        return String(formData[field] || '').trim();
      });
    }

    function buildNarrative(formData) {
      const config = assistantData.templates;
      const output = [];

      config.sections.forEach(sectionKey => {
        const section = config.templates[sectionKey];
        if (!section) return;

        const sectionStart = output.length;
        section.sentences.forEach(sentence => {
          const values = [...sentence.template.matchAll(/\{([^}]+)\}/g)].map(match => formData[match[1]]);
          const rendered = fillTemplate(sentence.template, formData);
          if (values.length && values.every(value => String(value || '').trim()) && rendered) output.push(rendered);
        });
        if (output.length > sectionStart) output.splice(sectionStart, 0, section.header);
      });

      return output.join('\n').trim();
    }

    function conditionApplies(condition, formData) {
      if (!condition) return true;
      if (condition === 'case_closed == true') return formData.case_closed === true;
      return true;
    }

    function validateNarrative(formData) {
      return (assistantData.validationRules.rules || []).filter(rule => {
        if (!conditionApplies(rule.condition, formData)) return false;
        return !formData[rule.field];
      });
    }

    function getAuthorityLabel(authority) {
      return Crosswalk.getAuthorityLabel(authority);
    }

    function getMatchSummary(match) {
      const parts = [];
      if (match.norsCodes?.length) parts.push(`NORS: ${match.norsCodes.join(', ')}`);
      if (match.keywords?.length) parts.push(`keywords: ${match.keywords.map(keyword => `"${keyword}"`).join(', ')}`);
      return parts.join('; ');
    }

    function formatTopicName(topic) {
      return (topic || '').replace(/_/g, ' ');
    }

    function getTopicSourceText(match) {
      const hasNors = match.norsCodes?.length;
      const hasKeywords = match.keywords?.length;
      if (hasNors && hasKeywords) return 'Source: selected NORS code and note text';
      if (hasNors) return 'Source: selected NORS code';
      if (hasKeywords) return 'Source: note text keywords';
      return 'Matched from local topic rules';
    }

    function getKeywordMatchText(match) {
      const count = match.keywordMatchCount || match.keywords?.length || 0;
      if (!count) return 'Keyword matches: none';
      return `Keyword matches: ${count}`;
    }

    function getAllLikelyNorsCodes(match) {
      return [...new Set([...(match.norsCodes || []), ...(match.likelyNorsCodes || [])])];
    }

    function getLikelyNorsCodeText(match) {
      const codes = getAllLikelyNorsCodes(match);
      if (!codes.length) return '';
      return `Likely NORS code${codes.length === 1 ? '' : 's'}: ${codes.join(', ')}`;
    }

    function renderInlineLikelyNorsCodes(output, topicMatches) {
      const codes = [];
      topicMatches.forEach(match => {
        getAllLikelyNorsCodes(match).forEach(code => {
          if (!codes.some(item => item.code === code)) {
            const detail = Crosswalk.getNorsCodeDetail(code, assistantData);
            const isSelected = (match.norsCodes || []).includes(code);
            codes.push({
              code,
              label: detail?.label || 'Label not available',
              source: isSelected ? 'Selected NORS code' : 'Suggested from note text'
            });
          }
        });
      });

      if (!codes.length) {
        output.textContent = 'No likely NORS codes identified yet.';
        return;
      }

      output.innerHTML = `
        <div class="code-pill-row">
          ${codes.map(item => `
            <span class="code-pill">
              <strong>${escapeHtml(item.code)} - ${escapeHtml(item.label)}</strong>
              <span class="subtle">${escapeHtml(item.source)}</span>
            </span>
          `).join('')}
        </div>
        <div class="notice">Informational only: suggested NORS codes should be reviewed before use.</div>
      `;
    }

    function getTopicSourceDetail(match) {
      const details = [];
      if (match.norsCodes?.length) {
        details.push(`NORS code: ${match.norsCodes.join(', ')}`);
      }
      if (match.likelyNorsCodes?.length) {
        details.push(`Likely NORS code from note text: ${match.likelyNorsCodes.join(', ')}`);
      }
      if (match.keywords?.length) {
        details.push(`Keywords: ${match.keywords.map(keyword => `"${keyword}"`).join(', ')}`);
      }
      return details;
    }

    function getReferenceList(group) {
      return group.authorities || group.references || [];
    }

    function getReferenceCategory(reference) {
      return `Category: ${reference.category || reference.label || 'Reference'}`;
    }

    function getReferenceReason(reference, group) {
      return reference.reason || getMatchSummary(group) || 'Matched through the topic crosswalk.';
    }

    function renderAuthorityLink(authority) {
      const label = escapeHtml(authority.citation || 'Reference');
      if (!authority.url) return label;
      return `<a href="${escapeHtml(authority.url)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    }

    function renderAuthoritySourceLine(authority) {
      const source = authority.sourceInfo;
      if (!source) return '';
      const label = source.title || source.owner || 'Official source';
      const verified = source.lastVerified ? `; verified ${source.lastVerified}` : '';
      const sourceLink = source.url
        ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`
        : escapeHtml(label);
      return `<br><span class="subtle">Source: ${sourceLink}${verified}</span>`;
    }

    function renderTraceItem(item) {
      if (typeof item === 'string') return escapeHtml(item);
      const links = item.links || [];
      const linkHtml = links.length
        ? `<div class="subtle">Official source${links.length === 1 ? '' : 's'}: ${links.map(link => `<a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(link.label || 'source')}</a>`).join(', ')}</div>`
        : '';
      return `${escapeHtml(item.message || '')}${linkHtml}`;
    }

    function retrieveReferences(crosswalkResult) {
      return crosswalkResult.authorityGroups || [];
    }

    function renderValidation(flags) {
      const output = document.getElementById('validation-output');

      if (!flags.length) {
        output.innerHTML = '<div class="notice">No missing required or warning fields were found. Review still required before use.</div>';
        return;
      }

      const items = flags.map(flag => {
        const label = flag.severity === 'error' ? 'Required' : 'Warning';
        return `<li><strong>${label}:</strong> ${flag.message}</li>`;
      }).join('');

      output.innerHTML = `<ul class="result-list">${items}</ul>`;
    }

    function getOrganizedSections(formData) {
      return [
        { field: 'problem_description', label: 'Problem Description' },
        { field: 'resident_perspective', label: 'Resident Perspective' },
        { field: 'complainant_actions_taken', label: 'Complainant / Resident Prior Actions' },
        { field: 'resident_desired_outcome', label: 'Resident Desired Outcome' },
        { field: 'authorization_note', label: 'Authorization Note' },
        { field: 'actions_taken', label: 'Ombudsman Actions' },
        { field: 'facility_response', label: 'Facility Response' },
        { field: 'follow_up', label: 'Follow-up' },
        { field: 'status_or_outcome', label: 'Status or Outcome' }
      ].map(section => ({
        ...section,
        value: formData[section.field] || ''
      }));
    }

    function renderOrganizedSections(formData) {
      const output = document.getElementById('organized-output');
      const sections = getOrganizedSections(formData);
      const present = sections.filter(section => section.value);

      if (!present.length) {
        output.textContent = 'No note fields are entered yet. Load a synthetic example or enter invented facts in the fields below.';
        return;
      }

      output.innerHTML = present.map(section => `
        <div style="margin-bottom:12px;">
          <strong>${escapeHtml(section.label)}</strong>
          <div class="subtle" style="white-space:pre-wrap;">${escapeHtml(section.value)}</div>
        </div>
      `).join('');
    }

    function getChecklistStatus(section, formData) {
      if (section.value) return 'Present';
      if (section.field === 'authorization_note' && formData.identity_permission) return 'Present';
      if (section.field === 'status_or_outcome' && formData.case_status) return 'Present';
      if (section.field === 'problem_description' && !formData.problem_description && !formData.concern_area && !formData.nors_code) return 'Unclear';
      return 'Missing';
    }

    function getChecklistStatusClass(status) {
      if (status === 'Present') return 'status-present';
      if (status === 'Missing') return 'status-missing';
      return 'status-unclear';
    }

    function renderChecklistReview(formData) {
      const output = document.getElementById('checklist-output');
      const sections = getOrganizedSections(formData);

      output.innerHTML = `
        <ul class="result-list">
          ${sections.map(section => {
            const status = getChecklistStatus(section, formData);
            const note = status === 'Missing'
              ? 'Not found in this note; may be acceptable for follow-up or partial notes.'
              : status === 'Unclear'
                ? 'Not enough information to classify from this note.'
                : 'Supported by extracted or structured fields.';
            return `<li><strong>${escapeHtml(section.label)}</strong><span class="status-badge ${getChecklistStatusClass(status)}">${escapeHtml(status)}</span><br><span class="subtle">${escapeHtml(note)}</span></li>`;
          }).join('')}
        </ul>
        <div class="notice">Checklist is informational. The tool does not assume this is an initial intake note, and missing fields are not treated as errors unless existing validation rules flag them.</div>
      `;
    }

    function renderTopics(topicMatches) {
      const output = document.getElementById('topics-output');

      if (!topicMatches.length) {
        output.textContent = 'No likely topics identified yet. Add a NORS code or matching scenario keywords.';
        return;
      }

      output.innerHTML = topicMatches.map(match => `
        <div class="topic-summary">
          <strong>${escapeHtml(formatTopicName(match.topic))}</strong>
          <div class="subtle summary-line">${escapeHtml(getTopicSourceText(match))}</div>
          <span class="match-count">${escapeHtml(getKeywordMatchText(match))}</span>
        </div>
      `).join('');
    }

    function renderTopicReasons(topicMatches) {
      const output = document.getElementById('topic-reasons-output');

      if (!topicMatches.length) {
        output.textContent = 'No match reasons available yet.';
        return;
      }

      output.innerHTML = topicMatches.map(match => `
        <div class="topic-summary">
          <strong>${escapeHtml(formatTopicName(match.topic))}</strong>
          <ul class="result-list">
            ${getTopicSourceDetail(match).map(detail => `<li>${escapeHtml(detail)}</li>`).join('') || '<li>Matched through local topic rules.</li>'}
            <li>${escapeHtml(getKeywordMatchText(match))}</li>
          </ul>
        </div>
      `).join('') + `
      <div class="notice">Informational only: topic matches are surfaced from selected NORS code and/or extracted keywords for drafting support.</div>`;
    }

    function renderReferences(referenceGroups, topicMatches) {
      const output = document.getElementById('references-output');

      if (!referenceGroups.length) {
        output.textContent = topicMatches.length
          ? 'No citation matches were found for the identified topics.'
          : 'No topics identified. Add a NORS code or keywords such as abuse, discharge, rights, call light, medication, food, or staffing.';
        return;
      }

      output.innerHTML = referenceGroups.map(group => `
        <div class="reference-summary">
          <strong>${escapeHtml(formatTopicName(group.topic))}</strong>
          <div class="subtle summary-line">${escapeHtml(getTopicSourceText(group))}</div>
          <ul class="result-list">
            ${getReferenceList(group).map(reference => `
              <li>
                <strong>${renderAuthorityLink(reference)}</strong>
                ${reference.title ? `<br><span>${escapeHtml(reference.title)}</span>` : ''}
                <br><span class="subtle reference-meta">${escapeHtml(getReferenceCategory(reference))}</span>
                ${reference.authorityLevel ? `<br><span class="subtle">Authority layer: ${escapeHtml(reference.authorityLevel.replace(/_/g, ' '))}</span>` : ''}
                ${reference.guidanceNote ? `<br><span class="subtle">Guidance note: ${escapeHtml(reference.guidanceNote)}</span>` : ''}
                <br><span class="subtle">Why shown: ${escapeHtml(getReferenceReason(reference, group))}</span>
              </li>
            `).join('')}
          </ul>
        </div>
      `).join('') + `
      <div class="notice">Informational guardrail: references are shown for drafting support only. CMS Appendix PP/F-tags are interpretive survey guidance tied to federal nursing facility requirements. This tool organizes user-entered fields and published references for human review.</div>`;
    }

    function generateDraft() {
      if (!assistantData) {
        document.getElementById('draft-output').textContent = 'Assistant data is not loaded yet.';
        return;
      }

      const formData = getFormData();
      const narrative = buildNarrative(formData);
      const flags = validateNarrative(formData);
      const crosswalkResult = runDraftCrosswalk(formData);
      const topicMatches = crosswalkResult.topicMatches;
      const references = retrieveReferences(crosswalkResult);

      document.getElementById('draft-output').textContent = `Draft Only\n\n${narrative}\n\nInformational guardrail: This draft is assembled from fields you entered. Human review is required.`;
      renderInlineCrosswalk(crosswalkResult);
      renderValidation(flags);
      renderOrganizedSections(formData);
      renderChecklistReview(formData);
      renderTopics(topicMatches);
      renderTopicReasons(topicMatches);
      renderReferences(references, topicMatches);
    }

    function bindPhase0Controls() {
      document.getElementById('extract-fields-button')?.addEventListener('click', extractScenarioFields);
      document.getElementById('generate-button')?.addEventListener('click', generateDraft);
      document.getElementById('load-synthetic-scenario')?.addEventListener('click', applySyntheticScenario);
    }

    async function loadSyntheticScenarios() {
      const select = document.getElementById('synthetic-scenario');
      if (!select) return;
      const response = await fetch('../data/nors_synthetic_scenarios.json');
      if (!response.ok) throw new Error('Synthetic examples could not be loaded.');
      const examples = await response.json();
      select.innerHTML += examples.map(example => `<option value="${escapeHtml(example.id)}">${escapeHtml(example.label)} (synthetic)</option>`).join('');
      window.norsSyntheticExamples = examples;
    }

    function applySyntheticScenario() {
      const select = document.getElementById('synthetic-scenario');
      const example = (window.norsSyntheticExamples || []).find(item => item.id === select.value);
      const status = document.getElementById('synthetic-load-status');
      if (!example) { status.textContent = 'Choose a synthetic example first.'; return; }
      document.getElementById('scenario-notes').value = example.notes;
      Object.entries(example.fields).forEach(([field, value]) => {
        const id = fieldIds[field];
        const element = id ? document.getElementById(id) : null;
        if (element) element.value = value;
      });
      status.textContent = `${example.label} loaded. Decision and consent fields remain blank.`;
      const formData = getFormData();
      const crosswalkResult = runDraftCrosswalk(formData);
      renderInlineCrosswalk(crosswalkResult);
      renderOrganizedSections(formData);
      renderChecklistReview(formData);
      renderTopics(crosswalkResult.topicMatches);
      renderTopicReasons(crosswalkResult.topicMatches);
      renderReferences(retrieveReferences(crosswalkResult), crosswalkResult.topicMatches);
    }

    document.addEventListener('DOMContentLoaded', loadData);
