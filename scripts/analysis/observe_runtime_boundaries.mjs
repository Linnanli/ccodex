// Execute only saved first-party function units with synthetic in-memory inputs.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {EventEmitter} from 'node:events';

const [root, outputDirectory] = process.argv.slice(2);
const work = path.join(root,'.analysis-local/runtime-decisions-work/source-01');
const stages = ['main-CqEoQDOU','bootstrap-CooIJpZm'];
const sources = stages.flatMap(stage => {
  const contract = JSON.parse(fs.readFileSync(path.join(work,stage,'source-contracts.json')));
  return contract.units.map(unit=>({...unit,path:path.join(work,stage,unit.sourceFilename)}));
});
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const used = new Map();
function unit(fragment) {
  const matches=sources.filter(u=>u.sourceFilename.includes(fragment));assert.equal(matches.length,1,fragment);
  const selected=matches[0],data=fs.readFileSync(selected.path);assert.equal(hash(data),selected.spanHash);
  used.set(selected.path,selected);return data.toString('utf8');
}
const guardSource=unit('runtime-entry-guard'),handlerSource=unit('task-manager-handler');
const observerSource=unit('method-observeRelaunchNotificationPolicy-');
const getterSource=unit('method-getRelaunchNotificationPolicy-');
const schedulerSource=unit('method-scheduleForcedUpdateInstall-');
const installSource=unit('method-installForcedUpdate-');
const leaseSource=unit('002-function-eJ.txt');
const results=[];
function method(source,globals={}) {return vm.runInNewContext('({'+source+'})',globals,{timeout:1000})[source.match(/^(?:async )?([^ (]+)/)[1]];}
function errorMessage(action) {try{action();return null;}catch(e){return e.message;}}
async function scenario(id,claim,action) {
  await action();results.push({id,claim,status:'passed',scope:'selected-source-unit with synthetic dependencies; no app or native execution'});
}
await scenario('RB-OBS-01','非空Electron版本且缺少能力时，原guard拒绝启动',()=>{
  const message=errorMessage(()=>vm.runInNewContext(guardSource,{process:{versions:{electron:'synthetic'}},f:{app:{}}},{timeout:1000}));
  assert.match(message,/requires the Owl app shell/);
});
await scenario('RB-OBS-02','函数值只通过shape门槛，guard不会调用该能力',()=>{
  let called=0;vm.runInNewContext(guardSource,{process:{versions:{electron:'synthetic'}},f:{app:{showTaskManager(){called++;}}}},{timeout:1000});assert.equal(called,0);
});
await scenario('RB-OBS-03','Electron版本为空时跳过该guard',()=>{
  vm.runInNewContext(guardSource,{process:{versions:{}},f:{app:{}}},{timeout:1000});
});
await scenario('RB-OBS-04','非空但falsy版本仍进入guard，不是truthy检查',()=>{
  assert.match(errorMessage(()=>vm.runInNewContext(guardSource,{process:{versions:{electron:''}},f:{app:{}}},{timeout:1000})),/requires the Owl app shell/);
});
await scenario('RB-OBS-05','Help handler无参数调用能力并直接返回值',()=>{
  const token={synthetic:true};let args=null;
  const fn=vm.runInNewContext('('+handlerSource+')',{_:{app:{showTaskManager(...a){args=a;return token;}}}},{timeout:1000});assert.equal(fn(),token);assert.equal(args.length,0);
});
await scenario('RB-OBS-06','Help handler同步异常直接传播',()=>{
  const fn=vm.runInNewContext('('+handlerSource+')',{_:{app:{showTaskManager(){throw Error('synthetic-task-manager-error');}}}},{timeout:1000});assert.equal(errorMessage(fn),'synthetic-task-manager-error');
});
await scenario('RB-OBS-07','空策略发现结果不订阅事件、不启动强制调度',()=>{
  let schedule=0;const state={scheduleForcedUpdateInstall(){schedule++;}};method(observerSource,{ut:()=>null}).call(state);assert.equal(state.owlUpdatePolicies,null);assert.equal(schedule,0);
});
await scenario('RB-OBS-08','有效provider先订阅再调度，策略事件再触发调度',()=>{
  const order=[];let listener;
  const provider={on(event,fn){assert.equal(event,'relaunch-notification-policy-changed');order.push('subscribe');listener=fn;}};
  const state={scheduleForcedUpdateInstall(){order.push('schedule');}};method(observerSource,{ut:()=>provider}).call(state);assert.deepEqual(order,['subscribe','schedule']);listener();assert.deepEqual(order,['subscribe','schedule','schedule']);
});
await scenario('RB-OBS-09','provider.on抛错不会在observer内吞掉，也不会继续调度',()=>{
  let schedule=0;const state={scheduleForcedUpdateInstall(){schedule++;}};
  assert.equal(errorMessage(()=>method(observerSource,{ut:()=>({on(){throw Error('synthetic-on-error');}})}).call(state)),'synthetic-on-error');assert.equal(schedule,0);
});
await scenario('RB-OBS-10','空policy getter返回null，不访问native getter',()=>{
  let get=0;assert.equal(method(getterSource,{dt(){get++;}}).call({owlUpdatePolicies:null}),null);assert.equal(get,0);
});
await scenario('RB-OBS-11','native policy读取异常直接传播',()=>{
  assert.equal(errorMessage(()=>method(getterSource,{dt(){throw Error('synthetic-policy-read-error');}}).call({owlUpdatePolicies:{}})),'synthetic-policy-read-error');
});
function scheduleState(policy,overrides={}) {
  const events=[];const state={forcedUpdateTimer:{syntheticTimer:true},isUpdateReady:true,updateDownloadedAtMs:100,forcedUpdateInstallStarted:false,forcedUpdateRetryAtMs:null,
    getRelaunchNotificationPolicy(){return policy;},setRelaunchNotice(v){events.push(['notice',v]);},scheduleForcedUpdateInstallAt(...a){events.push(['schedule',...a]);},...overrides};
  const fn=method(schedulerSource,{clearTimeout(timer){events.push(['clear',timer]);},ft:()=>250,Un:60,Date:{now:()=>101}});
  fn.call(state);return{state,events};
}
await scenario('RB-OBS-12','null策略清除既有timer、清空notice并停止强制安装调度',()=>{
  const {state,events}=scheduleState(null);assert.equal(state.forcedUpdateTimer,null);assert.equal(events[0][0],'clear');assert.deepEqual(events.slice(1),[['notice',null]]);
});
await scenario('RB-OBS-13','非2的relaunchNotification不进入强制安装路径',()=>{
  const {events}=scheduleState({relaunchNotification:1});assert.deepEqual(events.slice(1),[['notice',null]]);
});
await scenario('RB-OBS-14','未ready的更新不进入强制安装路径',()=>{
  const {events}=scheduleState({relaunchNotification:2},{isUpdateReady:false});assert.deepEqual(events.slice(1),[['notice',null]]);
});
await scenario('RB-OBS-15','已开始强制安装时不重复调度',()=>{
  const {events}=scheduleState({relaunchNotification:2},{forcedUpdateInstallStarted:true});assert.deepEqual(events.slice(1),[['notice',null]]);
});
await scenario('RB-OBS-16','有效策略保留retry deadline与notice边界的计算顺序',()=>{
  const {events}=scheduleState({relaunchNotification:2},{forcedUpdateRetryAtMs:300});assert.deepEqual(events.slice(1),[['notice',null],['schedule',300,250,103]]);
});
await scenario('RB-OBS-17','强制安装成功时保持started且不安排重试',async()=>{
  let retry=0;const state={forcedUpdateInstallStarted:false,isUpdateReady:true,setRelaunchNotice(){},logger:{info(){}},async installUpdatesIfAvailable(){return true;},scheduleForcedUpdateInstall(){retry++;}};
  await method(installSource,{Vn:1000,Date:{now:()=>10}}).call(state);assert.equal(state.forcedUpdateInstallStarted,true);assert.equal(retry,0);
});
await scenario('RB-OBS-18','安装返回false但更新仍ready时复位started并定时重试',async()=>{
  let retry=0;const state={forcedUpdateInstallStarted:false,isUpdateReady:true,setRelaunchNotice(){},logger:{info(){}},async installUpdatesIfAvailable(){return false;},scheduleForcedUpdateInstall(){retry++;}};
  await method(installSource,{Vn:1000,Date:{now:()=>10}}).call(state);assert.equal(state.forcedUpdateInstallStarted,false);assert.equal(state.forcedUpdateRetryAtMs,1010);assert.equal(retry,1);
});
const lease=vm.runInNewContext('('+leaseSource+')',{}, {timeout:1000});
function view(result='synthetic-lease') {
  const v=new EventEmitter();Object.assign(v,{id:7,destroyed:false,destroyCount:0,receivedOwner:null,_createWebViewAdoptionLease(owner){this.receivedOwner=owner;return result;},isDestroyed(){return this.destroyed;},destroy(){this.destroyCount++;this.destroyed=true;this.emit('destroyed');}});return v;
}
await scenario('RB-OBS-19','有效lease按owner创建，登记route与history并在destroyed清理',()=>{
  const owner={owned:true},state={owner,pendingAdoptedWebviewsByWebContentsId:new Map()},v=view(),route={browserTabId:'synthetic'},history={navigation:'back'};
  assert.equal(lease(state,v,route,history),'synthetic-lease');assert.equal(v.receivedOwner,owner);const pending=state.pendingAdoptedWebviewsByWebContentsId.get(7);
  assert.equal(pending.route,route);assert.equal(pending.initialHistoryNavigation,history);assert.equal(pending.acceptedHostIdentity,null);v.destroy();assert.equal(state.pendingAdoptedWebviewsByWebContentsId.size,0);assert.equal(v.listenerCount('destroyed'),0);
});
await scenario('RB-OBS-20','空lease销毁仍存活的view，且不留下pending记录',()=>{
  const state={owner:{},pendingAdoptedWebviewsByWebContentsId:new Map()},v=view('');assert.match(errorMessage(()=>lease(state,v,{},null)),/lease is empty/);assert.equal(v.destroyCount,1);assert.equal(state.pendingAdoptedWebviewsByWebContentsId.size,0);
});
await scenario('RB-OBS-21','lease创建抛错时保留异常并销毁仍存活的view',()=>{
  const state={owner:{},pendingAdoptedWebviewsByWebContentsId:new Map()},v=view();v._createWebViewAdoptionLease=()=>{throw Error('synthetic-lease-error');};assert.equal(errorMessage(()=>lease(state,v,{},null)),'synthetic-lease-error');assert.equal(v.destroyCount,1);
});
await scenario('RB-OBS-22','已销毁view的无效lease不会再次destroy',()=>{
  const state={owner:{},pendingAdoptedWebviewsByWebContentsId:new Map()},v=view('');v.destroyed=true;assert.match(errorMessage(()=>lease(state,v,{},null)),/lease is empty/);assert.equal(v.destroyCount,0);
});
fs.mkdirSync(outputDirectory);
const result={baselineId:'codex-26.1007.30912-c5b273322a83',recordedAtUtc:new Date().toISOString(),nodeVersion:process.version,
  selectedSourceUnits:[...used.values()],scenarios:results,counts:{passed:results.length,failed:0,actualNativeOrUiBehaviorsVerified:0,modelSubmissionsAdded:0,originalClientRunsAdded:0},
  limitations:['Synthetic globals and memory-only receivers; no whole target Program executed.','Policy parsing, timer implementation, ft timing helper and native event delivery not verified.','No actual task-manager UI, updater, adoption token consumer or selected shell compatibility accepted.']};
fs.writeFileSync(path.join(outputDirectory,'observations.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result.counts));
