"""Publish bounded settings access families; preserve all prior feature and reader snapshots."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
WORK=ROOT/'.analysis-local/settings-mode-boundary-work'
AUTHOR=WORK/'author-02'
PREFIX='raw/settings-mode-boundary/'
def pin(b): return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def encode(x): return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
x=json.loads((AUTHOR/'settings-mode-boundary-contracts.json').read_bytes())
v=json.loads((WORK/'verification-01.json').read_bytes())
assert v['status']=='passed' and v['uniqueSourceSpansChecked']==367
assert len(x['facts'])==25 and len(x['selectedUnits'])==80 and len(x['settingsSectionReviews'])==53
stages=['analyze-01','trace-01','access-01','policy-01','visibility-01','factors-01','visibility-02',
        'curate-01','curate-02','verify-author-01']
for stage in stages:
    receipt=json.loads((WORK/'attempts'/stage/'receipt.json').read_bytes())
    assert receipt['exitCode']==0 and receipt['sourcesUnchanged']
planned={}
copies=[]
def copy(relative,path,kind='metadata_only'):
    b=path.read_bytes()
    destination=PREFIX+relative
    assert destination not in planned
    planned[destination]=b
    copies.append({'original':str(path),'outputPath':destination,**pin(b),'kind':kind})
names=['settings-mode-boundary-contracts.json','settings-mode-boundary-scenarios.json']
for name in names:
    copy('author/'+name,AUTHOR/name)
    planned[name]=(AUTHOR/name).read_bytes()
    copy('history/author-01/'+name,WORK/'author-01'/name)
for number in range(1,8):
    p=WORK/f'source-{number:02}'
    for file in sorted(p.iterdir()):
        assert file.suffix in ['.json','.txt']
        copy('analysis/'+p.name+'/'+file.name,file,
             'selected_application_source_or_discarded_candidate' if file.suffix=='.txt' else 'analysis_metadata')
copy('author/verification.json',WORK/'verification-01.json')
for stage in stages:
    for file in sorted((WORK/'attempts'/stage).iterdir()):
        copy('attempts/'+stage+'/'+file.name,file,
             'analysis_tool_source' if file.suffix in ['.py','.mjs'] else 'execution_metadata')
records=[]
for f in x['facts']:
    r=f['sourceReferences'][0]
    records.append({'id':f['id'],'baselineId':BASE,'claim':f['claim'],'sourcePath':r['sourcePath'],
      'sourceHash':r['sourceHash'],'locator':{'kind':'byte-range',**r['byteRange']},'spanHash':r['spanHash'],
      'sourceReferences':f['sourceReferences'],'method':f['method'],'confidence':f['confidence'],
      'verificationStatus':f['verificationStatus'],'qualification':f['qualification'],
      'mode':'unknown','newGlobalEvidenceRecord':False,'actualControlExecuted':False})
planned['settings-mode-boundary-evidence.jsonl']=('\n'.join(json.dumps(r,ensure_ascii=False) for r in records)+'\n').encode()
summary='''# 设置分类、访问资格与产品模式边界

本批把设置分类接到实际访问状态定义，确认它们不能直接作为删除ChatGPT功能的清单。见[逐项来源合同](settings-mode-boundary-contracts.json)、[25条限定证据](settings-mode-boundary-evidence.jsonl)、[12条待执行规格](settings-mode-boundary-scenarios.json)及[来源与执行记录](settings-mode-boundary-provenance.json)。本批没有运行目标函数、启动客户端、修改设置或提交模型任务。

| 分类标签 | 分类项数 | 所选源码中的访问条件 |
| --- | ---: | --- |
| chatGpt | 14 | DG.status为allowed；DG取调试覆盖或TTn，TTn检查surface、认证来源、账户匹配和plan |
| chatGptOrCodex | 4 | chatGpt或codex选择器为true |
| codex | 7 | _q.status为allowed；组合local与Work云端／本地状态 |
| codexOrWorkLocal | 9 | JAn.status为allowed；组合local与Work本地状态 |
| codexLocal | 6 | pq.status为allowed；调试覆盖或fq.local |

Ta共40个分类项；Tt有53个命名可见性分支，另13分支无Ta分类。53项与旧settings registry逐范围关联，并保留git-settings等fall-through到实际return分支的关系。它们是设置条件的有限清单，不能替代完整功能分母；每项仍为mode unknown、排除false、featureId未分配。

local、voice、workCloud、workLocal由不同规则生成。GK先处理surface和认证加载；非chatgpt/chatgptAuthTokens认证的所选路径返回allowed/accountId:null，ChatGPT认证继续检查账户、plan与workspace开关。FAn再对Work云端、本地copilot与voice施加不同unsupported-auth规则。源码返回allowed不证明真实客户端或后台服务已经授权。认证来源、访问资格、主机能力和home composer的chat/work偏好须分开记录。

LAn按首个allowed、loading、第一项error、第二项error、第一实参的次序合并，不能用简单mode标签替代。pq、mq、hq、DG还受调试覆盖和gate影响，实际provider、输入订阅及gate值未观察。设置hook的第二参数默认true；false时仅Ca的12个slug继续处理，本批未把该参数的全部调用点接上，不能猜测它是产品模式。

分类条件与逐页predicate相交；无分类时只跳过这一层分类过滤，仍执行逐页条件。pending与error有各自处理，error没有简单乘上分类条件。可见列表、导航列表、选中项fallback与route内容渲染分别受控，不应在恢复时合并成一个菜单开关。

computer-use归入codexOrWorkLocal，再叠加主机能力及加载状态。本批只闭合设置列表的访问条件；页面内部、Messages直接子路由、手机setup、安装后步骤和本地服务仍按[CUA消费者合同](cua-settings-consumer-summary.md)分别判断。14个chatGpt分类也不等于14个可删除功能；后续还需核对实际调用方及共享依赖。

拟恢复源码的职责边界是：账户与workspace访问状态、host capability、设置目录／可见性、home composer偏好及各页面application facade。状态保留loading/error/denied原因和组合顺序；第三方state/query实现用依赖引入。本批提出职责分离，未还原原作者目录，未生成客户端工程，也未确定这些导入的完整第三方身份。

本批包含23条源码事实和2条作者推断，80个规范代码单位、140个词法位置和5个按模块身份连接的导入导出。7条数据解析命令共解析8个完整Program，涉及2个唯一文件；其中source-05虽命令成功退出，但漏读TemplateLiteral值，其派生表被拒绝，source-07修正后纳入规范结果。另一个初选Trt实际是图标，vr来自initial的U_t，已从分类证据排除；原候选保留供审计。作者第二稿为53项补旧证据ID及fall-through关系，未改变25条事实。所有版本、解析器元数据、工具、stdout/stderr和receipt保留；没有新增REA或独立语义审查。

作者核对2份冻结源码的367个唯一范围、731处坐标，含UTF-16与UTF-8位置，并核对已保存输入和导入模块身份；这些检查支持来源可追踪，不替代真实行为观察。12条规格未执行，也未并入原160条feature规格。当前37功能、40用户操作／5机制／26队列、967未映射旧入口及337 deferred保持；没有新模式分类或确认排除，完整分析仍未完成。

下一步追设置hook的实际调用参数、访问输入发布者和各候选页面的共享依赖，再决定保留范围；不能仅靠分类名删除页面。停止／重启的既有观察仍为interrupted，未证明续跑；已批准模型样例组已用2／2、剩余0。本批不增加模型或系统设置操作授权。
'''
planned['settings-mode-boundary-summary.md']=summary.encode()
index={'schemaVersion':1,'baselineId':BASE,'kind':'bounded-settings-access-family-source-contracts',
 'publishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exactCopies':copies,
 'derived':[{'path':n,**pin(planned[n])} for n in names+['settings-mode-boundary-evidence.jsonl','settings-mode-boundary-summary.md']],
 'sourceFacts':23,'inferredFacts':2,'selectedSourceUnits':80,'programLexicalJoins':140,
 'qualifiedImportExportUses':5,'settingsCases':53,'familyProperties':40,'unclassifiedFamilyCases':13,
 'unexecutedScenarios':12,'newOriginalProgramParses':8,'canonicalProgramParses':7,'rejectedDerivedMetadataParses':1,
 'distinctParsedSourcePrograms':2,'analysisCommands':7,'sourceProgramsByteChecked':2,
 'uniqueSourceSpansChecked':367,'sourceCoordinateOccurrencesChecked':731,
 'newFeatureDefinitions':0,'newModeAssignments':0,'newConfirmedExclusions':0,'globalRecordsAdded':0,
 'originalClientRunsAdded':0,'modelSubmissionsAdded':0,'runtimeRunsAdded':0,'newReaRuns':0,
 'actualSettingsMutationsAdded':0,'targetCodeExecuted':False,'thirdPartyImplementationsPublished':False,
 'independentSemanticPeerReviewAdded':False,'featureDenominatorEstablished':False,'fullAnalysisCompleted':False}
planned['settings-mode-boundary-provenance.json']=encode(index)
readers=['report.md','analysis-state.json','implementation-plan.md','gaps.md','behavior-checks.md']
before={n:(OUT/n).read_bytes() for n in readers}
old=json.loads(before['analysis-state.json'])
assert len(old)==93 and 'settingsModeBoundary' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining']==0
for name in planned: assert not (OUT/name).exists()
for name,b in planned.items():
    path=OUT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b)
    path.chmod(0o444)
patch,_,artifacts=build_context(OUT,BASE)
assert len(patch)==len(PROFILES)==28
assert all(old[k]==value for k,value in patch.items() if k!='settingsModeBoundary')
state={**old,'settingsModeBoundary':patch['settingsModeBoundary']}
assert all(state[k]==value for k,value in old.items())
note=next(p[4] for p in PROFILES if p[0]=='settingsModeBoundary')
marker='[完成标准审计](criteria-audit.md)'
report=before['report.md'].decode()
assert report.count(marker)==1
changes={'analysis-state.json':encode(state),
         'report.md':report.replace(marker,note+'\n\n'+marker).encode()}
extra={
 'implementation-plan.md':'\n\n[设置分类与访问资格](settings-mode-boundary-summary.md)支持将account/workspace access、host capability、设置可见性与home composer偏好分责。40分类项接53分支；分类为访问状态选择器，不能凭chatGpt标签删除模块。保留LAn合并顺序、pending/error及导航／route的区别；实际调用参数、发布者与依赖闭合后再决定源码模块范围。\n',
 'gaps.md':'\n\n[设置分类边界](settings-mode-boundary-summary.md)补23源码事实／2推断、80单位、53分支与40分类项；14个chatGpt分类尚不满足专用功能排除条件。已闭合所选access计算，实际输入发布者、hook调用参数、gate值及共享依赖仍未知。12规格未执行；37功能／26队列／160规格保持，完整分母未知、排除0。\n',
 'behavior-checks.md':'\n\n[设置访问12条待执行规格](settings-mode-boundary-scenarios.json)列出access合并顺序、认证来源、workspace加载／错误、调试覆盖、精简列表、fallback及computer-use能力条件。全部未执行、无feature ID，未计入原160规格；没有新目标函数运行、客户端运行、设置操作或模型任务。\n'}
for name,b in extra.items(): changes[name]=before[name]+b.encode()
readme_before=(ROOT/'README.md').read_bytes()
readme=readme_before+('\n- [设置分类与访问资格：40分类项、53分支及模式边界](analysis/'+BASE+'/settings-mode-boundary-summary.md)\n').encode()
snapshots={PREFIX+'reader-before/'+n:b for n,b in before.items()}
snapshots[PREFIX+'reader-before/README.md']=readme_before
for name,b in snapshots.items():
    path=OUT/name
    assert not path.exists()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b)
    path.chmod(0o444)
for name,b in changes.items():
    path=OUT/name
    assert path.read_bytes()==before[name]
    temp=path.with_name('.settings-mode-boundary-'+path.name)
    assert not temp.exists()
    temp.write_bytes(b)
    temp.chmod(path.stat().st_mode&0o777)
    temp.replace(path)
assert (ROOT/'README.md').read_bytes()==readme_before
temp=ROOT/'.settings-mode-boundary-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT/'README.md').stat().st_mode&0o777)
temp.replace(ROOT/'README.md')
print(json.dumps({'status':'published-and-integrated','companionIndices':len(patch),
 'oldStateKeysPreserved':len(old),'newStateKeys':1,'selectedArtifactsBeforeOwnCapture':len(artifacts),
 'snapshots':[{'path':n,**pin(b)} for n,b in snapshots.items()],
 'outputs':{n:pin(b) for n,b in changes.items()},'modelSubmissionsAdded':0,'fullAnalysisCompleted':False}))
