// Standalone analysis probe: synthetic local pages, no accounts or model calls.
const fs = require('node:fs');
const path = require('node:path');
const {app, WebContentsView} = require('electron');

const output = app.commandLine.getSwitchValue('ccodex-owned-output');
if (!output || !path.isAbsolute(output)) throw Error('Absolute owned output directory required');
fs.mkdirSync(output, {recursive: true});
for (const [kind, directory] of [['appData','app-data'],['userData','user-data'],['sessionData','session-data'],['crashDumps','crash-dumps']]) {
  const destination = path.join(output, directory); fs.mkdirSync(destination, {recursive: true}); app.setPath(kind, destination);
}
app.setAppLogsPath(path.join(output, 'logs'));
app.setName('ccodex-public-runtime-analysis');
for (const flag of ['disable-background-networking','disable-component-update','disable-sync','no-first-run']) app.commandLine.appendSwitch(flag);
const result = {kind:'owned-public-Electron-analysis-probe',startedAtUtc:new Date().toISOString(),
  versions:Object.fromEntries(['electron','node','chrome','modules','napi'].map(key=>[key,process.versions[key]])),
  probePid:process.pid,originalClientRunsAdded:0,modelSubmissionsAdded:0,accountDataRead:false,capabilities:{},observations:[],errors:[]};
const views=[];
let finished=false;
function finish(code) {
  if(finished)return;finished=true;result.completedAtUtc=new Date().toISOString();result.exitCode=code;
  fs.writeFileSync(path.join(output,'runtime-observations.json'),JSON.stringify(result,null,2)+'\n');
  console.log('CCODEX_PUBLIC_RUNTIME_RESULT '+JSON.stringify({versions:result.versions,capabilities:result.capabilities,observations:result.observations,errors:result.errors}));
  app.exit(code);
}
setTimeout(()=>{result.errors.push({phase:'timeout',message:'Owned runtime probe exceeded 20 seconds'});finish(2);},20000).unref();
function newView() {
  const view=new WebContentsView({webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});views.push(view);return view.webContents;
}
app.whenReady().then(async()=>{
  const contents=newView();
  Object.assign(result.capabilities,{
    showTaskManager:typeof app.showTaskManager,getAppMetrics:typeof app.getAppMetrics,
    webContentsClone:typeof contents.clone,webViewAdoptionLease:typeof contents._createWebViewAdoptionLease,
    setAgentActive:typeof contents.setAgentActive,
    navigationHistoryRestore:typeof contents.navigationHistory?.restore,
    navigationHistoryGetAllEntries:typeof contents.navigationHistory?.getAllEntries,
    permissionObject:typeof process.permission,
    allowIpcInNodeEnvironmentFlags:process.allowedNodeEnvironmentFlags.has('--allow-ipc'),
    permissionInNodeEnvironmentFlags:process.allowedNodeEnvironmentFlags.has('--permission')});
  try {const binding=process._linkedBinding('electron_browser_owl_update_policies');result.capabilities.owlUpdateBinding=typeof binding;}
  catch(error){result.capabilities.owlUpdateBinding='unavailable';result.observations.push({id:'public-owl-update-binding',status:'unavailable',message:error.message});}
  const metrics=app.getAppMetrics();
  result.observations.push({id:'public-process-metrics',status:'returned',records:metrics.length,
    recordKeys:[...new Set(metrics.flatMap(item=>Object.keys(item)))].sort(),
    cpuKeys:[...new Set(metrics.flatMap(item=>Object.keys(item.cpu||{})))].sort(),
    memoryKeys:[...new Set(metrics.flatMap(item=>Object.keys(item.memory||{})))].sort()});
  const pageA='data:text/html,'+encodeURIComponent('<!doctype html><title>CCODEX_PUBLIC_A</title><input id="fixture" value="initial"><script>window.fixtureHeapSentinel="owned-memory-only"</script>');
  const pageB='data:text/html,'+encodeURIComponent('<!doctype html><title>CCODEX_PUBLIC_B</title><p>owned synthetic fixture</p>');
  await contents.loadURL(pageA);
  await contents.executeJavaScript('document.getElementById("fixture").value="edited-owned-fixture";window.fixtureHeapSentinel="edited-live-heap"');
  await contents.loadURL(pageB);
  const entries=contents.navigationHistory.getAllEntries(),restored=newView();
  await restored.navigationHistory.restore({index:0,entries});
  const restoredState=await restored.executeJavaScript('({input:document.getElementById("fixture")?.value??null,heap:window.fixtureHeapSentinel??null,title:document.title})');
  result.observations.push({id:'public-navigation-history-restore',status:'resolved',entryCount:entries.length,
    entryKeys:[...new Set(entries.flatMap(entry=>Object.keys(entry)))].sort(),restoredIndex:restored.navigationHistory.getActiveIndex(),
    restoredUrlMatchesSyntheticA:restored.getURL()===pageA,restoredState,
    limitation:'Public primitive observation only; no Owl clone/adoption or full functional equivalence tested.'});
  finish(0);
}).catch(error=>{result.errors.push({phase:'probe',message:error.message});finish(1);});
