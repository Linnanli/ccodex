// Match the target's webview embedding with synthetic host/guest controls only.
const fs = require('node:fs'), path = require('node:path');
const {app, BrowserWindow, session} = require('electron');
const output = app.commandLine.getSwitchValue('ccodex-owned-output');
if (!path.isAbsolute(output)) throw Error('Absolute owned output required');
for (const [kind, name] of [['appData', 'app-data'], ['userData', 'user-data'],
  ['sessionData', 'session-data'], ['crashDumps', 'crash-dumps']]) {
  const directory = path.join(output, name); fs.mkdirSync(directory, {recursive: true}); app.setPath(kind, directory);
}
app.setAppLogsPath(path.join(output, 'logs')); app.setName('ccodex-owned-native-settings-guest');
for (const flag of ['disable-background-networking', 'disable-component-update', 'disable-sync', 'no-first-run'])
  app.commandLine.appendSwitch(flag);
const urls = ['chrome://settings/addresses', 'chrome://settings/contactInfo', 'chrome://extensions/',
  'chrome://password-manager/passwords', 'chrome://password-manager/', 'chrome://settings/content',
  'chrome://settings/handlers', 'chrome://settings/cookies'];
const result = {kind: 'owned-native-settings-webview-probe', startedAtUtc: new Date().toISOString(),
  versions: {electron: process.versions.electron, node: process.versions.node, chrome: process.versions.chrome},
  observations: [], blockedExternalRequests: 0, errors: [], originalClientRunsAdded: 0,
  modelSubmissionsAdded: 0, realBrowserDataRead: false, originalModulesLoaded: false};
let finished = false;
function checkpoint(phase) {
  if (finished) return;
  fs.appendFileSync(path.join(output, 'phase-journal.jsonl'), JSON.stringify({phase, atUtc: new Date().toISOString()}) + '\n');
  fs.writeFileSync(path.join(output, 'runtime-observations.json'), JSON.stringify({...result, phase, terminal: false}, null, 2) + '\n');
}
function finish(code) {
  if (finished) return; finished = true;
  result.exitCode = code; result.terminal = true; result.completedAtUtc = new Date().toISOString();
  fs.writeFileSync(path.join(output, 'runtime-observations.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({exitCode: code, observations: result.observations.length, errors: result.errors}));
  app.exit(code);
}
setTimeout(() => {result.errors.push({phase: 'overall-timeout'}); finish(2);}, 47000).unref();
checkpoint('before-ready');
app.whenReady().then(async () => {
  if (finished) return; checkpoint('ready');
  const partition = 'ccodex-owned-settings-guest', guestSession = session.fromPartition(partition);
  guestSession.setPermissionCheckHandler(() => false);
  guestSession.setPermissionRequestHandler((_, __, callback) => callback(false));
  for (const ownedSession of [session.defaultSession, guestSession])
    ownedSession.webRequest.onBeforeRequest((details, callback) => {
      const external = /^(https?|wss?|ftp):/i.test(details.url);
      if (external) result.blockedExternalRequests++;
      callback({cancel: external});
    });
  const window = new BrowserWindow({show: false, width: 400, height: 300, webPreferences: {
    webviewTag: true, sandbox: true, contextIsolation: true, nodeIntegration: false}});
  const contents = window.webContents;
  await contents.loadURL('data:text/html,' + encodeURIComponent('<!doctype html><title>CCODEX_OWNED_HOST</title><main></main>'));
  result.hostControl = await contents.executeJavaScript('document.title');
  if (result.hostControl !== 'CCODEX_OWNED_HOST') throw Error('host control mismatch');
  const guestControl = 'data:text/html,' + encodeURIComponent('<!doctype html><title>CCODEX_OWNED_GUEST</title>owned');
  const guest = await contents.executeJavaScript(`new Promise(resolve=>{
    const view=document.createElement('webview');view.style='width:300px;height:200px';
    view.setAttribute('partition',${JSON.stringify(partition)});view.setAttribute('src',${JSON.stringify(guestControl)});
    window.ownedView=view;let done=false;const finish=value=>{if(done)return;done=true;clearTimeout(timer);resolve(value)};
    const timer=setTimeout(()=>finish({status:'timeout'}),4000);
    view.addEventListener('dom-ready',async()=>{try{finish({status:'resolved',title:await view.executeJavaScript('document.title')})}catch(error){finish({status:'rejected',message:error.message})}},{once:true});
    view.addEventListener('did-fail-load',event=>{if(event.isMainFrame)finish({status:'rejected',message:event.errorDescription})});
    document.body.append(view);
  })`);
  result.guestControl = guest; checkpoint('guest-control-complete');
  if (guest.status !== 'resolved' || guest.title !== 'CCODEX_OWNED_GUEST') throw Error('guest control mismatch');
  for (const url of urls) {
    if (finished) return; checkpoint('before-' + url);
    const observation = await contents.executeJavaScript(`(async()=>{
      const view=window.ownedView;let timer;
      try{await Promise.race([view.loadURL(${JSON.stringify(url)}),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('navigation-timeout')),2000)})]);
        return {status:'resolved',url:view.getURL(),title:await view.executeJavaScript('document.title')};
      }catch(error){return {status:'rejected',message:error.message}}
      finally{clearTimeout(timer)}
    })()`);
    result.observations.push({requestedUrl: url, ...observation}); checkpoint('after-' + url);
  }
  result.qualification = 'Same synthetic host and guest webview in a fresh memory partition; direct URL load only. No functional settings actions, original Owl, credentials or personal browser state tested.';
  finish(0);
}).catch(error => {result.errors.push({phase: 'probe', message: error.message}); finish(1);});
