'use strict';
// Owned public-runtime capability observation. No target modules or services are loaded.
const fs=require('fs'),path=require('path');
const electron=require('electron');
const prefix='--ccodex-owned-surface=';
const work=process.argv.find(x=>x.startsWith(prefix))?.slice(prefix.length);
if(!work || !path.isAbsolute(work))throw new Error('owned output required');
const comparison=JSON.parse(fs.readFileSync(path.join(work,'surface-comparison.json'),'utf8'));
const {app,BrowserWindow,session}=electron;
const profile=path.join(work,'probe-01/profile');
fs.mkdirSync(profile,{recursive:true});
app.setPath('userData',profile);app.setPath('sessionData',profile);
app.commandLine.appendSwitch('disable-background-networking');
app.commandLine.appendSwitch('disable-component-update');
app.commandLine.appendSwitch('disable-sync');
app.commandLine.appendSwitch('disable-default-apps');
let window;
const result={kind:'owned-fixed-public-runtime-surface-observation',versions:process.versions,originalClientRunsAdded:0,modelSubmissionsAdded:0,realServiceCalls:0,observations:[],controls:[]};
const save=()=>fs.writeFileSync(path.join(work,'probe-01/observation.json'),JSON.stringify(result,null,2)+'\n');
setTimeout(()=>{result.error='20-second probe deadline';save();app.exit(8);},20000).unref();
app.whenReady().then(()=>{
  const ownedSession=session.fromPartition('ccodex-owned-surface',{cache:false});
  window=new BrowserWindow({show:false,width:320,height:240,webPreferences:{session:ownedSession,sandbox:true,contextIsolation:true,nodeIntegration:false}});
  for(const row of comparison.rows.filter(x=>!x.publicTypes.found)) {
    const parts=row.normalizedApi.replace(/^electron\./,'').split('.');
    const first=parts.shift();
    let receiver=first==='BrowserWindow#instance'?window:first==='Session#instance'?ownedSession:electron[first];
    for(const key of parts)receiver=receiver==null?undefined:receiver[key];
    result.observations.push({id:row.id,canonicalApi:row.canonicalApi,type:typeof receiver,invoked:false});
  }
  for(const [name,value]of [['app.getAppMetrics',app.getAppMetrics],['window.setAlwaysOnTop',window.setAlwaysOnTop],['window.setShape',window.setShape],['screen.getCursorScreenPoint',electron.screen.getCursorScreenPoint],['session.setPermissionRequestHandler',ownedSession.setPermissionRequestHandler],['systemPreferences.getMediaAccessStatus',electron.systemPreferences.getMediaAccessStatus]])result.controls.push({name,type:typeof value,invoked:false});
  result.windowLoadedUrl=window.webContents.getURL();
  window.destroy();result.ownedWindowDestroyed=window.isDestroyed();
  result.complete=true;save();app.quit();
}).catch(error=>{result.error=error.stack;save();if(window&&!window.isDestroyed())window.destroy();app.exit(1);});
