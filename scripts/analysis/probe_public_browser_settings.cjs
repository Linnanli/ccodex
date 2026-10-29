// Independent public Electron, fresh owned data/partition and privileged URLs only.
const fs = require('node:fs'), path = require('node:path');
const {app, BrowserWindow, session} = require('electron');
const output = app.commandLine.getSwitchValue('ccodex-owned-output');
if (!output || !path.isAbsolute(output)) throw Error('Absolute owned output required');
for (const [kind, name] of [['appData', 'app-data'], ['userData', 'user-data'],
  ['sessionData', 'session-data'], ['crashDumps', 'crash-dumps']]) {
  const directory = path.join(output, name); fs.mkdirSync(directory, {recursive: true}); app.setPath(kind, directory);
}
app.setAppLogsPath(path.join(output, 'logs'));
app.setName('ccodex-owned-browser-settings-probe');
for (const flag of ['disable-background-networking', 'disable-component-update', 'disable-sync', 'no-first-run'])
  app.commandLine.appendSwitch(flag);
const targets = [
  {kind: 'contactInfo', url: 'chrome://settings/addresses'},
  {kind: 'contactInfoAlternative', url: 'chrome://settings/contactInfo'},
  {kind: 'extensions', url: 'chrome://extensions/'},
  {kind: 'passwordManager', url: 'chrome://password-manager/passwords'},
  {kind: 'passwordManagerRoot', url: 'chrome://password-manager/'},
  {kind: 'siteSettings', url: 'chrome://settings/content'},
  {kind: 'siteHandlers', url: 'chrome://settings/handlers'},
  {kind: 'siteCookies', url: 'chrome://settings/cookies'},
];
const result = {kind: 'owned-public-native-browser-settings-probe', startedAtUtc: new Date().toISOString(),
  versions: {electron: process.versions.electron, node: process.versions.node, chrome: process.versions.chrome},
  targets, observations: [], blockedExternalRequests: [], errors: [], originalClientRunsAdded: 0,
  modelSubmissionsAdded: 0, realBrowserDataRead: false, originalModulesLoaded: false};
let finished = false;
function checkpoint(phase, details = {}) {
  if (finished) return;
  fs.appendFileSync(path.join(output, 'phase-journal.jsonl'), JSON.stringify({phase, ...details, atUtc: new Date().toISOString()}) + '\n');
  fs.writeFileSync(path.join(output, 'runtime-observations.json'), JSON.stringify({...result, terminal: false, phase}, null, 2) + '\n');
}
function finish(code) {
  if (finished) return; finished = true;
  for (const window of BrowserWindow.getAllWindows()) window.destroy();
  result.exitCode = code; result.terminal = true; result.completedAtUtc = new Date().toISOString();
  fs.writeFileSync(path.join(output, 'runtime-observations.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({exitCode: code, observations: result.observations.length, errors: result.errors}));
  app.exit(code);
}
setTimeout(() => {result.errors.push({phase: 'overall-timeout'}); finish(2);}, 28000).unref();
checkpoint('before-app-ready');
app.whenReady().then(async () => {
  if (finished) return;
  checkpoint('app-ready');
  const owned = session.fromPartition('ccodex-owned-native-settings');
  owned.setPermissionRequestHandler((_, __, callback) => callback(false));
  owned.setPermissionCheckHandler(() => false);
  owned.webRequest.onBeforeRequest((details, callback) => {
    const external = /^(https?|wss?|ftp):/i.test(details.url);
    if (external) result.blockedExternalRequests.push({method: details.method, resourceType: details.resourceType,
      protocol: details.url.split(':')[0]});
    callback({cancel: external});
  });
  const control = {kind: 'ownedDataControl', url: 'data:text/html,' + encodeURIComponent(
    '<!doctype html><title>CCODEX_OWNED_NATIVE_SETTINGS_CONTROL</title><p id="fixture">owned</p>')};
  const window = new BrowserWindow({show: false, width: 400, height: 300, webPreferences: {
    session: owned, sandbox: true, contextIsolation: true, nodeIntegration: false}});
  const contents = window.webContents;
  contents.setWindowOpenHandler(() => ({action: 'deny'}));
  for (const target of [control, ...targets]) {
    if (finished) return;
    const observation = {kind: target.kind,
      requestedUrl: target.kind === 'ownedDataControl' ? 'data:owned-control' : target.url, failures: []};
    const failHandler = (_, code, description, url, isMainFrame) => {
      if (isMainFrame) observation.failures.push({code, description, url});
    };
    contents.on('did-fail-load', failHandler);
    let timer;
    try {
      checkpoint('before-load', {kind: target.kind});
      await Promise.race([contents.loadURL(target.url), new Promise((_, reject) => {
        timer = setTimeout(() => reject(Error('owned-navigation-timeout')), 2200);
      })]);
      observation.loadStatus = 'resolved';
      observation.document = await contents.executeJavaScript(
        '({url:location.href,title:document.title,fixture:document.getElementById("fixture")?.textContent??null})');
      if (target.kind === 'ownedDataControl' && observation.document.fixture !== 'owned')
        throw Error('Owned control DOM mismatch');
    } catch (error) {
      observation.loadStatus = 'rejected'; observation.message = error.message;
      if (target.kind === 'ownedDataControl' || error.message === 'owned-navigation-timeout')
        result.errors.push({phase: target.kind, message: error.message});
    } finally {
      clearTimeout(timer); result.observations.push(observation);
      contents.removeListener('did-fail-load', failHandler);
      checkpoint('navigation-complete', {kind: target.kind, loadStatus: observation.loadStatus});
    }
  }
  result.qualification = 'A rejected URL establishes missing direct-load capability in this fixed public runtime only. A resolved page is not functional equivalence. No extensions, credentials, personal history, native permissions or remote pages were used.';
  finish(result.errors.length === 0 ? 0 : 1);
}).catch(error => {result.errors.push({phase: 'probe', message: error.message}); finish(1);});
