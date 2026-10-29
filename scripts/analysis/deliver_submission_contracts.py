"""Deliver the frozen submission-provider catalog and scoped recovery guidance."""
import json
from pathlib import Path

from deliver_frozen_metadata import BASELINE, OUT, WORKSPACE, encode, pin, prepare, write_new

PROFILE = {
    'id': 'submission-host-instance', 'directory': 'submission-host-instance-work',
    'main': 'main.json', 'manifest': 'freeze-manifest.json',
    'manifestHash': 'fc02f3b049e1c9e8c7885fdf503f7904c3e2c89ce044d44dbd66307a26782ebd',
    'pathField': 'path', 'peer': 'independent-review.json',
    'peerMarkdown': 'independent-review.md', 'records': 30,
    'authorCountField': 'checkCount', 'authorChecks': 6165,
    'peerCountField': 'checkCount', 'peerChecks': 881,
    'core': ['main.json', 'evidence.jsonl', 'summary.md', 'validation.json'],
}

MODULES = [
    ('provider-lifecycle', 'renderer provider 生命周期', [2, 3, 4], [0, 9, 10],
     '组件所属 scope、effect 安装与清理；registry 存在性选择分支。',
     '实际 mount、effect 和 scope；不要把 registry 存在性当产品模式。'),
    ('host-rpc-selector', 'host RPC 选择与缓存', [5, 6, 7, 8], [5],
     'primary forHost、client.rpc、缓存、延迟 RPC 及退役条件。',
     '运行选中的分支、注册状态、RPC framework 的能力语义。'),
    ('domain-host-registry', '域 manager 注册与替换', [9, 10, 11, 12, 13, 14], [4, 6, 7, 8, 10],
     'X3 注册、条件 Sii 创建、N3 发布／替换／删除及 disposal。',
     '其他 manager 发布者、ordinary host 注册与实际初始化顺序；X3 没有 forHost。'),
    ('internal-manager-rpc-adapter', '内部 manager 到 RPC 的应用封装', list(range(15, 25)), [1, 3, 11, 12],
     '捕获 manager、MessageChannel、manager／coordinator facade 的原参数转发及重连清理。',
     'nIt／eIt 的来源、接口兼容与实际 port delivery；不要生成第三方实现。'),
    ('host-provided-rpc-adapter', 'host 提供的 RPC registry 适配', [25, 26], [2],
     'ready manager RPC 的 duplicate、watch、lease、connection 替换与清理。',
     '外部 registry endpoint 实现、manager 身份和实际连接；没有 Dfn 身份连接证明。'),
]

SCENARIOS = [
    ('ordinary-submit-instance', '普通提交的实际接收实例', [2, 3, 5, 15, 16, 18, 19, 27, 28],
     '一次获授权的自有提交；能关联同一 scope／host、provider、N3 manager 和 KI 分支。',
     '原参数到 coordinator 的收据与同 turn 完成事件对应。',
     '唯一只读样例已完成并重新打开，但未记录上述实例身份；本场景仍部分未验证。'),
    ('primary-unavailable-registration', 'unavailable 状态与注册条件', [5],
     'provider 存在；分别观察 unavailable 且已登记／未登记的 host。',
     '未登记仍允许 primary 尝试；已登记跳过 primary，随后依据 client／cache 走 fallback。',
     '仅源码条件已确认，未触发这两种实际状态。'),
    ('primary-error-fallback', 'primary 异常后的 fallback', [5, 6, 7, 8],
     'primary 条件成立且 forHost 抛错；分别有 client、有 cache、均无。',
     '异常被吞后按序选择 RPC；延迟能力的拒绝、duplicate 和 dispose 单独记录。',
     '未执行；受控 fixture 的检查不能代替原客户端行为。'),
    ('manager-replacement', '同 host 的 manager 替换与重连', [12, 15, 21, 22, 23, 24],
     '经自有 host 生命周期产生不同 manager／broken callback，不操作个人 host。',
     '旧能力清理、状态迁移、重获 client；stale callback 不覆盖新连接。',
     '未触发；端口送达与重连时序仍待观察。'),
    ('host-registry-ready', 'host registry 分支的 ready 与断开', [4, 25, 26, 28],
     '真实 host 提供 appServerManagers，registry 发出 ready／replacement／断开。',
     'RPC duplicate 和 lease/watch 清理；独立确认 endpoint，不推定 Dfn。',
     '未执行；平台、账户与 endpoint 条件尚未确定。'),
    ('cancel-during-turn', '任务执行中的普通取消', [19, 20, 27, 28],
     '额外合成任务获得授权并已进入执行状态；仅使用产品取消入口。',
     '关联具体 provider、manager 与取消请求；请求发出、后台接受、终态分别验证。',
     '未执行；已有唯一样例授权不覆盖额外任务。'),
    ('interrupted-restart', '执行中断后的重启恢复', [3, 13, 24, 26, 28],
     '额外自有合成任务获得授权；进程归属确认后中断并重启同专用 profile。',
     '旧能力清理、新连接、原 turn 状态和存储恢复对应；不能重发原任务作为恢复。',
     '未执行；已完成任务重新打开的证据不覆盖执行中断。'),
]


