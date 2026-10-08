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
