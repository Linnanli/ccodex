"""Publish completed owned scenario and four selected receiver ranges, then integrate readers."""
import datetime
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT=Path(__file__).resolve().parents[2]
BASELINE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASELINE
WORK=ROOT/'.analysis-local/behavior-interventions-work'
NATIVE=ROOT/'.analysis-local/mode-persistence-receiver-work/selected-source-20261023'
def pin(b):
    return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def encode(v):
    return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def load(name):
    return json.loads((WORK/name).read_bytes())
assert sorted(p.name for p in WORK.glob('submission-*.json'))==['submission-owned-running-cancel-02.json','submission-owned-running-stop-restart-03.json']
stopped=load('owned-running-stop-restart-03-attempt-05.json')
observed=load('stop-restart-observation-01.json')
launch=load('resume-20261023-03/result.json')
cleanup=load('resume-20261023-03/cleanup.json')
registration=load('project-recovery-resolution.json')
assert stopped['status']=='stopped-awaiting-approved-restart' and stopped['shutdownVerified']
assert stopped['modelSubmissions']==1 and stopped['intervention']['signals']==1
assert stopped['beforeIntervention']['status']=='inProgress' and stopped['beforeIntervention']['cwdMatches']
assert observed['identity']==stopped['identity'] and observed['actualTerminalStatus']=='interrupted'
assert observed['status']=='same-turn-terminal-observed' and observed['readmeAfter']['unchanged']
assert observed['modelSubmissions']==observed['resumeRpcCalls']==0 and observed['navigationClicks']==1
assert launch['runtimeVerification']['pid']==observed['runtimePid']!=stopped['runtimePid']
assert registration['status']=='ready' and registration['trustClicks']==registration['registrationCallsAdded']==0
assert cleanup['status']=='owned-runtime-cleanup-verified' and cleanup['shutdownVerified']
assert cleanup['scenarioSignals']==cleanup['modelSubmissions']==0
native=json.loads((NATIVE/'contracts.json').read_bytes())
assert len(native['records'])==12 and native['selectedSourceBytes']==1235 and len(native['selectedUnits'])==4
assert native['confidenceCounts']=={'confirmed':11,'inferred':1}
assert native['syntaxReceipt']['exitCode']==0 and native['syntaxReceipt']['targetCodeExecuted'] is False
planned={}
def copies(prefix, selected):
    rows=[]
    for name, source in selected:
        raw=source.read_bytes()
        target=prefix+'/author/'+name
        assert target not in planned
        planned[target]=raw
        rows.append({'original':str(source),'outputPath':target,**pin(raw),'kind':'metadata_only'})
    return rows
behavior_names=[
    'project-recovery-proposal.md','project-recovery-authorization.json','project-registration-20261023.json',
    'project-recovery-result.json','project-recovery-dialog-readonly.json','project-recovery-resolution.json','project-scope-override.json',
    'resume-20261023-02/result.json','owned-running-stop-restart-03-attempt-05.json',
    'submission-owned-running-stop-restart-03.json','resume-20261023-03/result.json',
    'stop-restart-observation-01.json','resume-20261023-03/cleanup.json',
    'attempts/project-recovery-01/receipt.json','attempts/project-recovery-resolve-01/receipt.json',
    'attempts/ui-prepare-resume-02/receipt.json','attempts/stop-05/receipt.json','attempts/restart-observation-01/receipt.json']