def main():
    inputs, provenance = prepare(PROFILE)
    catalog = json.loads(inputs['main.json'])
    outputs = {}
    for name, raw in inputs.items():
        target = Path('raw/submission-host-instance') / name
        outputs[target] = raw
        provenance['copies'].append({'original': str(WORKSPACE / '.analysis-local' /
                                    PROFILE['directory'] / name), 'published': target.as_posix(),
                                    **pin(raw), 'role': 'exact-copy'})
    for target, source in {
        'submission-host-instance.json': 'main.json',
        'submission-host-instance-evidence.jsonl': 'evidence.jsonl',
        'submission-host-instance-validation.json': 'validation.json',
        'submission-host-instance-peer-review.json': 'independent-review.json',
    }.items():
        outputs[Path(target)] = inputs[source]
        provenance['copies'].append({'original': str(WORKSPACE / '.analysis-local' /
                                    PROFILE['directory'] / source), 'published': target,
                                    **pin(inputs[source]), 'role': 'exact-alias'})
    modules = []
    for mid, title, contract_indices, unit_indices, responsibility, unknown in MODULES:
        modules.append({
            'id': mid, 'title': title, 'responsibility': responsibility,
            'confidence': 'inferred', 'verificationStatus': 'maintenance-proposal-not-implemented',
            'sourceContracts': [{'id': catalog['contracts'][i]['id'], 'jsonPointer': f'/contracts/{i}'}
                                for i in contract_indices],
            'sourceUnits': [{'label': catalog['completeUnits'][i]['label'],
                             'jsonPointer': f'/completeUnits/{i}',
                             'sourceRanges': catalog['completeUnits'][i]['sourceRanges']}
                            for i in unit_indices],
            'unresolved': unknown, 'mode': 'unknown', 'runtimeValidated': False,
        })
    scenarios = [{'id': sid, 'title': title, 'trigger': trigger, 'expectedObservation': expected,
                  'currentEvidence': current, 'newRuntimeRun': False,
                  'sourceContracts': [catalog['contracts'][i]['id'] for i in indices]}
                 for sid, title, indices, trigger, expected, current in SCENARIOS]
    guidance = {'baselineId': BASELINE, 'status': 'scoped-recovery-and-behavior-guidance',
                'sourceCatalog': {'path': 'submission-host-instance.json', **pin(inputs['main.json'])},
                'modules': modules, 'scenarios': scenarios,
                'limits': ['5 module proposals and 7 scenarios are new maintenance guidance, not features.',
                           'Static source composition is conditional; actual UI and host endpoint remain unverified.',
                           'No target/package execution or additional model tasks occurred.']}
    outputs[Path('submission-recovery-guidance.json')] = encode(guidance)
    outputs[Path('submission-host-instance-provenance.json')] = encode(provenance)
    for target, raw in outputs.items():
        write_new(OUT / target, raw)
    assert all((OUT / target).read_bytes() == raw for target, raw in outputs.items())
    print(json.dumps({'status': 'delivered', 'records': 30, 'outputs': len(outputs),
                      'moduleProposals': len(modules), 'behaviorScenarios': len(scenarios),
                      'runtimeRunsAdded': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
