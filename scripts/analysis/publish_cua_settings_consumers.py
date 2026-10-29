"""Publish bounded CUA settings consumer contracts and append the current reader context."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/cua-settings-consumer-work'
AUTHOR = WORK / 'author-03'
PREFIX = 'raw/cua-settings-consumer/'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


review = json.loads((AUTHOR / 'cua-settings-consumer-contracts.json').read_bytes())
verification = json.loads((WORK / 'verification-01.json').read_bytes())
assert verification['status'] == 'passed' and verification['uniqueSourceSpansChecked'] == 371
assert len(review['facts']) == 32 and len(review['selectedUnits']) == 77 and len(review['operationRelations']) == 14
stages = ['inventory-01','analyze-01','qualify-01','gates-01','query-bindings-01',
          'curate-01','curate-02','curate-03','verify-author-01','verify-author-02']
for stage in stages:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == (1 if stage == 'verify-author-01' else 0) and receipt['sourcesUnchanged']
planned, copies = {}, []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = PREFIX + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


names = ['cua-settings-consumer-contracts.json', 'cua-settings-consumer-scenarios.json']
for name in names:
    copy('author/' + name, AUTHOR / name)
    planned[name] = (AUTHOR / name).read_bytes()
    for version in ['author-01', 'author-02']:
        copy('history/' + version + '/' + name, WORK / version / name)
for relative in ['source-01/inventory.json','source-02/source-contracts.json',
                 'source-context-01/context-contracts.json','source-gates-01/gate-contracts.json',
                 'source-query-01/query-bindings.json']:
    copy('analysis/' + relative, WORK / relative)
for unit in review['selectedUnits']:
    path = Path(unit['rawSourcePath'])
    copy('selected-source/' + unit['unitId'] + '-' + path.name, path, 'selected_first_party_application_source')
copy('author/verification.json', WORK / 'verification-01.json')
for stage in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in {'.py','.mjs'} else 'execution_metadata')
records = []
for f in review['facts']:
    primary = f['sourceReferences'][0]
    records.append({'id':f['id'],'baselineId':BASELINE,'claim':f['claim'],
      'sourcePath':primary['sourcePath'],'sourceHash':primary['sourceHash'],
      'locator':{'kind':'byte-range',**primary['byteRange']},'spanHash':primary['spanHash'],
      'sourceReferences':f['sourceReferences'],'method':f['method'],'confidence':f['confidence'],
      'verificationStatus':f['verificationStatus'],'qualification':f['qualification'],
      'mode':'unknown','newGlobalEvidenceRecord':False,'actualControlExecuted':False})
planned['cua-settings-consumer-evidence.jsonl'] = ('\n'.join(json.dumps(r,ensure_ascii=False) for r in records)+'\n').encode()
summary = '''# 电脑使用设置：实际控件、共用服务与条件边界

本批为原14个电脑使用包装接上限定消费者，形成30条源码事实、2条作者推断、77个完整代码单位、139处原Program词法绑定和44处import/export使用。见[合同与逐操作连接](cua-settings-consumer-contracts.json)、[32条限定证据](cua-settings-consumer-evidence.jsonl)、[20条待执行控件规格](cua-settings-consumer-scenarios.json)及[来源与命令捕获](cua-settings-consumer-provenance.json)。没有启动客户端、执行目标函数、修改系统设置、发送审批决定或提交模型任务。

| 消费者 | 本批接上的操作 | 必须保留的交互差异 |
| --- | --- | --- |
| 应用始终允许列表 | getAppApprovals / removeAppApproval | 挂载refetch、loading/error/empty、bundleIdentifier确认、null抛错、成功清除确认对象 |
| 声音菜单 | getSoundMode / setSoundMode | 三个enum；invalid非null显示缺省，null隐藏；本地mutation options无onError |
| 锁屏使用设置 | getLockedUseState / setLockedUseEnabled | 主视图macOS、availability、locked capability条件；图标缓存保留，null结果隐藏 |
| Messages读取 | getMessagesReadDecisions / setMessagesReadAccessPolicy / setMessagesReadDecision / removeMessagesReadDecision / searchMessagesChats | 全局policy与逐聊天decision分开；三mutation先cancel query；搜索串行、debounce、session与abort边界 |
| Messages发送 | getMessagesSendApprovals / setMessagesSendAllowAllChats / removeMessagesSendApproval | 全局allowAll仅隐藏逐聊天列表；remove没有global send/read mutation的onMutate cancel |
| 手机setup与插件安装后步骤 | 共用locked query及setLockedUseEnabled | 手机先关locked且严格false才关插件；安装flag默认false，非true结果警告后继续所选流程 |

旧目录将9项标为operation，其中含8个写操作和1个搜索；另5个query定义。这不是14个用户功能，也不是9个写操作。本批consumer关系覆盖该有限14项，但没有宣称覆盖整个电脑使用、手机setup、插件安装或浏览器／Office功能。

入口沿用已保存的settings页表第38项，动态import返回ComputerUseSettings；本批导出绑定至Vr，原表项与import字节重新核对。没有凭computer-use标签给旧lexical section候选补身份。Vr的browser及Messages子路由先于主视图返回，因此主视图availability条件不能自动当成直接Messages路由的guard。ei分别处理插件加载、未installed重定向与已installed；Hr的可用性筛选是另一处条件。

能力条件需要分层保存：Messages availability明确要求local、macOS、computer-use availability和gate；locked capability依赖gate、remote visibility及host requirements。Windows额外条件读取authMethod===chatgpt、账户plan与beta setting，这属于认证来源检查，不能直接当成ChatGPT产品模式。页面能力/插件查询使用selectedHostId，而14个本地设置包装没有host参数；旧主进程合同中的平台全局文件、defaults和installer也不因renderer选中host而隔离。

read策略包含askPerChat、allowUnconfiguredChats、allowAllChats；逐聊天决定另为alwaysAllow、ask、alwaysDeny。allowAll隐藏逐聊天控件，所选代码没有在该分支清除保存项。搜索只从ready状态取chats，权限待完成／缺权限／错误／无结果分别显示。UI取消精确query key，服务仍是串行队列且只在出队前后检查signal，不能声称原生查询已取消。

复刻工程可以据此把页面交互、typed application facade/query策略、desktop本地适配和capability条件分开。手机与安装后步骤应复用同一服务边界，保留不同参数、错误提示、pending和null处理；不要把第三方query/cache、React或其他导入实现一起展开。本批只发布选定应用逻辑及声明片段，完整依赖身份/修改清单仍沿既有独立分析，未据本批导入名新增依赖归属结论。

本批运行5条只解析数据的命令，共16次完整Program解析、7个唯一文件；另核对继承的initial表项，合计8个文件371个唯一范围、758处坐标。没有新REA调用；这是既有REA分析的限定AST与字节补充，没有独立语义peer review。初稿把9 operation误称9 mutation，第二稿修正；首轮校验又发现两个query的edge只按导出名筛选，混入另一个模块的同名导出，第三稿加上目标模块身份后通过。三稿与失败校验的完整工具/日志/receipt均保留，当前使用第三稿。

37项有限feature、40用户操作／5机制／26队列、160条功能规格保留原快照。本批14个CUA候选虽已补消费者，仍在粒度／模式／依赖审查队列；新增20条是未分配feature ID的控件规格，不把它们计入原160条功能验收，更没有计为已执行。37模式unknown、confirmed排除0、967旧入口未映射、337 deferred及完整功能分母未知均不变。

后续把这些消费者按用户目标归属，再追mobile返回对象、安装flag的实际入口、mode与transitive dependencies，并在可验证隔离的环境核对query竞态、实际receiver、native权限和重开持久化。本批不授予任何系统设置操作或模型提交权限；已批准的两条模型样例组已用2／2、剩余0，最近的停止／重启结果保持此前的限定。
'''
planned['cua-settings-consumer-summary.md'] = summary.encode()
index = {'schemaVersion':1,'baselineId':BASELINE,'kind':'bounded-cua-settings-consumer-source-contracts',
 'publishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exactCopies':copies,
 'derived':[{'path':n,**pin(planned[n])} for n in names+['cua-settings-consumer-evidence.jsonl','cua-settings-consumer-summary.md']],
 'sourceFacts':30,'inferredFacts':2,'selectedSourceUnits':77,'operationConsumers':14,
 'programLexicalJoins':139,'qualifiedImportExportUses':44,'newOriginalProgramParses':16,'distinctParsedSourcePrograms':7,
 'sourceProgramsByteChecked':8,'uniqueSourceSpansChecked':371,'sourceCoordinateOccurrencesChecked':758,
 'unexecutedControlSpecifications':20,'operationKinds':{'writes':8,'serializedSearches':1,'queryDefinitions':5},
 'originalClientRunsAdded':0,'modelSubmissionsAdded':0,'actualSettingsMutationsAdded':0,'newFeatureDefinitions':0,
 'runtimeRunsAdded':0,'targetCodeExecuted':False,'globalRecordsAdded':0,'newReaRuns':0,
 'newConfirmedExclusions':0,'featureDenominatorEstablished':False,'thirdPartyImplementationsPublished':False,
 'independentSemanticPeerReviewAdded':False,'fullAnalysisCompleted':False}
planned['cua-settings-consumer-provenance.json'] = encode(index)
readers = ['report.md','analysis-state.json','implementation-plan.md','gaps.md','behavior-checks.md']
before = {n:(OUT/n).read_bytes() for n in readers}
old = json.loads(before['analysis-state.json'])
assert len(old)==92 and 'cuaSettingsConsumers' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining']==0
for name in planned:
    assert not (OUT/name).exists()
for name,raw in planned.items():
    path=OUT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch,_,artifacts=build_context(OUT,BASELINE)
assert len(patch)==len(PROFILES)==27
assert all(old[k]==v for k,v in patch.items() if k!='cuaSettingsConsumers')
state={**old,'cuaSettingsConsumers':patch['cuaSettingsConsumers']}
assert all(state[k]==v for k,v in old.items())
note=next(p[4] for p in PROFILES if p[0]=='cuaSettingsConsumers')
marker='[完成标准审计](criteria-audit.md)'
report=before['report.md'].decode()
assert report.count(marker)==1
changes={'report.md':report.replace(marker,note+'\n\n'+marker).encode(),'analysis-state.json':encode(state)}
extras={
 'implementation-plan.md':'\n\n[电脑使用设置消费者合同](cua-settings-consumer-summary.md)接上14个包装的控件/共用服务，建议页面交互、application query/service、desktop本地适配与capability分责。8写／1搜索／5query定义不等于14功能；手机和安装后消费者保留各自pending/error/null语义。当前37功能及26队列保持，模式与完整依赖待闭合。\n',
 'gaps.md':'\n\n[电脑使用设置消费者](cua-settings-consumer-summary.md)补30源码事实／2推断、77单位／139词法关系／44导入导出使用；14包装已有限接消费者，8写／1搜索／5query分开。没有真实设置操作、native取消、receiver或持久化验证。20控件规格单列未执行；37功能／160功能规格／26队列未改，mode/完整分母未知、排除0。\n',
 'behavior-checks.md':'\n\n[电脑使用设置20条待执行控件规格](cua-settings-consumer-scenarios.json)覆盖read/send分离、query取消与并发、sound/locked null、应用移除确认、手机先关locked及安装后warning分支。均无feature ID且未执行，不增加原160条feature验收执行数。没有新目标函数/客户端运行、系统设置变更或模型提交；样例组剩余0。\n',
}
for name,extra in extras.items():
    changes[name]=before[name]+extra.encode()
readme_before=(ROOT/'README.md').read_bytes()
readme=readme_before+('\n- [电脑使用设置：14条消费者连接、条件与20条待执行控件规格](analysis/'+BASELINE+'/cua-settings-consumer-summary.md)\n').encode()
snapshots={PREFIX+'reader-before/'+n:raw for n,raw in before.items()}
snapshots[PREFIX+'reader-before/README.md']=readme_before
for name,raw in snapshots.items():
    path=OUT/name
    assert not path.exists()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name,raw in changes.items():
    path=OUT/name
    assert path.read_bytes()==before[name]
    temp=path.with_name('.cua-settings-consumer-'+path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode&0o777)
    temp.replace(path)
assert (ROOT/'README.md').read_bytes()==readme_before
temp=ROOT/'.cua-settings-consumer-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT/'README.md').stat().st_mode&0o777)
temp.replace(ROOT/'README.md')
print(json.dumps({'status':'published-and-integrated','companionIndices':len(patch),
 'oldStateKeysPreserved':len(old),'newStateKeys':1,'selectedArtifactsBeforeOwnCapture':len(artifacts),
 'snapshots':[{'path':n,**pin(raw)} for n,raw in snapshots.items()],
 'outputs':{n:pin(raw) for n,raw in changes.items()},'modelSubmissionsAdded':0,'fullAnalysisCompleted':False}))
