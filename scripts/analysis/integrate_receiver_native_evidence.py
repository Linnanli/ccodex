"""Append the reviewed receiver-source and independently built native evidence."""
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md',
         'dependency-import-decisions.md', 'behavior-checks.md']
before = {name: (OUT / name).read_bytes() for name in names}
readme_before = (ROOT / 'README.md').read_bytes()
assert pin(before['report.md']) == {'bytes': 46855, 'sha256': '104e7b99807902ff7b7177c9bb05886706d4e75fbb4c95028869119738f820df'}
assert pin(before['analysis-state.json']) == {'bytes': 135994, 'sha256': '6d880f12692afc270982077d9c65444320649d357cbaeec54fe5347ae0434c08'}
old_state = json.loads(before['analysis-state.json'])
assert old_state['fullAnalysisCompleted'] is False and old_state['featureDenominatorEstablished'] is False
patch, _, artifacts = build_context(OUT, BASELINE)
new_keys = ['settingsConfigReceiverOrigin', 'objcIndependentBuild']
assert len(patch) == 11 and all(key not in old_state for key in new_keys)
assert all(old_state[key] == value for key, value in patch.items() if key not in new_keys)
new_state = {**old_state, **{key: patch[key] for key in new_keys}}
assert all(new_state[key] == value for key, value in old_state.items())

notes = '\n\n'.join(profile[4] for profile in PROFILES if profile[0] in new_keys)
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1 and notes not in report
planned = {'report.md': report.replace(marker, notes + '\n\n' + marker).encode(),
           'analysis-state.json': encode(new_state)}
supplements = {
    'implementation-plan.md': '\n[配置接收链来源](settings-config-receiver-origin-summary.md)为项目文件读取／环境配置保存提出可维护的分层依据：renderer分发、主进程对象注入、host client操作分别恢复。非项目KI/rpc仍需单独调查，不能用项目桥替代。[objc-js独立构建](objc-independent-build-summary.md)给出官方依赖加SDK ffi配方的本机构建候选；正式方案需补齐完整package build输入、固定Node headers及libffi来源，核对实际ARC编译标志，再在目标Owl／架构上验证ABI和回调。一次Node22模块加载不是完整客户端构建验收。\n',
    'dependency-import-decisions.md': '\n[objc-js独立构建结果](objc-independent-build-summary.md)将原配方的ffi.h失败与SDK ffi候选的实际成功分别登记。27个native源文件未改；配方变化仅涉及ffi include/link。可维护候选是固定官方包加独立构建配方，而非生成库实现副本。Node header缓存来源、系统libffi可复现来源、实际未带-fobjc-arc的命令、Owl Node24和ARM均须继续验证；未证明可直接替换随包binary。\n',
    'behavior-checks.md': '\n## 独立源码原生模块构建与加载\n\n[objc-js构建记录](objc-independent-build-summary.md)保存官方1.5.0源码的实际独立构建：原配方configure成功、native build因ffi.h缺失失败；仅调整SDK ffi include和-lffi的候选配方configure/build成功。产物为x86_64，在Node22.23.2/x64唯一一次加载后核对10个导出均为函数。模块初始化确实执行，加载后导出原生方法调用数为0；原客户端／随包prebuilt运行新增0，模型任务新增0。\n\n作者实际命令、stdio、时间和退出码保留，独立65项metadata／82项构建日志检查没有重编译或重载。这个观察仅验证该本机构建与初始化；Owl Node24、ARM、ABI、回调／RunLoop／事件、完整package build和干净环境可复现仍未验证。原22条静态合同与15场景、已有桌面样例及重启记录保持各自范围。\n\n[配置接收链来源](settings-config-receiver-origin-summary.md)另属静态源绑定分析，未执行read-file/config-save、非项目RPC或实际文件写入；其取消／错误／持久化场景仍待行为验证。\n',
}
for name, extra in supplements.items():
    assert extra not in before[name].decode()
    planned[name] = before[name] + extra.encode()
gap_extra = '\n[配置接收链来源](settings-config-receiver-origin-summary.md)闭合选定构造函数中的$L／Ude／MMe绑定，实际实例与di／U实现、非项目RPC、client/source实参、I/O取消和持久化仍待调查。[objc-js独立构建](objc-independent-build-summary.md)将GAP-07推进到本机Node22 x64候选构建及一次模块初始化；GAP-08仍需干净输入、完整build脚本、header／libffi来源、实际ARC标志、Owl Node24／ARM与ABI和回调验证。\n'
gaps = before['gaps.md'].decode()
table_at = gaps.index('\n| ')
planned['gaps.md'] = (gaps[:table_at] + gap_extra + gaps[table_at:]).encode()
readme_extra = '\n- [项目配置保存的主进程接收链](analysis/' + BASELINE + '/settings-config-receiver-origin-summary.md)\n- [objc-js独立源码构建与有限加载结果](analysis/' + BASELINE + '/objc-independent-build-summary.md)\n'
assert readme_extra not in readme_before.decode()
readme_after = readme_before + readme_extra.encode()

snapshots = {'raw/receiver-native-integration/reader-before-' + name: raw for name, raw in before.items()}
snapshots['raw/receiver-native-integration/reader-before-README.md'] = readme_before
for relative, raw in {**snapshots, **planned}.items():
    target = OUT / relative
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    if relative in before:
        assert target.read_bytes() == before[relative]
    else:
        assert not target.exists() or target.read_bytes() == raw
assert (ROOT / 'README.md').read_bytes() == readme_before
for relative, raw in snapshots.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)
for relative, raw in planned.items():
    target = OUT / relative
    temporary = target.with_name('.receiver-native-' + target.name)
    assert not temporary.exists()
    temporary.write_bytes(raw)
    temporary.chmod(target.stat().st_mode & 0o777)
    temporary.replace(target)
    assert target.read_bytes() == raw
temporary = ROOT / '.receiver-native-README.md'
assert not temporary.exists()
temporary.write_bytes(readme_after)
temporary.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temporary.replace(ROOT / 'README.md')
print(json.dumps({'status': 'integrated', 'companionIndices': 11, 'newStateFields': new_keys,
                  'oldStateValuesPreserved': True,
                  'snapshots': {name: pin(raw) for name, raw in snapshots.items()},
                  'outputs': {name: pin(raw) for name, raw in planned.items()},
                  'readme': pin(readme_after), 'selectedArtifactPaths': len(artifacts),
                  'globalRecordsAdded': 0, 'originalClientRunsAdded': 0,
                  'nativeModuleLoadsObserved': 1, 'nativeMethodsInvokedAfterModuleInit': 0,
                  'deliveryRuntimeRunsAdded': 0, 'additionalModelTasks': 0,
                  'fullAnalysisCompleted': False}))
