"""Publish a bounded runtime surface decision without changing product scope."""
from collections import Counter
from datetime import datetime, timezone
import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
WORK=ROOT/'.analysis-local/runtime-surface-disposition-work'


def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def pin(path):return {'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


NOTES={
 'electron.app.beginNativeMenuTracking':('native-menu','原生菜单menu-open事件调用begin；menu-close及destroy路径调用end。需保留原生菜单生命周期，公开菜单popup存在不证明等价。'),
 'electron.app.endNativeMenuTracking':('native-menu','menu-close及status-item销毁均调用end；本地方法未检查该能力是否存在。'),
 'electron.app.collectMeasurements':('measurements','第一方包装直接返回运行时结果；另一个音频直方图消费者处理ready、计数不连续及unsupported，异常转unavailable。不能以公开进程metrics替换直方图结果。'),
 'electron.app.configureMeasurementCollection':('measurements','包装直接调用；音频配置使用具名histogram，异常可转unavailable。完整数据来源与保留消费者仍待确定。'),
 'electron.app.isRuntimeFeatureEnabled':('runtime-feature-policy','仅吞掉message以Unsupported Owl feature:开头的Error并返回false；其他异常继续抛出，缺少方法的TypeError不在该回退条件内。'),
 'electron.app.setDebugChromePagesEnabled':('runtime-feature-policy','设置写入、设置副作用及启动均调用；前两者把true与构建flavor的allowDebugMenu组合。启动的完整owner保留，不能将全部调用按debug名称排除。'),
 'electron.app.setLegacyChromePolicyFallbackEnabled':('runtime-feature-policy','启用路径限定Windows、非空且一致的认证accountId及能力predicate；清理路径删除状态并在Windows及predicate成立时禁用。predicate和原生策略的实际效果未关闭。'),
 'electron.app.setRuntimeFeatures':('runtime-feature-policy','仅合并At允许键中的boolean，调用成功后替换e$；reset传空对象。允许键来源、消费者和每项原生效果仍需定位。'),
 'electron.app.showTaskManager':('diagnostics','Help菜单回调调用真实task manager；既有bootstrap guard和局部菜单条件的结论继续有效。公开getAppMetrics只提供数据原语。'),
 'electron.BrowserWindow.isAlwaysOnTopSupported':('window-capabilities','第一方修改操作在能力不支持时返回false；发布的chrome状态在不支持时为null。不能用无条件true替代检测。'),
 'electron.BrowserWindow.isInputShapeSupported':('window-capabilities','保存的完整调用为顶层能力检测；该记录没有完整封闭owner，功能消费者及平台条件仍待补。'),
 'electron.BrowserWindow.isSystemBackdropSupported':('window-capabilities','Windows且gpu_compositing非enabled时先返回false，其余情况调用运行时能力检测。'),
 'electron.BrowserWindow#instance.setHistorySwipeNavigationState':('window-capabilities','只对已登记primary窗口保存状态，并在darwin调用运行时方法；传入overlayBounds和overlayColor的空值转undefined。'),
 'electron.Notification.getPermissionStatus':('notification-authorization','authorization不可用时返回null；granted/denied/not-determined映射enabled/disabled/not-determined，其余null。运行时缺少方法时未见该方法内catch。'),
 'electron.screen.isCursorScreenPointSupported':('cursor-capability','静态create只有检测为true时构造controller；公开坐标getter存在不能证明全平台能力条件。'),
 'electron.Session#instance.setPermissionPromptHandler':('browser-permissions','app分区以permissionHandling:browser创建，注册prompt委托，同时request/check默认拒绝；还注册通知、下载与导航网络策略。公开request handler不可直接当同一prompt协议。'),
 'electron.systemPreferences.getFontFamilies':('font-enumeration','第一方getter直接调用运行时字体枚举，没有在该方法内定义缺失回退或替代数据源。'),
}


if __name__=='__main__':
    state_path=OUT/'analysis-state.json'
    state=read(state_path)
    before=copy.deepcopy(state)
    write(WORK/'state-before.json',before)
    comparison=read(WORK/'surface-comparison.json')
    source=read(WORK/'selected-source.json')
    contracts=read(OUT/'runtime-api-contracts.json')
    calls={x['id']:x for x in contracts['callSites']}
    evidence={x['id']:x for x in map(json.loads,(OUT/'runtime-api-evidence.jsonl').read_text().splitlines())}
    missing=[x for x in comparison['rows'] if not x['publicTypes']['found']]
    assert len(missing)==17 and set(NOTES)=={x['canonicalApi']for x in missing}
    observation=read(WORK/'probe-01/observation.json')
    receipt=read(WORK/'probe-01/receipt.json')
    assert observation['complete'] and len(observation['observations'])==17
    assert {x['type']for x in observation['observations']}=={'undefined'}
    assert all(x['type']=='function' for x in observation['controls'])
    assert receipt['timedOut'] and receipt['exitCode']==-9
    assert receipt['ownedProcessCheck']=={'exitCode':0,'matchingProcesses':[]}
    published=OUT/'raw/runtime-surface-disposition'
    published.mkdir(exist_ok=False)
    for name in ['surface-comparison.json','selected-source.json']:
        shutil.copyfile(WORK/name,published/name)
    shutil.copytree(WORK/'selected-firstparty',published/'selected-firstparty')
    # Public third-party descriptions remain analysis-only. The publication pins them.
    for name in ['fetch_runtime_surface_inputs.py','compare_runtime_surface.cjs','probe_runtime_surface.cjs','run_runtime_surface_probe.py','publish_runtime_surface.py']:
        shutil.copyfile(ROOT/'scripts/analysis'/name,published/name)
    shutil.copytree(WORK/'probe-01',published/'probe-01',ignore=shutil.ignore_patterns('profile','tmp'))
    shutil.copyfile(WORK/'acquisition.json',published/'acquisition-attempt-01.json')
    shutil.copyfile(WORK/'attempt-02/acquisition.json',published/'acquisition-attempt-02.json')
    shutil.copytree(WORK/'comparison-attempt-01',published/'comparison-attempt-01')
    facts=[]
    for index,row in enumerate(missing,1):
        call=calls[row['callSiteIds'][0]];ev=evidence[call['evidenceId']]
        group,note=NOTES[row['canonicalApi']]
        row['dispositionGroup']=group
        row['localConsumerConstraint']=note
        row['runtimeObservation']={'path':'raw/runtime-surface-disposition/probe-01/observation.json','pointer':f'/observations/{index-1}','type':'undefined','processOutcome':'observation-produced; shutdown-timeout; supervisor-cleanup-verified'}
        row['handlingDecision']='保留第一方调用职责；由独立运行时或有来源的适配实现提供能力。该方法名不得直接标为普通Electron已支持，也不按名称删除。'
        row['mode']='unknown; retained pending proven ChatGPT-only exclusion'
        facts.append({'id':f'RSDF-{index:02d}','baselineId':BASE,
          'claim':f'{row["canonicalApi"]}在固定Electron 42.3.0两份公开描述中未声明，且自有实例读数为undefined；{note}',
          'sourcePath':ev['sourcePath'],'sourceHash':ev['sourceHash'],'locator':ev['locator'],
          'method':'saved-full-program-source-contract + fixed-public-description-AST/JSON + owned-runtime-property-observation',
          'confidence':'confirmed','verificationStatus':'bounded-static-and-property-presence-confirmed; replacement-behavior-unverified',
          'sourceEvidenceIds':row['evidenceIds'],'callSiteIds':row['callSiteIds'],
          'publicTypeProof':row['publicTypes'],'publicJsonProof':row['publicJson'],
          'runtimeObservation':row['runtimeObservation'],
          'qualification':'Runtime property lookup only. No missing method was invoked; original Owl behavior and substitute implementations were not tested.'})
    # Assign the reviewed row additions to the published comparison.
    missing_by_id={x['id']:x for x in missing}
    for i,row in enumerate(comparison['rows']):
        if row['id']in missing_by_id:comparison['rows'][i]=missing_by_id[row['id']]
    write(published/'surface-comparison.json',comparison)
    original_pins=[pin(OUT/name)for name in ['runtime-api-contracts.json','runtime-api-evidence.jsonl','runtime-capability-decisions.json','browser-ownership-contracts.json','browser-clone-route-qualification.json','public-history-duplicate-comparison.json','native-browser-settings-comparison.json','public-runtime-comparison.json','runtime-distribution.json','feature-scope-v25.json','restoration-coverage-v16.json']]
    raw_pins=[pin(p)for p in sorted(published.rglob('*')) if p.is_file()]
    product_counts=read(OUT/'restoration-coverage-v16.json')['counts']
    result={'schemaVersion':1,'baselineId':BASE,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
      'scope':'Reused 10-file resolved runtime paths; fixed public Electron 42.3.0 descriptions and one owned property probe. Not whole-app capability or client acceptance.',
      'inputPins':original_pins+comparison['inputs'][:5], 'rawPins':raw_pins,
      'comparison':{'path':'raw/runtime-surface-disposition/surface-comparison.json','pointer':'/rows'},
      'facts':facts,
      'counts':{**comparison['counts'],'boundedCustomDescriptionGroups':len(Counter(x['dispositionGroup']for x in missing)),
        'missingDescriptionCallSites':sum(x['callSiteCount']for x in missing),'selectedFirstPartyUnits':len(source['selectedUnits']),
        'ownedSurfacePropertyObservations':17,'positivePropertyControls':6,'publicRuntimeLaunchAttempts':1,
        'cleanlyExitedProbeRuns':0,'observationProducedBeforeForcedCleanup':1,
        'newOriginalProgramParses':0,'newReaRuns':0,'modelSubmissionsAdded':0,'originalClientRunsAdded':0,
        'productScenarioPassesAdded':0,'featureDefinitionsAdded':0,'modeClassificationsChanged':0,'clientImplementationAdded':0},
      'currentProductScope':product_counts,
      'reconciledDecisions':[
        {'id':'RSD-01','decision':'普通Electron 42.3.0不能直接执行已登记的Owl能力调用；公开声明中的212条保留为公开接口候选，17条须独立处置。','confidence':'confirmed','limitation':'No argument, callback, event, platform or behavioral compatibility implied.'},
        {'id':'RSD-02','decision':'第一方适配按菜单、测量、运行时策略、诊断、窗口、通知授权、鼠标能力、浏览器权限和字体枚举九组能力分界。运行时实现由独立依赖提供，不导出第三方实现。','confidence':'inferred','limitation':'Maintenance responsibility proposal; no substitute selected, implemented or proven.'},
        {'id':'RSD-03','decision':'浏览器will-attach及did-attach的接收身份、重复接收拒绝、generation检查与清理顺序已有BA-04至BA-08静态证据，不再把这部分列为完全未知。','confidence':'confirmed','evidence':['browser-ownership-contracts.json#/facts/3','browser-ownership-contracts.json#/facts/4','browser-ownership-contracts.json#/facts/7'],'limitation':'Native lease consumption, transfer/clone effects and whole lifecycle integration remain unverified.'},
        {'id':'RSD-04','decision':'live-history复制的公开导航原语及当前表单差异复用既有对照；不重复发起同一探针，也不把公开JS堆差异误写为原Owl保证。','confidence':'confirmed','evidence':['public-history-duplicate-comparison.json','browser-clone-route-qualification.json']},
        {'id':'RSD-05','decision':'独立Owl来源、Node网络/IPC执行、更新原生provider、adoption/clone及特权浏览器设置属于额外边界，17条不是全部私有能力分母。','confidence':'unresolved','evidence':['runtime-distribution.json','public-runtime-comparison.json','native-browser-settings-comparison.json','runtime-capability-decisions.json']}
      ],
      'failuresPreserved':[
        {'kind':'anonymous-source-acquisition','attempt':1,'outcome':'DNS failure; second unsandboxed anonymous acquisition verified both published digests'},
        {'kind':'comparison-tool-review','attempt':1,'outcome':'Four Dock union traversals falsely appeared absent; corrected nullable-property resolution. Raw attempt retained; not a runtime failure.'},
        {'kind':'owned-public-runtime-probe','attempt':1,'outcome':'All 17 readings and 6 controls written, hidden owned window destroyed; quit did not finish within deadline. Supervisor terminated own process group; no owned processes remain. Not counted as clean probe success.'}
      ],
      'nextAction':{'issueId':'SD-02','fixedInput':'Saved main Program contracts and complete function selections; do not repeat public API presence or already established attach receivers.',
        'question':'What are the allowed runtime feature keys, legacy-policy capability predicate and retained consumers, and which effects require a native/runtime provider?',
        'closure':'Bind At/e$/n$ to their original declarations and callers, enumerate exact feature keys and reset/unsupported conditions, and assign each effect to an evidenced source/provider or an explicit unresolved native boundary. Do not generate more feature definitions for the same capability.',
        'authorization':'Offline frozen-source work only; model submissions remaining 0.'},
      'fullRuntimeRouteSelected':False,'independentRuntimeBuildProven':False,'fullAnalysisCompleted':False,'clientImplementationStarted':False,
      'limits':comparison['limits']+['Property observations survive as bounded evidence despite process shutdown failure; no graceful-exit or product pass is claimed.',
        'All 17 absent entries are in the saved main Program. Dynamic/unknown receivers can hide other private capabilities, including already known clone/adoption calls.',
        'Public descriptor version and received digests are fixed; no latest-runtime or universal cross-version absence claim.']}
    write(OUT/'runtime-surface-disposition.json',result)
    (OUT/'runtime-surface-disposition-evidence.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in facts))
    with (OUT/'runtime-surface-disposition.csv').open('w',newline='')as stream:
        writer=csv.writer(stream);writer.writerow(['id','canonicalApi','publicDescriptionStatus','calls','dispositionGroup','consumerConstraint','runtimePropertyType','mode','replacementVerified'])
        for row in missing:writer.writerow([row['id'],row['canonicalApi'],row['status'],row['callSiteCount'],row['dispositionGroup'],row['localConsumerConstraint'],'undefined',row['mode'],False])
    table='\n'.join(f'| `{row["canonicalApi"].removeprefix("electron.")}` | {row["dispositionGroup"]} | {row["callSiteCount"]} |'for row in missing)
    (OUT/'runtime-surface-disposition.md').write_text(f'''# 固定公开运行时的接口差异与第一方职责

对原有10文件范围的229条已解析API路径、1242个调用位置核对固定Electron 42.3.0的[官方发布描述](https://github.com/electron/electron/releases/expanded_assets/v42.3.0)：189条同时有API JSON和类型声明，23条仅有类型声明，17条在两者中均未声明。三条`.bind`路径对应6处JavaScript绑定调用，按底层函数核对。该比较不证明参数、事件、平台或行为兼容。

自有公开运行时探针读到17条均为`undefined`，6条公开正例均为函数；没有调用缺失方法。隐藏窗口已销毁，但app.quit未在期限内完成，监督器最终终止了自有进程组，进程检查无残留。读数作为有限证据保留，完整成功运行数为0；不重试掩盖退出问题。

| 固定描述中缺少的路径 | 第一方能力边界 | 已保存调用数 |
| --- | --- | ---: |
{table}

[逐项调用约束和证据](runtime-surface-disposition.json)覆盖24个精确第一方源码单元、25个上述调用。测量不是进程metrics，字体getter没有局部缺失回退；不支持Owl feature的特定异常可返回false，但缺失方法的TypeError不自动进入该分支。浏览器prompt handler还与默认拒绝、通知、下载和导航策略共同配置，不能仅替换方法名。

当前处理决定：第一方源码维护九组能力接口及业务状态，运行时或有来源的独立实现提供底层能力。普通Electron直接替换路线仍被排除；带第一方适配的路线继续保留候选资格。Owl独立分发/源码尚未取得资格，完整运行时路线未选定。

旧决策中的浏览器接收方未知已由[所有权合同](browser-ownership-contracts.json)BA-04至BA-08部分关闭：重复接收、路由、generation和清理顺序已有静态定位；实际native lease消费及转移/clone仍未知。既有[公开历史对照](public-history-duplicate-comparison.md)继续使用，不重复验证。

17条不是全部私有能力清单。4293个名称候选、34个解析预算触顶表达式仍在未解析范围；原生更新provider、Node网络/IPC、adoption/clone和特权浏览器设置另有已登记边界。公开描述及类型文件只在分析临时目录保存，发布物不包含第三方实现。

下一项定向分析限定为runtime feature允许键、reset和unsupported条件、legacy-policy能力predicate及保留消费者，定位`At`、`e$`和`n$`，再确定需要哪些native provider。功能仍为373项、48任务组、1216条未执行规格；本批新增模型提交、原客户端运行和产品验收通过均为0，完整分析尚未完成。
''')
    overlay={'result':pin(OUT/'runtime-surface-disposition.json'),'summary':pin(OUT/'runtime-surface-disposition.md'),
      'csv':pin(OUT/'runtime-surface-disposition.csv'),'evidence':pin(OUT/'runtime-surface-disposition-evidence.jsonl'),
      'counts':result['counts'],'fullRuntimeRouteSelected':False,'fullAnalysisCompleted':False}
    # State pins use output-relative paths, preserving existing state conventions.
    for key in ['result','summary','csv','evidence']:
        overlay[key]['path']=str(Path(overlay[key]['path']).relative_to(OUT.relative_to(ROOT)))
    state['runtimeSurfaceDisposition']=overlay
    state['runtimeCapabilityDecisions']['currentSurfaceOverlay']=copy.deepcopy(overlay)
    state['stageDecisions']['runtimeSurfaceOverlay']=copy.deepcopy(overlay)
    state['stageDecisions']['nextAction']=result['nextAction']
    state['updatedAtUtc']=result['recordedAtUtc']
    write(state_path,state)
    paragraph='[固定运行时接口差异](runtime-surface-disposition.md)核对229条已解析路径：212条有公开声明，17条在固定描述中缺少且自有实例读为undefined；6个公开正例存在。读数完成后退出超时，已终止且无残留，不计完整运行成功。浏览器接收方已有静态证据已同步，完整替代路线未选定；下一项限定为runtime feature键、策略predicate及实际provider。\n\n'
    for name in ['report.md','gaps.md']:
        p=OUT/name;shutil.copyfile(p,WORK/(name+'.before'));text=p.read_text();head,rest=text.split('\n',1);p.write_text(head+'\n\n'+paragraph+rest.lstrip('\n'))
    for p in [OUT/'runtime-surface-disposition.json',OUT/'runtime-surface-disposition.md',OUT/'runtime-surface-disposition.csv',OUT/'runtime-surface-disposition-evidence.jsonl',*published.rglob('*')]:
        if p.is_file():p.chmod(0o444)
    print(json.dumps(result['counts'],ensure_ascii=False))
