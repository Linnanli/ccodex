"""Integrate bounded request-port and IPC decisions without claiming runtime delivery."""
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/backend-ipc-roles-work'
PINS = {}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    v = {'path': str(p.relative_to(OUT)), 'bytes': len(b), 'sha256': sha(b)} if p.is_relative_to(OUT) else {'path': str(p.relative_to(ROOT)), 'pathBase': 'workspace', 'bytes': len(b), 'sha256': sha(b)}
    PINS[str(p)] = v
    return v


def load(p):
    pin(p)
    return json.loads(p.read_text())


def write(p, v):
    b = v if isinstance(v, bytes) else (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)
    p.chmod(0o444)
    return pin(p)


state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
with (WORK / 'state-before.json').open('xb') as f:
    f.write(before)
state = json.loads(before)
assert state['legacyEntryDispositions']['result']['path'] == 'legacy-entry-dispositions-v3.json'
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
legacy = load(OUT / 'legacy-entry-dispositions-v3.json')
families = load(OUT / 'entry-family-map.json')
query = load(WORK / 'backend-ipc-roles.json')
helpers = load(WORK / 'port-helpers/source-contracts.json')
protocol = load(OUT / 'exported-protocol-comparison.json')
compat = load(OUT / 'protocol-compatibility.json')
coverage = load(OUT / 'protocol-coverage.json')
ipc = load(OUT / 'ipc.json')
for name in ('preload-app-host.json', 'host-http-service.json', 'app-host-context.json', 'resume-provider-resolution.json'):
    load(OUT / name)
pin(ROOT / 'scripts/analysis/analyze_backend_ipc_roles.mjs')
pin(ROOT / 'scripts/analysis/resume_provider_ast.mjs')
pin(Path(__file__))
helper_inputs = []
for u in helpers['units']:
    helper_inputs.append({'label': u['label'], 'source': {k: u[k] for k in ('sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType')},
                          'file': pin(WORK / 'port-helpers' / u['file']), 'expression': (WORK / 'port-helpers' / u['file']).read_text()})
assert query['counts']['backendRecords'] == 91 and query['counts']['ipcRecords'] == 50
assert query['counts']['ipcSourceRoleCounts'] == {'channel-name-declaration': 41, 'parameterized-channel-name-builder': 4, 'channel-argument-in-call': 3, 'channel-discriminator-in-event-handler': 2}
assert not query['targetCodeExecuted']
query_pin = write(OUT / 'raw/backend-ipc-roles-v1/source-roles.json', (WORK / 'backend-ipc-roles.json').read_bytes())
helpers_pin = write(OUT / 'raw/backend-ipc-roles-v1/port-helpers.json', helpers)
method_names = sorted({x['method'] for x in query['backendRows']})
assert method_names == sorted(coverage['clientMethods'])
assert len(method_names) == 52
method_decisions = []
for method in method_names:
    comparisons = {}
    for mode in ('stable', 'experimental'):
        rows = protocol['comparisons'][mode]['variantContracts']
        matches = [(i, x) for i, x in enumerate(rows) if x['union'] == 'ClientRequest.json' and x['method'] == method]
        assert len(matches) <= 1
        if matches:
            i, x = matches[0]
            assert x['publicPresent'] and x['frozenPresent'] and x['effectiveContract']['status'] == 'equal'
            comparisons[mode] = {'status': 'equal-effective-schema-contract', 'source': {**pin(OUT / 'exported-protocol-comparison.json'), 'jsonPointer': '/comparisons/' + mode + '/variantContracts/' + str(i)}}
        else:
            comparisons[mode] = {'status': 'not-in-selected-stable-union' if mode == 'stable' else 'absent'}
    assert comparisons['experimental']['status'] == 'equal-effective-schema-contract'
    status = 'stable-schema-candidate' if comparisons['stable']['status'] == 'equal-effective-schema-contract' else 'experimental-schema-candidate'
    method_decisions.append({'method': method, 'entryIds': [x['entryId'] for x in query['backendRows'] if x['method'] == method],
                             'schemaComparisons': comparisons, 'adoption': status,
                             'qualification': 'Exact call literal joins a schema method. This does not validate every dynamic argument, prove actual receiver/service support, or establish successful behavior.'})