behavior_copies=copies('raw/behavior-stop-restart',[(n,WORK/n) for n in behavior_names])
latest={
    'schemaVersion':1,'baselineId':BASELINE,'publishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'authorization':{'groupMaximum':2,'groupConsumed':2,'groupRemaining':0,'newSubmissionsOn20261023':1,
        'setupException':'project-recovery-authorization.json','earlierOneTaskAuthorizationIncluded':False},
    'scenarioId':stopped['scenarioId'],'identity':stopped['identity'],
    'project':{'originalProjectId':load('project-scope-override.json')['originalProjectId'],'currentProjectId':registration['projectId'],
        'sameApprovedDirectory':True,'registrationCalls':1,'trustClicks':0,'registrationRetries':0,
        'initialObserverFailure':load('project-recovery-result.json')['failure'],
        'resolution':'The same original call later fulfilled; root and unique UI identity were checked by read-only observations. No dialog click or second registration.'},
    'preStop':{'uiSampleAtUtc':stopped['beforeIntervention']['atUtc'],'status':'inProgress','samePropsObject':True,
        'cwdMatches':True,'pid':stopped['runtimePid'],'nativeCliDescendants':len(stopped['processBeforeStop']['cli']),
        'row':stopped['ownedRowBeforeStop'],'limits':'UI state immediately before control; not an independent backend task-start event.'},
    'stop':{'atUtc':stopped['intervention']['atUtc'],'signals':1,'signal':'SIGTERM','shutdownVerified':True},
    'restart':{'pid':observed['runtimePid'],'sameApplicationProfilePolicy':True,'nativeCliVerified':True,
        'firstAutomaticRestorationSample':observed['automaticRestoration'],'navigation':observed['navigation'],
        'observedOwnedRow':observed['preNavigationOwnedRows'][0],
        'finalUiSampleAtUtc':observed['finalObservation']['atUtc'],'sameThreadTurn':True,'actualTerminalStatus':'interrupted',
        'itemTypes':[i['type'] for i in observed['finalObservation']['turn']['items']],
        'resumeRpcCalls':0,'newPromptsAfterRestart':0},
    'cleanup':{'verified':True,'atUtc':cleanup['completedAtUtc'],'signals':1,'scope':'Separate cleanup of restarted runtime after terminal observation; not another scenario intervention.'},
    'readmeAfter':observed['readmeAfter'],'outcome':'same-turn-interrupted-observed-after-restart',
    'cancelScenarioOutcome':'not-tested/control-binding-unavailable',
    'limits':['No resumed execution was observed.','No automatic current-page restoration in the first recorded sample; no general restoration policy conclusion.',
              'Same-turn state is observed through bound UI props; independent backend delivery and durable write are not proved.',
              'No file read/tool use was observed in this interrupted turn; unchanged fixture is not a tool audit.',
              'This group is exhausted. No third model task or retry is authorized.'],
    'globalRecordsAdded':0,'fullAnalysisCompleted':False,'thirdPartyImplementationsPublished':False,
}
summary='''# 执行中停止／重启的实际结果

本组2次授权已用2次、余0。第二条按原精确提示提交一次；首条取消仍未测到。[结构化结果](behavior-stop-restart.json)及[来源索引](behavior-stop-restart-provenance.json)保存各次检查。

停止前，同一thread/turn的UI明确为inProgress、cwd匹配；重新核实自有主PID后发送一次SIGTERM，主进程及当时记录的3个CLI子进程退出。之后以同一冻结应用、profile、CODEX_HOME和策略启动新PID，CLI身份复核通过。

重启后首次当前页样本未显示原提示。专用项目内实际侧栏行已从临时client-new-thread标识变为local:加后端UUID；先从该行自身entry.conversationId/cwd确认身份，再定位实际已观察行点击一次。原thread/turn重新出现，状态为interrupted，记录的items只有userMessage。没有新提示、重发、resume RPC或继续按钮操作，没有观察到继续执行。这验证本次中断状态可重新打开，不证明后台自动恢复执行或耐久写入机制。

此前用户明确允许对同一合成目录重新登记，得到新项目ID。登记仅调用一次：初版观察器因额外dialog计数而停下，稍后同一原调用已fulfilled，根目录与实际UI均核实；未点击信任、未重试登记。早先“项目控件缺失／剩余1次”是中间快照，当前预算以本批为准。

README仍匹配原71字节／SHA256；该会话没有独立文件读取审计。完成观察后，自有应用及已记录CLI子进程清理退出已核实。第一条的completed UI与本条interrupted UI分别保存；取消、其他故障恢复、PTY、审批和完整功能仍待分析。
'''
planned['behavior-stop-restart.json']=encode(latest)
planned['behavior-stop-restart-summary.md']=summary.encode()
behavior_index={'schemaVersion':1,'baselineId':BASELINE,'kind':'approved-owned-stop-restart-metadata',
    'metadataOnly':True,'exactCopies':behavior_copies,
    'derived':[{'path':n,**pin(planned[n])} for n in ['behavior-stop-restart.json','behavior-stop-restart-summary.md']],
    'groupModelSubmissionsObserved':2,'remainingModelSubmissions':0,'newModelSubmissionsOn20261023':1,
    'scenarioStopSignals':1,'scenarioRestarts':1,'actualTerminalStatus':'interrupted',
    'deliveryRuntimeRunsAdded':0,'deliveryModelTasksAdded':0,'globalRecordsAdded':0,
    'fullAnalysisCompleted':False,'thirdPartyImplementationsPublished':False}
planned['behavior-stop-restart-provenance.json']=encode(behavior_index)
native_copies=copies('raw/mode-persistence-receiver',[
    ('contracts.json',NATIVE/'contracts.json'),('evidence.jsonl',NATIVE/'evidence.jsonl'),
    ('syntax-receipt.json',NATIVE/'syntax-receipt.json'),
    ('existing-metadata-selection.json',ROOT/'.analysis-local/mode-persistence-receiver-work/existing-metadata-selection.json')])
