// Exact selected source in resource-free VM fixtures; not a client or service test.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const work=path.resolve('.analysis-local/product-flow-ownership-work');
const directory=path.join(work,'selected-units');
const contracts=JSON.parse(fs.readFileSync(path.join(directory,'contracts.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function unit(name){const u=contracts.units.find(x=>x.name===name),b=fs.readFileSync(path.join(directory,u.sourceFilename));if(sha(b)!==u.spanHash)throw Error('Source unit changed');return b.toString('utf8');}
const fragment=id=>{const f=contracts.fragments.find(x=>x.id===id);if(!f)throw Error(id);return f.expression;};
const cases=[];
const homeCases=[
 ['codex-home',{},'Tzt',null],
 ['work-home',{workProduct:true},'Ezt','work'],
 ['chat-home',{workProduct:true,mode:'chat'},'Ezt','chat'],
 ['chat-selection-independent-of-product-flag',{mode:'chat'},'Ezt','chat'],
 ['unresolved-mode',{mode:null},'Ozt',null],
 ['custom-assistant-forces-chat',{pathname:'/g/custom'},'Ezt','chat'],
 ['mission-control-forces-work',{pathname:'/mission-control',mode:'chat'},'Ezt','work'],
 ['aeon-draft-work-shared',{workProduct:true,state:{aeonDraft:{fixture:true}},mode:'chat'},'Ezt','work'],
 ['snapshot-work-shared',{workProduct:true,state:{sharedSnapshotId:'owned-fixture'},mode:'chat'},'Ezt','work'],
 ['sketch-forces-chat',{workProduct:true,search:'?sketch=1'},'Ezt','chat'],
 ['sketch-work-surface',{workProduct:true,search:'?sketch=1&surface=work'},'Ezt','work'],
 ['temporary-chat-forces-chat',{workProduct:true,search:'?temporary-chat=true'},'Ezt','chat'],
 ['work-only-prevents-temporary-chat-override',{workProduct:true,workOnly:true,search:'?temporary-chat=true'},'Ezt','work'],
 ['upgrade-state-keeps-shared-home',{workProduct:true,workStatus:'denied',workReason:'free-plan',unionStatus:'denied'},'Ezt','work'],
 ['project-closed-default-forces-chat',{workProduct:true,pathname:'/g/fixture/project',projectData:{kind:'fixture',gizmo:{id:'owned-project'}},projectOpen:'other'},'Ezt','chat'],
 ['chat-ineligible-keeps-codex-home',{chatCapable:false},'Tzt',null],
];
for(const [id,input,expectedType,expectedMode]of homeCases){
 const fixture={pathname:'/',search:'',hash:'',state:null,mode:'work',workProduct:false,workOnly:false,workStatus:'allowed',unionStatus:'allowed',chatCapable:true,chatLoading:false,seatCapable:false,seatLoading:false,...input};
 const context=vm.createContext({fixtureJSON:JSON.stringify(fixture)},{codeGeneration:{strings:false,wasm:false}});
 const code=`
 const fixture=JSON.parse(fixtureJSON),effects=[];
 class URLSearchParams{constructor(s){this.entries=String(s).replace(/^\\?/, '').split('&').map(x=>x.split('='));}get(k){return this.entries.find(x=>x[0]===k)?.[1]??null;}}
 const [ik,pu,Wl,Ne,li,ic,Po,hS,IV,yf]=['ik','pu','Wl','Ne','li','ic','Po','hS','IV','work-product'];
 const [UE,Yg,gk,iO,BC]=['UE','Yg','gk','iO','BC'];
 const J9=[],Nm={GO:'go',FREE:'free'},Tzt='Tzt',Ezt='Ezt',Ozt='Ozt',GDe='GDe',EFt='EFt';
 const Y9={c:n=>Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
 const X9={useContext:()=>null,useState:v=>[typeof v==='function'?v():v,()=>{}]};
 const Z9={Fragment:'Fragment',jsx:(type,props,key)=>({type,props,key}),jsxs:(type,props,key)=>({type,props,key})};
 function q(k){return k===ik?fixture.mode:k===pu?{status:fixture.unionStatus}:k===Wl?{status:fixture.workStatus,reason:fixture.workReason}:k===li?fixture.workOnly:k===Ne?false:undefined;}
 function Q(k,arg){return k===Po?(arg.name==='chatgpt'?{isCapable:fixture.chatCapable,isLoading:fixture.chatLoading,isError:false}:{isCapable:fixture.seatCapable,isLoading:fixture.seatLoading}):k===hS?{data:fixture.projectData??null}:undefined;}
 function ir(){return{value:{},get:q};}
 function Dt(){return{...fixture,key:'owned-location'};} function t_(){return true;}
 function Xg(p){return p==='/g/custom'?'owned-custom-assistant':null;}
 function vo(p){return p==='/g/fixture/project'?'owned-project':null;}
 function NO(s){return s?.chatGptProjectId??null;}
 function hde(v){return v!=null;} function wD(){return fixture.projectOpen??'open-default';}
 function gg(){return fixture.workProduct?yf:'codex-product';}
 function Xd(pattern,p){return p===pattern?{fixture:true}:null;}
 function Wg(s){return s.includes('temporary-chat=true');}
 function Df(){return'owned-input';} function BV(){return null;}
 const rzt=()=>{},eme=()=>{},QTe=()=>{},nw=()=>undefined,ZT=()=>false,bC=()=>({systemHints:[]}),wFe=()=>({systemHints:[]}),cT=()=>null,NT=()=>{},JAe=()=>{},yzt=()=>{};
 ${unit('cPt')}
 const Dbe=cPt;
 ${unit('wzt')}
 const root=wzt({routeProjectId:null,workspaceAgent:null});
 const tree=root.type==='GDe'?root.props.children({id:'owned-controller'}):root;
 const selected=tree.type==='Fragment'?tree.props.children.find(x=>x&&['Tzt','Ezt'].includes(x.type)):tree;
 globalThis.observation={rootType:root.type,selectedType:selected.type,mode:selected.props?.mode??null,canSwitchMode:selected.props?.canSwitchMode??null};
 `;
 try{
  vm.runInContext(code,context,{timeout:200});
  const actual=JSON.parse(JSON.stringify(context.observation));
  cases.push({id:'HOME:'+id,kind:'exact-complete-wzt-render-with-owned-dependencies',fixture,expected:{selectedType:expectedType,mode:expectedMode},actual,passed:actual.selectedType===expectedType&&actual.mode===expectedMode});
 }catch(e){cases.push({id:'HOME:'+id,fixture,passed:false,error:String(e)});}
}
const submitCases=[
 ['codex',{},'$X'],
 ['work-local',{mode:'work',location:'local'},'$X'],
 ['chat',{mode:'chat',location:'local'},'CIt'],
 ['work-cloud',{mode:'work',location:'cloud'},'CIt'],
 ['work-cloud-special',{mode:'work',location:'cloud',special:true},'$X'],
 ['work-cloud-special-temporary',{mode:'work',location:'cloud',special:true,temporary:true},'CIt'],
 ['work-cloud-special-project',{mode:'work',location:'cloud',special:true,projectId:'owned-project'},'CIt'],
 ['work-cloud-special-draft',{mode:'work',location:'cloud',special:true,draft:true},'CIt'],
 ['work-location-pending',{mode:'work'},'CIt'],
 ['chat-without-state',{mode:'chat',noState:true},'$X'],
 ['controller-not-mounted',{mode:'work',location:'local',noController:true},null],
];
for(const [id,input,expected]of submitCases){
 const fixture={mode:null,location:null,special:false,temporary:false,projectId:null,draft:false,noState:false,noController:false,...input};
 const context=vm.createContext({fixtureJSON:JSON.stringify(fixture)},{codeGeneration:{strings:false,wasm:false}});
 const code=`
 const f=JSON.parse(fixtureJSON),l=f.mode,c=f.noController?null:{id:'owned-controller'},s=f.noState?null:{runLocationState:{effectiveLocation:f.location,unavailableReasons:{cloud:'owned-pending'}},isTemporaryChat:f.temporary,composerProps:{projectId:f.projectId}};
 const Se=f.draft?{owned:true}:null,Ul='special',q=()=>f.special;
 let ${fragment('NRt:pt')}; let ${fragment('NRt:mt')}; let ${fragment('NRt:ht')};
 let ${fragment('NRt:Qt')}; let ${fragment('NRt:er')}; let ${fragment('NRt:vr')};
 const Bt=c===null,de=false,me=null,an=false,rn=true,on=false,y=l==null;
 const Mr=null,Dr=null,_r={kind:'home',chrome:null},ft='owned-thread',N={formatMessage:o=>o.defaultMessage},nt=null,jn='local',Gn=null,pr={},it=true,dn=null,pn=null;
 const [Px,x4,JV,CIt,$X,T5,qV,tIe,SC]=['Px','x4','JV','CIt','$X','T5','qV','tIe','SC'];
 const F9={jsx:(type,props)=>({type,props}),jsxs:(type,props)=>({type,props})},pL=()=>({}),j=false;
 const render=${fragment('NRt:Nr')};
 const tree=render(null,null),types=[];
 function walk(n){if(!n||typeof n!=='object')return;if(n.type)types.push(n.type);let c=n.props?.children;if(Array.isArray(c))c.forEach(walk);else walk(c);}
 walk(tree);globalThis.observation={usesRemoteComposer:!!vr,workLocal:!!er,cloudSpecial:!!ht,selectedComposer:types.find(x=>x==='CIt'||x==='$X')??null,types};
 `;
 try{
  vm.runInContext(code,context,{timeout:200});const actual=JSON.parse(JSON.stringify(context.observation));
  cases.push({id:'SUBMIT:'+id,kind:'exact-NRt-selected-callback-and-predicates-with-owned-free-variables',fixture,expected:{selectedComposer:expected},actual,passed:actual.selectedComposer===expected});
 }catch(e){cases.push({id:'SUBMIT:'+id,fixture,passed:false,error:String(e)});}
}
const result={baselineId:contracts.baselineId,recordedAtUtc:new Date().toISOString(),node:process.version,scope:'Exact complete wzt + cPt, and selected NRt predicates/callback only. Own VM dependency/free-variable fixtures; no React mount, original client, backend, native API, disk storage or model execution.',cases,counts:{cases:cases.length,passed:cases.filter(x=>x.passed).length,failed:cases.filter(x=>!x.passed).length,productFeaturePassesAdded:0,originalClientRunsAdded:0,modelSubmissionsAdded:0},fullAnalysisCompleted:false};
const output=process.argv[2]??path.join(work,'probe-observations.json');
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({output,counts:result.counts,failures:cases.filter(x=>!x.passed)}));
process.exitCode=result.counts.failed?1:0;