assert Counter(x['adoption'] for x in method_decisions) == {'stable-schema-candidate': 43, 'experimental-schema-candidate': 9}
assert sorted(x['method'] for x in method_decisions if x['adoption'] == 'experimental-schema-candidate') == sorted(compat['directClientCandidates']['notInPublicStableSchema'])

port = {x['name']: x for x in query['portMethods']}
helper = {x['label']: x for x in helper_inputs}
assert 'await this.ensureReady(),n?.()' in port['sendAppServerRequest']['expression']
assert 'this.configuration.handleSuccessfulRequest(e,t)' in port['sendAppServerRequest']['expression']
assert 'uB=3e4' == helper['binding-uB']['expression']
assert 'i.reject(a,!1)' in helper['binding-qL']['expression']
port_contracts = [
    {'id': 'PORT-READY', 'source': port['ensureReady']['source'], 'claim': '等待初始化/重连就绪；disposed、退出、不可重试错误和重试耗尽保持各自失败路径，不能只检测进程存在。'},
    {'id': 'PORT-SEND', 'source': port['sendAppServerRequest']['source'], 'claim': '就绪后调用可选 before-send 钩子，再生成 method:UUID 的请求 id，将 method/params/options 交给 sendInternalRequest；成功后保留配置处理及特定配置写入的 Chronicle 协调。'},
    {'id': 'PORT-PENDING', 'source': port['sendInternalRequest']['source'], 'claim': '保留重复 id 拒绝、pending map、startedAt、method/thread 关联、onSettled、认证切换跟踪、trace 和发送失败清理。默认 timeout 引用 Program uB=30000；显式 null 关闭定时器。'},
    {'id': 'PORT-CANCEL', 'source': port['sendInternalRequest']['source'], 'claim': 'pending reject 默认调用 connection.cancelRequest；这是传输取消钩子，不能等同于用户任务已取消或 turn/interrupt 已成功。'},
    {'id': 'PORT-TIMEOUT', 'source': helper['binding-qL']['source'], 'claim': '普通超时移除并拒绝；满足条件的 thread/start 或 thread/fork 分支先 reject(error,false)，保留晚到响应以 unsubscribe 线程并吞掉清理错误。条件输入和 helper 依赖必须保留，不可统一成立即删除 pending。'},
    {'id': 'PORT-RESPONSE', 'source': helper['binding-JL']['source'], 'claim': '内部响应清除 timer；error 交给 VL 转换并 reject，成功通过 o.S 后 resolve。VL/o.S 的完整错误和值变换合同未在本批扩展。'},
    {'id': 'PORT-ROUTE', 'source': port['routeResponse']['source'], 'claim': '响应按内部 pending、窗口/host 请求和 coalesced waiters 分流；观察、跟踪、归档、预热、配置成功处理、通知广播和销毁窗口检查不能从 transport 中直接删去。'},
    {'id': 'PORT-TRACE', 'source': helper['binding-zL']['source'], 'claim': 'zL 对 RL 选定方法增加 workspace-discovery/app-server tracing，并将返回 error 转为带 code 的异常；RL 的完整选择集合未在本批判定。'},
]
policy_pairs = []
for r in query['ipcRows']:
    if r['sourceRole'] != 'channel-discriminator-in-event-handler':
        continue
    senders = [(i, x) for i, x in enumerate(query['ipcUses']) if x['channel'] == r['channel'] and x['verb'] == 'sendSync']
    assert len(senders) == 1
    i, sender = senders[0]
    assert r['eventHandler']['discriminatedValueOrigin']['definitions'][0]['kind'] == 'parameter'
    policy_pairs.append({'channel': r['channel'], 'senderUse': {**query_pin, 'jsonPointer': '/ipcUses/' + str(i)},
                         'receiverEntryId': r['entryId'], 'receiver': r['eventHandler'],
                         'contract': 'sendSync -> WebContents ipc-message-sync event channel discriminator -> returnValue/policy branch',
                         'decision': '保留同步查询及接收端分支/平台条件，不替换为普通 invoke/handle。实际 WebContents 实例、触发和返回效果未验证。',
                         'actualDeliveryVerified': False})
