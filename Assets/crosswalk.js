(function () {
  const NORS_TABLE_2_URL = 'https://ltcombudsman.org/uploads/files/support/nors-codes-and-definitions.pdf';
  const APPENDIX_PP_URL = 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/som107ap_pp_guidelines_ltcf.pdf';
  const CT_NURSING_HOME_REGS_URL = 'https://eregulations.ct.gov/eRegsPortal/Browse/RCSA/Title_19Subtitle_19-13Section_19-13-d8t/';
  const CT_NURSING_HOME_STATUTES_URL = 'https://www.cga.ct.gov/current/pub/chap_368v.htm';
  const CT_OMBUDSMAN_STATUTES_URL = 'https://www.cga.ct.gov/current/pub/chap_319l.htm';

  const APPENDIX_PP_PAGE_BY_FTAG = {
    F607: 151
  };

  const KNOWLEDGE_AUTHORITY_ROW_SKIP = new Set([
    // Batch 1 labels this as an A01 direct row, but F602 is a misappropriation/exploitation tag.
    // Keep F602 tied to financial exploitation unless a later SME pass confirms a narrower use.
    'A01|F602'
  ]);

  const DEFAULT_PATHS = {
    norsHierarchy: ['../nors_hierarchy.json', '../data/nors_hierarchy.json'],
    keywordMap: ['../keyword_map.json', '../data/keyword_map.json'],
    norsToTopic: ['../nors_to_topic.json', '../data/nors_to_topic.json'],
    topicToAuthority: ['../topic_to_authority.json', '../data/topic_to_authority.json'],
    authorityIndex: ['../authority_index.json', '../data/reference_source_index.json'],
    crosswalkCatalog: ['../crosswalk_catalog.json', '../data/crosswalk_catalog.json'],
    retrievalRules: ['../retrieval_rules.json', '../data/retrieval_rules.json'],
    norsComplaintGuidance: ['../data/nors_complaint_code_guidance.json', '../nors_complaint_code_guidance.json'],
    norsResourceCatalog: ['../data/nors_resource_catalog.json', '../nors_resource_catalog.json'],
    norsKnowledgeBase: ['../data/nors_knowledge_base_batch1.json', '../nors_knowledge_base_batch1.json'],
    norsKnowledgeBaseBatch2: ['../data/nors_knowledge_base_batch2.json', '../nors_knowledge_base_batch2.json'],
    norsKnowledgeBaseBatch3: ['../data/nors_knowledge_base_batch3.json', '../nors_knowledge_base_batch3.json'],
    norsKnowledgeBaseBatch4: ['../data/nors_knowledge_base_batch4.json', '../nors_knowledge_base_batch4.json'],
    norsKnowledgeBaseBatch5: ['../data/nors_knowledge_base_batch5.json', '../nors_knowledge_base_batch5.json'],
    norsKnowledgeBaseBatch6: ['../data/nors_knowledge_base_batch6.json', '../nors_knowledge_base_batch6.json'],
    norsKnowledgeBaseBatch7: ['../data/nors_knowledge_base_batch7.json', '../nors_knowledge_base_batch7.json'],
    norsKnowledgeBaseBatch8: ['../data/nors_knowledge_base_batch8.json', '../nors_knowledge_base_batch8.json'],
    norsKnowledgeBaseBatch9: ['../data/nors_knowledge_base_batch9.json', '../nors_knowledge_base_batch9.json'],
    norsKnowledgeBaseBatch10: ['../data/nors_knowledge_base_batch10.json', '../nors_knowledge_base_batch10.json'],
    norsKnowledgeBaseBatch11: ['../data/nors_knowledge_base_batch11.json', '../nors_knowledge_base_batch11.json'],
    norsKnowledgeBaseBatch12: ['../data/nors_knowledge_base_batch12.json', '../nors_knowledge_base_batch12.json'],
    appendixPpTagPages: ['../data/appendix_pp_tag_pages.json', '../appendix_pp_tag_pages.json'],
    sourceRegistry: ['../data/source_registry.json', '../source_registry.json']
  };

  const OPTIONAL_DATA_KEYS = new Set(['norsToTopic', 'topicToAuthority', 'norsComplaintGuidance', 'norsResourceCatalog', 'norsKnowledgeBase', 'norsKnowledgeBaseBatch2', 'norsKnowledgeBaseBatch3', 'norsKnowledgeBaseBatch4', 'norsKnowledgeBaseBatch5', 'norsKnowledgeBaseBatch6', 'norsKnowledgeBaseBatch7', 'norsKnowledgeBaseBatch8', 'norsKnowledgeBaseBatch9', 'norsKnowledgeBaseBatch10', 'norsKnowledgeBaseBatch11', 'norsKnowledgeBaseBatch12', 'appendixPpTagPages', 'sourceRegistry']);

  function getOptionalFallback(key) {
    if (key === 'topicToAuthority') return { topics: {} };
    if (key === 'norsComplaintGuidance') return { items: [] };
    if (key === 'norsResourceCatalog') return { resources: [] };
    if (key === 'norsKnowledgeBase') return { code_summary_rows: [], authority_rows: [], do_not_map_catalog: [] };
    if (key === 'norsKnowledgeBaseBatch2') return { code_summary_rows: [], authority_rows: [], appendix_pp_page_rows: [], do_not_map_catalog: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch3') return { code_summary_rows: [], authority_rows: [], appendix_pp_page_rows: [], do_not_map_catalog: [], keyword_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch4') return { resource_rows: [], workflow_guidance_rows: [], source_quality_rows: [], plain_language_explainer_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch5') return { resource_corrections: [], additional_resource_rows: [], tooltip_rows: [], workflow_corrections: [], source_quality_corrections: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch6') return { resource_rows: [], resource_corrections: [], source_verification_rows: [], workflow_update_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch7') return { resource_rows: [], resource_corrections: [], source_verification_rows: [], workflow_update_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch8') return { code_routing_corrections: [], resource_corrections: [], source_verification_rows: [], resource_currency_rows: [], workflow_update_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch9') return { code_routing_corrections: [], resource_corrections: [], source_verification_rows: [], resource_currency_rows: [], workflow_update_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch10') return { source_rows: [], coding_principle_rows: [], ambiguity_rule_rows: [], keyword_routing_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch11') return { source_verification_rows: [], source_conflict_rows: [], keyword_routing_rows: [], tooltip_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch12') return { appendix_pp_related_investigation_rows: [], appendix_pp_source_rows: [], keyword_routing_rows: [], human_review_flags: [] };
    if (key === 'appendixPpTagPages') return { appendix_pp_tag_page_rows: [] };
    if (key === 'sourceRegistry') return { sources: [] };
    return {};
  }

  async function loadJsonFile(paths, keyName) {
    const candidates = Array.isArray(paths) ? paths : [paths];
    const errors = [];

    for (const path of candidates) {
      try {
        const response = await fetch(path);
        if (!response.ok) {
          console.warn(`[crosswalk] Failed to load ${keyName || 'data'} from ${path} (HTTP ${response.status})`);
          errors.push(`${path} returned HTTP ${response.status}`);
          continue;
        }
        const payload = await response.json();
        console.info(`[crosswalk] Loaded ${keyName || 'data'} from ${path}`);
        return payload;
      } catch (err) {
        console.warn(`[crosswalk] Failed to load ${keyName || 'data'} from ${path}: ${err.message}`);
        errors.push(`${path}: ${err.message}`);
      }
    }

    console.error(`[crosswalk] Could not load ${keyName || 'data'} from any path`, candidates);
    throw new Error(errors.join('; '));
  }

  async function loadCrosswalkData(paths = {}) {
    const mergedPaths = { ...DEFAULT_PATHS, ...paths };
    const entries = await Promise.all(Object.entries(mergedPaths).map(async ([key, path]) => {
      try {
        return [key, await loadJsonFile(path, key)];
      } catch (err) {
        if (!OPTIONAL_DATA_KEYS.has(key)) throw err;
        console.warn(`[crosswalk] Optional legacy data ${key} could not be loaded; continuing with normalized crosswalk catalog.`);
        return [key, getOptionalFallback(key)];
      }
    }));

    return Object.fromEntries(entries);
  }

  function addTopic(topicMatches, topic, sourceType, value) {
    if (!topic) return;
    if (!topicMatches[topic]) {
      topicMatches[topic] = { topic, norsCodes: [], likelyNorsCodes: [], keywords: [], keywordMatchCount: 0 };
    }
    if (sourceType === 'nors' && value && !topicMatches[topic].norsCodes.includes(value)) {
      topicMatches[topic].norsCodes.push(value);
    }
    if (sourceType === 'likely_nors' && value && !topicMatches[topic].likelyNorsCodes.includes(value)) {
      topicMatches[topic].likelyNorsCodes.push(value);
    }
    if (sourceType === 'keyword' && value) {
      if (!topicMatches[topic].keywords.includes(value)) {
        topicMatches[topic].keywords.push(value);
      }
      topicMatches[topic].keywordMatchCount = topicMatches[topic].keywords.length;
    }
  }

  function sortTopicMatches(topicMatches) {
    return Object.values(topicMatches).map(match => ({
      ...match,
      norsCodes: match.norsCodes || [],
      likelyNorsCodes: match.likelyNorsCodes || [],
      keywords: match.keywords || [],
      keywordMatchCount: match.keywordMatchCount || (match.keywords || []).length || 0
    })).sort((a, b) => {
      const aPriority = a.norsCodes.length ? 0 : 1;
      const bPriority = b.norsCodes.length ? 0 : 1;
      return aPriority - bPriority || (b.keywordMatchCount || 0) - (a.keywordMatchCount || 0) || a.topic.localeCompare(b.topic);
    });
  }

  function mergeTopicMatches(...topicMatchArrays) {
    const merged = {};
    topicMatchArrays.flat().forEach(match => {
      (match.norsCodes || []).forEach(code => addTopic(merged, match.topic, 'nors', code));
      (match.likelyNorsCodes || []).forEach(code => addTopic(merged, match.topic, 'likely_nors', code));
      (match.keywords || []).forEach(keyword => addTopic(merged, match.topic, 'keyword', keyword));
    });
    return sortTopicMatches(merged);
  }

  function getCatalogRecords(data) {
    return Array.isArray(data.crosswalkCatalog?.records) ? data.crosswalkCatalog.records : [];
  }

  function getKnowledgeBases(data) {
    return [data?.norsKnowledgeBase, data?.norsKnowledgeBaseBatch2, data?.norsKnowledgeBaseBatch3, data?.norsKnowledgeBaseBatch4, data?.norsKnowledgeBaseBatch5, data?.norsKnowledgeBaseBatch6, data?.norsKnowledgeBaseBatch7, data?.norsKnowledgeBaseBatch8, data?.norsKnowledgeBaseBatch9, data?.norsKnowledgeBaseBatch10, data?.norsKnowledgeBaseBatch11, data?.norsKnowledgeBaseBatch12].filter(Boolean);
  }

  function getKnowledgeCodeRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.code_summary_rows || []);
  }

  function getKnowledgeAuthorityRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.authority_rows || []);
  }

  function getKnowledgeDoNotMapRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.do_not_map_catalog || []);
  }

  function splitPhrasePattern(value) {
    return String(value || '')
      .split('|')
      .map(phrase => phrase.trim())
      .filter(Boolean);
  }

  function normalizeKeywordRoutingRow(row = {}) {
    const phrases = splitPhrasePattern(row.phrase_pattern || row.phrase || row.pattern);
    const likelyCodes = toArray(row.likely_nors_codes || row.primary_code).filter(Boolean);
    const relatedCodes = toArray(row.related_codes).filter(Boolean);
    const topics = toArray(row.topic_slugs || row.topics).filter(Boolean);
    const authorityIds = toArray(row.authority_ids).filter(Boolean);
    const notes = row.explanation_for_trace || row.warning_or_human_review_note || '';

    return phrases.map(phrase => ({
      ...row,
      phrase,
      keywords: [phrase],
      topics,
      likely_nors_codes: likelyCodes,
      related_codes: relatedCodes,
      authority_ids: authorityIds,
      notes
    }));
  }

  function getKnowledgeKeywordRows(data) {
    return getKnowledgeBases(data).flatMap(base => [
      ...(base.keyword_rows || []),
      ...(base.keyword_routing_rows || []).flatMap(normalizeKeywordRoutingRow)
    ]).sort((a, b) => getWordTokens(b.phrase || b.phrase_pattern || '').length - getWordTokens(a.phrase || a.phrase_pattern || '').length);
  }

  function getKnowledgeResourceRows(data) {
    return getKnowledgeBases(data)
      .flatMap(base => [...(base.resource_rows || []), ...(base.additional_resource_rows || [])])
      .map(normalizeKnowledgeResourceRow)
      .map(row => applyResourceCorrection(row, data))
      .map(row => applyCodeRoutingCorrection(row, data));
  }

  function getKnowledgeWorkflowRows(data) {
    const rows = getKnowledgeBases(data).flatMap(base => base.workflow_guidance_rows || []);
    return applyWorkflowCorrections(rows, data);
  }

  function getKnowledgeSourceQualityRows(data) {
    const rows = getKnowledgeBases(data).flatMap(base => base.source_quality_rows || []);
    return applySourceQualityCorrections(rows, data);
  }

  function getKnowledgeExplainerRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.plain_language_explainer_rows || []);
  }

  function getKnowledgeTooltipRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.tooltip_rows || []).map(normalizeKnowledgeTooltipRow);
  }

  function getKnowledgeHumanReviewFlags(data) {
    const resolved = getResolvedHumanReviewFlagIds(data);
    return getKnowledgeBases(data)
      .flatMap(base => base.human_review_flags || [])
      .filter(flag => !resolved.has(flag.flag_id || flag.id));
  }

  function getKnowledgeSourceVerificationRows(data) {
    const rows = getKnowledgeBases(data).flatMap(base => base.source_verification_rows || []);
    return applySourceVerificationCorrections(rows, data);
  }

  function getKnowledgeAppendixPpRelatedRows(data) {
    return getKnowledgeBases(data)
      .flatMap(base => base.appendix_pp_related_investigation_rows || [])
      .map(row => normalizeAppendixPpRelatedInvestigationRow(row, data));
  }

  function getKnowledgeResourceCorrections(data) {
    return getKnowledgeBases(data).flatMap(base => base.resource_corrections || []);
  }

  function getKnowledgeWorkflowCorrections(data) {
    return getKnowledgeBases(data).flatMap(base => base.workflow_corrections || []);
  }

  function getKnowledgeWorkflowUpdateRows(data) {
    const rows = getKnowledgeBases(data).flatMap(base => base.workflow_update_rows || []);
    const hasBatch7 = getKnowledgeBases(data).some(base => {
      return base?.meta?.batch === '7' || (base?.workflow_update_rows || []).some(row => /^WU-B7-/.test(row.id || ''));
    });
    return hasBatch7 ? rows.filter(row => row.id !== 'WU-001') : rows;
  }

  function getKnowledgeCodeRoutingCorrections(data) {
    return getKnowledgeBases(data).flatMap(base => base.code_routing_corrections || []);
  }

  function getKnowledgeSourceVerificationCorrections(data) {
    return getKnowledgeResourceCorrections(data).filter(correction => /^SV-/.test(correction.target_row_id || ''));
  }

  function getResolvedHumanReviewFlagIds(data) {
    return new Set(getKnowledgeResourceCorrections(data)
      .filter(correction => /^HRF-/.test(correction.target_row_id || '') && correction.corrected_value?.flag_type === 'resolved')
      .map(correction => correction.target_row_id));
  }

  function getKnowledgeSourceQualityCorrections(data) {
    return getKnowledgeBases(data).flatMap(base => base.source_quality_corrections || []);
  }

  function cleanReviewText(value) {
    return String(value || '')
      .replace(/\bCODEX\b:?\s*/gi, '')
      .replace(/\bInstruct Codex to\s*/gi, '')
      .trim();
  }

  function extractUrls(value) {
    return [...String(value || '').matchAll(/https?:\/\/[^\s;)]+/g)].map(match => match[0]);
  }

  function normalizeKnowledgeResourceRow(resource = {}) {
    const id = resource.id || '';
    if (/^RR-B7-00[1-5]$/.test(id)) {
      return {
        ...resource,
        applies_to_nors_codes: ['C02', 'C03'],
        human_review_note: cleanReviewText(resource.human_review_note || 'Batch 7 labeled these as D-series discharge resources; this app routes them to C02/C03 under the current NORS hierarchy.')
      };
    }
    if (['RR-B7-010', 'RR-B7-011'].includes(id)) {
      return {
        ...resource,
        applies_to_nors_codes: ['F13', 'D07']
      };
    }
    if (id === 'RR-B7-012') {
      return {
        ...resource,
        applies_to_nors_codes: ['F13']
      };
    }
    if (id === 'RR-B7-013') {
      return {
        ...resource,
        applies_to_nors_codes: ['F04', 'F12']
      };
    }
    if (id === 'RR-B7-008') {
      return {
        ...resource,
        applies_to_nors_codes: [...new Set([...toArray(resource.applies_to_nors_codes), 'A04', 'A05'])]
      };
    }
    return resource;
  }

  function normalizeKnowledgeTooltipRow(row = {}) {
    const id = row.id || row.tooltip_id || '';
    const label = row.term || row.label || row.tooltip_type?.replace(/_/g, ' ') || id;
    return {
      ...row,
      id,
      term: label,
      short_help: row.short_help || row.tooltip_text || '',
      details: row.details || row.authority || ''
    };
  }

  function normalizeAppendixPpRelatedInvestigationRow(row = {}, data) {
    const sourceTag = String(row.source_ftag || row.source_f_tag || '').toUpperCase();
    const relatedTag = String(row.related_ftag || row.related_f_tag || '').toUpperCase();
    const sourcePage = getAppendixPpTagPage(sourceTag, data);
    const relatedPage = getAppendixPpTagPage(relatedTag, data);

    return {
      ...row,
      rule_id: row.rule_id || `${sourceTag}-${relatedTag}`,
      source_ftag: sourceTag,
      related_ftag: relatedTag,
      source_pdf_page_start: sourcePage?.appendix_pp_pdf_page_start || row.source_pdf_page_start || null,
      source_heading_exact: sourcePage?.heading_exact || row.source_heading_exact || sourceTag,
      source_pdf_url: sourcePage?.appendix_pp_pdf_url || row.source_pdf_url || APPENDIX_PP_URL,
      related_pdf_page_start: relatedPage?.appendix_pp_pdf_page_start || row.related_pdf_page_start || null,
      related_heading_exact: relatedPage?.heading_exact || row.related_heading_exact || relatedTag,
      related_pdf_url: relatedPage?.appendix_pp_pdf_url || row.related_pdf_url || row.source_pdf_url || APPENDIX_PP_URL
    };
  }

  function applySourceVerificationCorrections(rows, data) {
    const corrections = getKnowledgeSourceVerificationCorrections(data);
    return rows.map(row => {
      const correction = corrections.find(item => item.target_row_id === row.id);
      if (!correction) return row;
      const corrected = correction.corrected_value || {};
      return {
        ...row,
        ...corrected,
        correction_note: cleanReviewText(correction.reason || '')
      };
    });
  }

  function applyResourceCorrection(resource = {}, data) {
    const corrections = getKnowledgeResourceCorrections(data).filter(item => {
      return item.resource_id === resource.id || item.target_row_id === resource.id || item.target_resource_id === resource.id;
    });
    if (!corrections.length) return resource;

    return corrections.reduce((current, correction) => {
      const corrected = correction.corrected_value || {};
      const correctedObject = typeof corrected === 'object' && corrected !== null && !Array.isArray(corrected) ? corrected : {};
      const isQso26Correction = current.id === 'RR-013' && correctedObject.subject_tag;
      const next = {
        ...current,
        title: correction.corrected_title || correctedObject.title || (isQso26Correction ? 'CMS QSO-26-03-NH - SOM Chapters 5 and 7 / complaint procedures / F610' : current.title),
        summary: correctedObject.description || correction.corrected_description || current.summary,
        url: correction.corrected_url || correctedObject.url || current.url,
        source_owner: correction.corrected_source_owner || correction.source_owner || current.source_owner,
        authority_level: correction.corrected_authority_level || correction.authority_level || current.authority_level,
        applies_to_nors_codes: isQso26Correction ? [] : current.applies_to_nors_codes,
        applies_to_topics: isQso26Correction ? ['complaint procedures', 'F610', 'SOM Chapters 5 and 7'] : current.applies_to_topics,
        when_to_show: isQso26Correction ? 'Staff reference for CMS QSO-26-03-NH complaint-procedure and F610 updates. This is not psychotropic medication guidance.' : current.when_to_show,
        human_review_note: cleanReviewText(correction.human_review_note || correction.authority_caveat || current.human_review_note || ''),
        correction_note: cleanReviewText(correction.reason || correction.issue || current.correction_note || ''),
        recommended_action: correction.recommended_action || current.recommended_action || ''
      };

      if (correction.field && Object.prototype.hasOwnProperty.call(correction, 'corrected_value')) {
        next[correction.field] = corrected;
      }

      return next;
    }, resource);
  }

  function applyCodeRoutingCorrection(resource = {}, data) {
    const hasExplicitResourceCodeCorrection = getKnowledgeResourceCorrections(data).some(item => {
      return (item.target_resource_id === resource.id || item.resource_id === resource.id || item.target_row_id === resource.id) &&
        item.field === 'applies_to_nors_codes' &&
        Object.prototype.hasOwnProperty.call(item, 'corrected_value');
    });
    if (hasExplicitResourceCodeCorrection) return resource;

    const correction = [...getKnowledgeCodeRoutingCorrections(data)].reverse().find(item => item.target_row_id === resource.id);
    if (!correction || !Object.prototype.hasOwnProperty.call(correction, 'corrected_codes')) return resource;

    const correctedCodes = toArray(correction.corrected_codes);
    return {
      ...resource,
      applies_to_nors_codes: correctedCodes,
      human_review_note: cleanReviewText(correction.human_review_note || resource.human_review_note || ''),
      correction_note: cleanReviewText(correction.reason || resource.correction_note || '')
    };
  }

  function applyWorkflowCorrections(rows, data) {
    const corrections = getKnowledgeWorkflowCorrections(data);
    return rows.map(row => {
      const correction = corrections.find(item => item.workflow_id === row.id);
      if (!correction || correction.recommended_action !== 'replace') return row;

      return {
        ...row,
        guidance_text: correction.corrected_guidance_text || row.guidance_text,
        do_not_say: correction.corrected_do_not_say || row.do_not_say,
        source_urls: correction.source_urls || row.source_urls || [],
        correction_note: correction.issue || ''
      };
    });
  }

  function applySourceQualityCorrections(rows, data) {
    const corrections = getKnowledgeSourceQualityCorrections(data);
    return rows.map(row => {
      const correction = corrections.find(item => item.source_id === row.source_id);
      if (!correction) return row;

      return {
        ...row,
        authority_level: correction.corrected_authority_level || row.authority_level,
        preferred_use: correction.corrected_preferred_use || row.preferred_use,
        limitations: correction.corrected_limitations || row.limitations,
        correction_note: correction.issue || ''
      };
    });
  }

  function normalizeKnowledgeSummary(row = {}) {
    if (!row || !Object.keys(row).length) return {};
    return {
      ...row,
      nors_label: row.nors_label || row.label || '',
      nors_table_2_page: row.nors_table_2_page || row.nors_pdf_page || '',
      nors_definition: row.nors_definition || row.definition || '',
      use_when: row.use_when || row.useWhen || '',
      do_not_use_when: row.do_not_use_when || row.doNotUseWhen || '',
      reporting_tips: row.reporting_tips || row.reportingTips || '',
      examples: row.examples || [],
      common_concern_phrases: row.common_concern_phrases || row.commonConcernPhrases || [],
      human_review_notes: row.human_review_notes || row.humanReviewNotes || row.notes || '',
      handout_or_resource_urls: row.handout_or_resource_urls || row.handoutOrResourceUrls || []
    };
  }

  function getNorsCodeOptions(data) {
    const majorCodes = data?.norsHierarchy?.major_codes || [];
    if (Array.isArray(majorCodes) && majorCodes.length) {
      return majorCodes.map(major => ({
        code: major.code,
        label: major.label || major.code,
        description: major.description || '',
        minorCodes: (major.minor_codes || []).map(minor => ({
          code: minor.code,
          label: minor.label || minor.code,
          description: minor.description || '',
          definition: minor.definition || minor.description || '',
          examples: minor.examples || [],
          reportingTips: minor.reporting_tips || minor.examples_and_reporting_tips || ''
        }))
      }));
    }

    const records = getCatalogRecords(data);
    if (records.length) {
      const grouped = {};
      records.forEach(record => {
        const majorCode = record.nors_major_code || (record.nors_minor_code || '').charAt(0);
        if (!majorCode) return;
        if (!grouped[majorCode]) {
          grouped[majorCode] = {
            code: majorCode,
            label: record.nors_major_label || majorCode,
            description: '',
            minorCodes: []
          };
        }
        if (record.nors_minor_code && !grouped[majorCode].minorCodes.some(minor => minor.code === record.nors_minor_code)) {
          grouped[majorCode].minorCodes.push({
            code: record.nors_minor_code,
            label: record.nors_minor_label || record.nors_minor_code,
            description: '',
            definition: '',
            examples: [],
            reportingTips: ''
          });
        }
      });
      return Object.values(grouped).sort((a, b) => a.code.localeCompare(b.code)).map(major => ({
        ...major,
        minorCodes: major.minorCodes.sort((a, b) => a.code.localeCompare(b.code))
      }));
    }

    const codes = Object.keys(data?.norsToTopic || {}).sort();
    const fallbackGroups = {};
    codes.forEach(code => {
      const majorCode = code.charAt(0);
      if (!fallbackGroups[majorCode]) {
        fallbackGroups[majorCode] = { code: majorCode, label: majorCode, description: '', minorCodes: [] };
      }
      fallbackGroups[majorCode].minorCodes.push({ code, label: code, description: '', definition: '', examples: [], reportingTips: '' });
    });
    return Object.values(fallbackGroups);
  }

  function getNorsCodeDetail(norsCode, data) {
    const code = (norsCode || '').trim();
    if (!code) return null;

    for (const major of getNorsCodeOptions(data)) {
      const minor = (major.minorCodes || []).find(item => item.code === code);
      if (minor) {
        const guidance = getNorsComplaintGuidance(code, data);
        const knowledge = getNorsKnowledgeSummary(code, data);
        return {
          majorCode: major.code,
          majorLabel: major.label,
          code: minor.code,
          label: minor.label,
          description: minor.description || '',
          definition: knowledge.nors_definition || guidance.definition || minor.definition || minor.description || '',
          examples: knowledge.examples || guidance.examples || minor.examples || [],
          reportingTips: knowledge.reporting_tips || guidance.reporting_tips || minor.reportingTips || '',
          useWhen: knowledge.use_when || guidance.use_when || '',
          likelyPhrases: knowledge.common_concern_phrases || guidance.likely_phrases || [],
          doNotUseWhen: knowledge.do_not_use_when || guidance.do_not_use_when || '',
          humanReview: knowledge.human_review_notes || guidance.human_review || '',
          source: knowledge.nors_table_2_page
            ? `NORS Table 2 complaint code guidance, page ${knowledge.nors_table_2_page}`
            : guidance.source || 'NORS Table 2 complaint code guidance'
        };
      }
    }

    return null;
  }

  function getNorsComplaintGuidance(norsCode, data) {
    const code = (norsCode || '').trim();
    const items = data?.norsComplaintGuidance?.items || [];
    return items.find(item => item.code === code) || {};
  }

  function getNorsKnowledgeSummary(norsCode, data) {
    const code = (norsCode || '').trim();
    const rows = getKnowledgeCodeRows(data);
    return normalizeKnowledgeSummary(rows.find(row => row.nors_code === code) || {});
  }

  function getMatchedNorsCodes(norsCode, topicMatches = []) {
    const codes = new Set();
    if (norsCode) codes.add(norsCode);
    topicMatches.forEach(match => {
      (match.norsCodes || []).forEach(code => codes.add(code));
      (match.likelyNorsCodes || []).forEach(code => codes.add(code));
    });
    return [...codes].filter(Boolean);
  }

  function normalizeTopicKey(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[_/-]+/g, ' ')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function resourceTopicMatches(resourceTopic, matchedTopics, searchableText, searchableTokens) {
    const normalizedResourceTopic = normalizeTopicKey(resourceTopic);
    if (!normalizedResourceTopic) return false;
    return matchedTopics.some(topic => {
      const normalizedTopic = normalizeTopicKey(topic);
      return normalizedTopic && (
        normalizedResourceTopic === normalizedTopic ||
        normalizedResourceTopic.includes(normalizedTopic) ||
        normalizedTopic.includes(normalizedResourceTopic)
      );
    }) || keywordPhraseMatches(normalizedResourceTopic, searchableText, searchableTokens);
  }

  function hasDischargeTerms(keywordText) {
    return /\b(discharge|discharged|eviction|evict|transfer|transferred|appeal|hearing|notice|readmit|readmission|bed hold)\b/i.test(String(keywordText || ''));
  }

  function isPureC04RoomLookup(matchedCodes, keywordText) {
    return matchedCodes.length === 1 && matchedCodes.includes('C04') && !hasDischargeTerms(keywordText);
  }

  function isDischargeSupportResource(resource = {}) {
    const id = resource.id || '';
    const text = [
      id,
      resource.title,
      resource.summary,
      resource.description,
      resource.when_to_show,
      resource.whenToShow,
      toArray(resource.applies_to_topics).join(' ')
    ].join(' ');
    return ['RR-001', 'RR-002', 'RR-003', 'RR-B7-001', 'RR-B7-002', 'RR-B7-003', 'RR-B7-004', 'RR-B7-005'].includes(id) ||
      /\b(discharge|eviction|transfer notice|appeal rights|f627|f628|qso-25-14)\b/i.test(text);
  }

  function getResourcesForInputs({ norsCode, keywordText, topicMatches = [] } = {}, data) {
    const resources = data?.norsResourceCatalog?.resources || [];
    const knowledgeResources = getKnowledgeResourceRows(data);
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedMajors = [...new Set(matchedCodes.map(code => code.charAt(0)).filter(Boolean))];
    const matchedTopics = topicMatches.map(match => match.topic).filter(Boolean);
    const searchableText = String(keywordText || '').toLowerCase();
    const searchableTokens = getWordTokens(searchableText);
    const seen = new Set();
    const output = [];
    const suppressDischargeForC04 = isPureC04RoomLookup(matchedCodes, keywordText);

    resources.forEach(resource => {
      const appliesTo = resource.applies_to || {};
      const reasons = [];
      const resourceCodes = appliesTo.nors_codes || [];
      const resourceMajors = appliesTo.major_codes || [];
      const resourceTopics = appliesTo.topics || [];
      const resourceKeywords = appliesTo.keywords || [];

      if (appliesTo.all_nors_codes && matchedCodes.length) {
        reasons.push('shown for NORS code lookup support');
      }
      resourceCodes.filter(code => matchedCodes.includes(code)).forEach(code => {
        reasons.push(`matched NORS code ${code}`);
      });
      resourceMajors.filter(code => matchedMajors.includes(code)).forEach(code => {
        reasons.push(`matched NORS major code ${code}`);
      });
      resourceTopics.filter(topic => matchedTopics.includes(topic)).forEach(topic => {
        reasons.push(`matched topic ${formatTopicName(topic)}`);
      });
      resourceKeywords.filter(keyword => searchableText.includes(String(keyword).toLowerCase())).forEach(keyword => {
        reasons.push(`matched keyword "${keyword}"`);
      });

      if (!reasons.length || seen.has(resource.id)) return;
      seen.add(resource.id);
      output.push({
        id: resource.id,
        title: resource.title || 'Resource',
        description: resource.description || '',
        type: resource.type || resource.resource_type || 'Resource',
        url: resource.url || '',
        source: resource.source || '',
        audience: resource.audience || '',
        reason: reasons[0],
        informational_only: resource.informational_only !== false
      });
    });

    knowledgeResources.forEach(resource => {
      if (suppressDischargeForC04 && isDischargeSupportResource(resource)) return;

      const reasons = [];
      const resourceCodes = toArray(resource.applies_to_nors_codes).filter(Boolean);
      const resourceTopics = toArray(resource.applies_to_topics).filter(Boolean);
      const resourceId = resource.id || resource.url || resource.title || `knowledge_resource_${output.length + 1}`;

      resourceCodes.filter(code => matchedCodes.includes(code)).forEach(code => {
        reasons.push(`matched NORS code ${code}`);
      });
      resourceTopics.filter(topic => resourceTopicMatches(topic, matchedTopics, searchableText, searchableTokens)).forEach(topic => {
        reasons.push(`matched resource topic ${topic}`);
      });

      if (!reasons.length || seen.has(resourceId)) return;
      seen.add(resourceId);
      if (resource.url) seen.add(resource.url);

      output.push({
        id: resource.id || `knowledge_resource_${output.length + 1}`,
        title: resource.title || 'Resource',
        description: resource.summary || '',
        type: resource.resource_type || 'Resource',
        url: resource.url || '',
        source: resource.source_owner || '',
        audience: resource.audience || '',
        reason: reasons[0],
        whenToShow: resource.when_to_show || '',
        lastVerified: resource.last_verified || '',
        authorityLevel: resource.authority_level || '',
        humanReviewNote: resource.human_review_note || resource.correction_note || '',
        recommendedAction: resource.recommended_action || '',
        informational_only: resource.informational_only !== false
      });
    });

    getKnowledgeCodeRows(data).map(normalizeKnowledgeSummary).forEach(row => {
      if (!matchedCodes.includes(row.nors_code)) return;
      (row.handout_or_resource_urls || []).forEach(resource => {
        if (!resource?.url || seen.has(resource.url)) return;
        seen.add(resource.url);
        output.push({
          id: `knowledge_${row.nors_code}_${resource.url}`,
          title: resource.label || `${row.nors_code} resource`,
          description: `Source-backed resource from the ${row.nors_code} knowledge-base handoff.`,
          type: 'Knowledge-base resource',
          url: resource.url,
          source: 'NORS knowledge base batch 1',
          audience: 'Ombudsman staff',
          reason: `matched NORS code ${row.nors_code}`,
          informational_only: true
        });
      });
    });

    return output;
  }

  function getKnowledgeCaveatWarnings(norsCode, topicMatches = [], data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    if (!matchedCodes.length) return [];

    return getKnowledgeDoNotMapRows(data)
      .filter(row => {
        const rowCodes = String(row.nors_code || '').split(',').map(code => code.trim()).filter(Boolean);
        return rowCodes.some(code => matchedCodes.includes(code));
      })
      .map(row => `Review caveat for ${row.nors_code}: ${row.reason}`);
  }

  function codeMatchesPrefix(matchedCodes, prefixes) {
    return matchedCodes.some(code => prefixes.some(prefix => code.startsWith(prefix)));
  }

  function getWorkflowUpdateGuidanceForInputs({ norsCode, keywordText = '', topicMatches = [], resources = [] } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic));
    const resourceIds = new Set(resources.map(resource => resource.id).filter(Boolean));
    const suppressDischargeForC04 = isPureC04RoomLookup(matchedCodes, keywordText);

    return getKnowledgeWorkflowUpdateRows(data)
      .filter(row => {
        const area = row.workflow_area || '';
        const rowCodes = toArray(row.applies_to_nors_codes);
        const rowTopics = toArray(row.applies_to_topics).map(normalizeTopicKey);
        const rowText = `${row.workflow_id || row.id || ''} ${area} ${rowTopics.join(' ')}`;

        if (suppressDischargeForC04 && /discharge|transfer|appeal|ct discharge|admission transfer discharge/.test(rowText)) {
          return false;
        }

        if (rowCodes.some(code => matchedCodes.includes(code)) ||
          rowTopics.some(topic => matchedTopics.some(matchTopic => matchTopic.includes(topic) || topic.includes(matchTopic)))) {
          return true;
        }

        if (area === 'medication_tag_routing') {
          return ['F04', 'F05', 'F07', 'F11', 'F12'].some(code => matchedCodes.includes(code)) ||
            matchedTopics.some(topic => /medication|drug|psychotropic|chemical restraint/.test(topic));
        }
        if (area === 'staffing_complaint_routing') {
          return ['J01', 'J02', 'J03'].some(code => matchedCodes.includes(code)) ||
            matchedTopics.some(topic => /staffing|nursing staff|sufficient staff/.test(topic));
        }
        if (area === 'qso_memo_routing') {
          return resourceIds.has('RR-013');
        }
        if (area === 'discharge_resource_routing') {
          return ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
            matchedTopics.some(topic => /discharge|transfer/.test(topic));
        }
        if (area === 'ct_dph_inspection_data_routing') {
          return ['RR-B7-006', 'RR-B7-007', 'RR-B7-008'].some(id => resourceIds.has(id)) ||
            matchedTopics.some(topic => /inspection|survey|quality standards|abuse|neglect/.test(topic));
        }
        if (area === 'qso_25_07_nh_effective_date') {
          return ['RR-B7-005', 'RR-B7-013', 'RR-025'].some(id => resourceIds.has(id)) ||
            matchedTopics.some(topic => /medication|drug|psychotropic|chemical restraint/.test(topic));
        }
        return false;
      })
      .map(row => ({
        id: row.id || row.workflow_id,
        workflow: row.workflow_area || row.workflow_id || row.id,
        trigger: row.update_type ? `${row.update_type.replace(/_/g, ' ')} update` : 'Workflow update',
        guidance_text: row.corrected_guidance || row.guidance || '',
        do_not_say: /^none\.?$/i.test(cleanReviewText(row.caveat || row.do_not_say || '')) ? '' : cleanReviewText(row.caveat || row.do_not_say || ''),
        source_urls: row.source_urls || extractUrls(row.authority || '')
      }));
  }

  function getWorkflowGuidanceForInputs({ norsCode, keywordText = '', topicMatches = [], resources = [] } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic));

    const workflowRows = getKnowledgeWorkflowRows(data).filter(row => {
      const workflow = row.workflow || '';
      if (workflow === 'abuse_case') {
        return matchedCodes.some(code => /^A0[1-5]$/.test(code)) ||
          matchedTopics.some(topic => /abuse|neglect|exploitation/.test(topic));
      }
      if (workflow === 'discharge_case') {
        return ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
          matchedTopics.some(topic => /discharge|transfer/.test(topic));
      }
      if (workflow === 'medication_case') {
        return ['F04', 'F05', 'F07', 'F11', 'F12'].some(code => matchedCodes.includes(code)) ||
          matchedTopics.some(topic => /medication|drug|psychotropic|chemical restraint/.test(topic));
      }
      if (workflow === 'rights_case') {
        return codeMatchesPrefix(matchedCodes, ['D', 'B']) ||
          matchedTopics.some(topic => /right|privacy|visitor|dignity|choice|grievance|retaliation/.test(topic));
      }
      if (workflow === 'outside_agency_case') {
        return codeMatchesPrefix(matchedCodes, ['K', 'L']) ||
          matchedTopics.some(topic => /outside agency|medicare|medicaid|non facility|transition/.test(topic));
      }
      if (workflow === 'nors_lookup') {
        return matchedCodes.length || topicMatches.length;
      }
      return false;
    });

    return [...workflowRows, ...getWorkflowUpdateGuidanceForInputs({ norsCode, keywordText, topicMatches, resources }, data)];
  }

  function getKnowledgeHumanReviewWarnings({ norsCode, topicMatches = [], resources = [], keywordText = '' } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic)).join(' ');
    const text = normalizeTopicKey(keywordText);
    const resourceIds = new Set(resources.map(resource => resource.id).filter(Boolean));
    const hasBatch6Verification = getKnowledgeSourceVerificationRows(data).length > 0;
    const hasBatch7Verification = getKnowledgeBases(data).some(base => {
      return base?.meta?.batch === '7' || (base?.source_verification_rows || []).some(row => /^SV-B7-/.test(row.id || ''));
    });
    const hasBatch8Verification = getKnowledgeBases(data).some(base => {
      return base?.meta?.batch === '8' || (base?.source_verification_rows || []).some(row => /^SV-B8-/.test(row.source_id || row.id || ''));
    });
    const hasBatch9Verification = getKnowledgeBases(data).some(base => {
      return base?.meta?.batch === '9' || (base?.source_verification_rows || []).some(row => /^SV-B9-/.test(row.source_id || row.id || ''));
    });
    const hasCorrectedDischargeWorkflow = getKnowledgeWorkflowCorrections(data).some(row => row.workflow_id === 'WG-002');
    const warnings = [];

    getKnowledgeHumanReviewFlags(data).forEach(flag => {
      const id = flag.flag_id || flag.id || '';
      const action = cleanReviewText(flag.recommended_action || flag.action_required || flag.description || '');
      if (!action) return;

      if (id === 'HRF-B4-001' && !hasBatch6Verification && resourceIds.has('RR-024')) {
        warnings.push(`Source check (${id}): ${action}`);
      }
      if (id === 'HRF-B4-002' && !hasBatch6Verification && (
        matchedCodes.some(code => ['F04', 'F05', 'F07', 'F11', 'F12', 'I01', 'I02', 'I03', 'I04', 'I05'].includes(code)) ||
        /medication|infection/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B4-003' && !hasCorrectedDischargeWorkflow && matchedCodes.some(code => ['C01', 'C02'].includes(code))) {
        warnings.push(`Discharge workflow note (${id}): ${action}`);
      }
      if (id === 'HRF-B4-004' && /consent|permission|identity|authorization|release/.test(text)) {
        warnings.push(`Consent terminology note (${id}): ${action}`);
      }
      if (id === 'HRF-B4-005' && resourceIds.has('RR-005')) {
        warnings.push(`Resource caveat (${id}): ${action}`);
      }
      if (id === 'HRF-B5-001' && ['RR-019', 'RR-020', 'RR-021'].some(resourceId => resourceIds.has(resourceId))) {
        warnings.push(`Source review (${id}): ${action}`);
      }
      if (id === 'HRF-B5-002' && (
        matchedCodes.some(code => /^A0[1-5]$/.test(code)) ||
        resourceIds.has('RR-005')
      )) {
        warnings.push(`Mandatory reporting caveat (${id}): ${action}`);
      }
      if (id === 'HRF-B5-003' && (
        matchedCodes.some(code => /^A0[1-5]$/.test(code) || code === 'B03') ||
        /consent|permission|identity|authorization|disclosure|report/.test(text)
      )) {
        warnings.push(`Consent workflow note (${id}): ${action}`);
      }
      if (id === 'HRF-B5-004' && !hasCorrectedDischargeWorkflow && matchedCodes.some(code => ['C01', 'C02'].includes(code))) {
        warnings.push(`Discharge timeline note (${id}): ${action}`);
      }
      if (id === 'HRF-B5-005' && !hasBatch6Verification && (
        matchedCodes.some(code => ['F13', 'I01', 'I02', 'I03', 'I04', 'I05'].includes(code)) ||
        /infection|infection control/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B5-006' && !hasBatch6Verification && (
        matchedCodes.some(code => ['F04', 'F05', 'F07', 'F11', 'F12'].includes(code)) ||
        /medication|drug|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B5-007' && !hasBatch6Verification && (
        matchedCodes.some(code => ['J01', 'J02', 'J03'].includes(code)) ||
        ['RR-037', 'RR-038', 'RR-039'].some(resourceId => resourceIds.has(resourceId))
      )) {
        warnings.push(`Staffing resource caveat (${id}): ${action}`);
      }
      if (id === 'HRF-B6-001' && !hasBatch7Verification && (
        matchedCodes.some(code => ['F04', 'F05', 'F07', 'F11', 'F12'].includes(code)) ||
        /medication|drug|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Medication resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B6-002' && !hasBatch7Verification && (
        matchedCodes.some(code => ['F13', 'I01', 'I02', 'I03', 'I04', 'I05'].includes(code)) ||
        /infection|infection control|outbreak/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Infection-control resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B6-003' && resourceIds.has('RR-024')) {
        warnings.push(`CT LTCOP URL note (${id}): ${action}`);
      }
      if (id === 'HRF-B6-004' && /survey|inspection|care compare/.test(`${matchedTopics} ${text}`)) {
        warnings.push(`Survey-results URL note (${id}): ${action}`);
      }
      if (id === 'HRF-B6-005' && !hasBatch7Verification && (
        matchedCodes.some(code => ['F07', 'F11', 'F12'].includes(code)) ||
        /psychotropic|antipsychotic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`CMS QSO source note (${id}): ${action}`);
      }
      if (id === 'HRF-B7-001' && !hasBatch8Verification && (
        matchedCodes.some(code => ['F04', 'F07', 'F11', 'F12'].includes(code)) ||
        /medication|drug|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Medication handout gap (${id}): ${action}`);
      }
      if (id === 'HRF-B7-002' && !hasBatch8Verification && (
        matchedCodes.some(code => ['F07', 'F11', 'F12'].includes(code)) ||
        /psychotropic|antipsychotic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`CMS QSO source note (${id}): ${action}`);
      }
      if (id === 'HRF-B7-003' && !hasBatch8Verification && (
        matchedCodes.includes('F13') ||
        ['RR-B7-010', 'RR-B7-011'].some(resourceId => resourceIds.has(resourceId))
      )) {
        warnings.push(`Infection resource currency note (${id}): ${action}`);
      }
      if (id === 'HRF-B7-004' && !hasBatch8Verification && (
        ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
        ['RR-B7-001', 'RR-B7-002', 'RR-B7-003'].some(resourceId => resourceIds.has(resourceId))
      )) {
        warnings.push(`CT discharge resource currency note (${id}): ${action}`);
      }
      if (id === 'HRF-B8-001' && (
        matchedCodes.some(code => ['F04', 'F07', 'F11', 'F12'].includes(code)) ||
        /medication|drug|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Medication handout gap (${id}): ${action}`);
      }
      if (id === 'HRF-B8-002' && (
        matchedCodes.includes('F13') ||
        ['RR-B7-010', 'RR-B7-011'].some(resourceId => resourceIds.has(resourceId))
      )) {
        warnings.push(`Infection resource caveat (${id}): ${action}`);
      }
      if (id === 'HRF-B8-003' && !hasBatch9Verification && (
        matchedCodes.some(code => ['F07', 'F11', 'F12'].includes(code)) ||
        ['RR-B7-013', 'RR-B7-005'].some(resourceId => resourceIds.has(resourceId)) ||
        /qso 25 07|qso-25-07|f605|f757|f758|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`CMS QSO source note (${id}): ${action}`);
      }
      if (id === 'HRF-B8-004' && !hasBatch9Verification && (
        ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
        ['RR-B7-001', 'RR-B7-002', 'RR-B7-003'].some(resourceId => resourceIds.has(resourceId))
      )) {
        warnings.push(`CT discharge resource currency note (${id}): ${action}`);
      }
      if (id === 'HRF-B9-001' && (
        ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
        resourceIds.has('RR-B7-002')
      )) {
        warnings.push(`CT discharge portal manual note (${id}): ${action}`);
      }
      if (id === 'HRF-B9-002' && (
        matchedCodes.some(code => ['C01', 'C02', 'C03', 'F07', 'F11', 'F12'].includes(code)) ||
        ['RR-B7-003', 'RR-B7-005', 'RR-B7-013'].some(resourceId => resourceIds.has(resourceId)) ||
        /qso 25 07|qso-25-07|qso 25 14|qso-25-14|f627|f628|f605|f757|f758|psychotropic|discharge|transfer/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`CMS QSO source note (${id}): ${action}`);
      }
    });

    return warnings;
  }

  function getContextTipsForInputs({ norsCode, topicMatches = [], workflowGuidance = [], resources = [], keywordText = '' } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const contexts = new Set();
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic)).join(' ');
    const text = normalizeTopicKey(keywordText);
    const resourceIds = new Set(resources.map(resource => resource.id).filter(Boolean));
    const resourceUrls = resources.map(resource => resource.url || '').join(' ');

    if (matchedCodes.length || topicMatches.length) contexts.add('nors_lookup');
    matchedCodes.forEach(code => contexts.add(`nors_lookup_${code}`));
    workflowGuidance.forEach(row => {
      if (row.workflow) contexts.add(`${row.workflow}_workflow`);
    });

    return getKnowledgeTooltipRows(data).filter(row => {
      if (toArray(row.where_to_show).some(context => contexts.has(context))) return true;

      const type = row.tooltip_type || row.tooltip_id || '';
      if (type === 'staffing_rescission_notice') {
        return matchedCodes.some(code => ['J01', 'J02', 'J03'].includes(code)) ||
          /staffing|nursing staff|sufficient staff/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'qso_memo_correction_notice') {
        return resourceIds.has('RR-013') || /qso 26 03|qso-26-03|f610/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'f757_scope_notice') {
        return matchedCodes.some(code => ['F07', 'F11', 'F12'].includes(code)) ||
          /f757|psychotropic|antipsychotic|chemical restraint|unnecessary medication/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'ct_portal_url_caution') {
        return resourceIds.has('RR-024');
      }
      if (type === 'discharge_portal_notice') {
        return ['C02', 'C03'].some(code => matchedCodes.includes(code)) ||
          /discharge|transfer/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'ct_inspection_data_notice') {
        return ['RR-B7-006', 'RR-B7-007', 'RR-B7-008'].some(id => resourceIds.has(id)) ||
          /inspection|survey|care compare|deficiency|plan of correction/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'qso_25_07_nh_effective_date_notice') {
        return ['RR-B7-005', 'RR-B7-013', 'RR-025'].some(id => resourceIds.has(id)) ||
          /qso 25 07|qso-25-07|f605|f757|f758|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B8-001') {
        return ['RR-B7-005', 'RR-B7-013', 'RR-025'].some(id => resourceIds.has(id)) ||
          /qso 25 07|qso-25-07|f605|f757|f758|psychotropic|chemical restraint/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B8-002') {
        return matchedCodes.includes('F13') ||
          ['RR-B7-010', 'RR-B7-011', 'RR-B7-012'].some(id => resourceIds.has(id)) ||
          /infection|outbreak|covid/.test(`${matchedTopics} ${text}`);
      }
      if (isPureC04RoomLookup(matchedCodes, keywordText) && ['TT-B8-003', 'TT-B9-001', 'TT-B9-002'].includes(type)) {
        return false;
      }
      if (type === 'TT-B8-003') {
        return ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
          /discharge|transfer|appeal/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B9-001') {
        return ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
          /discharge|transfer|appeal|eviction|admission/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B9-002') {
        return ['C01', 'C02', 'C03'].some(code => matchedCodes.includes(code)) ||
          /discharge|transfer|appeal|hearing|stay/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B10-001') {
        return matchedCodes.some(code => ['F02', 'F09', 'J03'].includes(code)) ||
          /call bell|call bells|call light|call lights|no one came|toilet help|bathroom help/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B10-002') {
        return matchedCodes.includes('C04') ||
          /room change|moved rooms|moved to another room|lost my room|roommate/.test(`${matchedTopics} ${text}`);
      }
      if (type === 'TT-B10-003') {
        return matchedCodes.some(code => /^A0[1-5]$/.test(code)) ||
          /abuse|abused|gross neglect|rough handling|hit|slapped|exploitation/.test(`${matchedTopics} ${text}`);
      }
      return false;
    });
  }

  function getAuthorityIndex(data) {
    const authorities = data.authorityIndex?.authorities || {};
    if (Array.isArray(authorities)) {
      return authorities.reduce((index, authority) => {
        index[authority.authority_id] = authority;
        return index;
      }, {});
    }
    return authorities;
  }

  function isSupersededCallLightKnowledgeKeyword(row = {}, phrase = '') {
    const normalizedPhrase = String(phrase || '').toLowerCase().trim();
    const code = row.nors_code || row.primary_code || '';
    return ['F01', 'F07', 'F09'].includes(code) &&
      ['call light', 'call lights', 'call light ignored', 'call light not answered'].includes(normalizedPhrase);
  }

  function getKeywordEntries(data) {
    const keywords = data.keywordMap?.keywords || {};
    const mappedEntries = Array.isArray(keywords) ? keywords : Object.entries(keywords).map(([phrase, topics]) => ({
      phrase,
      topics
    }));
    const catalogRecords = getCatalogRecords(data);
    const topicByNorsCode = catalogRecords.reduce((index, record) => {
      if (record.nors_minor_code && record.topic_slug) index[record.nors_minor_code] = record.topic_slug;
      return index;
    }, {});
    const knownTopics = new Set(catalogRecords.map(record => record.topic_slug).filter(Boolean));
    const catalogEntries = catalogRecords.flatMap(record => {
      const phrases = [
        record.topic_label,
        record.nors_minor_label,
        ...(record.keywords || [])
      ].filter(Boolean);
      const labelPrefix = (record.nors_minor_label || '').split(':')[0].trim();
      if (labelPrefix) phrases.push(labelPrefix);

      return phrases.map(phrase => ({
        phrase,
        topics: [record.topic_slug],
        likely_nors_codes: [record.nors_minor_code]
      }));
    });
    const complaintGuidanceEntries = (data?.norsComplaintGuidance?.items || []).flatMap(item => {
      const topic = topicByNorsCode[item.code];
      if (!topic) return [];
      return (item.likely_phrases || []).map(phrase => ({
        phrase,
        topics: [topic],
        likely_nors_codes: [item.code]
      }));
    });
    const knowledgeGuidanceEntries = getKnowledgeCodeRows(data).map(normalizeKnowledgeSummary).flatMap(row => {
      const topic = topicByNorsCode[row.nors_code];
      if (!topic) return [];
      return (row.common_concern_phrases || []).map(phrase => ({
        phrase,
        topics: [topic],
        likely_nors_codes: [row.nors_code]
      }));
    });
    const knowledgeKeywordEntries = getKnowledgeKeywordRows(data).flatMap(row => {
      const likelyCodes = toArray(row.nors_code || row.likely_nors_codes || row.primary_code).filter(Boolean);
      const rowTopics = toArray(row.topics || row.topic_slugs)
        .filter(topic => knownTopics.has(topic));
      const codeTopics = likelyCodes
        .map(code => topicByNorsCode[code])
        .filter(Boolean);
      const topics = [...new Set([...rowTopics, ...codeTopics])];
      if (!topics.length) return [];
      const authorityIds = (row.related_ftags || [])
        .map(item => normalizeAuthorityCitation(item).toLowerCase())
        .filter(item => item && item !== 'f556')
        .map(item => item === 'f758' ? 'f605' : item)
        .concat(toArray(row.authority_ids));
      const phrases = toArray(row.keywords).length
        ? toArray(row.keywords)
        : splitPhrasePattern(row.phrase_pattern || row.phrase || row.pattern);
      return phrases.filter(phrase => !isSupersededCallLightKnowledgeKeyword(row, phrase)).map(phrase => ({
        phrase,
        topics,
        likely_nors_codes: likelyCodes,
        authority_ids: [...new Set(authorityIds.filter(Boolean))],
        notes: row.notes || row.explanation_for_trace || (row.ombudsman_tips || []).join(' ')
      }));
    });

    return [...mappedEntries, ...catalogEntries, ...complaintGuidanceEntries, ...knowledgeGuidanceEntries, ...knowledgeKeywordEntries].map(entry => ({
      ...entry,
      topics: toArray(entry.topics).filter(Boolean),
      likely_nors_codes: toArray(entry.likely_nors_codes).filter(Boolean),
      authority_ids: toArray(entry.authority_ids).filter(Boolean)
    }));
  }

  function toArray(value) {
    if (!value) return [];
    return Array.isArray(value) ? value : [value];
  }

  function getWordTokens(value) {
    return String(value || '').toLowerCase().match(/[a-z0-9]+/g) || [];
  }

  function getWordStem(value) {
    let token = String(value || '').toLowerCase();
    if (token === 'staffing') return token;
    if (token.endsWith('ies') && token.length > 4) return `${token.slice(0, -3)}y`;
    if (token.endsWith('ing') && token.length > 5) token = token.slice(0, -3);
    if (token.endsWith('ed') && token.length > 4) token = token.slice(0, -2);
    if (token.endsWith('s') && token.length > 3) token = token.slice(0, -1);
    if (token.endsWith('e') && token.length > 3) token = token.slice(0, -1);
    return token;
  }

  function tokensMatch(keywordToken, textToken) {
    if (keywordToken === textToken) return true;
    return getWordStem(keywordToken) === getWordStem(textToken);
  }

  function keywordPhraseMatches(phrase, searchableText, searchableTokens) {
    const normalizedPhrase = String(phrase || '').toLowerCase().trim();
    if (!normalizedPhrase) return false;
    if (searchableText.includes(normalizedPhrase)) return true;

    const phraseTokens = getWordTokens(normalizedPhrase);
    if (!phraseTokens.length) return false;
    return phraseTokens.every(phraseToken => {
      return searchableTokens.some(textToken => tokensMatch(phraseToken, textToken));
    });
  }

  function getTopicsFromNorsCode(norsCode, data) {
    const topicMatches = {};
    const code = (norsCode || '').trim();
    if (!code) return [];

    const catalogTopics = getCatalogRecords(data)
      .filter(record => record.nors_minor_code === code)
      .map(record => record.topic_slug)
      .filter(Boolean);
    const mappedTopics = catalogTopics.length ? catalogTopics : data.norsToTopic?.[code] || [];

    mappedTopics.forEach(topic => {
      addTopic(topicMatches, topic, 'nors', code);
    });

    return sortTopicMatches(topicMatches);
  }

  function getTopicsFromKeywords(text, data) {
    const topicMatches = {};
    const searchableText = (text || '').toLowerCase();
    const searchableTokens = getWordTokens(searchableText);
    if (!searchableText) return [];

    getKeywordEntries(data).forEach(entry => {
      const phrase = entry.phrase || '';
      if (keywordPhraseMatches(phrase, searchableText, searchableTokens)) {
        (entry.topics || []).forEach(topic => {
          addTopic(topicMatches, topic, 'keyword', phrase);
          (entry.likely_nors_codes || []).forEach(code => addTopic(topicMatches, topic, 'likely_nors', code));
        });
      }
    });

    return sortTopicMatches(topicMatches);
  }

  function getTopicsFromInputs({ norsCode, keywordText } = {}, data) {
    const topicMatches = {};
    const rules = data.retrievalRules?.matching || {};
    const useNorsFirst = rules.use_nors_code_first !== false;
    const useKeywordFallback = rules.use_keyword_fallback !== false;

    if (useNorsFirst) {
      getTopicsFromNorsCode(norsCode, data).forEach(match => {
        match.norsCodes.forEach(code => addTopic(topicMatches, match.topic, 'nors', code));
      });
    }

    if (useKeywordFallback) {
      getTopicsFromKeywords(keywordText, data).forEach(match => {
        match.likelyNorsCodes.forEach(code => addTopic(topicMatches, match.topic, 'likely_nors', code));
        match.keywords.forEach(keyword => addTopic(topicMatches, match.topic, 'keyword', keyword));
      });
    }

    return sortTopicMatches(topicMatches);
  }

  function getAuthorityLabel(authority = {}) {
    if (isAppendixPpAuthority(authority)) return 'CMS Appendix PP Survey Guidance';
    if (authority.category) return authority.category;
    const type = authority.type || '';
    const layer = authority.layer || '';
    const title = (authority.title || '').toLowerCase();

    if (type === 'federal_regulation' && title.includes('resident rights')) {
      return 'Federal Resident Rights';
    }
    if (type === 'federal_regulation' || layer === 'federal') {
      return 'Federal Regulation';
    }
    if (type === 'appendix_pp' || layer === 'appendix_pp') {
      return 'CMS Appendix PP Survey Guidance';
    }
    if (type === 'training' || layer === 'training') {
      return 'Training / Guidance';
    }
    return type || layer ? `${layer || type}`.replace(/_/g, ' ') : 'Reference';
  }

  function isAppendixPpAuthority(authority = {}) {
    const citation = authority.citation || authority.authority_citation || '';
    const category = authority.category || authority.label || '';
    const type = authority.type || authority.authority_type || '';
    const layer = authority.layer || '';
    const url = authority.url || authority.appendix_pp_pdf_url || authority.appendixPpPdfUrl || '';
    return /^F\d+/i.test(citation) ||
      /^appendix_pp/i.test(type) ||
      layer === 'appendix_pp' ||
      /Appendix PP/i.test(category) ||
      /som107ap_pp|appendix-pp/i.test(url);
  }

  function getAuthorityLevel(authority = {}) {
    if (isAppendixPpAuthority(authority)) return 'interpretive_guidance';
    if (/Federal Regulation|Resident Rights/i.test(authority.category || authority.label || '')) return 'regulation';
    if (/State Statute|State Regulation/i.test(authority.category || authority.label || '')) return 'state_authority';
    if (/Ombudsman Program Authority/i.test(authority.category || authority.label || '')) return 'program_authority';
    return authority.authority_level || authority.authorityLevel || '';
  }

  function getAuthorityGuidanceNote(authority = {}) {
    if (!isAppendixPpAuthority(authority)) return '';
    return 'CMS Appendix PP is interpretive survey guidance tied to federal nursing facility requirements. It supports review and context; this tool does not determine violations.';
  }

  function getMatchSummary(match) {
    const parts = [];
    if (match.norsCodes?.length) parts.push(`NORS: ${match.norsCodes.join(', ')}`);
    if (match.keywords?.length) parts.push(`keywords: ${match.keywords.map(keyword => `"${keyword}"`).join(', ')}`);
    return parts.join('; ');
  }

  function formatTopicName(topic) {
    return String(topic || '').replace(/_/g, ' ');
  }

  function getCtStatuteSection(value) {
    const sectionMatch = String(value || '').match(/\b(17a|19a)-\d+[a-z]?\b/i);
    return sectionMatch ? sectionMatch[0].toLowerCase() : '';
  }

  function getCtStatuteChapterUrl(authority = {}) {
    const citation = authority.citation || '';
    const explicitUrl = authority.url || '';
    const searchText = `${citation} ${explicitUrl} ${authority.authority_id || ''}`;
    const section = getCtStatuteSection(searchText);

    if (section.startsWith('17a-')) return CT_OMBUDSMAN_STATUTES_URL;
    if (section.startsWith('19a-')) return CT_NURSING_HOME_STATUTES_URL;
    if (/chapter\s*319l|chap_319l|ct_17a_870/i.test(searchText)) return CT_OMBUDSMAN_STATUTES_URL;
    if (/chapter\s*368v|chap_368v|ct_nursing_home_statutes/i.test(searchText)) return CT_NURSING_HOME_STATUTES_URL;
    return '';
  }

  function getCtStatuteUrl(authority = {}) {
    const citation = authority.citation || '';
    const explicitUrl = authority.url || '';

    if (/cga\.ct\.gov/i.test(explicitUrl) && /#sec_/i.test(explicitUrl)) {
      return explicitUrl;
    }

    const baseUrl = getCtStatuteChapterUrl(authority);
    if (!baseUrl) return '';

    const section = getCtStatuteSection(`${citation} ${explicitUrl}`);
    return section ? `${baseUrl}#sec_${section}` : baseUrl;
  }

  function getSourceRegistry(data) {
    return data?.sourceRegistry?.sources || [];
  }

  function findSourceById(data, id) {
    return getSourceRegistry(data).find(source => source.id === id) || null;
  }

  function getSourceIdForAuthority(authority = {}) {
    const citation = authority.citation || '';
    const category = authority.category || authority.label || '';
    const url = authority.url || '';

    if (/^F\d+/i.test(citation) || /Appendix PP/i.test(category) || /som107ap_pp|appendix-pp/i.test(url)) return 'cms_appendix_pp';
    if (/42\s+CFR/i.test(citation) || /title-42|part-483/i.test(url)) return 'ecfr_42_part_483';
    if (/45\s+CFR/i.test(citation) || /title-45|part-1324/i.test(url)) return 'ecfr_45_part_1324';
    if (/19-13-D8t/i.test(citation) || /eregulations\.ct\.gov/i.test(url)) return 'ct_eregulations_19_13_d8t';
    if (/17a-/i.test(citation) || /chap_319l/i.test(url) || authority.authority_id === 'ct_17a_870') return 'ct_chapter_319l';
    if (/19a-/i.test(citation) || /^CGS/i.test(citation) || /chap_368v/i.test(url)) return 'ct_chapter_368v';
    if (/NORS/i.test(category) || /ltcombudsman\.org/i.test(url)) return 'nors_table_2';
    return '';
  }

  function getAuthoritySourceInfo(authority = {}, data) {
    const sourceId = authority.source_id || authority.sourceId || getSourceIdForAuthority(authority);
    const source = sourceId ? findSourceById(data, sourceId) : null;
    if (!source) return null;

    return {
      id: source.id,
      title: source.title,
      owner: source.owner,
      category: source.category,
      url: source.url,
      versionOrRevision: source.version_or_revision || '',
      lastVerified: source.last_verified || ''
    };
  }

  function getCtStatuteUrlFromCitation(citation) {
    const section = getCtStatuteSection(citation);
    if (!section) return '';
    const baseUrl = section.startsWith('17a-') ? CT_OMBUDSMAN_STATUTES_URL : CT_NURSING_HOME_STATUTES_URL;
    return `${baseUrl}#sec_${section}`;
  }

  function getAuthorityIdFromKnowledgeRow(row = {}) {
    const citation = normalizeAuthorityCitation(row.authority_citation || row.citation || '');
    const ftagMatch = citation.match(/^F\d+/i);
    if (ftagMatch) return ftagMatch[0].toLowerCase();

    const cfrMatch = citation.match(/\b(42|45)\s+CFR\s+(?:§\s*)?([0-9.]+)/i);
    if (cfrMatch) {
      const subsectionParts = [...citation.matchAll(/\(([a-z0-9]+)\)/gi)].map(match => match[1].toLowerCase());
      return `${cfrMatch[1]}cfr_${cfrMatch[2].replace(/\./g, '_')}${subsectionParts.length ? `_${subsectionParts.join('_')}` : ''}`;
    }

    const ctSection = getCtStatuteSection(citation);
    if (ctSection) {
      const subsectionParts = [...citation.matchAll(/\(([a-z0-9]+)\)/gi)].map(match => match[1].toLowerCase());
      return `ct_${ctSection.replace(/-/g, '_')}${subsectionParts.length ? `_${subsectionParts.join('_')}` : ''}`;
    }

    return String(citation || row.authority_label || 'authority')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
  }

  function getKnowledgeAuthorityCategory(row = {}) {
    const type = row.authority_type || '';
    if (type.startsWith('appendix_pp')) return 'CMS Appendix PP Survey Guidance';
    if (type.startsWith('federal_reg')) return 'Federal Regulation';
    if (type === 'ombudsman_authority') return 'Ombudsman Program Authority';
    if (type === 'ct_statute' || type === 'state_overlay') return 'State Statute';
    if (type === 'ct_regulation') return 'State Regulation';
    if (type === 'handout_resource' || type === 'ct_official_resource') return 'Training';
    return 'Reference';
  }

  function getKnowledgeAuthorityUrl(row = {}) {
    const citation = normalizeAuthorityCitation(row.authority_citation || row.citation || '');
    const ftagMatch = citation.match(/^F\d+/i);
    if (ftagMatch) {
      return row.appendix_pp_pdf_url || APPENDIX_PP_URL;
    }

    const cfrMatch = citation.match(/\b(42|45)\s+CFR\s+(?:§\s*)?([0-9.]+)/i);
    if (cfrMatch?.[1] === '42') {
      return `https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483/subpart-B/section-${cfrMatch[2]}`;
    }
    if (cfrMatch?.[1] === '45') {
      return `https://www.ecfr.gov/current/title-45/subtitle-B/chapter-XIII/subchapter-C/part-1324/subpart-A/section-${cfrMatch[2]}`;
    }

    const ctUrl = getCtStatuteUrlFromCitation(citation);
    return ctUrl || row.authority_url || '';
  }

  function getKnowledgeMappingType(row = {}) {
    if (row.authority_type === 'ct_statute' || row.authority_type === 'ct_regulation' || row.authority_type === 'state_overlay') return 'state_overlay';
    return row.mapping_confidence || 'related';
  }

  function normalizeAuthorityCitation(citation) {
    const value = String(citation || '').trim();
    const ftagMatch = value.match(/^F\d+/i);
    if (ftagMatch) return ftagMatch[0].toUpperCase();
    return value.replace(/\s*\(page\s*\d+\)\s*/i, '').trim();
  }

  function getKnowledgeAuthorityMappingsForMatch(match = {}, data) {
    const matchedCodes = [...new Set([...(match.norsCodes || []), ...(match.likelyNorsCodes || [])])];
    if (!matchedCodes.length) return [];

    return getKnowledgeAuthorityRows(data)
      .filter(row => matchedCodes.includes(row.nors_code))
      .filter(row => !KNOWLEDGE_AUTHORITY_ROW_SKIP.has(`${row.nors_code}|${normalizeAuthorityCitation(row.authority_citation || row.citation || '')}`))
      .filter(row => normalizeAuthorityCitation(row.authority_citation || row.citation || '') !== 'F556')
      .map(row => {
        const citation = normalizeAuthorityCitation(row.authority_citation || row.citation || '');
        const redirectedCitation = citation === 'F758' ? 'F605' : citation;
        const mappingType = getKnowledgeMappingType(row);
        const isAppendixPp = isAppendixPpAuthority(row);
        return {
          authority_id: citation === 'F758' ? 'f605' : getAuthorityIdFromKnowledgeRow(row),
          reason: row.mapping_rationale_short || row.notes || `${mappingType.replace(/_/g, ' ')} knowledge-base mapping`,
          citation: redirectedCitation,
          title: row.authority_label || row.description || '',
          category: getKnowledgeAuthorityCategory(row),
          authorityLevel: isAppendixPp ? 'interpretive_guidance' : '',
          guidanceNote: isAppendixPp ? getAuthorityGuidanceNote({ authority_type: 'appendix_pp' }) : '',
          url: getKnowledgeAuthorityUrl(row),
          mapping_type: mappingType,
          human_review_note: row.human_review_note || '',
          official_source_urls: row.official_source_urls || [],
          appendixPpPdfUrl: row.appendix_pp_pdf_url || '',
          appendixPpHeadingExact: row.appendix_pp_heading_exact || '',
          appendixPpPageStart: row.appendix_pp_pdf_page_start || null
        };
      });
  }

  function getAppendixPpTagPage(fTag, data) {
    const tag = String(fTag || '').toUpperCase();
    const rows = data?.appendixPpTagPages?.appendix_pp_tag_page_rows || [];
    return rows.find(row => String(row.f_tag || '').toUpperCase() === tag) || null;
  }

  function applyAppendixPpTagPage(authority = {}, data) {
    const citation = authority.citation || '';
    const ftagMatch = citation.match(/^F\d+/i);
    if (!ftagMatch) return authority;

    const tag = ftagMatch[0].toUpperCase();
    const pageRow = getAppendixPpTagPage(tag, data);
    if (!pageRow || pageRow.status !== 'confirmed' || !pageRow.appendix_pp_pdf_page_start) return authority;

    return {
      ...authority,
      appendixPpPageStart: pageRow.appendix_pp_pdf_page_start,
      appendixPpHeadingExact: pageRow.heading_exact || '',
      appendixPpPdfUrl: pageRow.appendix_pp_pdf_url || APPENDIX_PP_URL,
      url: `${pageRow.appendix_pp_pdf_url || APPENDIX_PP_URL}#page=${pageRow.appendix_pp_pdf_page_start}`
    };
  }

  function getAuthorityUrl(authority = {}) {
    const citation = authority.citation || '';
    const category = authority.category || authority.label || '';
    const cfrMatch = citation.match(/\b(42|45)\s+CFR\s+(?:§|Â§)?\s*([0-9.]+)/i);
    if (cfrMatch?.[1] === '42') {
      return `https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483/subpart-B/section-${cfrMatch[2]}`;
    }
    if (cfrMatch?.[1] === '45') {
      return `https://www.ecfr.gov/current/title-45/subtitle-B/chapter-XIII/subchapter-C/part-1324/subpart-A/section-${cfrMatch[2]}`;
    }
    const ftagMatch = citation.match(/^F\d+/i);
    if (ftagMatch) {
      if (authority.url && /#page=/i.test(authority.url)) return authority.url;
      if (authority.appendixPpPageStart) {
        return `${authority.appendixPpPdfUrl || APPENDIX_PP_URL}#page=${authority.appendixPpPageStart}`;
      }
      const ftag = ftagMatch[0].toUpperCase();
      const page = APPENDIX_PP_PAGE_BY_FTAG[ftag];
      return page ? `${APPENDIX_PP_URL}#page=${page}` : APPENDIX_PP_URL;
    }
    if (/19-13-D8t/i.test(citation) || authority.authority_id === 'ct_nursing_home_regs') {
      return CT_NURSING_HOME_REGS_URL;
    }
    if (/State Statute/i.test(category) || /^CGS/i.test(citation)) {
      const ctStatuteUrl = getCtStatuteUrl(authority);
      if (ctStatuteUrl) return ctStatuteUrl;
      if (/State Statute/i.test(category) && authority.url) return authority.url;

      const sectionMatch = citation.match(/(?:§+|Sec\.?\s*)\s*(17a-\d+[a-z]?|19a-\d+[a-z]?)/i);
      if (/17a-/i.test(citation) || authority.authority_id === 'ct_17a_870') {
        return sectionMatch
          ? `${CT_OMBUDSMAN_STATUTES_URL}#sec_${sectionMatch[1].toLowerCase()}`
          : CT_OMBUDSMAN_STATUTES_URL;
      }
      return sectionMatch
        ? `${CT_NURSING_HOME_STATUTES_URL}#sec_${sectionMatch[1].toLowerCase()}`
        : CT_NURSING_HOME_STATUTES_URL;
    }
    if (authority.url) return authority.url;
    return '';
  }
  function normalizeAuthority(authorityId, authority, reason, match, data) {
    const sourceInfo = getAuthoritySourceInfo(authority, data);
    return {
      id: authorityId,
      citation: authority?.citation || 'Citation not available',
      title: authority?.title || (authority ? 'Title not available' : 'Authority metadata not found'),
      category: authority ? getAuthorityLabel(authority) : 'Missing metadata',
      label: authority ? getAuthorityLabel(authority) : 'Missing metadata',
      url: getAuthorityUrl(authority),
      reason: reason || (authority ? 'Selected by topic mapping.' : 'Selected by topic mapping, but details are missing from authority index.'),
      matchSummary: getMatchSummary(match),
      rank: authority ? 0 : -1,
      missing: !authority,
      authorityLevel: authority ? getAuthorityLevel(authority) : '',
      guidanceNote: authority ? getAuthorityGuidanceNote(authority) : '',
      humanReviewNote: authority?.human_review_note || authority?.humanReviewNote || '',
      officialSourceUrls: authority?.official_source_urls || authority?.officialSourceUrls || [],
      appendixPpHeadingExact: authority?.appendixPpHeadingExact || authority?.appendix_pp_heading_exact || '',
      appendixPpPageStart: authority?.appendixPpPageStart || authority?.appendix_pp_pdf_page_start || null,
      sourceInfo
    };
  }

  function normalizeMappingList(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'object' && Object.keys(value).length) return [value];
    return [];
  }

  function getAuthoritiesForTopics(topicMatches, data) {
    const topicMap = data.topicToAuthority?.topics || {};
    const authorityIndex = getAuthorityIndex(data);
    const ranking = data.retrievalRules?.ranking || {};
    const output = data.retrievalRules?.output || {};
    const maxResults = data.retrievalRules?.max_results || output.max_results || 8;
    const dedupe = data.retrievalRules?.dedupe !== false && data.retrievalRules?.matching?.deduplicate_authorities !== false;
    const catalogRecords = getCatalogRecords(data);
    const groups = [];
    const seen = new Set();
    let resultCount = 0;

    topicMatches.forEach(match => {
      const authorities = [];
      const matchedCodesForTopic = [...new Set([...(match.norsCodes || []), ...(match.likelyNorsCodes || [])])];
      const catalogMappings = catalogRecords
        .filter(record => {
          if (matchedCodesForTopic.length) return matchedCodesForTopic.includes(record.nors_minor_code);
          return record.topic_slug === match.topic;
        })
        .flatMap(record => [
          ...normalizeMappingList(record.federal_regulations),
          ...normalizeMappingList(record.appendix_pp_tags),
          ...normalizeMappingList(record.connecticut_overlay)
        ])
        .filter(item => item.authority_id)
        .map(item => ({
          authority_id: item.authority_id,
          reason: item.reason || item.mapping_rationale_short || (item.mapping_type ? `${item.mapping_type.replace(/_/g, ' ')} mapping` : ''),
          citation: item.citation,
          title: item.title,
          category: item.category,
          url: item.url,
          mapping_type: item.mapping_type,
          human_review_note: item.human_review_note || '',
          official_source_urls: item.official_source_urls || []
        }));
      const knowledgeMappings = getKnowledgeAuthorityMappingsForMatch(match, data);
      const hasExactOmbudsmanAuthority = knowledgeMappings.some(item => /^45cfr_1324_19_/.test(item.authority_id));
      const hasExactCtStatute = knowledgeMappings.some(item => item.category === 'State Statute');
      const filteredCatalogMappings = catalogMappings.filter(item => {
        if (hasExactOmbudsmanAuthority && item.authority_id === '45cfr_1324_19') return false;
        if (hasExactCtStatute && item.authority_id === 'ct_nursing_home_statutes') return false;
        return true;
      });
      const baseMappings = filteredCatalogMappings.length ? filteredCatalogMappings : topicMap[match.topic] || [];
      const mappings = [...knowledgeMappings, ...baseMappings];

      mappings.forEach(item => {
        if (resultCount >= maxResults) return;
        if (dedupe && seen.has(item.authority_id)) return;

        const indexedAuthority = authorityIndex[item.authority_id] || {};
        const authority = applyAppendixPpTagPage({
          ...indexedAuthority,
          authority_id: item.authority_id,
          citation: item.citation || indexedAuthority.citation,
          title: item.title || indexedAuthority.title,
          category: item.category || indexedAuthority.category,
          authorityLevel: item.authorityLevel || indexedAuthority.authorityLevel || indexedAuthority.authority_level || '',
          guidanceNote: item.guidanceNote || indexedAuthority.guidanceNote || '',
          url: item.url || indexedAuthority.url,
          human_review_note: item.human_review_note || indexedAuthority.human_review_note || '',
          official_source_urls: item.official_source_urls || indexedAuthority.official_source_urls || [],
          appendixPpPdfUrl: item.appendixPpPdfUrl || indexedAuthority.appendixPpPdfUrl || '',
          appendixPpHeadingExact: item.appendixPpHeadingExact || indexedAuthority.appendixPpHeadingExact || '',
          appendixPpPageStart: item.appendixPpPageStart || indexedAuthority.appendixPpPageStart || null
        }, data);
        seen.add(item.authority_id);
        resultCount += 1;

        const normalized = normalizeAuthority(item.authority_id, authority, item.reason, match, data);
        normalized.rank = authority ? ranking[authority.type] || ranking[authority.category] || 0 : -1;
        authorities.push(normalized);
      });

      authorities.sort((a, b) => b.rank - a.rank || a.citation.localeCompare(b.citation));
      if (authorities.length) {
        groups.push({
          topic: match.topic,
          norsCodes: match.norsCodes || [],
          keywords: match.keywords || [],
          authorities,
          references: authorities
        });
      }
    });

    return groups;
  }

  function getFTagFromValue(value) {
    const match = String(value || '').match(/\bF\d{3}\b/i);
    return match ? match[0].toUpperCase() : '';
  }

  function getAuthorityFtags(authorityGroups = []) {
    const tags = new Set();
    authorityGroups.forEach(group => {
      (group.authorities || []).forEach(authority => {
        [
          authority.citation,
          authority.id,
          authority.title,
          authority.appendixPpHeadingExact,
          authority.appendix_pp_heading_exact
        ].forEach(value => {
          const tag = getFTagFromValue(value);
          if (tag) tags.add(tag);
        });
      });
    });
    return tags;
  }

  function getAppendixPpRelatedInvestigationRowsForInputs({ norsCode, keywordText = '', topicMatches = [], authorityGroups = [] } = {}, data) {
    const rows = getKnowledgeAppendixPpRelatedRows(data);
    if (!rows.length) return [];

    const authorityFtags = getAuthorityFtags(authorityGroups);
    const matchedCodes = new Set(getMatchedNorsCodes(norsCode, topicMatches));
    const matchedTopicText = topicMatches.map(match => normalizeTopicKey(match.topic)).join(' ');
    const keywordSearchText = normalizeTopicKey(keywordText);
    const seen = new Set();

    return rows.filter(row => {
      const sourceTag = getFTagFromValue(row.source_ftag);
      const relatedTag = getFTagFromValue(row.related_ftag);
      const likelyCodes = toArray(row.likely_nors_codes);
      const relatedTopics = toArray(row.related_topics).map(normalizeTopicKey);
      const reasons = [];

      if (sourceTag && authorityFtags.has(sourceTag)) {
        reasons.push(`current authority trail includes ${sourceTag}`);
      }
      if (relatedTag && authorityFtags.has(relatedTag)) {
        reasons.push(`current authority trail includes related tag ${relatedTag}`);
      }
      likelyCodes.filter(code => matchedCodes.has(code)).forEach(code => {
        reasons.push(`matched related NORS code ${code}`);
      });
      relatedTopics.filter(topic => {
        return topic && (
          (matchedTopicText && matchedTopicText.includes(topic)) ||
          (matchedTopicText && topic.includes(matchedTopicText)) ||
          keywordSearchText.includes(topic)
        );
      }).forEach(topic => {
        reasons.push(`matched related topic ${topic}`);
      });

      if (!reasons.length) return false;
      row.match_reason = reasons[0];
      return true;
    }).filter(row => {
      const id = row.rule_id || `${row.source_ftag}-${row.related_ftag}`;
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    }).sort((a, b) => {
      const aSourceMatch = authorityFtags.has(a.source_ftag) ? 0 : 1;
      const bSourceMatch = authorityFtags.has(b.source_ftag) ? 0 : 1;
      return aSourceMatch - bSourceMatch || String(a.related_ftag || '').localeCompare(String(b.related_ftag || ''));
    });
  }

  function buildCrosswalkTrace({ norsCode, keywordText, topicMatches, authorityGroups, data } = {}) {
    const trace = [];
    const code = (norsCode || '').trim();
    const keyword = (keywordText || '').trim();
    const addTrace = (message, links = []) => {
      trace.push({ message, links: links.filter(link => link && link.url) });
    };

    if (code && !topicMatches.some(match => match.norsCodes.includes(code))) {
      addTrace(`The selected NORS code ${code} did not map to a topic in the local crosswalk data.`);
    }

    if (keyword && !topicMatches.some(match => match.keywords.length)) {
      addTrace('The keyword / concern text did not match a keyword phrase, NORS label, or catalog keyword in the local crosswalk data.');
    } else if (!keyword) {
      addTrace('No keyword / concern text was used for this run; results are based on the selected NORS code only.');
    }

    topicMatches.forEach(match => {
      if (match.norsCodes.length) {
        const codeLabels = match.norsCodes.map(item => {
          const detail = getNorsCodeDetail(item, data || {});
          return detail ? `${item} (${detail.label})` : item;
        });
        addTrace(`Selected NORS code ${codeLabels.join(', ')} maps to the topic "${formatTopicName(match.topic)}".`, [{
          label: 'NORS Table 2',
          url: NORS_TABLE_2_URL
        }]);
      }
      if (match.keywords.length) {
        addTrace(`The keyword text matched ${match.keywords.map(item => `"${item}"`).join(', ')}, which maps to the topic "${formatTopicName(match.topic)}".`);
      }
      if (match.likelyNorsCodes?.length) {
        const codeLabels = match.likelyNorsCodes.map(item => {
          const detail = getNorsCodeDetail(item, data || {});
          return detail ? `${item} (${detail.label})` : item;
        });
        addTrace(`Based on matched keywords, the crosswalk suggests likely NORS code${codeLabels.length === 1 ? '' : 's'} ${codeLabels.join(', ')} for review.`, [{
          label: 'NORS Table 2',
          url: NORS_TABLE_2_URL
        }]);
      }

      const group = authorityGroups.find(item => item.topic === match.topic);
      if (!group || !group.authorities.length) {
        addTrace(`The topic "${formatTopicName(match.topic)}" was identified, but no authority references were found for it.`);
        return;
      }

      addTrace(`The topic "${formatTopicName(match.topic)}" surfaced ${group.authorities.length} possible reference${group.authorities.length === 1 ? '' : 's'} from the crosswalk data and knowledge base.`, group.authorities.map(authority => ({
        label: authority.citation,
        url: authority.url
      })));
      group.authorities.forEach(authority => {
        if (authority.missing) {
          addTrace(`Authority metadata is missing for ${authority.id}.`);
        } else {
          addTrace(`${authority.citation} (${authority.title}) is included as a ${authority.category} reference because ${authority.reason || 'it is mapped to the identified topic'}.`, [{
            label: authority.citation,
            url: authority.url
          }]);
        }
      });
    });

    return trace;
  }

  function runCrosswalk({ norsCode, keywordText } = {}, data) {
    const code = (norsCode || '').trim();
    const text = (keywordText || '').trim();
    const norsMatches = code ? getTopicsFromNorsCode(code, data) : [];
    const keywordMatches = text ? getTopicsFromKeywords(text, data) : [];
    const topicMatches = mergeTopicMatches(norsMatches, keywordMatches);
    const authorityGroups = getAuthoritiesForTopics(topicMatches, data);
    const resources = getResourcesForInputs({ norsCode: code, keywordText: text, topicMatches }, data);
    const workflowGuidance = getWorkflowGuidanceForInputs({ norsCode: code, keywordText: text, topicMatches, resources }, data);
    const contextTips = getContextTipsForInputs({ norsCode: code, topicMatches, workflowGuidance, resources, keywordText: text }, data);
    const relatedInvestigations = getAppendixPpRelatedInvestigationRowsForInputs({ norsCode: code, keywordText: text, topicMatches, authorityGroups }, data);
    const trace = buildCrosswalkTrace({ norsCode: code, keywordText: text, topicMatches, authorityGroups, data });
    const warnings = [];

    if (!topicMatches.length) {
      warnings.push('No topics were matched from the supplied NORS code or keyword text.');
    }
    if (topicMatches.length && !authorityGroups.length) {
      warnings.push('Topics were matched, but no authority references were found.');
    }
    getKnowledgeCaveatWarnings(code, topicMatches, data).forEach(warning => warnings.push(warning));
    workflowGuidance.forEach(row => {
      if (row.do_not_say) warnings.push(`Workflow guardrail (${row.id}): ${row.do_not_say}`);
    });
    getKnowledgeHumanReviewWarnings({ norsCode: code, topicMatches, resources, keywordText: text }, data).forEach(warning => warnings.push(warning));
    authorityGroups.forEach(group => {
      group.authorities.forEach(authority => {
        if (authority.missing) {
          warnings.push(`Authority metadata missing for ${authority.id}.`);
        }
      });
    });

    return {
      topicMatches,
      authorityGroups,
      relatedInvestigations,
      resources,
      workflowGuidance,
      contextTips,
      trace,
      warnings
    };
  }

  window.Crosswalk = {
    loadCrosswalkData,
    getTopicsFromNorsCode,
    getTopicsFromKeywords,
    getTopicsFromInputs,
    getAuthoritiesForTopics,
    getNorsCodeOptions,
    getNorsCodeDetail,
    getResourcesForInputs,
    getAppendixPpRelatedInvestigationRowsForInputs,
    getKnowledgeResourceRows,
    getKnowledgeWorkflowRows,
    getKnowledgeSourceQualityRows,
    getKnowledgeExplainerRows,
    getKnowledgeTooltipRows,
    getKnowledgeHumanReviewFlags,
    getKnowledgeSourceVerificationRows,
    getKnowledgeWorkflowUpdateRows,
    getAuthorityLabel,
    getAuthorityUrl,
    getAuthoritySourceInfo,
    buildCrosswalkTrace,
    runCrosswalk
  };
})();