planned['mode-persistence-receiver.json']=encode(native)
native_summary='''# 主进程persisted-atom接收候选

依据已保存REA/AST坐标，从冻结main读取4个完整范围，共1235字节：2个switch case、sendPersistedAtomState与updatePersistedAtomState。形成11条限定来源事实及1条receiver关联推断，见[合同](mode-persistence-receiver.json)与[来源索引](mode-persistence-receiver-provenance.json)。只作一次Node包装范围语法检查，未执行目标代码；MMe归属与同类方法关联沿用固定旧metadata，没有新增独立词法绑定分析。

更新分支把deleted转换为undefined后连同recordUpdate传入方法；recordUpdate仍可能参与计算，不能把deleted直接等同于最终删除。方法保留unread key／非primary owner门控；pR返回false时仅广播旧值并返回。其他分支用直接值或hR的record更新，旧值为空时才考虑legacyStorageKey回退；最终undefined删除键，其他值定义own configurable/enumerable/writable属性，再调用globalState.set并广播。所选方法内同步set抛错会阻止后续广播；没有await，不推断异步落盘。

同步快照按primary owner、TY及shouldSync条件筛选状态；critical优先级走chunked sender，其余走普通发送。原窗口、sender、存储实例及g.bt频道绑定未闭合。TY/pR/hR、广播实现、Rkc真实caller、gS store/provider、renderer实际送达及耐久后端仍未知；匹配消息type不等于已验证跨进程通信。

建议维护路径apps/desktop/src/main/persistence/persisted-atoms.ts，只承载第一方消息与状态适配，四个完整原范围逐项映射。该路径为inferred提案；globalState、owner/filter和sender应保留依赖接口，不能假设都是localStorage或复制运行时实现。未恢复原目录、未重建客户端，旧全局证据分母和模式排除数保持。
'''
planned['mode-persistence-receiver-summary.md']=native_summary.encode()
native_index={'schemaVersion':1,'baselineId':BASELINE,'kind':'selected-main-receiver-source-metadata',
    'metadataOnly':True,'exactCopies':native_copies,
    'derived':[{'path':n,**pin(planned[n])} for n in ['mode-persistence-receiver.json','mode-persistence-receiver-summary.md']],
    'selectedUnits':4,'selectedSourceBytes':1235,'confidenceCounts':{'confirmed':11,'inferred':1},
    'targetCodeExecuted':False,'modelSubmissionsAdded':0,'globalRecordsAdded':0,
    'fullAnalysisCompleted':False,'thirdPartyImplementationsPublished':False}
planned['mode-persistence-receiver-provenance.json']=encode(native_index)
for n in planned:
    assert not (OUT/n).exists()
for n,raw in planned.items():
    p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(raw);p.chmod(0o444)

# Mutable readers preserve every earlier state value; current budget has an explicit new pointer.
names=['report.md','analysis-state.json','implementation-plan.md','gaps.md','dependency-import-decisions.md','behavior-checks.md']
before={n:(OUT/n).read_bytes() for n in names}
old=json.loads(before['analysis-state.json'])
assert len(old)==83 and old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
patch,_,artifacts=build_context(OUT,BASELINE)
new_keys=['behaviorStopRestartOutcome','modePersistenceReceiver']
assert len(patch)==len(PROFILES)==20
assert all(k not in old for k in new_keys)
assert all(old[k]==v for k,v in patch.items() if k not in new_keys)
state={**old,**{k:patch[k] for k in new_keys},'latestBehaviorAuthorizationState':{
    'path':'behavior-stop-restart.json','groupMaximum':2,'groupConsumed':2,'groupRemaining':0,
    'supersedesForCurrentBudget':'behavior-interventions.json','historicalSnapshotsPreserved':True}}