assert len(policy_pairs) == 2

records = []
for i, x in enumerate(query['backendRows']):
    records.append({'entryId': x['entryId'], 'family': 'backend-calls', 'sourceRole': x['sourceRole'],
                    'source': x['originalSource'], 'call': x['call'], 'query': {**query_pin, 'jsonPointer': '/backendRows/' + str(i)},
                    'methodDecisionIndex': method_names.index(x['method']),
                    'maintenanceDecision': '恢复第一方 request-port 调用与发送前钩子；按具体 receiver/配置保留跨层委托。只有选定 mB 同 class 的5处调用有本地 sendAppServerRequest 定义；其余86处保留注入/派生实例缺口。',
                    'remainingWork': '实际 receiver/连接 transport/服务接受、动态参数合法性、模式及持久化/通知后效仍须分别确认。',
                    'actualRuntimeVerified': False, 'functionalEntryFullyResolved': False})
for i, x in enumerate(query['ipcRows']):
    pure = x['sourceRole'] in ('channel-name-declaration', 'parameterized-channel-name-builder')
    records.append({'entryId': x['entryId'], 'family': 'ipc-channels', 'sourceRole': x['sourceRole'],
                    'source': x['originalSource'], 'query': {**query_pin, 'jsonPointer': '/ipcRows/' + str(i)},
                    'nonUserOperationSource': pure,
                    'maintenanceDecision': '合并为传输契约的声明/生成函数，保留全部消费者；不新增用户功能。' if pure else '保留实际 API 调用或事件通道分支，不以通道字符串独立认定用户功能或运行送达。',
                    'remainingWork': '完整 main/worker 调用方和接收实例仍需对应 source-qualified contracts；同名字符串只说明通道值，不证明具体对象身份或成功通信。',
                    'actualRuntimeVerified': False, 'functionalEntryFullyResolved': False})
assert len(records) == 141

review = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
          'scope': 'All saved 91 direct request-port candidates and 50 IPC channel candidates; selected provider contracts and bounded IPC source uses.',
          'records': records, 'sourceQuery': query_pin, 'portHelperQuery': helpers_pin,
          'sourceUnits': query['sourceUnits'], 'helperInputs': helper_inputs, 'portContracts': port_contracts,
          'methodAdoptionDecisions': method_decisions, 'browserPolicyPairs': policy_pairs,
          'appHostBoundary': {'sourceContracts': [pin(OUT / x) for x in ('preload-app-host.json', 'host-http-service.json', 'app-host-context.json')],
                              'decision': 'connect-app-host 保持 window message/MessagePort 转发、主进程 trust/context 和 App-host 服务连接；HTTP service 不按名字并入 app-server request port。',
                              'qualification': '复用已有精确绑定合同；本批不宣称新增跨进程端口送达或实际实例观察。'},
          'maintenanceOwnership': [
              {'owner': 'packages/contracts/src/desktop-ipc.ts', 'role': '通道常量/参数化名称与消息合同；原重复声明按版本化契约统一，调用端仍保持原 transport form'},
              {'owner': 'apps/desktop/src/preload/desktop-bridge.ts', 'role': 'invoke/send/sendSync/postMessage、订阅及清理；转移端口的列表及 window 来源检查保留'},
              {'owner': 'apps/desktop/src/main/browser/policy-ipc.ts', 'role': '同步浏览器策略查询和 ipc-message-sync 接收分支及 returnValue/platform 行为'},
              {'owner': 'packages/backend-adapter/src/app-server-connection.ts', 'role': '请求就绪/超时/错误/取消、响应关联及客户端领域副作用；公开后端替代通过该边界接入'},
              {'owner': 'apps/desktop/src/main/app-host/connection.ts', 'role': '已记录 trust/context、MessagePort 与 httpFetch 服务委托；不与模型请求合并'}],
          'publicBackendDecision': {'reference': pin(OUT / 'exported-protocol-comparison.json'),
                                    'publicVersion': protocol['publicCli']['versionOutput'],
                                    'stableMethodCandidates': 43, 'experimentalMethodCandidates': 9,
                                    'decision': '52个直接方法的选定 experimental 有效 schema 相同，其中43个也在 stable 中相同；可作为适配层候选合同。9个非 stable 方法须单列服务/启用条件，不能按普通 stable 能力验收。',
                                    'limits': '这是52个直接请求方法的 schema 结论；不改变全协议466变体中11组差异的既有结论，不证明动态请求均合法、服务可用或二进制与公开提交绑定。',
                                    'runtimeAdoptionQualified': False},
          'counts': {**query['counts'], 'methodAdoptionCounts': {'stable-schema-candidate': 43, 'experimental-schema-candidate': 9},
                     'nonUserIpcSourceRecords': 45, 'remainingIpcEndpointRecords': 5, 'exactBrowserPolicySourcePairs': 2,
                     'newFullProgramQueries': 5, 'distinctFullProgramSources': 4, 'portHelperDefinitions': 4},
          'limits': query['limitations'], 'newModelSubmissions': 0, 'newClientRuns': 0, 'newReaRuns': 0,
          'newProductScenarioPasses': 0, 'newFeatureDefinitions': 0, 'newClientImplementation': 0,
          'fullAnalysisCompleted': False, 'inputPins': list(PINS.values())}
