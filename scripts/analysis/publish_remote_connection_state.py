"""Publish the bounded remote state analysis once, preserving existing reader state."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
W=ROOT/'.analysis-local/remote-connection-state-work'
A=W/'author-01'
PREFIX='raw/remote-connection-state/'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):return json.loads(p.read_bytes())
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()

c=read(A/'remote-connection-state-contracts.json')
counts=read(A/'counts.json')
verification=read(W/'verification-01.json')
assert verification['status']=='passed'
assert len(c['selectedUnits'])==45 and len(c['facts'])==23 and len(c['programLexicalJoins'])==616
stages=['analyze-01','extract-01','observe-01','curate-01','verify-author-01','verify-author-02']
for stage in stages:
    receipt=read(W/'attempts'/stage/'receipt.json')
    assert receipt['exitCode']==(1 if stage=='verify-author-01' else 0) and receipt['sourcesUnchanged']
readers=['report.md','analysis-state.json','implementation-plan.md','gaps.md','behavior-checks.md']
before={n:(OUT/n).read_bytes() for n in readers}
old=json.loads(before['analysis-state.json'])
assert len(old)==97 and 'remoteConnectionState' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining']==0
previous,_,_=build_context(OUT,BASE)
assert len(previous)==31 and all(old[k]==v for k,v in previous.items())
for item in c['inputPins']:
    assert pin((OUT/item['path']).read_bytes())=={k:item[k] for k in ['bytes','sha256']}
planned,copies={},[]
def copy(relative,path,kind='analysis_metadata'):
    b=path.read_bytes();target=PREFIX+relative
    assert target not in planned
    planned[target]=b
    copies.append({'original':str(path),'outputPath':target,**pin(b),'kind':kind})
for name in ['remote-connection-state-contracts.json','remote-connection-state-scenarios.json']:
    copy('author/'+name,A/name)
    planned[name]=(A/name).read_bytes()
for name in ['counts.json','summary.md']:
    copy('author/'+name,A/name)
copy('author/verification-01.json',W/'verification-01.json')
copy('observations/observations-01.json',W/'observations-01.json','synthetic_vm_observations')
planned['remote-connection-state-observations.json']=(W/'observations-01.json').read_bytes()
planned['remote-connection-state-summary.md']=(A/'summary.md').read_bytes()
for folder in ['source-01','source-02']:
    for path in sorted((W/folder).iterdir()):
        copy('analysis/'+folder+'/'+path.name,path,'selected_application_source' if path.suffix=='.txt' else 'analysis_metadata')
for stage in stages:
    for path in sorted((W/'attempts'/stage).iterdir()):
        copy('attempts/'+stage+'/'+path.name,path,'analysis_tool_source' if path.suffix in ['.mjs','.py'] else 'execution_metadata')
records=[]
for fact in c['facts']:
    r=fact['sourceReferences'][0]
    records.append({'id':fact['id'],'baselineId':BASE,'claim':fact['claim'],'sourcePath':r['sourcePath'],
                    'sourceHash':r['sourceHash'],'locator':{'kind':'byte-range',**r['byteRange']},
                    'spanHash':r['spanHash'],'sourceReferences':fact['sourceReferences'],
                    'method':fact['method'],'confidence':fact['confidence'],'verificationStatus':fact['verificationStatus'],
                    'qualification':fact['qualification'],'mode':'unknown','newGlobalEvidenceRecord':False,
                    'actualUiControlExecuted':False})
planned['remote-connection-state-evidence.jsonl']=('\n'.join(json.dumps(x,ensure_ascii=False) for x in records)+'\n').encode()
derived_names=['remote-connection-state-contracts.json','remote-connection-state-scenarios.json',
               'remote-connection-state-observations.json','remote-connection-state-summary.md','remote-connection-state-evidence.jsonl']
index={'schemaVersion':1,'baselineId':BASE,'kind':'bounded-remote-state-producer-and-refresh-contracts',
       'publishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'exactCopies':copies,'derived':[{'path':n,**pin(planned[n])} for n in derived_names],
       **counts,**c['constraints'],
       'sourceFilesByteChecked':verification['sourceFilesByteChecked'],
       'uniqueSourceSpansChecked':verification['uniqueSourceSpansChecked'],
       'sourceCoordinateOccurrencesChecked':verification['sourceCoordinateOccurrencesChecked'],
       'authorVerificationAttempts':2,'failedAuthorVerificationAttempts':1,
       'retainedFailure':'verify-author-01 used filename prefix to select a folder; source-02 also has 01-prefixed filenames. verify-author-02 uses the recorded savedPath folder. No observation failed.'}
planned['remote-connection-state-provenance.json']=encode(index)
for name in planned:assert not (OUT/name).exists(),name
for name,b in planned.items():
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);path.chmod(0o444)
patch,_,artifacts=build_context(OUT,BASE)
assert len(patch)==len(PROFILES)==32
assert all(old[k]==v for k,v in patch.items() if k!='remoteConnectionState')
state={**old,'remoteConnectionState':patch['remoteConnectionState']}
assert all(state[k]==v for k,v in old.items())
note=next(p[4] for p in PROFILES if p[0]=='remoteConnectionState')
marker='[完成标准审计](criteria-audit.md)'
report=before['report.md'].decode();assert report.count(marker)==1
changes={'analysis-state.json':encode(state),'report.md':report.replace(marker,note+'\n\n'+marker).encode()}
additions={
 'implementation-plan.md':'\n\n[远程目录刷新契约](remote-connection-state-summary.md)为目录状态、连接reconcile、平台/服务适配和共享契约提出四个职责边界。保留SSH旧失败传播、WSL最新等待/null保留/一次重试、remote-control授权矩阵与断开等待；目录发布不等于connected。renderer query、真实实例及耐久保存仍是阶段出口，第三方实现通过依赖引入。\n',
 'gaps.md':'\n\n[远程状态生产端](remote-connection-state-summary.md)补21源码事实/2推断及35项合成观察，关闭fKe注入、三类刷新/发布及registry查询的所选静态缺口。当前下一动作限定为接上renderer a8a/Zs状态query和实际host参数，再核对真实subscriber/provider/registry，最后核对appState耐久及平台行为。10集成场景未执行；37功能/26队列/160规格、模式unknown、排除0与完整分母未知保持。\n',
 'behavior-checks.md':'\n\n[远程刷新35项隔离观察](remote-connection-state-observations.json)运行完整fKe/wee构造器与选定方法，9保存单位24785字节。appState、registry、服务、比较器、类型谓词和计时器均为替身；没有hXe真实构造、native、IPC、SSH文件、网络或模型任务。[10集成规格](remote-connection-state-scenarios.json)未执行且不加入原160功能规格的执行数；模型样例余0。\n',
}
for name,addition in additions.items():changes[name]=before[name]+addition.encode()
readme_before=(ROOT/'README.md').read_bytes()
readme=readme_before+('\n- [远程目录与刷新：三类并发/失败策略、35项合成观察及剩余出口](analysis/'+BASE+'/remote-connection-state-summary.md)\n').encode()
snapshots={PREFIX+'reader-before/'+n:b for n,b in before.items()}
snapshots[PREFIX+'reader-before/README.md']=readme_before
for name,b in snapshots.items():
    path=OUT/name;assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);path.chmod(0o444)
for name,b in changes.items():
    path=OUT/name;assert path.read_bytes()==before[name]
    temporary=path.with_name('.remote-connection-state-'+path.name);assert not temporary.exists()
    temporary.write_bytes(b);temporary.chmod(path.stat().st_mode&0o777);temporary.replace(path)
assert (ROOT/'README.md').read_bytes()==readme_before
temporary=ROOT/'.remote-connection-state-README.md';assert not temporary.exists()
temporary.write_bytes(readme);temporary.chmod((ROOT/'README.md').stat().st_mode&0o777);temporary.replace(ROOT/'README.md')
print(json.dumps({'status':'published-and-integrated','companionIndices':len(patch),
                  'oldStateKeysPreserved':len(old),'newStateKeys':1,'selectedArtifactsBeforeOwnCapture':len(artifacts),
                  'snapshots':[{'path':n,**pin(b)} for n,b in snapshots.items()],
                  'outputs':{n:pin(b) for n,b in changes.items()},'modelSubmissionsAdded':0,'fullAnalysisCompleted':False}))
