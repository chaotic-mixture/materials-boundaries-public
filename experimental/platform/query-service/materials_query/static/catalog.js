'use strict';
const element = id => document.getElementById(id);
let version = null;
async function post(path, body) {
  const response = await fetch('/api/catalog/' + path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...body, version})});
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'Query rejected; check the inputs.');
  if (value.version !== version) throw new Error('Version changed. Reload and select again.');
  return value.result;
}
async function initialize() {
  try {
    const response = await fetch('/api/catalog/status');
    if (!response.ok) throw new Error('Could not read catalog status.');
    const status = await response.json();
    if (!status.enabled) { element('catalog-status').textContent = 'Local catalog disabled: ' + status.reason + '. See local installation instructions.'; return; }
    version = status.version;
    element('catalog-version').textContent = version;
    element('catalog-status').textContent = status.counts.local_catalog_unique_material_count + ' local unique materials; ' + status.counts.local_material_state_count + ' material states. Historical content pin.';
    element('catalog-submit').disabled = false;
  } catch (error) { element('catalog-status').textContent = error.message; }
}
element('catalog-form').addEventListener('submit', async event => {
  event.preventDefault();
  element('catalog-submit').disabled = true;
  element('catalog-results').replaceChildren();
  element('catalog-detail').textContent = '';
  const kind = element('catalog-kind').value;
  try {
    const result = await post('search', {kind, query: element('catalog-query').value, limit: Number(element('catalog-limit').value)});
    element('catalog-result-status').textContent = result.records.length + ' records returned' + (result.truncated ? '; more matches exist.' : '.');
    for (const record of result.records) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = record.id;
      button.addEventListener('click', async () => {
        button.disabled = true;
        try {
          const detail = kind === 'materials' ? await post('resolve', {state_id: record.id}) : await post('exact', {kind, record_id: record.id});
          element('catalog-detail').textContent = JSON.stringify(detail, null, 2);
        } catch (error) { element('catalog-detail').textContent = error.message; }
        finally { button.disabled = false; }
      });
      element('catalog-results').appendChild(button);
    }
  } catch (error) { element('catalog-result-status').textContent = error.message; }
  finally { element('catalog-submit').disabled = false; }
});
initialize();

let formalVersion = null;
async function initializeFormal() {
  try {
    const response = await fetch('/api/catalog/project/status');
    if (!response.ok) throw new Error('Could not read formal project status.');
    const status = await response.json();
    if (!status.enabled) throw new Error('Formal project admissions unavailable: ' + status.reason);
    formalVersion = status.version;
    const counts = status.counts;
    element('formal-status').textContent = counts.formal_project_admission_count + ' formal project admissions: ' + counts.legacy_source_qualified_identity_count + ' legacy source-qualified identities + ' + counts.reviewed_computed_composition_count + ' reviewed computed composition buckets. Categories: ' + JSON.stringify(counts.categories) + '. Policy: ' + status.count_policy.schema;
    element('formal-submit').disabled = false;
  } catch (error) { element('formal-status').textContent = error.message; }
}
element('formal-form').addEventListener('submit', async event => {
  event.preventDefault();
  element('formal-submit').disabled = true;
  element('formal-results').replaceChildren();
  element('formal-detail').textContent = '';
  try {
    const response = await fetch('/api/catalog/project/list', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({version: formalVersion, partition: element('formal-partition').value || null, query: element('formal-query').value || null, offset: Number(element('formal-offset').value), limit: 20})});
    const value = await response.json();
    if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'Invalid formal selection.');
    if (value.version !== formalVersion) throw new Error('Formal version changed; reload the page.');
    element('formal-result-status').textContent = value.matched_count + ' matches; showing ' + value.records.length + ' at offset ' + value.offset + (value.truncated ? '; more matches remain.' : '.');
    for (const record of value.records) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = record.name + ' · ' + record.partition;
      button.addEventListener('click', () => { element('formal-detail').textContent = JSON.stringify(record, null, 2); });
      element('formal-results').appendChild(button);
    }
  } catch (error) { element('formal-result-status').textContent = error.message; }
  finally { element('formal-submit').disabled = false; }
});
initializeFormal();