review_pin = write(OUT / 'backend-ipc-roles-v1.json', review)
evidence = []
for i, row in enumerate(records):
    source = row['call'] if row['family'] == 'backend-calls' else row['source']
    evidence.append({'id': 'BACKEND-IPC-ROLE-' + str(i).zfill(3), 'baselineId': BASE,
                     'claim': row['sourceRole'] + '; bounded source role, not full functional identity or runtime delivery.',
                     'sourcePath': source['sourcePath'], 'sourceHash': source['sourceHash'],
                     'locator': {'byteRange': source['byteRange'], 'spanHash': source['spanHash'], 'entryId': row['entryId']},
                     'method': 'frozen-source-AST; exact-legacy-contained-call-or-channel-span-join',
                     'confidence': 'confirmed', 'verificationStatus': 'source-role-confirmed; provider-instance-and-runtime-unverified'})
for x in port_contracts:
    source = x['source']
    evidence.append({'id': x['id'], 'baselineId': BASE, 'claim': x['claim'], 'sourcePath': source['sourcePath'],
                     'sourceHash': source['sourceHash'], 'locator': {'byteRange': source['byteRange'], 'spanHash': source['spanHash']},
                     'method': 'complete-frozen-class-method-or-Program-helper-AST-and-source-review',
                     'confidence': 'confirmed', 'verificationStatus': 'source-contract-only; helper/import/provider/runtime qualifications retained'})
