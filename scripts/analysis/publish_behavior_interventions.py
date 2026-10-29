"""Publish bounded, metadata-only results of the two approved scenario attempts."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/behavior-interventions-work'
PREFIX = 'raw/behavior-interventions'
def pin(b):
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
def encode(v):
    return (json.dumps(v, ensure_ascii=False, indent=2)+'\n').encode()
def read(name):
    return json.loads((WORK / name).read_bytes())
sources = [
    ('authorization.json', WORK / 'authorization.json'),
    ('approved-scenarios.json', ROOT / '.analysis-local/behavior-next-scenarios-work/scenarios.json'),
    ('cancel-preflight-failure.json', WORK / 'owned-running-cancel-02.json'),
    ('cancel-submitted.json', WORK / 'owned-running-cancel-02-attempt-02.json'),
    ('cancel-reservation.json', WORK / 'submission-owned-running-cancel-02.json'),
    ('cancel-later-state.json', WORK / 'cancel-readonly-state-01.json'),
    ('cancel-later-reply-row.json', WORK / 'cancel-readonly-reply-row-01.json'),
    ('cancel-command-receipt.json', WORK / 'attempts/cancel-02/receipt.json'),
    ('cancel-state-command-receipt.json', WORK / 'attempts/cancel-readonly-state-01/receipt.json'),
    ('cancel-reply-command-receipt.json', WORK / 'attempts/cancel-readonly-reply-row-01/receipt.json'),
    ('resume-launch.json', WORK / 'resume-20261023-01/result.json'),
    ('resume-project-preflight.json', WORK / 'ui-prepare-resume-01.json'),
    ('resume-project-preflight-receipt.json', WORK / 'attempts/ui-prepare-resume-01/receipt.json'),
    ('resume-ui-counts.json', WORK / 'ui-resume-probe-02.json'),
    ('resume-cleanup.json', WORK / 'resume-20261023-01/cleanup.json'),
]
auth = read('authorization.json')
approved = Path(auth['plan']['path']).read_bytes()
assert pin(approved) == {k: auth['plan'][k] for k in ['bytes', 'sha256']}
plan = json.loads(approved)
assert plan['baselineId'] == BASELINE and auth['maxSubmissions'] == 2
assert sorted(p.name for p in WORK.glob('submission-*.json')) == ['submission-owned-running-cancel-02.json']
cancel = read('owned-running-cancel-02-attempt-02.json')
later = read('cancel-readonly-reply-row-01.json')
counts = read('ui-resume-probe-02.json')
cleanup = read('resume-20261023-01/cleanup.json')
assert cancel['modelSubmissions'] == 1 and cancel['intervention'] is None
assert cancel['status'] == 'unresolved/observation-timeout' and cancel['readmeAfter']['unchanged']
assert later['status'] == 'observed' and later['identity'] == cancel['identity'] and later['readmeAfter']['unchanged']
assert len(later['turn']) == 1 and later['turn'][0]['status'] == 'completed' and later['turn'][0]['cwdMatches']
assert counts['ownedProject'] == {'labelCount': 0, 'containerCount': 0}
assert cleanup['status'] == 'owned-runtime-cleanup-verified' and cleanup['shutdownVerified']
assert cleanup['scenarioSignals'] == 0 and cleanup['modelSubmissions'] == 0
copies, planned = [], {}
for name, source in sources:
    raw = source.read_bytes()
    # These are selected synthetic-task metadata, never runner/source/AST/profile dumps.
    json.loads(raw)
    destination = PREFIX + '/author/' + name
    copies.append({'original': str(source), 'outputPath': destination, **pin(raw), 'kind': 'metadata_only'})
    planned[destination] = raw
reader = {
    'schemaVersion': 1, 'baselineId': BASELINE, 'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Approved two-task synthetic desktop scenarios; exact UI props and process identities only. Not complete product behavior verification.',
    'authorization': {'maxAdditionalSubmissions': 2, 'reservedSubmissions': 1, 'remainingSubmissions': 1,
        'newSubmissionsOn20261023': 0, 'priorSeparateOneTaskAuthorizationIncluded': False,
        'remainingScenario': plan['scenarios'][1]['id']},
    'cancelScenario': {'id': plan['scenarios'][0]['id'], 'modelSubmissions': 1, 'identity': cancel['identity'],
        'initialObservation': cancel['status'], 'laterUiState': 'completed', 'cwdMatches': True,
        'cancelClicks': 0, 'outcome': 'not-tested/control-binding-unavailable',
        'controlReason': 'A visible enabled stop button was observed, but exact same-props thread/turn/running association was not closed; no click was made.',
        'sameTurnReconnectItems': ['Reconnecting... 2/5', 'Reconnecting... 3/5', 'Reconnecting... 4/5', 'Reconnecting... 5/5'],
        'reconnectErrorInfoKey': 'responseStreamDisconnected',
        'agentFinalReply': later['turn'][0]['agentMessages'][-1]['text'],
        'replyQualification': 'The model stated that no direct read-only file tool was available. This is a reply, not independent file-access instrumentation.',
        'ownedSidebarRow': 'local:client-new-thread:f95b8117-fe69-43ff-9d95-f773179c7f47',
        'rowQualification': 'The temporary UI row was associated by its own fiber entry.conversationId, not by guessing a local:UUID selector.',
        'readmeAfterOriginalSampleMatches': True,
        'limits': ['No cancellation outcome measured.', 'UI state is not independent backend delivery/storage proof.',
                   'Reconnect items do not establish quota exhaustion, rate limiting or a service-side root cause.']},
    'stopRestartScenario': {'id': plan['scenarios'][1]['id'], 'modelSubmissions': 0, 'scenarioSignals': 0, 'scenarioRestarts': 0,
        'status': 'not-submitted/existing-project-precondition-unavailable',
        'observedAtUtc': counts['atUtc'], 'projectControlCounts': counts['ownedProject'],
        'ownedApplicationLoaded': counts['document']['readyState'] == 'complete',
        'fixtureRestored': read('resume-20261023-01/result.json')['fixtureRestoration'],
        'ownedLaunchAndCliVerified': True, 'cleanupVerified': True,
        'limits': ['No second prompt was filled or submitted.', 'Zero matching controls does not prove the stored project was deleted or identify why it is absent.',
                   'Cleanup SIGTERM occurred with no submitted scenario turn and is not a stop/restart intervention.',
                   'Fixture restoration is not proof of uninterrupted filesystem persistence.',
                   'The remaining one-task authorization is unconsumed; the original plan requires the existing project and forbids creating another.']},
    'globalRecordsAdded': 0, 'fullAnalysisCompleted': False, 'thirdPartyImplementationsPublished': False,
}
summary = '''# 两条获授权行为样例的实际进度

本组最多2次模型提交，已用1次、余1次；2026-10-23新增提交0。先前另一组单独批准的1次任务不计入本组。[结构化读者](behavior-interventions.json)与[输入索引](behavior-interventions-provenance.json)保留精确来源。

| 场景 | 已发生 | 结论 |
| --- | --- | --- |
| 执行中取消 | 1次提交；60秒观察超时；稍后同一thread/turn的UI状态为completed；取消点击0 | 取消未测试。停止按钮与精确运行turn的关联未关闭，没有点击。 |
| 执行中停止／重启 | 2026-10-23重新启动并核实自有冻结应用和CLI；原项目名称及项目ID控件均0；提交0，场景停止0、重启0 | 前置条件不可用，任务未发送。清理退出不算场景介入；剩余1次授权保留。 |

第一条模型最终回复称没有直接只读文件工具，按提示停止；这是模型陈述，不能作为独立文件访问审计。相同turn出现Reconnecting 2/5至5/5与responseStreamDisconnected，不据此推断额度、限流或服务端根因。初始超时记录不改写；后续completed观察单列。原README在样例后hash保持。

侧栏实际采用临时client-new-thread行，通过该行entry.conversationId绑定后端thread；不能假设所有行均为local:加UUID。该观察与后续重启的未知条目恢复分别记录。

恢复本轮工作时原PID已不存在，合成README也已被临时目录清理；按原计划恢复同一路径、完全相同的71字节和SHA256。这不证明文件跨会话持续存在。独立配置与模型认证隔离仍未建立；未读取个人历史、数据库或凭据。界面已加载但原项目两种精确身份控件都未出现，原因尚未知；未重建项目、修改信任或使用fallback任务RPC。自有主进程与已记录CLI子进程清理退出已核实。

本批仅登记有限真实观察，不把取消、执行中恢复、文件读取能力或整个功能组改为通过。原全局证据分母、模式排除数与完整分析状态保持。
'''
planned['behavior-interventions.json'] = encode(reader)
planned['behavior-interventions-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE, 'kind': 'approved-owned-behavior-metadata-delivery',
    'metadataOnly': True, 'exactCopies': copies,
    'derived': [{'path': n, **pin(planned[n])} for n in ['behavior-interventions.json', 'behavior-interventions-summary.md']],
    'authorizedModelSubmissions': 2, 'modelSubmissionsObserved': 1, 'remainingModelSubmissions': 1,
    'newModelSubmissionsOn20261023': 0, 'cancelClicks': 0, 'stopRestartScenarioSignals': 0,
    'deliveryRuntimeRunsAdded': 0, 'deliveryModelTasksAdded': 0, 'globalRecordsAdded': 0,
    'fullAnalysisCompleted': False, 'thirdPartyImplementationsPublished': False}
planned['behavior-interventions-provenance.json'] = encode(index)
for relative in planned:
    assert not (OUT / relative).exists(), 'Preserve any prior publication'
for relative, raw in planned.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as f:
        f.write(raw)
    target.chmod(0o444)
print(json.dumps({'status': 'published', 'exactMetadataCopies': len(copies), 'modelSubmissionsObserved': 1,
    'remainingModelSubmissions': 1, 'newModelSubmissionsOn20261023': 0,
    'outputs': [{'path': n, **pin(b)} for n,b in planned.items()]}, ensure_ascii=False))
