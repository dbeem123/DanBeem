(function () {
  const DEFAULT_PATHS = {
    keywordMap: ['../keyword_map.json', '../data/keyword_map.json'],
    norsToTopic: ['../nors_to_topic.json', '../data/nors_to_topic.json'],
    topicToAuthority: ['../topic_to_authority.json', '../data/topic_to_authority.json'],
    authorityIndex: ['../authority_index.json', '../data/reference_source_index.json'],
    retrievalRules: ['../retrieval_rules.json', '../data/retrieval_rules.json']
  };

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
      return [key, await loadJsonFile(path, key)];
    }));

    return Object.fromEntries(entries);
  }

  function addTopic(topicMatches, topic, sourceType, value) {
    if (!topic) return;
    if (!topicMatches[topic]) {
      topicMatches[topic] = { topic, norsCodes: [], keywords: [] };
    }
    if (sourceType === 'nors' && value && !topicMatches[topic].norsCodes.includes(value)) {
      topicMatches[topic].norsCodes.push(value);
    }
    if (sourceType === 'keyword' && value && !topicMatches[topic].keywords.includes(value)) {
      topicMatches[topic].keywords.push(value);
    }
  }

  function sortTopicMatches(topicMatches) {
    return Object.values(topicMatches).sort((a, b) => {
      const aPriority = a.norsCodes.length ? 0 : 1;
      const bPriority = b.norsCodes.length ? 0 : 1;
      return aPriority - bPriority || a.topic.localeCompare(b.topic);
    });
  }

  function getTopicsFromNorsCode(norsCode, data) {
    const topicMatches = {};
    const code = (norsCode || '').trim();
    if (!code) return [];

    (data.norsToTopic?.[code] || []).forEach(topic => {
      addTopic(topicMatches, topic, 'nors', code);
    });

    return sortTopicMatches(topicMatches);
  }

  function getTopicsFromKeywords(text, data) {
    const topicMatches = {};
    const searchableText = (text || '').toLowerCase();
    if (!searchableText) return [];

    Object.entries(data.keywordMap?.keywords || {}).forEach(([keyword, mappedTopics]) => {
      if (searchableText.includes(keyword.toLowerCase())) {
        mappedTopics.forEach(topic => {
          addTopic(topicMatches, topic, 'keyword', keyword);
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
        match.keywords.forEach(keyword => addTopic(topicMatches, match.topic, 'keyword', keyword));
      });
    }

    return sortTopicMatches(topicMatches);
  }

  function getAuthorityLabel(authority = {}) {
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

  function normalizeAuthority(authorityId, authority, reason, match) {
    return {
      id: authorityId,
      citation: authority?.citation || 'Citation not available',
      title: authority?.title || (authority ? 'Title not available' : 'Authority metadata not found'),
      category: authority ? getAuthorityLabel(authority) : 'Missing metadata',
      label: authority ? getAuthorityLabel(authority) : 'Missing metadata',
      reason: reason || (authority ? 'Selected by topic mapping.' : 'Selected by topic mapping, but details are missing from authority index.'),
      matchSummary: getMatchSummary(match),
      rank: authority ? 0 : -1,
      missing: !authority
    };
  }

  function getAuthoritiesForTopics(topicMatches, data) {
    const topicMap = data.topicToAuthority?.topics || {};
    const authorityIndex = data.authorityIndex?.authorities || {};
    const ranking = data.retrievalRules?.ranking || {};
    const output = data.retrievalRules?.output || {};
    const maxResults = output.max_results || 8;
    const dedupe = data.retrievalRules?.matching?.deduplicate_authorities !== false;
    const groups = [];
    const seen = new Set();
    let resultCount = 0;

    topicMatches.forEach(match => {
      const authorities = [];
      const mappings = topicMap[match.topic] || [];

      mappings.forEach(item => {
        if (resultCount >= maxResults) return;
        if (dedupe && seen.has(item.authority_id)) return;

        const authority = authorityIndex[item.authority_id];
        seen.add(item.authority_id);
        resultCount += 1;

        const normalized = normalizeAuthority(item.authority_id, authority, item.reason, match);
        normalized.rank = authority ? ranking[authority.type] || 0 : -1;
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

  function buildCrosswalkTrace({ norsCode, keywordText, topicMatches, authorityGroups } = {}) {
    const trace = [];
    const code = (norsCode || '').trim();
    const keyword = (keywordText || '').trim();

    if (code && !topicMatches.some(match => match.norsCodes.includes(code))) {
      trace.push(`NORS code ${code} did not map to a topic in nors_to_topic.json.`);
    }

    if (keyword && !topicMatches.some(match => match.keywords.length)) {
      trace.push('Keyword / concern text did not match keyword_map.json.');
    }

    topicMatches.forEach(match => {
      if (match.norsCodes.length) {
        trace.push(`NORS code ${match.norsCodes.join(', ')} maps to topic "${match.topic}".`);
      }
      if (match.keywords.length) {
        trace.push(`Keyword(s) ${match.keywords.map(item => `"${item}"`).join(', ')} map to topic "${match.topic}".`);
      }

      const group = authorityGroups.find(item => item.topic === match.topic);
      if (!group || !group.authorities.length) {
        trace.push(`Topic "${match.topic}" has no authority IDs in topic_to_authority.json.`);
        return;
      }

      trace.push(`Topic "${match.topic}" maps to authority ID(s): ${group.authorities.map(item => item.id).join(', ')}.`);
      group.authorities.forEach(authority => {
        if (authority.missing) {
          trace.push(`Authority ID "${authority.id}" is missing from authority_index.json.`);
        } else {
          trace.push(`Authority ID "${authority.id}" resolves to ${authority.citation}.`);
        }
      });
    });

    return trace;
  }

  function runCrosswalk({ norsCode, keywordText } = {}, data) {
    const topicMatches = getTopicsFromInputs({ norsCode, keywordText }, data);
    const authorityGroups = getAuthoritiesForTopics(topicMatches, data);
    const trace = buildCrosswalkTrace({ norsCode, keywordText, topicMatches, authorityGroups });
    const warnings = [];

    if (!topicMatches.length) {
      warnings.push('No topics were matched from the supplied NORS code or keyword text.');
    }
    if (topicMatches.length && !authorityGroups.length) {
      warnings.push('Topics were matched, but no authority references were found.');
    }
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
    getAuthorityLabel,
    buildCrosswalkTrace,
    runCrosswalk
  };
})();
