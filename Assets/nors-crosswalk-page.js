    let crosswalkData = null;

    const crosswalkPaths = {
      norsHierarchy: ['../nors_hierarchy.json', '../data/nors_hierarchy.json'],
      keywordMap: ['../keyword_map.json', '../data/keyword_map.json'],
      norsToTopic: '../nors_to_topic.json',
      topicToAuthority: '../topic_to_authority.json',
      authorityIndex: ['../authority_index.json', '../data/reference_source_index.json'],
      retrievalRules: '../retrieval_rules.json'
    };

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function populateNorsCodes() {
      const select = document.getElementById('nors-code');
      const groups = Crosswalk.getNorsCodeOptions(crosswalkData);

      select.innerHTML = '<option value="">No NORS code selected</option>' + groups.map(group => {
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

    function renderNorsCodeGuidance() {
      const select = document.getElementById('nors-code');
      const output = document.getElementById('nors-code-guidance');
      const detail = Crosswalk.getNorsCodeDetail(select.value, crosswalkData);

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

    function formatTopicName(topic) {
      return String(topic || 'topic').replace(/_/g, ' ');
    }

    function getAuthorityList(authorityGroups) {
      return (authorityGroups || []).flatMap(group => group.authorities || []);
    }

    function getMatchedCodeValues(topicMatches) {
      const codes = new Set();
      (topicMatches || []).forEach(match => {
        (match.norsCodes || []).forEach(code => codes.add(code));
        (match.likelyNorsCodes || []).forEach(code => codes.add(code));
      });
      return [...codes].filter(Boolean);
    }

    function getCodeLabel(code) {
      const detail = crosswalkData && window.Crosswalk ? Crosswalk.getNorsCodeDetail(code, crosswalkData) : null;
      return detail ? `${code} - ${detail.label}` : code;
    }

    function renderCodeChip(code, className = '') {
      return `<span class="code-chip ${className}">${escapeHtml(getCodeLabel(code))}</span>`;
    }

    function getAuthoritySectionKey(authority) {
      const level = authority.authorityLevel || '';
      const category = authority.category || authority.label || '';
      if (level === 'regulation') return 'primary';
      if (level === 'interpretive_guidance' || /^F\d{3}$/i.test(authority.citation || '')) return 'appendix';
      if (level === 'state_authority' || level === 'program_authority') return 'localProgram';
      if (/Training/i.test(category)) return 'related';
      return 'related';
    }

    function getAuthoritySections(authorities) {
      const buckets = {
        primary: [],
        appendix: [],
        related: [],
        localProgram: []
      };

      authorities.forEach(authority => {
        buckets[getAuthoritySectionKey(authority)].push(authority);
      });

      return [
        { key: 'primary', label: 'Primary References', authorities: buckets.primary, collapsible: false },
        { key: 'appendix', label: 'Appendix PP / F-tags', authorities: buckets.appendix, collapsible: false },
        { key: 'related', label: 'Additional Context', authorities: buckets.related, collapsible: false },
        { key: 'localProgram', label: 'CT / Program', authorities: buckets.localProgram, collapsible: true }
      ].filter(section => section.authorities.length);
    }

    function renderAuthorityItem(authority) {
      return `
        <div class="authority-item">
          <div class="result-title">
            <strong>${renderAuthorityLink(authority)}</strong>
            <span class="meta-chip">${escapeHtml(authority.category || authority.label || 'Reference')}</span>
          </div>
          <div class="meta-line">${escapeHtml(authority.title || 'Authority reference')}</div>
          <div class="subtle meta-line">Authority ID: ${escapeHtml(authority.id || 'unknown')}</div>
          ${authority.authorityLevel ? `<div class="subtle meta-line">Authority layer: ${escapeHtml(authority.authorityLevel.replace(/_/g, ' '))}</div>` : ''}
          ${authority.guidanceNote ? `<div class="subtle meta-line">Guidance note: ${escapeHtml(authority.guidanceNote)}</div>` : ''}
          ${authority.appendixPpPageStart ? `<div class="subtle meta-line">Appendix PP PDF page: ${escapeHtml(authority.appendixPpPageStart)}</div>` : ''}
          ${renderAuthoritySourceLine(authority)}
          <div class="subtle meta-line">Why selected: ${escapeHtml(authority.reason || 'Mapped to the identified topic.')}</div>
        </div>
      `;
    }

    function renderAuthoritySection(section) {
      if (section.collapsible) {
        return `
          <details class="authority-collapse">
            <summary>
              <span>${escapeHtml(section.label)}</span>
              <span class="authority-collapse-count">${section.authorities.length} reference${section.authorities.length === 1 ? '' : 's'}</span>
            </summary>
            <div class="authority-collapse-body">
              ${section.authorities.map(renderAuthorityItem).join('')}
            </div>
          </details>
        `;
      }

      return `
        <div class="authority-section">
          <div class="authority-section-title">${escapeHtml(section.label)}</div>
          <div>
            ${section.authorities.map(renderAuthorityItem).join('')}
          </div>
        </div>
      `;
    }

    function getAuthorityLayerSummary(authorities) {
      const layers = new Set();
      authorities.forEach(authority => {
        const text = `${authority.citation || ''} ${authority.category || ''} ${authority.authorityLevel || ''}`.toLowerCase();
        if (/appendix|f\d{3}/.test(text)) layers.add('Appendix PP / F-tags');
        if (/42\s*cfr|federal/.test(text)) layers.add('42 CFR');
        if (/45\s*cfr|ombudsman/.test(text)) layers.add('Ombudsman authority');
        if (/\bct\b|connecticut|state statute/.test(text)) layers.add('CT overlay');
      });
      return [...layers];
    }

    function renderSummary(result) {
      const output = document.getElementById('summary-output');
      const topicMatches = result.topicMatches || [];
      const authorities = getAuthorityList(result.authorityGroups || []);
      const codes = getMatchedCodeValues(topicMatches);
      const layers = getAuthorityLayerSummary(authorities);
      const supportCount = (result.relatedInvestigations || []).length + (result.workflowGuidance || []).length + (result.contextTips || []).length + (result.resources || []).length;
      const warningCount = (result.warnings || []).length;
      const codeDisplay = codes.length
        ? codes.slice(0, 5).map(code => escapeHtml(code)).join(', ') + (codes.length > 5 ? ` +${codes.length - 5}` : '')
        : 'No code match';
      const topicDisplay = topicMatches.length
        ? topicMatches.slice(0, 3).map(match => escapeHtml(formatTopicName(match.topic))).join(', ') + (topicMatches.length > 3 ? ` +${topicMatches.length - 3}` : '')
        : 'No topic match';
      const layerDisplay = layers.length ? layers.slice(0, 3).join(', ') + (layers.length > 3 ? ` +${layers.length - 3}` : '') : 'No authority trail';

      output.innerHTML = `
        <div class="summary-card">
          <span class="summary-label">Likely NORS</span>
          <span class="summary-value">${codeDisplay}</span>
          <div class="subtle summary-note">One case may contain multiple distinct complaints.</div>
        </div>
        <div class="summary-card">
          <span class="summary-label">Matched Topic</span>
          <span class="summary-value">${topicDisplay}</span>
          <div class="subtle summary-note">Driven by selected code and/or keyword language.</div>
        </div>
        <div class="summary-card">
          <span class="summary-label">Authority Layers</span>
          <span class="summary-value">${escapeHtml(layerDisplay)}</span>
          <div class="subtle summary-note">${authorities.length} reference${authorities.length === 1 ? '' : 's'} surfaced for review.</div>
        </div>
        <div class="summary-card">
          <span class="summary-label">Review Support</span>
          <span class="summary-value">${supportCount} note${supportCount === 1 ? '' : 's'}</span>
          <div class="subtle summary-note">${warningCount} warning${warningCount === 1 ? '' : 's'} or human-review flag${warningCount === 1 ? '' : 's'}.</div>
        </div>
      `;
    }

    function renderTopics(topicMatches) {
      const output = document.getElementById('topics-output');
      if (!topicMatches.length) {
        output.innerHTML = '<span class="empty-state">No likely topics matched.</span>';
        return;
      }

      output.innerHTML = topicMatches.map(match => `
        <div class="result-item">
          <div class="result-title">
            <span>${escapeHtml(formatTopicName(match.topic))}</span>
            ${match.keywordMatchCount ? `<span class="meta-chip accent">${match.keywordMatchCount} keyword match${match.keywordMatchCount === 1 ? '' : 'es'}</span>` : ''}
          </div>
          <div class="subtle meta-line">
            ${match.norsCodes.length && match.keywords.length
              ? 'Matched from selected NORS code and keyword language.'
              : match.norsCodes.length
                ? 'Matched from the selected NORS code.'
                : 'Matched from keyword language.'}
          </div>
          <div class="result-meta">
            ${match.norsCodes.map(code => renderCodeChip(code, 'accent')).join('')}
            ${(match.likelyNorsCodes || []).map(code => renderCodeChip(code)).join('')}
            ${match.keywords.map(keyword => `<span class="meta-chip">keyword: ${escapeHtml(keyword)}</span>`).join('')}
          </div>
        </div>
      `).join('');
    }

    function renderAuthorities(authorityGroups) {
      const output = document.getElementById('authorities-output');
      if (!authorityGroups.length) {
        output.innerHTML = '<span class="empty-state">No authority mappings found for matched topics.</span>';
        return;
      }

      output.innerHTML = authorityGroups.map(group => `
        <div class="authority-group">
          <div class="authority-group-header">
            <div class="authority-topic">${escapeHtml(formatTopicName(group.topic))}</div>
            <div class="result-meta">
              ${(group.norsCodes || []).map(code => renderCodeChip(code, 'accent')).join('')}
              ${(group.keywords || []).slice(0, 3).map(keyword => `<span class="meta-chip">keyword: ${escapeHtml(keyword)}</span>`).join('')}
            </div>
          </div>
          <div class="authority-sections">
            ${getAuthoritySections(group.authorities).map(renderAuthoritySection).join('')}
          </div>
        </div>
      `).join('') + `
      <div class="notice">Informational guardrail: references are shown for review support only. CMS Appendix PP/F-tags are interpretive survey guidance tied to federal nursing facility requirements. This tool support human review; staff make all case decisions.</div>`;
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
      return `<div class="subtle meta-line">Source: ${sourceLink}${verified}</div>`;
    }

    function renderResources(resources) {
      const output = document.getElementById('resources-output');
      if (!resources.length) {
        output.innerHTML = '<span class="empty-state">No handouts or resources matched this lookup.</span>';
        return;
      }

      output.innerHTML = `
        <div class="output-section">
          ${resources.map(resource => `
            <div class="result-item">
              <div class="result-title"><strong>${renderResourceLink(resource)}</strong></div>
              ${resource.description || resource.summary ? `<div class="meta-line">${escapeHtml(resource.description || resource.summary)}</div>` : ''}
              <div class="subtle meta-line">Type: ${escapeHtml(resource.type || 'Resource')}</div>
              ${resource.audience ? `<div class="subtle meta-line">Audience: ${escapeHtml(Array.isArray(resource.audience) ? resource.audience.join(', ') : resource.audience)}</div>` : ''}
              ${resource.reason ? `<div class="subtle meta-line">Why shown: ${escapeHtml(resource.reason)}</div>` : ''}
              ${resource.whenToShow || resource.when_to_show ? `<div class="subtle meta-line">Use when: ${escapeHtml(resource.whenToShow || resource.when_to_show)}</div>` : ''}
              ${resource.source ? `<div class="subtle meta-line">Source: ${escapeHtml(resource.source)}</div>` : ''}
              ${resource.lastVerified ? `<div class="subtle meta-line">Last verified: ${escapeHtml(resource.lastVerified)}</div>` : ''}
              ${resource.authorityLevel || resource.authority_level ? `<div class="subtle meta-line">Authority level: ${escapeHtml(resource.authorityLevel || resource.authority_level)}</div>` : ''}
              ${resource.humanReviewNote || resource.human_review_note ? `<div class="subtle meta-line">Review note: ${escapeHtml(resource.humanReviewNote || resource.human_review_note)}</div>` : ''}
            </div>
          `).join('')}
        </div>
        <div class="notice">Informational guardrail: resources are for education and review support only. They support human review; staff make all case decisions.</div>
      `;
    }

    function renderAppendixPpLink(url, page, label) {
      const href = url && page ? `${url}#page=${encodeURIComponent(page)}` : url;
      if (!href) return escapeHtml(label || 'Appendix PP');
      return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label || 'Appendix PP')}</a>`;
    }

    function renderRelatedInvestigations(rows) {
      const output = document.getElementById('related-investigation-output');
      if (!output) return;
      if (!rows.length) {
        output.innerHTML = '<span class="empty-state">No related Appendix PP considerations matched this lookup.</span>';
        return;
      }

      output.innerHTML = `
        <div class="output-section">
          ${rows.map(row => `
            <div class="result-item">
              <div class="result-title">
                <strong>${escapeHtml(row.source_ftag || 'Source tag')} to ${escapeHtml(row.related_ftag || 'related tag')}</strong>
                <span class="meta-chip">${escapeHtml(row.mapping_type || 'related')}</span>
              </div>
              <div class="meta-line">${escapeHtml(row.plain_language_when_to_consider || row.appendix_pp_condition_text || '')}</div>
              ${row.appendix_pp_condition_text ? `<div class="subtle meta-line">Appendix PP trigger: ${escapeHtml(row.appendix_pp_condition_text)}</div>` : ''}
              <div class="result-meta">
                ${(row.likely_nors_codes || []).map(code => renderCodeChip(code)).join('')}
                ${(row.related_topics || []).map(topic => `<span class="meta-chip">${escapeHtml(formatTopicName(topic))}</span>`).join('')}
              </div>
              <div class="subtle meta-line">Why shown: ${escapeHtml(row.match_reason || 'Matched the current code/topic/authority trail.')}</div>
              <div class="subtle meta-line">
                Source: ${renderAppendixPpLink(row.source_pdf_url, row.source_pdf_page_start, `${row.source_ftag} page ${row.source_pdf_page_start || ''}`)}
                ${row.related_ftag ? `; Related: ${renderAppendixPpLink(row.related_pdf_url || row.source_pdf_url, row.related_pdf_page_start, `${row.related_ftag} page ${row.related_pdf_page_start || ''}`)}` : ''}
              </div>
              ${row.human_review_note ? `<div class="subtle meta-line">Review note: ${escapeHtml(row.human_review_note)}</div>` : ''}
            </div>
          `).join('')}
        </div>
        <div class="notice">These rows come from Appendix PP cross-references. They are prompts for additional review, not automatic NORS coding or deficiency findings.</div>
      `;
    }

    function renderResourceLink(resource) {
      const label = escapeHtml(resource.title || 'Resource');
      if (!resource.url) return label;
      return `<a href="${escapeHtml(resource.url)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    }

    function renderWorkflowGuidance(rows, contextTips) {
      const output = document.getElementById('workflow-output');
      if (!rows.length && !contextTips.length) {
        output.innerHTML = '<span class="empty-state">No workflow guidance matched this lookup.</span>';
        return;
      }

      output.innerHTML = `
        ${rows.length ? `<div class="output-section">
          ${rows.map(row => `
            <div class="result-item">
              <strong>${escapeHtml((row.workflow || row.workflow_id || row.id || 'Workflow').replace(/_/g, ' '))}</strong>
              ${row.trigger ? `<br><span class="subtle">Trigger: ${escapeHtml(row.trigger)}</span>` : ''}
              ${row.guidance_text || row.guidance ? `<br><span>${escapeHtml(row.guidance_text || row.guidance)}</span>` : ''}
              ${row.do_not_say ? `<br><span class="subtle">Guardrail: ${escapeHtml(row.do_not_say)}</span>` : ''}
              ${renderWorkflowSourceLinks(row.source_urls || [])}
            </div>
          `).join('')}
        </div>` : ''}
        ${contextTips.length ? `
          <p><strong>Context Tips</strong></p>
          <div class="output-section">
            ${contextTips.map(row => `
              <div class="result-item">
                <strong>${escapeHtml(row.term || row.label || row.id || 'Tip')}</strong>
                ${row.short_help ? `<br><span>${escapeHtml(row.short_help)}</span>` : ''}
                ${row.details ? `<br><span class="subtle">${escapeHtml(row.details)}</span>` : ''}
                ${renderWorkflowSourceLinks(row.source_urls || [])}
              </div>
            `).join('')}
          </div>
        ` : ''}
        <div class="notice">Workflow notes are informational reminders for human review. They support human review; staff make all case decisions.</div>
      `;
    }

    function renderWorkflowSourceLinks(urls) {
      if (!urls.length) return '';
      return `<br><span class="subtle">Sources: ${urls.map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">source ${index + 1}</a>`).join(', ')}</span>`;
    }

    function renderTraceItem(item) {
      if (typeof item === 'string') return escapeHtml(item);
      const links = item.links || [];
      const linkHtml = links.length
        ? `<div class="subtle">Official source${links.length === 1 ? '' : 's'}: ${links.map(link => `<a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(link.label || 'source')}</a>`).join(', ')}</div>`
        : '';
      return `${escapeHtml(item.message || '')}${linkHtml}`;
    }

    function renderTrace(trace) {
      const output = document.getElementById('trace-output');
      if (!trace.length) {
        output.innerHTML = '<span class="empty-state">No trace generated.</span>';
        return;
      }
      output.innerHTML = `<ul class="result-list">${trace.map(item => `<li>${renderTraceItem(item)}</li>`).join('')}</ul>`;
    }

    function renderWarnings(warnings) {
      const output = document.getElementById('warnings-output');
      if (!warnings.length) {
        output.innerHTML = '<span class="empty-state">No warnings.</span>';
        return;
      }
      output.innerHTML = `<ul class="result-list">${warnings.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
    }

    function renderResult(result) {
      renderSummary(result);
      renderTopics(result.topicMatches);
      renderAuthorities(result.authorityGroups);
      renderRelatedInvestigations(result.relatedInvestigations || []);
      renderResources(result.resources || []);
      renderWorkflowGuidance(result.workflowGuidance || [], result.contextTips || []);
      renderTrace(result.trace);
      renderWarnings(result.warnings);
    }

    function showInputWarning(message) {
      const output = document.getElementById('input-warning');
      if (!message) {
        output.style.display = 'none';
        output.textContent = '';
        return;
      }
      output.style.display = 'block';
      output.textContent = message;
    }

    function runKeywordCrosswalk() {
      const keywordText = document.getElementById('keyword-text').value.trim();
      if (!keywordText) {
        showInputWarning('Enter a keyword or concern before running keyword lookup.');
        return;
      }
      showInputWarning('');
      const result = Crosswalk.runCrosswalk({ norsCode: '', keywordText }, crosswalkData);

      renderResult(result);
    }

    function runNorsCodeCrosswalk() {
      const norsCode = document.getElementById('nors-code').value;
      if (!norsCode) {
        showInputWarning('Select a NORS code before running NORS code lookup.');
        return;
      }
      showInputWarning('');
      const result = Crosswalk.runCrosswalk({ norsCode, keywordText: '' }, crosswalkData);

      renderResult(result);
    }

    async function loadPage() {
      const status = document.getElementById('load-status');
      const keywordButton = document.getElementById('run-keyword-crosswalk');
      const norsButton = document.getElementById('run-nors-crosswalk');

      try {
        if (!window.Crosswalk) throw new Error('Shared crosswalk logic did not load.');
        crosswalkData = await Crosswalk.loadCrosswalkData(crosswalkPaths);
        populateNorsCodes();
        document.getElementById('nors-code').addEventListener('change', renderNorsCodeGuidance);
        keywordButton.disabled = false;
        norsButton.disabled = false;
        keywordButton.addEventListener('click', runKeywordCrosswalk);
        norsButton.addEventListener('click', runNorsCodeCrosswalk);
        status.className = 'notice';
        status.textContent = 'Crosswalk data loaded.';
      } catch (err) {
        status.className = 'notice error';
        status.textContent = `Crosswalk data could not be loaded. Details: ${err.message}`;
        keywordButton.disabled = true;
        norsButton.disabled = true;
      }
    }

    document.addEventListener('DOMContentLoaded', loadPage);