evidence_pin = write(OUT / 'backend-ipc-roles-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence).encode())
legacy['previousSnapshot'] = pin(OUT / 'legacy-entry-dispositions-v3.json')
legacy['recordedAtUtc'] = review['recordedAtUtc']; legacy['backendIpcRoleReview'] = review_pin
by_id = {x['entryId']: (i, x) for i, x in enumerate(records)}
for x in legacy['entries']:
    if x['entryId'] not in by_id:
        continue
    i, row = by_id[x['entryId']]
    assert x['disposition'] == 'awaiting-disposition'
    disposition = 'partial-backend-request-port' if row['family'] == 'backend-calls' else 'non-user-operation-source' if row['nonUserOperationSource'] else 'partial-ipc-endpoint-role'
    x.update(disposition=disposition, sourceRoleConfirmed=True, sourceRole=row['sourceRole'],
             roleEvidenceRef={**review_pin, 'jsonPointer': '/records/' + str(i)},
             retentionDecision=row['maintenanceDecision'], remainingWork=row['remainingWork'])
counts = Counter(x['disposition'] for x in legacy['entries'])
assert counts['awaiting-disposition'] == 253 and counts['non-user-operation-source'] == 280
legacy['counts'].update(entriesAwaitingDisposition=253, nonUserOperationSourceRecords=280,
                        ipcChannelDeclarations=41, ipcChannelNameBuilders=4, partialBackendRequestPorts=91,
                        partialIpcEndpoints=5, selectedBackendIpcSourceRoles=141, dispositionCounts=dict(counts))
legacy['accountingPolicy']['unknown'] = '253 entries await source-role disposition. 91 request-port calls,5 IPC endpoints,143 host labels and189 menu records retain consumer/mode/runtime gaps. 45 IPC declarations/builders are transport support source, not user features.'
legacy['frozenSourceValidation']['backendIpcSupplement'] = {'sourceQuery': query_pin, 'portHelperQuery': helpers_pin,
                                                         'legacyRangesChecked': 141, 'backendCompleteCallsChecked': 91, 'wholeIpcPrograms': 4, 'selectedOwners': 43}
legacy_pin = write(OUT / 'legacy-entry-dispositions-v4.json', legacy)
buf = io.StringIO(); writer = csv.DictWriter(buf, fieldnames=['entryId', 'entryKind', 'family', 'label', 'disposition', 'sourceRoleConfirmed', 'productMode', 'functionalEntryFullyResolved'], extrasaction='ignore')
writer.writeheader(); writer.writerows(legacy['entries'])
legacy_csv = write(OUT / 'legacy-entry-dispositions-v4.csv', buf.getvalue().encode())

summary = '''# 后台请求与 IPC 的恢复决定

本批将原有 91 条后台候选和 50 条 IPC 候选接到冻结源码中的完整调用或通道位置。没有增加功能定义、运行通过数或模型提交。

91 条调用对应 52 个方法：5 条在选定 mB class 内明确调用同 class 的 sendAppServerRequest 定义，其余 86 条的参数、字段或调用结果来源已记录，实际注入实例仍未知。不能将这些记录直接解释为 91 项功能或已确认送达的后台调用。

## 公开后台的采用边界

固定公开 CLI 0.162.0 与随包 CLI 的既有导出比较中，这 52 个方法的 experimental 有效 schema 均相同；43 个也在 stable 中相同。9 个非 stable 方法为 project/delete、project/list、project/move、project/read、project/update、remoteControl/enable、rollout/compress、thread/realtime/stop、thread/settings/update。

决定：公开 app-server 可作为这些请求合同的适配候选，9 个非 stable 方法须单列服务和启用条件。schema 相同不证明动态参数均合法、实际服务支持或成功后效；全协议 466 变体中的 11 组差异仍保留。

## 连接适配器必须保留的行为

- 初始化/重连等待和退出/失败条件、发送前钩子、请求 id、pending 关联、认证与 trace。
- 默认 30 秒超时及 null 关闭定时器、onSettled、传输 cancelRequest 钩子与发送失败清理。
- 条件性的 thread/start、thread/fork 超时晚到响应清理；不能统一为立即删除 pending。
- 配置成功处理、Chronicle 协调、归档/预热/观察/广播，以及内部请求、窗口/host 请求和合并等待者的分流。

传输取消不等于用户任务取消。VL/o.S 的完整错误和值变换、RL 的 tracing 选择集合及实际 transport/provider 不在本批闭合范围。

## IPC 不是用户功能清单

50 条记录分为 41 条通道常量、4 条参数化通道名生成函数、3 条 API 参数和2 条事件通道判断分支。前45条归入传输支持声明，避免按重复通道制造功能。四个完整 IPC Program 和 ICe 函数中的36处 API 使用已登记；不代表完整 main/worker 消费者覆盖。

两个浏览器策略查询已形成源级协议配对：browser preload 的 sendSync 对应 main WebContents 的 ipc-message-sync 通道判断。保留同步查询、returnValue 和平台分支；实际对象、触发和返回效果未观察。connect-app-host 继续沿用已验证来源的 MessagePort/trust/context/App-host 服务合同，httpFetch 不并入 app-server request port。

恢复源码职责据此分为 IPC 合同、preload bridge、main browser policy、app-server connection 和 App-host connection；标准 Electron 与第三方库通过依赖提供。本批没有生成客户端实现。

当前[旧入口 v4](legacy-entry-dispositions-v4.json)仍保留全部968个 ID，253条待源码角色处置；完整功能解决数仍为0。373项功能、48任务及1216条未执行规格保持原定义，由当前 overlay 更新入口与协议决定。

明细：[来源、请求合同和维护决定](backend-ipc-roles-v1.json)、[九字段证据](backend-ipc-roles-v1-evidence.jsonl)。下一步处置剩余路由/导航/快捷键入口的支持、容器与用户操作角色，并连接既有功能，避免重做后台/IPC枚举。
'''
summary_pin = write(OUT / 'backend-ipc-roles-v1.md', summary.encode())
overlay = {'contracts': review_pin, 'summary': summary_pin, 'evidence': evidence_pin, 'legacyEntryDispositions': legacy_pin,
           'counts': review['counts'], 'legacyCounts': legacy['counts'],
           'qualification': 'Feature v27/task v18/scenario definitions unchanged; only legacy source roles and bounded request/IPC maintenance decisions updated.',
           'fullAnalysisCompleted': False}
state['backendIpcRoles'] = overlay; state['stageDecisions']['backendIpcRoleOverlay'] = overlay
state['legacyEntryDispositions'].update(result=legacy_pin, summary=summary_pin, csv=legacy_csv, counts=legacy['counts'])
state['featureScopeCurrentView']['legacyEntryDispositionOverlay'] = legacy_pin
state['featureScopeCurrentView']['backendIpcRoleOverlay'] = review_pin
state['featureScopeCurrentView']['counts'].update(legacyEntriesAwaitingDisposition=253, legacyEntriesWithDefinitiveNonUserRole=280,
                                                legacyEntriesWithReviewedBackendRequestPort=91, legacyIpcEndpointRoles=5)
state['restorationCoverageCurrentOverlay']['backendIpcRoleOverlay'] = overlay
state['stageDecisions']['nextAction'] = {'issueId': 'SD-01',
    'question': 'Disposition remaining saved route/navigation/shortcut entries as support, container, alias or user-operation consumers and join existing feature contracts.',
    'fixedInput': '253 still-awaiting entries; saved full-Program route/command contracts, feature v27/task v18 and existing handler/provider decisions.',
    'closure': 'Every reviewed source record has a justified role; concrete feature joins require exact source evidence. Do not create features from route/command labels or repeat source enumeration.',
    'authorization': 'Frozen source and saved artifacts only; no client/model/service invocation.'}
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
assert state['latestBehaviorAuthorizationState'] == json.loads(before)['latestBehaviorAuthorizationState']
assert not state['fullAnalysisCompleted']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
for name in ('report.md', 'gaps.md'):
    p = OUT / name; text = p.read_text(); (WORK / (name + '.before')).write_text(text)
    first, sep, rest = text.partition('\n\n')
    p.write_text('当前后台/IPC恢复决定见[请求与传输边界](backend-ipc-roles-v1.md)：91条请求对应52方法，43 stable/9 experimental schema候选分列；客户端超时、取消钩子、响应和配置副作用保留。50条IPC中45条为声明/名称生成，两个浏览器同步策略源级配对明确。旧入口v4尚有253条待角色处置，完整功能解决0；373项功能、48任务、1216未执行规格不变，完整分析未完成。' + sep + rest)
print(json.dumps({'review': review_pin, 'legacy': legacy_pin, 'counts': review['counts'], 'legacyCounts': legacy['counts']}, ensure_ascii=False))
