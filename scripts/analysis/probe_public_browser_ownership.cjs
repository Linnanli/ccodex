// Public-runtime capability probe using one synthetic page and hidden owned windows.
const fs=require('node:fs'),path=require('node:path');
const {app,BaseWindow,WebContentsView}=require('electron');
const output=app.commandLine.getSwitchValue('ccodex-owned-output');
if(!output||!path.isAbsolute(output))throw Error('Absolute owned output required');
fs.mkdirSync(output,{recursive:true});
for(const [kind,directory]of [['appData','app-data'],['userData','user-data'],['sessionData','session-data'],['crashDumps','crash-dumps']]){
 const destination=path.join(output,directory);fs.mkdirSync(destination,{recursive:true});app.setPath(kind,destination);
}
app.setAppLogsPath(path.join(output,'logs'));app.setName('ccodex-owned-browser-capability-probe');
for(const flag of ['disable-background-networking','disable-component-update','disable-sync','no-first-run'])app.commandLine.appendSwitch(flag);
const result={kind:'owned-public-browser-ownership-probe',startedAtUtc:new Date().toISOString(),
 versions:{electron:process.versions.electron,node:process.versions.node,chrome:process.versions.chrome},
 originalClientRunsAdded:0,modelSubmissionsAdded:0,observations:[],errors:[]};
let finished=false;
function finish(code){
 if(finished)return;finished=true;result.exitCode=code;result.completedAtUtc=new Date().toISOString();
 fs.writeFileSync(path.join(output,'runtime-observations.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result));app.exit(code);
}
setTimeout(()=>{result.errors.push({phase:'timeout'});finish(2)},20000).unref();
app.whenReady().then(async()=>{
 const a=new BaseWindow({show:false,width:120,height:100}),b=new BaseWindow({show:false,width:120,height:100});
 const view=new WebContentsView({webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
 a.contentView.addChildView(view);view.setBounds({x:0,y:0,width:100,height:80});
 const contents=view.webContents,id=contents.id;
 await contents.loadURL('data:text/html,'+encodeURIComponent('<!doctype html><title>CCODEX_OWNED_TRANSFER</title><input id="fixture" value="initial"><script>window.fixtureHeap="initial-heap"</script>'));
 await contents.executeJavaScript('document.getElementById("fixture").value="edited-form";window.fixtureHeap="edited-live-heap"');
 const getState=()=>contents.executeJavaScript('({input:document.getElementById("fixture").value,heap:window.fixtureHeap})');
 const before=await getState();
 a.contentView.removeChildView(view);b.contentView.addChildView(view);
 const moved=await getState();
 result.observations.push({id:'move-existing-view-between-owned-windows',status:'completed',sameWebContentsId:view.webContents.id===id,before,after:moved});
 b.contentView.removeChildView(view);
 try{
  const adopted=new WebContentsView({webContents:contents});b.contentView.addChildView(adopted);
  result.observations.push({id:'construct-view-adopting-existing-contents',status:'completed',sameWebContentsId:adopted.webContents.id===id,after:await getState()});
 }catch(error){result.observations.push({id:'construct-view-adopting-existing-contents',status:'rejected',message:error.message});}
 result.limitation='Same owned live WebContents only; no duplication, renderer webview lease, original Owl transfer, route admission or account state tested.';
 finish(0);
}).catch(error=>{result.errors.push({phase:'probe',message:error.message});finish(1)});
