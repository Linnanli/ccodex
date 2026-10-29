// Public runtime only: owned local files/profile, no accounts or model service.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const {app, WebContentsView, session} = require('electron');
const output = app.commandLine.getSwitchValue('ccodex-owned-output');
if (!path.isAbsolute(output)) throw Error('Absolute owned output required');
fs.mkdirSync(output, {recursive: true});
for (const [kind, directory] of [['appData', 'app-data'], ['userData', 'user-data'], ['sessionData', 'session-data'], ['crashDumps', 'crash-dumps']]) {
  const owned = path.join(output, directory); fs.mkdirSync(owned, {recursive: true}); app.setPath(kind, owned);
}
app.setAppLogsPath(path.join(output, 'logs'));
app.setName('ccodex-public-history-analysis');
for (const flag of ['disable-background-networking', 'disable-component-update', 'disable-sync', 'no-first-run']) app.commandLine.appendSwitch(flag);
const result = {
  kind: 'owned-public-history-duplication', startedAtUtc: new Date().toISOString(), probePid: process.pid,
  versions: Object.fromEntries(['electron', 'node', 'chrome', 'modules', 'napi'].map(k => [k, process.versions[k]])),
  originalClientRunsAdded: 0, modelSubmissionsAdded: 0, productScenarioPassesAdded: 0,
  accountDataRead: false, snapshots: [], cases: [], errors: [], deniedRequests: [], cleanup: [],
};
const views = [];
const urls = {};
let finished = false;
function record(id, claim, passed, actual) { result.cases.push({id, claim, passed: Boolean(passed), actual}); }
function finish(code) {
  if (finished) return; finished = true;
  result.completedAtUtc = new Date().toISOString(); result.exitCode = code;
  result.counts = {casesPassed: result.cases.filter(c => c.passed).length, casesFailed: result.cases.filter(c => !c.passed).length,
    snapshots: result.snapshots.length, publicRuntimeRunsAdded: 1, originalClientRunsAdded: 0,
    modelSubmissionsAdded: 0, productScenarioPassesAdded: 0};
  fs.writeFileSync(path.join(output, 'runtime-observations.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({counts: result.counts, errors: result.errors}));
  app.exit(code);
}
setTimeout(() => { result.errors.push({phase: 'timeout', message: 'Owned probe exceeded 30 seconds'}); finish(2); }, 30000).unref();
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
function entries(contents) {
  return contents.navigationHistory.getAllEntries().map(e => ({
    label: Object.entries(urls).find(([, url]) => url === e.url)?.[0] ?? 'unknown',
    title: e.title, keys: Object.keys(e).sort(), pageStateSha256: typeof e.pageState === 'string' ? sha(e.pageState) : null,
  }));
}
async function snapshot(contents, label) {
  const dom = await contents.executeJavaScript('({title:document.title,input:document.getElementById("fixture")?.value??null,heap:window.fixtureHeapSentinel??null})');
  const record = {label, webContentsId: contents.id, activeIndex: contents.navigationHistory.getActiveIndex(),
    length: contents.navigationHistory.length(), canGoBack: contents.navigationHistory.canGoBack(),
    canGoForward: contents.navigationHistory.canGoForward(), entries: entries(contents),
    page: Object.entries(urls).find(([, url]) => url === contents.getURL())?.[0] ?? 'unknown', ...dom};
  result.snapshots.push(record); return record;
}
async function edit(contents, input, heap) {
  await contents.executeJavaScript(`document.getElementById('fixture').value=${JSON.stringify(input)};window.fixtureHeapSentinel=${JSON.stringify(heap)}`);
}
function navigate(contents, action) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => done(Error('Navigation event timeout')), 5000);
    function loaded() { done(); }
    function failed(event, code, description, url, mainFrame) { if (mainFrame && code !== -3) done(Error(`${code}: ${description}`)); }
    function done(error) {
      clearTimeout(timer); contents.removeListener('did-finish-load', loaded); contents.removeListener('did-fail-load', failed);
      if (error) reject(error); else resolve();
    }
    contents.once('did-finish-load', loaded); contents.on('did-fail-load', failed);
    try { action(); } catch (error) { done(error); }
  });
}
async function close(contents, label) {
  if (contents.isDestroyed()) { result.cleanup.push({label, alreadyDestroyed: true}); return; }
  await new Promise(resolve => { contents.once('destroyed', resolve); contents.close(); });
  result.cleanup.push({label, isDestroyed: contents.isDestroyed()});
}
app.whenReady().then(async () => {
  const fixtures = path.join(output, 'fixtures'); fs.mkdirSync(fixtures);
  for (const label of ['A', 'B', 'C', 'D']) {
    const file = path.join(fixtures, `${label}.html`);
    fs.writeFileSync(file, `<!doctype html><title>CCODEX_HISTORY_${label}</title><input id="fixture" value="initial-${label}"><script>window.fixtureHeapSentinel="loaded-${label}"</script>`);
    urls[label] = pathToFileURL(file).href;
  }
  const ownedSession = session.fromPartition('persist:ccodex-owned-history-duplicate');
  ownedSession.setPermissionRequestHandler((contents, permission, callback) => callback(false));
  ownedSession.setPermissionCheckHandler(() => false);
  ownedSession.webRequest.onBeforeRequest((details, callback) => {
    const allowed = details.url.startsWith(pathToFileURL(fixtures).href + '/') || details.url === 'about:blank';
    if (!allowed) result.deniedRequests.push({url: details.url, resourceType: details.resourceType});
    callback({cancel: !allowed});
  });
  function newContents() {
    const view = new WebContentsView({webPreferences: {session: ownedSession, sandbox: true, contextIsolation: true, nodeIntegration: false}});
    view.webContents.setWindowOpenHandler(() => ({action: 'deny'})); views.push(view); return view.webContents;
  }
  const source = newContents(); const destination = newContents();
  record('HD-01', 'Independent WebContents identities share the explicitly owned session.', source.id !== destination.id && source.session === destination.session,
    {sourceId: source.id, destinationId: destination.id, sameSession: source.session === destination.session});
  for (const page of ['A', 'B', 'C']) {
    await source.loadURL(urls[page]); await edit(source, `edited-source-${page}`, `source-heap-${page}`);
  }
  const original = await snapshot(source, 'source-before-copy');
  const history = structuredClone(source.navigationHistory.getAllEntries());
  await destination.navigationHistory.restore({index: original.activeIndex, entries: history});
  const copied = await snapshot(destination, 'destination-after-copy');
  record('HD-02', 'Copy restores the three-entry stack and current C index without navigating source.',
    copied.length === 3 && copied.activeIndex === 2 && copied.page === 'C', copied);
  record('HD-03', 'Candidate preserves the currently edited form value at copy time.', copied.input === original.input,
    {sourceInput: original.input, destinationInput: copied.input, qualification: 'Candidate property, not an established Owl native guarantee.'});
  record('HD-04', 'Restored page has a separately initialized JS heap.', copied.heap === 'loaded-C', {sourceHeap: original.heap, destinationHeap: copied.heap});
  await edit(destination, 'edited-destination-C', 'destination-heap-C');
  let currentSource = await snapshot(source, 'source-after-destination-edit');
  record('HD-05', 'Destination DOM/heap edits do not change the source C page.',
    currentSource.input === original.input && currentSource.heap === original.heap && currentSource.activeIndex === 2, currentSource);
  await navigate(destination, () => destination.navigationHistory.goBack());
  const backB = await snapshot(destination, 'destination-back-B');
  record('HD-06', 'Copied history can go back to B and retains its saved form.',
    backB.page === 'B' && backB.activeIndex === 1 && backB.input === 'edited-source-B', backB);
  await navigate(destination, () => destination.navigationHistory.goBack());
  const backA = await snapshot(destination, 'destination-back-A');
  record('HD-07', 'Copied history can reach oldest A and retains its saved form.',
    backA.page === 'A' && backA.activeIndex === 0 && !backA.canGoBack && backA.input === 'edited-source-A', backA);
  await navigate(destination, () => destination.navigationHistory.goForward());
  const forwardB = await snapshot(destination, 'destination-forward-B');
  record('HD-08', 'Forward reaches B with both directions still available.',
    forwardB.page === 'B' && forwardB.activeIndex === 1 && forwardB.canGoBack && forwardB.canGoForward, forwardB);
  await edit(destination, 'before-reload-B', 'before-reload-heap-B');
  await navigate(destination, () => destination.reload());
  const reloaded = await snapshot(destination, 'destination-reload-B');
  record('HD-09', 'Reload keeps the B entry/index and reinitializes its script.',
    reloaded.page === 'B' && reloaded.activeIndex === 1 && reloaded.length === 3 && reloaded.heap === 'loaded-B', reloaded);
  await destination.loadURL(urls.D);
  const divergent = await snapshot(destination, 'destination-new-D');
  currentSource = await snapshot(source, 'source-after-destination-diverges');
  record('HD-10', 'New destination navigation cuts only its own forward stack; source remains C.',
    divergent.entries.map(e => e.label).join(',') === 'A,B,D' && !divergent.canGoForward && currentSource.page === 'C' && currentSource.length === 3 && currentSource.input === original.input,
    {source: currentSource, destination: divergent});
  await navigate(source, () => source.navigationHistory.goBack());
  const sourceBack = await snapshot(source, 'source-back-B');
  await navigate(source, () => source.navigationHistory.goForward());
  const sourceForward = await snapshot(source, 'source-forward-C');
  const destinationStill = await snapshot(destination, 'destination-after-source-navigation');
  record('HD-11', 'Source history remains usable and its navigation does not move destination D.',
    sourceBack.page === 'B' && sourceForward.page === 'C' && sourceForward.input === original.input && destinationStill.page === 'D',
    {sourceBack, sourceForward, destination: destinationStill});
  const destinationHistory = destination.navigationHistory;
  await close(destination, 'destination');
  const sourceAfterClose = await snapshot(source, 'source-after-destination-close');
  record('HD-12', 'Closing destination leaves the original source alive and at C.',
    !source.isDestroyed() && sourceAfterClose.page === 'C' && sourceAfterClose.input === original.input, sourceAfterClose);
  let destroyedError = null;
  try { destinationHistory.getAllEntries(); } catch (error) { destroyedError = error.message; }
  record('HD-13', 'History access on the destroyed destination is rejected.', destroyedError !== null, {error: destroyedError});
  await close(source, 'source');
  result.limitations = [
    'Public runtime primitives with owned local file pages only; no original Owl native behavior or renderer lease integration tested.',
    'Same owned session only; cross-partition permissions/cookies/preloads, popups, network pages and privileged browser settings are outside this run.',
    'HTML form/script observations are candidate properties; failure does not establish original Owl requirements.',
  ];
  finish(0);
}).catch(async error => {
  result.errors.push({phase: 'probe', message: error.message, stack: error.stack});
  for (const view of views) if (!view.webContents.isDestroyed()) view.webContents.close();
  finish(1);
});
