"""Publish the bounded resume classification and provider/receiver source joins."""
import copy
import csv
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/resume-provider-resolution-work'
RAW = OUT / 'raw/resume-provider-resolution'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
OP = 'operation:ttc:TTC-OP-thread-resume'


def read(p):
    return json.loads(p.read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    return {'path': str(p.relative_to(OUT)) if p.is_relative_to(OUT) else str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}


def save(p, value):
    with p.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    state = read(OUT / 'analysis-state.json')
    old = read(OUT / 'feature-scope-v25.json')
    assert len(old['operationReviewQueue']) == 1 and old['operationReviewQueue'][0]['operationId'] == OP
    assert old['counts']['queuedOperations'] == 1 and len(old['supportOperations']) == 116
    RAW.mkdir(exist_ok=False)
    save(WORK / 'state-before.json', state)
    shutil.copyfile(WORK / 'state-before.json', RAW / 'state-before.json')
    for name in ['report.md', 'gaps.md']:
        shutil.copyfile(OUT / name, RAW / (name + '.before'))
    units, queries = {}, []

    def add(label, unit, metadata, pointer):
        b = (FROZEN / unit['sourcePath'].removeprefix('app.asar/')).read_bytes()
        span = b[unit['byteRange']['start']:unit['byteRange']['endExclusive']]
        assert sha(b) == unit['sourceHash'] and sha(span) == unit['spanHash'], label
        path = RAW / (label.replace('#', 'private-') + '.txt')
        path.write_bytes(span)
        units[label] = {**unit, 'origin': {**pin(metadata), 'jsonPointer': pointer}, 'savedSource': pin(path)}

    for folder in ['main-01', 'manager-01', 'manager-exports-01', 'manager-focus-01', 'transport-01', 'publish-01', 'publish-02']:
        metadata = WORK / folder / 'source-contracts.json'
        index = read(metadata)
        queries.append({'metadata': pin(metadata), 'sourcePath': index['sourcePath'], 'sourceHash': index['sourceHash'], 'nodeCount': index['nodeCount'], 'parserErrors': index['parserErrors'], 'config': index['config']})
        for i, u in enumerate(index['units']):
            wanted = folder in ['manager-focus-01', 'transport-01']
            if folder == 'main-01':
                wanted = u['label'] in ['binding-jfe', 'binding-Afe', 'binding-Ofe', 'binding-_fe', 'binding-Zde', 'binding-i'] or u['name'] in ['u0e', 'vXe', 'createAppHost', 'constructor']
            if folder == 'manager-exports-01':
                wanted = u['label'] in ['binding-kM', 'binding-vp', 'cjs-getter-Yn', 'cjs-getter-Tr']
            if folder == 'publish-02':
                wanted = u['label'] in ['binding-It', 'binding-ge', 'binding-de'] or u['label'].startswith('member-use-resumeThread')
            if wanted:
                add(folder + '-' + u['label'], u, metadata, f'/units/{i}')
    selection = read(WORK / 'connection-factory-selection.json')['selection']
    add('main-connection-factory', selection['owner'], WORK / 'connection-factory-selection.json', '/selection/owner')
    gate = read(WORK / 'startup-gate.json')
    for i, u in enumerate(gate['declarations']):
        add('startup-local-' + u['name'], u, WORK / 'startup-gate.json', f'/declarations/{i}')
    # The already-parsed Program has a sole getter literal for pn; no module execution.
    source_path = '.vite/build/src-BJv5Mk7n.js'
    data = (FROZEN / source_path).read_bytes()
    literal = b'Object.defineProperty(exports,"pn",{enumerable:!0,get:function(){return mB}})'
    assert data.count(literal) == 1
    start = data.index(literal)
    getter = {'sourcePath': 'app.asar/' + source_path, 'sourceHash': sha(data), 'byteRange': {'start': start, 'endExclusive': start + len(literal)}, 'spanHash': sha(literal), 'nodeType': 'bounded-exact-CJS-getter-literal; no additional AST parse'}
    add('connection-export-pn', getter, WORK / 'manager-focus-01/source-contracts.json', '/bindings/2')
    units['connection-export-pn']['origin']['qualification'] = 'Pointer identifies the separately whole-Program-qualified mB declaration; getter range is a unique literal read from that same frozen Program.'

    def find(folder, label):
        key = folder + '-' + label
        assert key in units, key
        return key

    main_constructor = next(k for k, u in units.items() if k.startswith('main-01') and u.get('name') == 'constructor')
    main_host = next(k for k, u in units.items() if k.startswith('main-01') and u.get('name') == 'createAppHost')
    facts = []

    def fact(claim, labels, confidence='confirmed'):
        u = units[labels[0]]
        facts.append({'id': f'RESUME-PROVIDER-{len(facts)+1:03}', 'baselineId': BASE, 'claim': claim,
                      'sourcePath': u['sourcePath'], 'sourceHash': u['sourceHash'], 'locator': {'kind': 'byte-range', **u['byteRange']},
                      'method': 'frozen-source AST and exact-byte review; no target execution', 'confidence': confidence,
                      'verificationStatus': 'source-contract-only; actual instance/service/durable effects unobserved', 'sourceUnitIds': labels})

    fact('启动函数u0e令z=!app.isPackaged，ne=z且CODEX_APP_SERVER_MANAGER_IN_MAIN严格等于字符串1，再将ne传入vXe。打包条件为真时该开关为假；本批没有读取运行中app.isPackaged或环境变量。', ['startup-local-z', 'startup-local-ne', next(k for k,u in units.items() if u.get('name') == 'u0e')])
    fact('hXe只在runAppServerManagerInMain为真时创建jfe(hostAppServerManagers)，否则服务为undefined；createAppHost把该值发布为appServerManagers。服务存在性仍不等于产品模式。', [main_constructor, main_host, find('main-01', 'binding-jfe')])
    fact('Afe按连接、读取身份context和generation维护资源，调用注入create并在结果仍current时发布；jfe.open只为当前有效resource返回ready，manager为i.Tr闭包，闭包每次调用先assertCurrent再取同一个resource.manager。', [find('main-01', 'binding-Afe'), find('main-01', 'binding-jfe')])
    fact('Ofe将new i.Yn保存为返回resource.manager，注入new _fe(connection,hostId,assertCurrent,threadAccessGetter)。main的i来自src-BJv5Mk7n；该文件的Yn getter绑定Program变量kM，Tr getter绑定vp。这是主进程实例的源码连接，不把kM等同于另一bundle的Dfn对象。', [find('main-01', 'binding-Ofe'), find('main-01', 'binding-i'), find('manager-exports-01', 'cjs-getter-Yn'), find('manager-exports-01', 'cjs-getter-Tr')])
    fact('vp构造器保存getter；resumeConversation与resumeThread各自返回转发原参数的函数。jfe提供的getter仍带current检查，能力复制与实际RPC送达属于依赖/运行边界。', [find('manager-focus-01', 'class-method-vp-constructor'), find('manager-focus-01', 'class-method-vp-resumeConversation'), find('manager-focus-01', 'class-method-vp-resumeThread')])
    fact('kM.resumeThread直接sendRequest(thread/resume,原参数)，将返回thread映射并合并live状态，然后返回完整response；resumeConversation进入#t(view)，#e合并in-flight并协调hydration，#t释放readResumeInputs并返回ready/not-ready、已有activeTurnId与threadSource。二者不是相同接口/效果。', [find('manager-focus-01', 'class-method-kM-resumeThread'), find('manager-focus-01', 'class-method-kM-resumeConversation'), find('manager-focus-01', 'class-method-kM-#e'), find('manager-focus-01', 'class-method-kM-#t')])
    fact('kM的协调恢复路径调用DT与zw；DT经ET发送构造后的thread/resume，并包含history/permission/notification/state恢复。ET的默认120秒超时及两次超时重试、closing-thread四次重试与旧shared Han同类，但本批不宣称两个完整pipeline或运行实例等价。', [find('manager-focus-01', 'class-method-kM-#e'), find('manager-focus-01', 'binding-DT'), find('manager-focus-01', 'binding-zw'), find('transport-01', 'binding-ET')])
    fact('kM.sendRequest转交构造器保存的requestClient；_fe生成id/method/params/trace，send调用connection.handleHostRequest并等待promise。thread/resume不在该sendRequest的outcome-unknown跟踪方法列表，超时abandon不能当作后台未执行或模型取消。', [find('manager-focus-01', 'class-method-kM-constructor'), find('manager-focus-01', 'class-method-kM-sendRequest'), find('main-01', 'binding-_fe')])
    fact('所选createAppServerConnection通过i.pn创建连接；src的pn getter返回mB。mB构造器把GR.handleHostRequest装到自身；GR建立host destination并交clientRequestQueue.enqueueHost，返回promise与abandon。该连接的实际transport取决于createAppServerConnection中的j5与host配置。', ['main-connection-factory', 'connection-export-pn', find('manager-focus-01', 'class-method-mB-constructor'), find('transport-01', 'binding-GR')])
    fact('mB为JI注入发送回调，回调交给MR.sendMessage；MR从getConnection取底层connection，按durable/普通分支序列化并调用send。实际socket/stdio/远程接收者、后台接受及通知/持久化未由这些静态边确认，不能直接换成公开CLI。', [find('manager-focus-01', 'class-method-mB-constructor'), find('transport-01', 'binding-JI'), find('transport-01', 'binding-MR')])
    publish_fn = find('publish-02', 'binding-It')
    fact('publish-actions的It创建create-environment-recovery-draft mutation。check分支确认历史中已有相同clientUserMessageId后调用l.resumeThread({threadId})，验证返回的唯一环境匹配目标，再强制加载历史并标记draft恢复ready；l绑定到ge(scope,de())，ge是shared y$t/KI导入。错误被该check分支吞掉；其他recover分支的startTurnWithOutcome是另一步。', [publish_fn, find('publish-02', 'binding-ge')])
    fact('旧TTC-OP-thread-resume记录的raw API应保留为支撑机制：已有独立的环境恢复调用者，且与页面resumeConversation的参数、协调、返回及状态副作用不同。不把它合并为页面操作，也不新建一个用户功能；消费者闭包和实际模式仍未知。', [publish_fn, find('manager-focus-01', 'class-method-kM-resumeThread')], 'inferred')

    publish_index = read(WORK / 'publish-02/source-contracts.json')
    receiver = next(r for r in publish_index['bindingReferences'] if r.get('member') == 'resumeThread')
    inherited_names = ['thread-resume-entry-contracts.json', 'thread-resume-isolated-observations.json', 'submission-host-instance.json', 'request-wrapper-contracts.json', 'feature-scope-v25.json', 'restoration-coverage-v16.json', 'analysis-stage-decisions-v4.json']
    result = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'question': state['stageDecisions']['nextAction'], 'sourceUnits': units, 'sourceFacts': facts,
              'lexicalReceiverEvidence': receiver, 'startupGate': gate,
              'sourceAnalysisQueries': queries, 'inheritedInputs': [pin(OUT / n) for n in inherited_names],
              'operationDisposition': {'operationId': OP, 'role': 'support', 'status': 'supporting-mechanism', 'excludedFromProductScope': False, 'featureIds': [], 'allConsumersAssigned': False, 'sameBusinessOperationAsPageResumeClaimed': False, 'actualUiToDfnInstanceProven': False, 'mode': 'unknown', 'basisFactIds': [facts[5]['id'], facts[10]['id'], facts[11]['id']]},
              'providerBranches': [
                  {'condition': 'appServerManagers is absent; startup gate guarantees absence when app.isPackaged is true', 'sourceChain': 'Bfn -> yMc, conditional X3/loi/Sii -> N3 manager -> vMc/X2t -> selected manager; KI primary/client/cache/deferred predicates retained', 'evidence': 'submission-host-instance.json', 'qualification': 'Static conditional composition. Actual mount, scope/host population and selected KI branch unobserved.'},
                  {'condition': 'unpackaged AND CODEX_APP_SERVER_MANAGER_IN_MAIN=1 AND host entry resource current/ready', 'sourceChain': 'createAppHost.appServerManagers -> SMc ready entry.manager -> jfe -> vp current getter -> Ofe resource.manager kM -> _fe -> connection mB/GR/JI/MR -> injected transport connection.send', 'qualification': 'New source receiver join; runtime flags, RPC delivery, identity readiness and service effects unobserved.'}],
              'maintenanceDecision': {'decision': 'Keep page resume coordination, raw thread/resume adapter, hydration/state effects, RPC provider lifecycle, transport delivery and environment-draft recovery distinct. Externalize RPC framework implementation. Preserve all provider branches and unknown capabilities.', 'confidence': 'inferred; design proposal', 'clientImplementationGenerated': False},
              'remainingBoundaries': ['Actual UI KI branch/scope/host/manager identity and initialization order', 'Underlying selected stdio/socket/remote service receiver and source/version binding; public CLI adoption still conditional', 'Full hydration/settings/permission/history delegates, notification ordering and durable recovery effects', 'Mode/account/cloud/platform ownership and complete consumers; no product exclusion inferred'],
              'nameSearchScope': {'method': 'rg -l literal resumeThread in frozen webview/assets and .vite/build JavaScript files', 'matchedPaths': ['app.asar/.vite/build/main-CqEoQDOU.js', 'app.asar/.vite/build/src-BJv5Mk7n.js', 'app.asar/webview/assets/app-shared-8bd9d0399038.js', 'app.asar/webview/assets/publish-actions-c0626be2877a.js'], 'qualification': 'Name-based discovery only; aliases/computed properties/native methods and consumer completeness not established.'},
              'counts': {'fullProgramParses': len(queries), 'distinctNewParsedPrograms': len({q['sourcePath'] for q in queries}), 'parsedProgramNodes': sum(q['nodeCount'] for q in queries), 'selectedUnitParses': 1, 'selectedUnitNodes': gate['nodeCount'], 'sourceFacts': len(facts), 'savedFirstPartySelectionsIncludingOverlaps': len(units), 'newReaRuns': 0, 'newModelSubmissions': 0, 'newClientRuns': 0, 'newTargetCodeExecutions': 0, 'newUserFeatures': 0, 'operationQueueBefore': 1, 'operationQueueAfter': 0, 'supportOperationsBefore': 116, 'supportOperationsAfter': 117, 'newProductScenarioPasses': 0},
              'limits': ['Repeated source queries are counted separately; all seven outputs are retained, including the first query without CJS getter selection and the first publish query without receiver-binding output.', 'The query runner evolved during this batch; saved query results are original receipts, and the saved final runner supports rerunning the named questions, not byte-identical reproduction of every intermediate metadata shape.', 'No actual module/RPC/IPC/service request was executed. The historical 19 isolated resume cases remain limited evidence and are not new observations here.', 'No raw API to page business equivalence or full application feature denominator is asserted.'], 'fullAnalysisCompleted': False}
    save(OUT / 'resume-provider-resolution.json', result)
    with (OUT / 'resume-provider-resolution-evidence.jsonl').open('x') as stream:
        stream.write(''.join(json.dumps(f, ensure_ascii=False) + '\n' for f in facts))
    ledger = copy.deepcopy(old)
    operation = ledger['operationReviewQueue'].pop()
    operation.update({'status': 'supporting-mechanism', 'supportKind': 'raw thread/resume request and local state refresh', 'classificationConfidence': 'inferred', 'reason': facts[-1]['claim'], 'supportDoesNotExhaustConsumers': True, 'dispositionRef': pin(OUT / 'resume-provider-resolution.json')})
    ledger['supportOperations'].append(operation)
    for row in ledger['rootCandidateDispositions']:
        if row['operationId'] == OP:
            assert row['role'] == 'pending'
            row['role'] = 'support'
    ledger['counts']['supportOperations'] = 117
    ledger['counts']['queuedOperations'] = 0
    for key in ['rootCandidateDispositionCounts', 'originalRootCandidateDispositionCounts']:
        ledger['counts'][key]['pending'] -= 1
        ledger['counts'][key]['support'] += 1
    ledger['previousScopeRef'] = pin(OUT / 'feature-scope-v25.json')
    ledger['resumeProviderDisposition'] = pin(OUT / 'resume-provider-resolution.json')
    ledger['newDefinitionIds'] = []
    save(OUT / 'feature-scope-v26.json', ledger)
    shutil.copyfile(OUT / 'feature-scope-v25.csv', OUT / 'feature-scope-v26.csv')
    coverage = read(OUT / 'restoration-coverage-v16.json')
    coverage['previousSnapshot'] = pin(OUT / 'restoration-coverage-v16.json')
    coverage['featureLedger'] = pin(OUT / 'feature-scope-v26.json')
    coverage['supportOperations'] = copy.deepcopy(ledger['supportOperations'])
    coverage['counts']['supportOperations'] = 117
    coverage['resumeProviderDisposition'] = pin(OUT / 'resume-provider-resolution.json')
    save(OUT / 'restoration-coverage-v17.json', coverage)
    summary = '''# 恢复入口与provider的有限结论

唯一待分类操作TTC-OP-thread-resume已登记为保留的支撑机制。页面的resumeConversation与低层resumeThread保持不同职责；没有新建功能、合并业务操作或确认模式。

新增源码证据接上了主进程提供的manager：启动开关只允许非打包应用且CODEX_APP_SERVER_MANAGER_IN_MAIN严格为1时发布appServerManagers；有效资源经jfe/vp转发到Ofe创建的kM，再经_fe和mB的GR/JI/MR到注入的底层connection.send。打包条件为真时该host服务不提供，renderer选择与内部manager的条件链沿用既有provider调查。实际UI的scope、host、注册对象与选支未观察。

raw resumeThread有具体消费者：云环境草稿恢复的check分支先找已提交的clientUserMessageId，再恢复线程、核对唯一目标环境并加载历史。它不是页面恢复操作的同义名称。raw入口返回完整响应并合并状态；页面入口还负责in-flight协调、输入释放、权限/配置与历史恢复，返回ready/not-ready及已有turn信息。

当前功能仍373项、用户操作377项、恢复任务48个、未执行规格1216条；支撑机制从116变为117，操作分类队列从1变为0。12项关联、3项重叠、旧来源角色及完整产品分母仍未完成。unknown模式372项与shared 1项保持不变，整项排除0。

本批只做冻结源码分析：7次完整Program解析（3个文件，重复查询计入）及1次已选启动函数解析，0个REA新运行、模型提交、客户端启动、源码执行或产品通过。查询中间产物均保留；最终脚本不宣称逐字节重现所有中间metadata格式。第三方RPC实现没有转成客户端维护代码。

实际传输端、公开CLI采用、hydration委托、通知顺序、持久化和模式闭包继续未知。本结论关闭的是操作分类与明确的静态接收链，不关闭整个后台问题。详见[源码事实和精确范围](resume-provider-resolution.json)；完整分析仍未完成。
'''
    with (OUT / 'resume-provider-resolution.md').open('x') as stream:
        stream.write(summary)
    after = copy.deepcopy(state)
    after['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
    after['resumeProviderResolution'] = {'contracts': pin(OUT / 'resume-provider-resolution.json'), 'summary': pin(OUT / 'resume-provider-resolution.md'), 'counts': result['counts'], 'actualUiToDfnIdentityConfirmed': False}
    view = after['featureScopeCurrentView']
    view.update({'snapshotVersion': 26, 'ledger': pin(OUT / 'feature-scope-v26.json'), 'csv': pin(OUT / 'feature-scope-v26.csv'), 'previousLedger': pin(OUT / 'feature-scope-v25.json'), 'counts': copy.deepcopy(ledger['counts']), 'resumeProviderDisposition': pin(OUT / 'resume-provider-resolution.json')})
    after['restorationCoverageCurrentOverlay'] = {'coverage': pin(OUT / 'restoration-coverage-v17.json'), 'qualification': 'Feature/task/scenario ownership unchanged; only the existing raw-resume support disposition is updated. Existing ordering v1 remains valid for the same 373 features and 48 tasks.'}
    after['stageDecisions']['resumeProviderOverlay'] = after['resumeProviderResolution']
    after['stageDecisions']['nextAction'] = {'issueId': 'SD-06', 'question': 'Join existing reviewed module proposals into one logical-module view with the plan-required fields, keeping unknown imports/exports/state/side effects explicit.', 'fixedInput': 'Existing 11 boundary proposals, six source-contract proposals, provider/runtime policy proposals and current feature/task ownership; no new feature discovery.', 'closure': 'Every existing reviewed proposal has a traceable responsibility/environment/mode/source-range/import/export/shared-state/side-effect/third-party/proposed-path record. Unanalysed source-file records remain a separate incomplete inventory.', 'authorization': 'Existing-artifact analysis/design only; no client implementation, live application or model requests.'}
    after['pending'] = [item.replace('UI resume与raw API仍有1项排队判定。', 'raw API已分类为支撑，静态host接收链与打包开关已闭合；实际实例/服务仍未验证。') for item in after['pending']]
    assert read(OUT / 'analysis-state.json') == state
    (OUT / 'analysis-state.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n')
    note = '恢复入口最新结论见[provider与操作分类](resume-provider-resolution.md)：373项/48任务不变，支撑117、操作队列0；静态打包开关及主进程接收链已补齐。真实实例、服务与持久化仍未验证，完整分析未完成。下文旧快照的1项排队操作由此更新。\n\n'
    for name in ['report.md', 'gaps.md']:
        (OUT / name).write_text(note + (RAW / (name + '.before')).read_text())
    for name in ['resume_provider_ast.mjs', 'extract_resume_gate.cjs', 'publish_resume_provider_resolution.py']:
        shutil.copyfile(ROOT / 'scripts/analysis' / name, RAW / name)
    for p in RAW.rglob('*'):
        if p.is_file():
            p.chmod(0o444)
    for name in ['resume-provider-resolution.json', 'resume-provider-resolution-evidence.jsonl', 'resume-provider-resolution.md', 'feature-scope-v26.json', 'feature-scope-v26.csv', 'restoration-coverage-v17.json']:
        (OUT / name).chmod(0o444)
    print(json.dumps({'counts': result['counts'], 'features': len(ledger['features']), 'support': len(ledger['supportOperations']), 'queue': len(ledger['operationReviewQueue']), 'fullAnalysisCompleted': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
