"""Publish bounded first-party policy metadata and preserve prior reader state."""
import datetime
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/main-persistence-policy-work'
SELECTED = WORK / 'selected-source-01'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


data = json.loads((SELECTED / 'contracts.json').read_bytes())
assert data['selectedSourceBytes'] == 2486 and len(data['selectedUnits']) == 8
assert data['confidenceCounts'] == {'confirmed': 20, 'inferred': 2} and len(data['records']) == 22
assert data['syntaxReceipt']['exitCode'] == 0 and data['targetCodeExecuted'] is False
assert len(data['unexecutedScenarios']) == 13 and not any(x['executed'] for x in data['unexecutedScenarios'])
assert data['globalRecordsAdded'] == data['modelSubmissionsAdded'] == 0
receipt = json.loads((WORK / 'attempts/analyze-01/receipt.json').read_bytes())
assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']

planned = {}
copies = []
selected = [('author/contracts.json', SELECTED / 'contracts.json', 'metadata_only'),
            ('author/evidence.jsonl', SELECTED / 'evidence.jsonl', 'metadata_only'),
            ('author/syntax-receipt.json', SELECTED / 'syntax-receipt.json', 'metadata_only')]
for name in ['receipt.json', 'stdout.txt', 'stderr.txt']:
    selected.append(('analysis-capture/' + name, WORK / 'attempts/analyze-01' / name, 'execution_metadata'))
selected.append(('analysis-tool/analyze.py', WORK / 'attempts/analyze-01/analyze.py', 'analysis_tool_source'))
for name, source, kind in selected:
    target = 'raw/main-persistence-policy/' + name
    raw = source.read_bytes()
    planned[target] = raw
    copies.append({'original': str(source), 'outputPath': target, **pin(raw), 'kind': kind})

planned['main-persistence-policy.json'] = encode(data)
summary = '''# 持久化键策略、记录合并与窗口广播

本批补充先前REA/AST接收候选，从同一冻结main选取8个完整范围，共2486字节，形成20条来源事实和2条推断，另列13个未执行场景。新范围用唯一文本边界定位，并作一次Node语法检查；没有执行目标函数、重跑REA或独立解析整个Program的作用域绑定。见[结构化契约](main-persistence-policy.json)及[来源索引](main-persistence-policy-provenance.json)。

TY测试thread-browser-tabs-v1:与thread-tab-routes-v1:两个前缀。pR对其他键或空incoming直接放行；对于cloud-aeon-sidebar-cache-v1且两次schema解析成功、身份一致时，检查revision、刷新时间或removalBaseRevision。这是特定缓存键的接纳条件，不能写成通用相等比较，也不能由名称决定模式归属。schema命名空间及比较器实现／版本仍待调查。

hR先取得解析后的记录或空对象，再按expectedValue条件、delete属性存在性、createOnly／updateOnly和时间戳比较处理条目。delete:false仍因属性存在而进入删除分支。随后按数值下限、条目数和反向枚举的JSON字节预算裁剪；超预算条目删除后不增加累计预算，后续较小条目仍可能保留。普通更新中的先delete再defineProperty可能改变非索引键的枚举顺序，因此不能随意替换为对象赋值。未执行schema／比较器，不能假设safeParse保留原对象身份或把比较器当作某个已确认包。

广播把undefined编码为value:null、deleted:true；普通null仍是deleted:false。非标签页键或任何删除发给所有窗口；标签页键的非删除只查来源webContents所在窗口，缺失时该分支不发送。delete方法筛选key in state后浅拷贝、删除、set，再逐键广播；筛选包含继承属性且不去重。reset先set空状态，再发全窗口sync，所选消息没有owner写入标志。上述方法内部没有证明实际sender送达或存储耐久性。

维护建议将第一方记录合并、缓存接纳与窗口消息适配分开，保留schema、比较器、window manager和globalState依赖接口；拟议路径及8范围映射见契约。未生成客户端源码或复制第三方实现。原Program词法绑定、真实调用实例、owner/filter、持久后端、MODE bootstrap/store及完整功能分母继续待查；本批不把停止／重启的interrupted观察扩大为恢复执行证明，也不增加模型提交。
'''
planned['main-persistence-policy-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE,
         'kind': 'bounded-main-persistence-policy-source-supplement',
         'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'exactCopies': copies,
         'derived': [{'path': n, **pin(planned[n])} for n in ['main-persistence-policy.json', 'main-persistence-policy-summary.md']],
         'selectedUnits': 8, 'selectedSourceBytes': 2486, 'confidenceCounts': data['confidenceCounts'],
         'unexecutedScenarios': 13, 'targetCodeExecuted': False, 'modelSubmissionsAdded': 0,
         'newReaRuns': 0, 'wholeProgramParses': 0, 'globalRecordsAdded': 0,
         'fullAnalysisCompleted': False, 'thirdPartyImplementationsPublished': False,
         'scope': 'Static facts are conditional on the selected source units. Caller/lexical instance joins remain inferred; syntax checking does not prove execution or delivery.'}
