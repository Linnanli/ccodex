"""Publish the bounded remote status consumer analysis once, preserving existing reader state."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
W=ROOT/'.analysis-local/remote-status-consumer-work'
A=W/'author-01'
PREFIX='raw/remote-status-consumer/'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):return json.loads(p.read_bytes())
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()

c=read(A/'remote-status-consumer-contracts.json')
counts=read(A/'counts.json')
verification=read(W/'verification-01.json')
assert verification['status']=='passed'
assert len(c['selectedUnits'])==70 and len(c['facts'])==20 and len(c['programLexicalJoins'])==958
stages=['analyze-initial-01','analyze-main-01','analyze-shared-01','analyze-injection-01','analyze-state-01','observe-01','verify-inherited-01','curate-01','verify-author-01']
for stage in stages:
    receipt=read(W/'attempts'/stage/'receipt.json')
    assert receipt['exitCode']==0 and receipt['sourcesUnchanged']
readers=['report.md','analysis-state.json','implementation-plan.md','gaps.md','behavior-checks.md']
before={n:(OUT/n).read_bytes() for n in readers}
old=json.loads(before['analysis-state.json'])
assert len(old)==98 and 'remoteStatusConsumer' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining']==0
previous,_,_=build_context(OUT,BASE)
assert len(previous)==32 and all(old[k]==v for k,v in previous.items())
for item in c['inputPins']:
    assert pin((OUT/item['path']).read_bytes())=={k:item[k] for k in ['bytes','sha256']}
planned,copies={},[]
def copy(relative,path,kind='analysis_metadata'):
    b=path.read_bytes();target=PREFIX+relative
    assert target not in planned
    planned[target]=b
    copies.append({'original':str(path),'outputPath':target,**pin(b),'kind':kind})
for name in ['remote-status-consumer-contracts.json','remote-status-consumer-scenarios.json']:
    copy('author/'+name,A/name)
    planned[name]=(A/name).read_bytes()
for name in ['counts.json','summary.md']:
    copy('author/'+name,A/name)
copy('author/verification-01.json',W/'verification-01.json')
copy('observations/observations-01.json',W/'observations-01.json','synthetic_vm_observations')
planned['remote-status-consumer-observations.json']=(W/'observations-01.json').read_bytes()
planned['remote-status-consumer-summary.md']=(A/'summary.md').read_bytes()
for folder in ['source-01','source-02','source-03','source-04','source-05','source-06']:
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
planned['remote-status-consumer-evidence.jsonl']=('\n'.join(json.dumps(x,ensure_ascii=False) for x in records)+'\n').encode()
derived_names=['remote-status-consumer-contracts.json','remote-status-consumer-scenarios.json',
               'remote-status-consumer-observations.json','remote-status-consumer-summary.md','remote-status-consumer-evidence.jsonl']
index={'schemaVersion':1,'baselineId':BASE,'kind':'bounded-remote-status-selector-and-bootstrap-contracts',
       'publishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'exactCopies':copies,'derived':[{'path':n,**pin(planned[n])} for n in derived_names],
       **counts,**c['constraints'],
       'sourceFilesByteChecked':verification['sourceFilesByteChecked'],
       'uniqueSourceSpansChecked':verification['uniqueSourceSpansChecked'],
       'sourceCoordinateOccurrencesChecked':verification['sourceCoordinateOccurrencesChecked']}
planned['remote-status-consumer-provenance.json']=encode(index)
for name in planned:assert not (OUT/name).exists(),name
for name,b in planned.items():
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);path.chmod(0o444)
patch,_,artifacts=build_context(OUT,BASE)
assert len(patch)==len(PROFILES)==33
assert all(old[k]==v for k,v in patch.items() if k!='remoteStatusConsumer')
state={**old,'remoteStatusConsumer':patch['remoteStatusConsumer']}
assert all(state[k]==v for k,v in old.items())
note=next(p[4] for p in PROFILES if p[0]=='remoteStatusConsumer')
marker='[完成标准审计](criteria-audit.md)'
report=before['report.md'].decode();assert report.count(marker)==1
changes={'analysis-state.json':encode(state),'report.md':report.replace(marker,note+'\n\n'+marker).encode()}
additions={
 'implementation-plan.md':'\n\n[连接状态聚合与启动请求](remote-status-consumer-summary.md)将renderer状态族、bootstrap manager生命周期、URI请求适配与main薄端点分责。保留严格快照身份、初始null manager接纳、Fn只写CF标志、progress先写后可能清空及cleanup不等于transport取消。真实React/bridge和后续事件写入继续验收；normalizer来源未明，不生成其实现。\n',
 'gaps.md':'\n\n[状态消费者增量](remote-status-consumer-summary.md)关闭上一批a8a/Zs聚合与所选ERs启动状态方法/host参数/静态端点来源缺口。a8a读本地state$而非轮询，Fn只设置CF标志。18源码事实/2推断、24替身观察；真实provider/transport、后续状态写入者与normalizer包版本仍未知。8集成规格未执行；37功能/26队列/160规格、模式unknown和排除0保持。\n',
 'behavior-checks.md':'\n\n[连接状态24项隔离观察](remote-status-consumer-observations.json)加载21单位4671字节，覆盖本地状态聚合、严格快照、manager变化、cleanup、失败保留和progress先后。React/compiler、scope、normalizer、watch/manager与transport均为替身，query/telemetry副作用单独替代；没有真实hooks、IPC、网络或模型。[8真实集成规格](remote-status-consumer-scenarios.json)未执行，不增加原160规格的执行数。\n',
}
for name,addition in additions.items():changes[name]=before[name]+addition.encode()
readme_before=(ROOT/'README.md').read_bytes()
readme=readme_before+('\n- [连接状态选择器与启动请求：24项隔离观察及真实provider缺口](analysis/'+BASE+'/remote-status-consumer-summary.md)\n').encode()
snapshots={PREFIX+'reader-before/'+n:b for n,b in before.items()}
snapshots[PREFIX+'reader-before/README.md']=readme_before
for name,b in snapshots.items():
    path=OUT/name;assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);path.chmod(0o444)
for name,b in changes.items():
    path=OUT/name;assert path.read_bytes()==before[name]
    temporary=path.with_name('.remote-status-consumer-'+path.name);assert not temporary.exists()
    temporary.write_bytes(b);temporary.chmod(path.stat().st_mode&0o777);temporary.replace(path)
assert (ROOT/'README.md').read_bytes()==readme_before
temporary=ROOT/'.remote-status-consumer-README.md';assert not temporary.exists()
temporary.write_bytes(readme);temporary.chmod((ROOT/'README.md').stat().st_mode&0o777);temporary.replace(ROOT/'README.md')
print(json.dumps({'status':'published-and-integrated','companionIndices':len(patch),
                  'oldStateKeysPreserved':len(old),'newStateKeys':1,'selectedArtifactsBeforeOwnCapture':len(artifacts),
                  'snapshots':[{'path':n,**pin(b)} for n,b in snapshots.items()],
                  'outputs':{n:pin(b) for n,b in changes.items()},'modelSubmissionsAdded':0,'fullAnalysisCompleted':False}))
