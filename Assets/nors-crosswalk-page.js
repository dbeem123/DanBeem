/* Source-only NORS and Appendix PP browser. No case text leaves this page. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const output = $('source-output');
  let definitions, tags, catalog, manifest, reviewedLinks, rejectedLinks, appSynonyms, searchWeights;
  let renderedHash = null;
  const STOP = new Set('request requests follow staff resident residents facility facilities care planning ability defined ensure consider timing practice will some can level limited medical during needs harm immediate report others based making failure risk appropriate may must also other including her his who there did having etc lack keep own take want wants my the and for from with that this their they have has was were are into than then when where which what would could should shall include includes example examples such each any all use used under section requirements requirement information provided provide upon person persons program code codes complaint complaints does not but its you your about'.split(' '));
  function stem(word) {
    if (word.length > 4 && word.endsWith('ies')) return word.slice(0, -3) + 'y';
    if (word.length > 5 && ['sses', 'shes', 'ches', 'xes', 'zes'].some(suffix => word.endsWith(suffix))) return word.slice(0, -2);
    if (word.length > 4 && word.endsWith('s') && !['ss', 'us', 'is'].some(suffix => word.endsWith(suffix))) return word.slice(0, -1);
    if (word.length > 6 && word.endsWith('ing')) { const base = word.slice(0, -3); return base.length > 3 && base.at(-1) === base.at(-2) ? base.slice(0, -1) : base; }
    if (word.length > 5 && word.endsWith('ed')) { const base = word.slice(0, -2); return base.length > 3 && base.at(-1) === base.at(-2) ? base.slice(0, -1) : base; }
    return word;
  }
  const STOP_STEMS = new Set([...STOP].map(stem));
  function normalizedTerms(text) {
    return new Set((text.toLowerCase().match(/[a-z][a-z0-9'-]{2,}/g) || []).map(stem).filter(word => !STOP.has(word) && !STOP_STEMS.has(word)));
  }
  function buildSearchWeights(records) {
    const frequencies = new Map();
    records.forEach(record => normalizedTerms(record.text).forEach(word => frequencies.set(word, (frequencies.get(word) || 0) + 1)));
    return new Map([...frequencies].map(([word, count]) => [word, Math.log((records.length + 1) / (count + 1)) + 1]));
  }
  const read = async path => {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Source unavailable (${response.status})`);
    return response.json();
  };
  const element = (name, text) => { const el = document.createElement(name); if (text !== undefined) el.textContent = text; return el; };
  const appendText = (parent, name, text) => { const child = element(name, text); parent.append(child); return child; };
  function clear() { output.replaceChildren(); }
  function sourceLink(parent, url, label) {
    if (!url || !/^https:\/\//.test(url)) return;
    const a = element('a', label); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; parent.append(a);
  }
  function tagValues(row) {
    const raw = row.appendix_pp_tags || [];
    return (Array.isArray(raw) ? raw : [raw]).map(x => typeof x === 'string' ? x : x.citation).filter(x => /^F\d{3,4}$/i.test(x || '')).map(x => x.toUpperCase());
  }
  function linkedTags(code) {
    const row = catalog.find(x => x.nors_minor_code === code);
    const existing = row ? tagValues(row).filter(tag => !rejectedLinks.some(link => link.nors_code === code && link.f_tag === tag)) : [];
    const reviewed = reviewedLinks.filter(x => x.nors_code === code).map(x => x.f_tag);
    return [...new Set([...existing, ...reviewed])];
  }
  function linkBasis(code, tag) {
    const row = catalog.find(x => x.nors_minor_code === code);
    return row && tagValues(row).includes(tag) && !rejectedLinks.some(link => link.nors_code === code && link.f_tag === tag) ? 'existing_app_link' : 'coded_by_reviewer';
  }
  function linkLabel(label, code, tag) {
    const weak = reviewedLinks.some(link => link.nors_code === code && link.f_tag === tag && link.link_strength === 'weak');
    return `${label} (${linkBasis(code, tag)}${weak ? '; weak — title-only, check' : ''})`;
  }
  function openButton(parent, label, fn) { const button = element('button', label); button.type = 'button'; button.className = 'btn secondary'; button.addEventListener('click', fn); parent.append(button); }
  function setHash(kind, id) {
    const hash = `#${kind}=${encodeURIComponent(id)}`;
    renderedHash = hash;
    if (location.hash !== hash) location.hash = hash;
  }
  function scrollResults() { if (typeof output.scrollIntoView === 'function') output.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  function verifiedSection(tag) {
    // Only these PDF boundaries were verified in the source audit. Other tags
    // stay ungrouped until their home section is verified; a first CFR mention
    // can be an unrelated cross-reference (for example F917).
    const f550 = tags.find(x => x.tag === 'F550');
    const f600 = tags.find(x => x.tag === 'F600');
    const f620 = tags.find(x => x.tag === 'F620');
    if (!f550 || !f600 || !f620) return 'Section not verified';
    if (tag.pdf_page_start >= f550.pdf_page_start && tag.pdf_page_start < f600.pdf_page_start) return '§483.10';
    if (tag.pdf_page_start >= f600.pdf_page_start && tag.pdf_page_start < f620.pdf_page_start) return '§483.12';
    return 'Section not verified';
  }
  function highlighted(parent, text, words) {
    const token = words.find(word => text.toLowerCase().includes(word));
    if (!token) { parent.textContent = text; return; }
    const start = text.toLowerCase().indexOf(token);
    parent.append(document.createTextNode(text.slice(0, start)), element('mark', text.slice(start, start + token.length)), document.createTextNode(text.slice(start + token.length)));
  }
  function showCode(code, updateRoute = true) {
    const item = definitions.find(x => x.code === code); if (!item) return;
    clear(); if (updateRoute) setHash('code', code); appendText(output, 'h3', `NORS ${code}`); appendText(output, 'p', item.text);
    const ref = appendText(output, 'p', `${item.citation} — ${item.locator}. `); sourceLink(ref, item.url, 'Open source');
    appendText(output, 'h4', 'Related F-tags (existing or reviewed links; context only)');
    const links = linkedTags(code).filter(tag => tags.some(item => item.tag === tag));
    if (!links.length) appendText(output, 'p', 'No existing app links are available.');
    links.forEach(tag => openButton(output, linkLabel(tag, code, tag), () => showTag(tag)));
    scrollResults();
  }
  async function showTag(tag, updateRoute = true) {
    if (!tags.some(item => item.tag === tag)) return;
    clear(); if (updateRoute) setHash('tag', tag); appendText(output, 'p', 'Loading source passages…');
    try {
      const record = await read(`../data/appendix_pp/${encodeURIComponent(tag)}.json`);
      clear(); appendText(output, 'h3', `${tag} — ${record.cms_short_title}`);
      appendText(output, 'p', `CMS citation description; ${verifiedSection(record)}; PDF pages ${record.pdf_page_start}–${record.pdf_page_end}.`);
      appendText(output, 'p', `Tag header: ${record.tag} — ${record.source_revision || 'revision not listed'}`);
      if (record.extraction_quality !== 'text_extracted') appendText(output, 'p', 'Source extraction is flagged for review; check the original document.');
      const ref = appendText(output, 'p', 'Appendix PP: '); sourceLink(ref, record.url, 'Open original source');
      const groups = new Map();
      record.passages.forEach(p => { const label = p.section_label === 'Regulation' ? 'Regulation (42 CFR)' : p.is_example || p.section_label === 'Deficiency categorization' ? 'CMS example of noncompliance (context)' : `CMS interpretive guidance — ${p.section_label}`; if (!groups.has(label)) groups.set(label, []); groups.get(label).push(p); });
      for (const [label, passages] of groups) {
        const details = element('details'); details.append(element('summary', label));
        passages.forEach(p => { appendText(details, 'p', p.text); appendText(details, 'small', `PDF page ${p.pdf_page}`); }); output.append(details);
      }
      appendText(output, 'h4', 'Related NORS codes (existing or reviewed links; context only)');
      const linked = definitions.filter(row => linkedTags(row.code).includes(tag));
      if (!linked.length) appendText(output, 'p', 'No existing or reviewed links are available.');
      linked.forEach(row => openButton(output, linkLabel(row.code, row.code, tag), () => showCode(row.code)));
      scrollResults();
    } catch (error) { clear(); appendText(output, 'p', `Unable to load this F-tag. ${error.message}`); }
  }
  function expandAppendixTerms(input, baseTerms) {
    const rawTokens = input.toLowerCase().match(/[a-z0-9]+/g) || [];
    const tokenStems = new Set(rawTokens.map(stem));
    const extra = [];
    const triggerTerms = new Set();
    appSynonyms.forEach(rule => {
      const matchedTriggers = rule.match_any_trigger.filter(item => {
        if (item.includes(' ')) return (` ${input.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()} `).includes(` ${item} `);
        return tokenStems.has(stem(item));
      });
      const medicationTerms = new Set(rule.alongside_any_medication_term.map(stem));
      if (matchedTriggers.length && rawTokens.some(token => medicationTerms.has(stem(token)))) {
        extra.push(...rule.expands_to.map(stem));
        matchedTriggers.forEach(trigger => trigger.split(' ').forEach(token => triggerTerms.add(stem(token))));
      }
    });
    return new Set([...baseTerms].filter(term => !triggerTerms.has(term)).concat(extra));
  }
  async function search(updateRoute = true, searchText) {
    const input = (searchText === undefined ? $('keyword-text').value : searchText).toLowerCase();
    const rawWords = [...new Set(input.match(/[a-z][a-z0-9'-]{2,}/g) || [])];
    const baseTerms = new Set(rawWords.map(stem).filter(word => !STOP.has(word) && !STOP_STEMS.has(word)));
    const appendixTerms = expandAppendixTerms(input, baseTerms);
    if (updateRoute) setHash('search', input.trim());
    clear(); if (!baseTerms.size) { appendText(output, 'p', 'Enter a source word to search.'); return; }
    appendText(output, 'p', 'Searching source text…');
    try {
      const termsByKind = { nors: baseTerms, appendix_pp: appendixTerms };
      const lookup = new Map();
      rawWords.forEach(raw => {
        const term = stem(raw);
        if (!STOP.has(term) && !STOP_STEMS.has(term)) { lookup.set(raw, term); lookup.set(term, term); }
      });
      [...appendixTerms].filter(term => !baseTerms.has(term)).forEach(term => lookup.set(term, term));
      const files = [...new Set([...lookup.keys()].map(word => manifest.shards.find(s => s.first <= word && word <= s.last)?.file).filter(Boolean))];
      const shards = await Promise.all(files.map(file => read(`../data/${file}`)));
      const hits = new Map();
      [...lookup.keys()].forEach(word => shards.forEach(shard => (shard[word] || []).forEach(hit => {
        const term = lookup.get(word);
        if (!termsByKind[hit.source_class]?.has(term)) return;
        if (hit.source_class === 'nors' && !definitions.some(d => d.id === hit.record_id)) return;
        const key = `${hit.source_class}|${hit.record_id}`; const old = hits.get(key) || { ...hit, words: new Set() }; old.words.add(term); hits.set(key, old);
      })));
      clear();
      for (const kind of ['nors', 'appendix_pp']) {
        appendText(output, 'h3', kind === 'nors' ? 'NORS definitions with matching words' : 'Appendix PP tags with matching words');
        const searchScore = hit => [...hit.words].reduce((score, word) => score + (searchWeights.get(word) || Math.log((definitions.length + 1)) + 1), 0);
        const matched = [...hits.values()].filter(x => x.source_class === kind).sort((a, b) => searchScore(b) - searchScore(a) || b.words.size - a.words.size || a.record_id.localeCompare(b.record_id)).slice(0, 30);
        if (!matched.length) appendText(output, 'p', 'No matching source words found.');
        for (const hit of matched) {
          const id = kind === 'nors' ? definitions.find(x => x.id === hit.record_id)?.code : tags.find(x => x.id === hit.record_id)?.tag;
          if (!id) continue;
          const row = element('div'); openButton(row, id, () => kind === 'nors' ? showCode(id) : showTag(id));
          appendText(row, 'span', ` Matched: ${[...hit.words].join(', ')}. ${hit.locators.join('; ')}`); output.append(row);
          const record = kind === 'nors' ? definitions.find(x => x.id === hit.record_id) : await read(`../data/appendix_pp/${encodeURIComponent(id)}.json`);
          const passages = kind === 'nors' ? [record.text] : record.passages.map(p => p.text);
          const found = passages.find(text => [...hit.words].some(word => text.toLowerCase().includes(word)));
          if (found) highlighted(appendText(row, 'p', ''), found, [...hit.words]);
          if (kind === 'appendix_pp') {
            const contextCodes = reviewedLinks.filter(link => link.f_tag === id).map(link => link.nors_code);
            if (contextCodes.length) appendText(row, 'p', `Reviewed NORS context: ${[...new Set(contextCodes)].join(', ')} (context only).`);
          }
        }
      }
      scrollResults();
    } catch (error) { clear(); appendText(output, 'p', `Search could not load its source index. ${error.message}`); }
  }
  async function init() {
    try {
      const [a, t, c, m, reviewed, synonyms] = await Promise.all([read('../data/nors_primary_authority.json'), read('../data/appendix_pp/index.json'), read('../crosswalk_catalog.json'), read('../data/term_index.json'), read('../data/nors_reviewed_links.json'), read('../data/nors_app_search_synonyms.json')]);
      definitions = a.authority_records.filter(x => x.authority_type === 'nors_table_2_definition'); tags = t.tags; catalog = c.records; manifest = m;
      appSynonyms = synonyms.status === 'approved_app_guidance' && synonyms.approved_by === 'Daniel' && synonyms.approved_date === '2026-11-13'
        ? (Array.isArray(synonyms.rules) ? synonyms.rules : []).filter(x => Array.isArray(x.match_any_trigger) && Array.isArray(x.alongside_any_medication_term) && Array.isArray(x.expands_to))
        : [];
      searchWeights = buildSearchWeights(definitions);
      const allReviewRows = Array.isArray(reviewed.links) ? reviewed.links : [];
      const acceptedReviewMethods = new Set(['approved Claude first-pass triage', 'Daniel-directed triage approved 2026-11-13']);
      const reviewMetaValid = x => x.reviewed_by === 'Daniel' && acceptedReviewMethods.has(x.review_method) && /^\d{4}-\d{2}-\d{2}$/.test(x.reviewed_date || '') && /^[A-L]\d{2}$/.test(x.nors_code || '') && /^F\d{3,4}$/.test(x.f_tag || '') && definitions.some(d => d.code === x.nors_code) && tags.some(t => t.tag === x.f_tag);
      rejectedLinks = allReviewRows.filter(x => x.status === 'rejected' && reviewMetaValid(x));
      const candidates = allReviewRows.filter(x => x.status === 'reviewed' && x.basis === 'coded_by_reviewer' && reviewMetaValid(x) && definitions.some(d => d.code === x.nors_code && d.id === x.nors_authority_id && typeof x.nors_excerpt === 'string' && x.nors_excerpt.trim() && d.text.includes(x.nors_excerpt)));
      const checked = await Promise.all(candidates.map(async link => {
        try { const record = await read(`../data/appendix_pp/${encodeURIComponent(link.f_tag)}.json`); return record.passages.some(p => p.id === link.appendix_passage_id && typeof link.appendix_excerpt === 'string' && link.appendix_excerpt.trim() && p.text.includes(link.appendix_excerpt)) ? link : null; }
        catch (_) { return null; }
      }));
      reviewedLinks = checked.filter(Boolean);
      const groups = new Map();
      catalog.forEach(row => { if (!groups.has(row.nors_major_code)) groups.set(row.nors_major_code, []); groups.get(row.nors_major_code).push(row); });
      for (const [letter, rows] of groups) { const group = element('optgroup'); group.label = `${letter} — ${rows[0].nors_major_label}`; rows.forEach(row => { const option = element('option', `${row.nors_minor_code} — ${row.nors_minor_label}`); option.value = row.nors_minor_code; group.append(option); }); $('nors-code').append(group); }
      const tagGroups = new Map(); tags.forEach(t => { const section = verifiedSection(t); if (!tagGroups.has(section)) tagGroups.set(section, []); tagGroups.get(section).push(t); });
      for (const [section, rows] of tagGroups) { const group = element('optgroup'); group.label = section; rows.forEach(row => { const option = element('option', `${row.tag} — ${row.cms_short_title}`); option.value = row.tag; group.append(option); }); $('ftag-code').append(group); }
      for (const [filterId, selectId] of [['nors-filter', 'nors-code'], ['ftag-filter', 'ftag-code']]) {
        $(filterId).addEventListener('input', () => {
          const query = $(filterId).value.trim().toLowerCase();
          for (const group of $(selectId).querySelectorAll('optgroup')) {
            for (const option of group.querySelectorAll('option')) option.hidden = !!query && !option.textContent.toLowerCase().includes(query);
            group.hidden = [...group.querySelectorAll('option')].every(option => option.hidden);
          }
        });
      }
      $('nors-code').addEventListener('change', () => { if ($('nors-code').value) showCode($('nors-code').value); });
      $('ftag-code').addEventListener('change', () => { if ($('ftag-code').value) showTag($('ftag-code').value); });
      $('run-keyword-crosswalk').addEventListener('click', search);
      const route = () => {
        if (location.hash === renderedHash) return;
        renderedHash = location.hash;
        const hash = new URLSearchParams(location.hash.slice(1)); const code = hash.get('code'); const tag = hash.get('tag'); const query = hash.get('search');
        if (code && /^[A-L]\d{2}$/.test(code)) showCode(code, false);
        else if (tag && /^F\d{3,4}$/.test(tag)) showTag(tag, false);
        else if (query) { $('keyword-text').value = query; search(false, query); }
      };
      window.addEventListener('hashchange', route); window.addEventListener('popstate', route);
      $('load-status').textContent = 'Source data loaded. Results are informational and require human review.';
      renderedHash = null; route();
    } catch (error) { $('load-status').textContent = `Sources could not load. ${error.message}`; }
  }
  document.addEventListener('DOMContentLoaded', init);
})();