planned['main-persistence-policy-provenance.json'] = encode(index)
for name in planned:
    assert not (OUT / name).exists()

names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md',
         'dependency-import-decisions.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in names}
old = json.loads(before['analysis-state.json'])
assert len(old) == 86 and old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
assert old['latestBehaviorAuthorizationState']['groupConsumed'] == 2
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0
assert 'mainPersistencePolicy' not in old
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)

patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 21
assert all(old[k] == v for k, v in patch.items() if k != 'mainPersistencePolicy')
state = {**old, 'mainPersistencePolicy': patch['mainPersistencePolicy']}
assert all(state[k] == v for k, v in old.items())
note = next(x[4] for x in PROFILES if x[0] == 'mainPersistencePolicy')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(),
           'analysis-state.json': encode(state)}
supplements = {
    'implementation-plan.md': '\n\n[持久化键策略与广播](main-persistence-policy-summary.md)提供8个所选范围到3个inferred职责路径的映射：窗口消息适配、记录条件更新与裁剪、特定sidebar缓存接纳。恢复时保留delete属性存在性、own检查、时间戳比较、删除再定义产生的顺序及反向字节预算；schema／比较器通过依赖接口接入，不能复制未确认的第三方实现。13个场景尚未执行；路径为维护建议，实际绑定和globalState后端没有闭合。\n',
    'gaps.md': '\n\n[持久化策略补充](main-persistence-policy-summary.md)现已保存TY/pR/hR及广播、delete/reset的完整选定定义；此前“定义未知”属于各旧批快照。本批22条记录仍不完成原Program词法绑定、schema n或U.default实现／版本、真实window manager与globalState实例、耐久写入和MODE store/provider。13场景未执行。模型授权当前仍2/2已用、余0，取消未测，完整功能分母和模式排除均未改变。\n',
    'dependency-import-decisions.md': '\n\n[持久化记录与键策略](main-persistence-policy-summary.md)只提取第一方控制契约；n.* schema API和U.default比较器仍是独立依赖边界，本批没有确认其版本／实现或生成库代码。不要因safeParse或default调用外形就把普通包替换视为等价，也不要将cache键名称当作ChatGPT专属判据。\n',
    'behavior-checks.md': '\n\n[持久化策略13场景](main-persistence-policy-summary.md)均未执行；本批唯一Node命令是8选定单位的语法检查，未运行原函数、窗口发送器或存储。停止／重启既有样例只观察到原turn为interrupted，不能拿来验证这些条件合并／广播分支或耐久写入。本组模型预算仍余0。\n',
}
for name, extra in supplements.items():
    changes[name] = before[name] + extra.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [持久化键策略、记录合并与窗口广播](analysis/' + BASELINE + '/main-persistence-policy-summary.md)\n').encode()
snapshots = {'raw/main-persistence-policy/reader-before/' + n: raw for n, raw in before.items()}
snapshots['raw/main-persistence-policy/reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.main-persistence-policy-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.main-persistence-policy-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
                  'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True,
                  'selectedArtifactsBeforeOwnCapture': len(artifacts),
                  'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
                  'outputs': {n: pin(raw) for n, raw in changes.items()},
                  'modelSubmissionsAdded': 0, 'targetCodeExecuted': False, 'fullAnalysisCompleted': False}))
