"""Integrate the 2026-10-23 reader additions without rewriting frozen evidence."""
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
PREFIX = 'raw/analysis-resume-20261023'
def pin(b):
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
def encode(v):
    return (json.dumps(v, ensure_ascii=False, indent=2)+'\n').encode()
names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md',
         'dependency-import-decisions.md', 'behavior-checks.md']
before = {n: (OUT/n).read_bytes() for n in names}
readme_before = (ROOT/'README.md').read_bytes()
assert pin(before['report.md']) == {'bytes': 50004, 'sha256': '5c224e508e0e8ccaeaa52f3ef75e42835be2c186c17e1a46499cc5e92dfeb842'}
assert pin(before['analysis-state.json']) == {'bytes': 139386, 'sha256': '630edd2c70e76f012b6b665f6ce117cf2240f99a0fae4cb863e93b6fed2b8778'}
old = json.loads(before['analysis-state.json'])
assert old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
patch, _, artifacts = build_context(OUT, BASELINE)
new_keys = ['sourceContextBehaviorObservations', 'modePublisherInstantiation', 'behaviorInterventions']
assert len(patch) == len(PROFILES) == 18
assert all(k not in old for k in new_keys)
assert all(old[k] == v for k,v in patch.items() if k not in new_keys)
state = {**old, **{k: patch[k] for k in new_keys}}
assert all(state[k] == v for k,v in old.items())
notes = '\n\n'.join(p[4] for p in PROFILES if p[0] in new_keys)
report = before['report.md'].decode()
marker = '[完成标准审计](criteria-audit.md)'
assert report.count(marker) == 1
report = report.replace(marker, notes+'\n\n'+marker)
old_row = '| 运行观察记录 | 30 条有限 UI／项目设置观察；专用草稿重启后保留；一个授权 README 桌面任务完成 | 项目 API 设置与 UI 创建分别判断；已完成样例重启后可重新打开；其他任务路径、失败、取消与执行中断恢复尚未验证 |'
new_row = old_row.replace('运行观察记录', '首批运行观察记录') + '\n| 后续获授权样例 | 本组2次授权已用1次、余1次；同turn稍后UI为completed；2026-10-23新增提交0 | 取消点击0；原合成项目两个精确控件均0，第二条未发送；执行中取消与重启仍未测试 |'
assert report.count(old_row) == 1
report = report.replace(old_row, new_row)
planned = {'report.md': report.encode(), 'analysis-state.json': encode(state)}
supplements = {
    'implementation-plan.md': '''

## 2026-10-23补充的维护依据

[MODE publisher来源](mode-publisher-instantiation.md)补上旧Storage46快照未定位的选定第二参数：Rkc内三次调用使用同一局部publisher，并接到renderer消息发送候选。bootstrap seed接到YRt的localStorage读取；这不证明native接收器或耐久写入。维护时分别保留本地状态／seed读取、publisher消息适配、真实后端与生命周期职责，不能把整个偏好系统简化为localStorage。Rkc真实caller、gS实际provider/store及运行投递仍是前置调查。

[8个source-context候选场景](source-context-behavior-observations-summary.md)补充[维护adapter建议](source-context-module-proposal.md)的本机回归参照：同步return/throw、Promise身份／结算、嵌套恢复和异步继承。只执行保存的36字节wrapper与新建Node22 builtin实例；目标runtime、实际rX、client/source与native回调仍须单独验收。没有复制Node实现或新增npm包。

[获授权行为样例](behavior-interventions-summary.md)要求把精确thread/turn、临时侧栏行与真实执行状态分开保存。临时client-new-thread行通过其自身entry.conversationId绑定，不能硬编码local:UUID。当前取消／执行中恢复均未通过；余下1次任务必须先恢复已批准的项目条件，或获得明确的场景范围调整。
''',
    'dependency-import-decisions.md': '''

[source-context候选观察](source-context-behavior-observations-summary.md)在本机Node22 builtin AsyncLocalStorage上实际执行8个局部场景。它支持该候选adapter的局部语义，不把内置API变成需恢复的第三方源码，也不证明Owl目标runtime兼容。选定builtin、第一方wrapper及真实运行时的取得／ABI仍分别登记。
''',
    'behavior-checks.md': '''

## 后续两条获授权任务的进度

[场景结果](behavior-interventions-summary.md)与[精确输入／receipt索引](behavior-interventions-provenance.json)保存本组2次授权：1次已提交、1次未用。第一条60秒原观察超时，稍后同一thread/turn的UI为completed；停止按钮关联不足，未点击，取消未测试。模型称没有直接只读文件工具；Reconnect错误与模型陈述都不替代独立工具审计。

2026-10-23只恢复并核实冻结应用和CLI，README按原71字节恢复。UI已加载，原项目名与ID控件均0；未发送第二条、未做场景SIGTERM／重启。随后清理自有进程并核实退出，不能计为执行中恢复。现有计划禁止另建项目，余下1次授权保留；控件缺失的存储／服务原因尚未确定。

## source-context的8个本机候选场景

[候选观察](source-context-behavior-observations-summary.md)一条实际Node22命令执行1个保存wrapper、36字节、8场景。每场景使用新的本机builtin ALS，覆盖同步返回与抛错、Promise身份与完成／拒绝、异步继承、嵌套恢复。没有运行实际目标rX或Node24；不能升级原9/16/25静态合同、真实client/source、native回调或完整fetch结论。

[MODE publisher的23条来源](mode-publisher-instantiation.md)仍属静态来源闭合，13场景未执行；旧Storage46与MODE26的运行状态不改写。
''',
}
for name, extra in supplements.items():
    assert extra not in before[name].decode()
    planned[name] = before[name] + extra.encode()
