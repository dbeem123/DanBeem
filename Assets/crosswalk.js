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
    appendixPpTagPages: ['../data/appendix_pp_tag_pages.json', '../appendix_pp_tag_pages.json'],
    sourceRegistry: ['../data/source_registry.json', '../source_registry.json']
  };

  const OPTIONAL_DATA_KEYS = new Set(['norsToTopic', 'topicToAuthority', 'norsComplaintGuidance', 'norsResourceCatalog', 'norsKnowledgeBase', 'norsKnowledgeBaseBatch2', 'norsKnowledgeBaseBatch3', 'norsKnowledgeBaseBatch4', 'appendixPpTagPages', 'sourceRegistry']);

  function getOptionalFallback(key) {
    if (key === 'topicToAuthority') return { topics: {} };
    if (key === 'norsComplaintGuidance') return { items: [] };
    if (key === 'norsResourceCatalog') return { resources: [] };
    if (key === 'norsKnowledgeBase') return { code_summary_rows: [], authority_rows: [], do_not_map_catalog: [] };
    if (key === 'norsKnowledgeBaseBatch2') return { code_summary_rows: [], authority_rows: [], appendix_pp_page_rows: [], do_not_map_catalog: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch3') return { code_summary_rows: [], authority_rows: [], appendix_pp_page_rows: [], do_not_map_catalog: [], keyword_rows: [], human_review_flags: [] };
    if (key === 'norsKnowledgeBaseBatch4') return { resource_rows: [], workflow_guidance_rows: [], source_quality_rows: [], plain_language_explainer_rows: [], human_review_flags: [] };
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
    return [data?.norsKnowledgeBase, data?.norsKnowledgeBaseBatch2, data?.norsKnowledgeBaseBatch3, data?.norsKnowledgeBaseBatch4].filter(Boolean);
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

  function getKnowledgeKeywordRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.keyword_rows || []);
  }

  function getKnowledgeResourceRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.resource_rows || []);
  }

  function getKnowledgeWorkflowRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.workflow_guidance_rows || []);
  }

  function getKnowledgeSourceQualityRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.source_quality_rows || []);
  }

  function getKnowledgeExplainerRows(data) {
    return getKnowledgeBases(data).flatMap(base => base.plain_language_explainer_rows || []);
  }

  function getKnowledgeHumanReviewFlags(data) {
    return getKnowledgeBases(data).flatMap(base => base.human_review_flags || []);
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

  function getWorkflowGuidanceForInputs({ norsCode, topicMatches = [] } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic));

    return getKnowledgeWorkflowRows(data).filter(row => {
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
  }

  function getKnowledgeHumanReviewWarnings({ norsCode, topicMatches = [], resources = [], keywordText = '' } = {}, data) {
    const matchedCodes = getMatchedNorsCodes(norsCode, topicMatches);
    const matchedTopics = topicMatches.map(match => normalizeTopicKey(match.topic)).join(' ');
    const text = normalizeTopicKey(keywordText);
    const resourceIds = new Set(resources.map(resource => resource.id).filter(Boolean));
    const warnings = [];

    getKnowledgeHumanReviewFlags(data).forEach(flag => {
      const id = flag.flag_id || flag.id || '';
      const action = flag.recommended_action || flag.description || '';
      if (!action) return;

      if (id === 'HRF-B4-001' && resourceIds.has('RR-024')) {
        warnings.push(`Source check (${id}): ${action}`);
      }
      if (id === 'HRF-B4-002' && (
        matchedCodes.some(code => ['F04', 'F05', 'F07', 'F11', 'F12', 'I01', 'I02', 'I03', 'I04', 'I05'].includes(code)) ||
        /medication|infection/.test(`${matchedTopics} ${text}`)
      )) {
        warnings.push(`Resource gap (${id}): ${action}`);
      }
      if (id === 'HRF-B4-003' && matchedCodes.some(code => ['C01', 'C02'].includes(code))) {
        warnings.push(`Discharge workflow note (${id}): ${action}`);
      }
      if (id === 'HRF-B4-004' && /consent|permission|identity|authorization|release/.test(text)) {
        warnings.push(`Consent terminology note (${id}): ${action}`);
      }
      if (id === 'HRF-B4-005' && resourceIds.has('RR-005')) {
        warnings.push(`Resource caveat (${id}): ${action}`);
      }
    });

    return warnings;
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
      const topic = topicByNorsCode[row.nors_code];
      if (!topic) return [];
      const authorityIds = (row.related_ftags || [])
        .map(item => normalizeAuthorityCitation(item).toLowerCase())
        .filter(item => item && item !== 'f556')
        .map(item => item === 'f758' ? 'f605' : item);
      return (row.keywords || []).map(phrase => ({
        phrase,
        topics: [topic],
        likely_nors_codes: [row.nors_code],
        authority_ids: authorityIds,
        notes: (row.ombudsman_tips || []).join(' ')
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
      return 'Appendix PP';
    }
    if (type === 'training' || layer === 'training') {
      return 'Training / Guidance';
    }
    return type || layer ? `${layer || type}`.replace(/_/g, ' ') : 'Reference';
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
    if (type.startsWith('appendix_pp')) return 'Appendix PP';
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
        return {
          authority_id: citation === 'F758' ? 'f605' : getAuthorityIdFromKnowledgeRow(row),
          reason: row.mapping_rationale_short || row.notes || `${mappingType.replace(/_/g, ' ')} knowledge-base mapping`,
          citation: redirectedCitation,
          title: row.authority_label || row.description || '',
          category: getKnowledgeAuthorityCategory(row),
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
    const workflowGuidance = getWorkflowGuidanceForInputs({ norsCode: code, topicMatches }, data);
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
      resources,
      workflowGuidance,
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
    getKnowledgeResourceRows,
    getKnowledgeWorkflowRows,
    getKnowledgeSourceQualityRows,
    getKnowledgeExplainerRows,
    getKnowledgeHumanReviewFlags,
    getAuthorityLabel,
    getAuthorityUrl,
    getAuthoritySourceInfo,
    buildCrosswalkTrace,
    runCrosswalk
  };
})();