assert all(state[k]==v for k,v in old.items())
notes='\n\n'.join(p[4] for p in PROFILES if p[0] in new_keys)
report=before['report.md'].decode()
marker='[完成标准审计](criteria-audit.md)';assert report.count(marker)==1
report=report.replace(marker,notes+'\n\n'+marker)
prior_row='| 后续获授权样例 | 本组2次授权已用1次、余1次；同turn稍后UI为completed；2026-10-23新增提交0 | 取消点击0；原合成项目两个精确控件均0，第二条未发送；执行中取消与重启仍未测试 |'
assert report.count(prior_row)==1
report=report.replace(prior_row,'| 后续获授权样例 | 本组2/2已用；停止前同turn UI为inProgress；SIGTERM关闭核实，新PID启动后原turn为interrupted | 首次当前页样本未自动恢复；从实际绑定行重新打开；未观察到继续执行，取消仍未测 |')
report=report.replace('[获授权行为样例进度](behavior-interventions-summary.md)记录本组授权2次已用1次、余1次。','项目恢复前的[行为中间快照](behavior-interventions-summary.md)当时记录本组授权2次已用1次、余1次；当前预算以[最终样例结果](behavior-stop-restart-summary.md)为准。')
changes={'report.md':report.encode(),'analysis-state.json':encode(state)}
supplements={
    'implementation-plan.md':'\n\n[执行中停止／重启结果](behavior-stop-restart-summary.md)观察到同一turn在重启后为interrupted，需经实际侧栏行打开；没有继续执行证明。维护时把临时client行标识与后端thread身份分开持久化／关联，并单独验收当前页恢复、终态重开和任务续跑。\n\n[main persisted-atom候选](mode-persistence-receiver-summary.md)将四原范围接到inferred维护路径main/persistence/persisted-atoms.ts。保留owner/filter、pR否定分支、recordUpdate/legacy回退、delete/属性定义、set再broadcast顺序；存储、广播与运行时接口继续独立调查。它不建立完整原目录或globalState耐久实现。\n',
    'behavior-checks.md':'\n\n## 本组停止／重启的完成结果\n\n[实际结果](behavior-stop-restart-summary.md)更新此前中间快照：2次授权全部使用。第二条同turn在停止前为inProgress，SIGTERM和3个CLI关闭已核实；同profile新PID启动后，点击已实际观察并绑定同thread/cwd的项目行，原turn为interrupted。无新提示、resume RPC或继续操作；未观察到执行恢复。README hash匹配，最后清理退出核实。原先缺失项目经用户明确许可登记一次；原调用稍后完成，未点击信任或重试。取消仍未测试。\n\n[main接收候选](mode-persistence-receiver-summary.md)的4个范围仅作语法检查与限定静态分析，没有执行真实存储、owner过滤、广播、错误或恢复场景。\n',
    'dependency-import-decisions.md':'\n\n[main persisted-atom接收候选](mode-persistence-receiver-summary.md)是第一方控制与适配职责；injected globalState、sender及owner/filter不等同于某个可直接安装的npm包。四选定范围没有恢复第三方实现；耐久后端及其版本来源继续调查。\n',
    'gaps.md':'\n\n[停止／重启完成结果](behavior-stop-restart-summary.md)替代此前预算中间快照：本组2/2已用、余0；同turn UI在重启后为interrupted且可从实际行打开，没有任务续跑证明。首条取消仍未测。项目设置例外已获明确授权，实际一次登记经后续只读核对完成；原控件缺失根因仍未知。\n\n[main接收候选12记录](mode-persistence-receiver-summary.md)接上所选switch与MMe方法的静态候选。继续TY/pR/hR、广播方法、globalState真实实例与耐久后端、Rkc caller/gS provider/store及实际跨进程送达；语法检查不关闭这些缺口。\n',
}
for n,extra in supplements.items():
    changes[n]=before[n]+extra.encode()
readme_before=(ROOT/'README.md').read_bytes()
readme=readme_before.decode().replace('后续两条获授权样例的实际进度]','后续两条样例的中间快照]')
readme+='\n- [执行中停止／重启的完成结果与当前授权预算](analysis/'+BASELINE+'/behavior-stop-restart-summary.md)\n- [主进程persisted-atom接收候选与维护边界](analysis/'+BASELINE+'/mode-persistence-receiver-summary.md)\n'
prefix='raw/completed-scenario-integration'
snapshots={prefix+'/reader-before-'+n:raw for n,raw in before.items()}
snapshots[prefix+'/reader-before-README.md']=readme_before
for n,raw in snapshots.items():
    p=OUT/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(0o444)
for n,raw in changes.items():
    p=OUT/n;assert p.read_bytes()==before[n]
    temp=p.with_name('.completed-scenario-'+p.name);assert not temp.exists()
    temp.write_bytes(raw);temp.chmod(p.stat().st_mode&0o777);temp.replace(p)
temp=ROOT/'.completed-scenario-README.md';assert not temp.exists()
temp.write_text(readme);temp.chmod((ROOT/'README.md').stat().st_mode&0o777);temp.replace(ROOT/'README.md')
print(json.dumps({'status':'published-and-integrated','companionIndices':20,'oldStateKeysPreserved':len(old),
    'oldStateValuesPreserved':True,'newStateKeys':new_keys+['latestBehaviorAuthorizationState'],
    'selectedArtifactsBeforeOwnCapture':len(artifacts),'publishedOutputs':len(planned),
    'snapshots':[{'path':n,**pin(raw)} for n,raw in snapshots.items()],
    'outputs':{n:pin(raw) for n,raw in changes.items()},'groupModelConsumed':2,'groupModelRemaining':0,
    'newModelTasksInPublication':0,'targetCodeRunsInPublication':0,'globalRecordsAdded':0,'fullAnalysisCompleted':False},ensure_ascii=False))