behavior = planned['behavior-checks.md'].decode()
behavior = behavior.replace('## 唯一获授权的桌面样例任务', '## 首个单独获授权的桌面样例任务')
behavior = behavior.replace('这是有限 UI 观察、一次未提交草稿重启验证及一个获授权的只读桌面任务，不能代表整个功能组通过。',
    '首批记录包括有限UI观察、未提交草稿重启及首个获授权只读任务；后续批次另列，不能代表整个功能组通过。')
behavior = behavior.replace('仅按用户明确授权提交了一个读取新建合成 README 的模型任务；',
    '首批按用户明确授权提交了一个读取新建合成README的模型任务；')
planned['behavior-checks.md'] = behavior.encode()
gap_extra = '''

2026-10-23更新：[MODE publisher23条静态来源](mode-publisher-instantiation.md)关闭选定Rkc内第二参数与YRt seed读取的来源关联，旧46条的未知边界作为历史快照保留。真实bootstrap caller、gS provider/store、native接收器／落盘、模式值域仍未知。[source-context8候选场景](source-context-behavior-observations-summary.md)只补本机Node22局部语义，目标实例与完整client未验收。

[行为样例](behavior-interventions-summary.md)本组已用1/2；取消0次点击、执行中恢复0次介入。第二条因原项目名称／ID控件均0而未发送，原因尚未知，剩余1次保留。仅此运行场景的前置条件不可用，其他静态分析继续。恢复README同字节不算持续存储证明；自有应用清理已核实。
'''
gaps = before['gaps.md'].decode()
at = gaps.index('\n| ')
planned['gaps.md'] = (gaps[:at]+gap_extra+gaps[at:]).encode()
readme = readme_before.decode().replace('实际行为核对与唯一授权样例', '实际行为核对与授权样例')
readme += '\n- [source-context的8个本机候选场景](analysis/'+BASELINE+'/source-context-behavior-observations-summary.md)\n- [MODE publisher实例化来源](analysis/'+BASELINE+'/mode-publisher-instantiation.md)\n- [后续两条获授权样例的实际进度](analysis/'+BASELINE+'/behavior-interventions-summary.md)\n'
snapshots = {PREFIX+'/reader-before-'+name: raw for name,raw in before.items()}
snapshots[PREFIX+'/reader-before-README.md'] = readme_before
for name, raw in {**snapshots, **planned}.items():
    target = OUT/name
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    if name in before:
        assert target.read_bytes() == before[name]
    else:
        assert not target.exists()
for name, raw in snapshots.items():
    target = OUT/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    target.chmod(0o444)
for name, raw in planned.items():
    target = OUT/name
    temp = target.with_name('.resume-'+target.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(target.stat().st_mode & 0o777)
    temp.replace(target)
assert (ROOT/'README.md').read_bytes() == readme_before
temp = ROOT/'.resume-README.md'
assert not temp.exists()
temp.write_text(readme)
temp.chmod((ROOT/'README.md').stat().st_mode & 0o777)
temp.replace(ROOT/'README.md')
print(json.dumps({'status':'integrated', 'companionIndices':len(patch), 'newStateFields':new_keys,
    'oldStateKeysPreserved':len(old), 'oldStateValuesPreserved':True, 'selectedArtifactPaths':len(artifacts),
    'outputs':{name:pin(raw) for name,raw in planned.items()}, 'readme':pin(readme.encode()),
    'snapshots':[{'path':name,**pin(raw)} for name,raw in snapshots.items()],
    'globalRecordsAdded':0, 'newModelSubmissionsOn20261023':0, 'fullAnalysisCompleted':False}, ensure_ascii=False))
