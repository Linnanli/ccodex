"""Publish a bounded SD-02 decision, using saved contracts rather than new probes."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/runtime-adoption-matrix-work"
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"
NOW = datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    path = Path(path)
    if not path.is_absolute():
        path = OUT / path
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": digest(data)}


def read(name):
    return json.loads((OUT / name).read_text())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def publish(name, data):
    path = OUT / name
    with path.open("xb") as handle:
        handle.write(data)
    path.chmod(0o444)
    return pin(path)


def ref(name, pointer):
    return {**pin(name), "jsonPointer": pointer}


def main():
    output_names = ["runtime-adoption-primary-review-v1.json", "runtime-adoption-matrix-v1.json",
                    "runtime-adoption-matrix-v1-evidence.jsonl", "runtime-adoption-matrix-v1.md",
                    "association-overlap-evidence-correction-v1.jsonl", "association-overlap-evidence-correction-v1.json"]
    assert not any((OUT / name).exists() for name in output_names), "immutable output already exists"
    names = [
        "runtime-surface-disposition.json", "runtime-capability-decisions.json",
        "runtime-distribution.json", "runtime-node-version.json",
        "runtime-native-accessors.json", "public-runtime-comparison.json",
        "browser-ownership-contracts.json", "browser-clone-route-qualification.json",
        "public-history-duplicate-comparison.json", "native-browser-settings-comparison.json",
        "runtime-feature-policy-contracts.json", "build-input-dispositions-v1.json",
        "dependency-investigation-actions-v1.json", "objc-independent-build.json",
        "implementation-milestones-v9.json", "restoration-coverage-v18.json",
        "feature-scope-v27.json", "feature-scope-v24-scenarios.json",
        "association-overlap-decisions-v1-evidence.jsonl",
    ]
    inputs = [pin(n) for n in names] + [pin(ROOT / "docs/reverse-engineering/analysis-plan.md"), pin(Path(__file__))]
    state_path = OUT / "analysis-state.json"
    state = json.loads(state_path.read_text())
    WORK.mkdir(parents=True, exist_ok=True)
    for name in ["analysis-state.json", "report.md", "gaps.md"]:
        with (WORK / (name + ".before")).open("xb") as handle:
            handle.write((OUT / name).read_bytes())

    commit = "e0127e99aeaa66bb580538fc7409831b5248cccb"
    commit_url = "https://github.com/electron/electron/commit/" + commit
    review = {
        "baselineId": BASE, "recordedAtUtc": NOW,
        "kind": "authored-primary-source-review; not an upstream byte snapshot",
        "hashMeaning": "A local hash identifies this review record only. No upstream source archive or binary was acquired by this review.",
        "observations": [
            {"id": "PUB-01", "url": "https://github.com/electron/electron/releases/tag/v42.3.0",
             "supportingUrl": commit_url, "locator": "release commit link; commit full URL",
             "finding": "The v42.3.0 release links to the full Electron commit recorded below.",
             "sourceCommit": commit, "relationToOwl": "unproven", "checkoutAcquired": False},
            {"id": "PUB-02", "url": commit_url, "locator": "DEPS diff, context lines 6-7",
             "finding": "The selected commit shows node_version v24.15.0. This is source metadata, not a measured Node version of a running Electron binary.",
             "nodeVersionInDeps": "24.15.0"},
            {"id": "PUB-03", "url": "https://nodejs.org/download/release/v24.19.0/docs/api/permissions.html",
             "locator": "Permission Model and Permission Model constraints",
             "finding": "The fixed document enumerates filesystem, process, worker, addon, WASI and inspector restrictions. It does not document the required scoped IPC and network policy."},
            {"id": "PUB-04", "url": "https://nodejs.org/download/release/v24.19.0/docs/api/cli.html",
             "locator": "full rendered document searches for --allow-ipc and --allow-net",
             "finding": "Neither flag name was found in this fixed CLI document. This is a bounded documentation observation, not proof about all Node versions or forks."},
            {"id": "PUB-05", "url": "https://raw.githubusercontent.com/sparkle-project/Sparkle/2.9.1/Package.swift",
             "locator": "version/tag/checksum declarations and targets.binaryTarget",
             "finding": "The Sparkle 2.9.1 Swift package consumes a binary target; using this package is a precompiled dependency route, not evidence of building Sparkle from source.",
             "version": "2.9.1", "binaryTargetChecksum": "9fec2b888e6e2940b1bfbd5d3d010b9f67076b52170923549095cbb74132403b"},
        ],
        "earlierAcquisitionLimits": [
            {"url": "https://github.com/electron/electron/tree/v42.3.0", "result": "web cache miss in preceding investigation; not a repository absence finding"},
            {"url": "https://github.com/electron/electron/blob/" + commit + "/docs/development/build-instructions-macos.md", "result": "web cache miss in preceding investigation; build recipe not acquired"},
            {"url": "https://github.com/electron/electron/blob/" + commit + "/docs/development/build-instructions-gn.md", "result": "web cache miss in preceding investigation; build recipe not acquired"},
        ],
    }
    review_pin = publish("runtime-adoption-primary-review-v1.json", encode(review))
    surface = read("runtime-surface-disposition.json")
    capability = read("runtime-capability-decisions.json")
    checked_spans = []
    for fact in surface["facts"] + capability["facts"]:
        span = fact.get("byteRange", fact.get("locator"))
        if not span or "start" not in span:
            continue
        source = FROZEN / fact["sourcePath"].removeprefix("app.asar/")
        raw = source.read_bytes()
        assert digest(raw) == fact["sourceHash"], fact["id"]
        selected = raw[span["start"]:span["endExclusive"]]
        assert len(selected) == span["endExclusive"] - span["start"]
        if fact.get("spanHash"):
            assert digest(selected) == fact["spanHash"], fact["id"]
        checked_spans.append({"factId": fact["id"], "sourcePath": fact["sourcePath"],
                              "sourceHash": fact["sourceHash"], "byteRange": span,
                              "spanHash": digest(selected)})

    # Each tuple is an authored maintenance decision, not a recovered source module.
    specs = [
        ("RAM-01", "原生菜单 tracking", [0, 3], "native-menu-tracking",
         "保留 menu-open/begin 与 menu-close/destroy/end 的成对生命周期。",
         "独立平台菜单桥或选定运行时提供 tracking；公开 popup 的存在不足以采用。",
         "菜单开启、关闭和销毁的原生时序及 tracking 副作用；取得对应实现源码或运行时扩展。",
         "在菜单关闭、窗口销毁和重复清理下对照基线时序，验证没有遗留 tracking。", "bounded-contract-available"),
        ("RAM-02", "音频 measurement", [1, 2], "measurement",
         "保留具名 histogram 配置、ready/unsupported/unavailable 和计数不连续分支。",
         "独立运行时 telemetry provider；进程 metrics 不作为音频 histogram 数据源。",
         "具名 histogram 的真实生产者、数据格式及调用消费者闭包；底层采集实现尚未取得。",
         "对照配置、采样、计数重置、unsupported 与异常分支；真实采样结果需要独立数据源。", "partial-consumer-and-provider-contract"),
        ("RAM-03", "运行时特性与 Windows policy", [4, 6, 7], "runtime-feature-policy",
         "沿用已分析的两键 allowlist、boolean 合并、成功后缓存、reset、认证 owner/generation 和特定 unsupported 错误映射。",
         "以独立接口调用支持相同特性的引擎或受维护运行时扩展；gate SDK/RPC 仍通过依赖引入。",
         "两键的原生效果、默认值与可逆性；supported-feature registry；Windows policy fallback 的实际清理效果。",
         "在目标平台核对 set/reset、账号切换、过期 generation、unsupported 与真实引擎效果。", "bounded-first-party-contract-available"),
        ("RAM-04", "Chrome 调试页策略", [5], "chrome-page-policy",
         "保留设置写入、副作用、启动路径与 allowDebugMenu 组合条件；不按名称排除。",
         "由有对应特权页和开关语义的运行时提供；普通页面路由不是替代实现。",
         "启动 owner 的完整条件及底层开关作用范围；选定运行时的等效页面/策略 provider。",
         "分别检查启动与设置切换，以及不同 build flavor 下允许和拒绝的页面范围。", "partial-startup-contract"),
        ("RAM-05", "Task Manager", [8], "diagnostics/task-manager",
         "由第一方承担菜单、能力声明、错误传播和独立诊断 UI 的集成；保留顶层 bootstrap 前提。",
         "独立诊断 UI 加真实进程数据 provider 是候选；getAppMetrics 仅作为数据原语，不能单独验收。",
         "基线实际字段、动作、刷新/关闭语义和独立 UI 实现；不以空函数满足 guard。",
         "菜单打开真实界面，核对进程数据、动作、刷新、关闭及错误；不把函数存在当作通过。", "bounded-entry-contract-available"),
        ("RAM-06", "窗口平台能力", [9, 10, 11], "window-capabilities",
         "保留 always-on-top 的 false/null 发布及 Windows GPU/backdrop 判定；input-shape 先补 owner。",
         "分别由平台/运行时能力探测器提供真实结果；三个能力不合并成恒真的通用 predicate。",
         "input-shape 实际功能消费者与平台条件仍需内部源码追踪；三项原生支持条件和实现 provider 未验证。",
         "逐平台验证不支持结果、状态发布、GPU 条件和操作副作用；补齐 input-shape 消费者后确定其验收。", "partial-input-shape-owner-unresolved"),
        ("RAM-07", "历史滑动导航", [12], "history-swipe",
         "保留 primary 窗口注册、darwin 限制、overlayBounds/Color 空值转换及状态保存。",
         "macOS 原生窗口/手势桥或运行时扩展；普通 back/forward 调用不足以覆盖 overlay 协议。",
         "原生手势、overlay 与导航状态同步的独立 provider 及目标 SDK/headers。",
         "检查非 primary 窗口、非 darwin、空 overlay、导航更新和销毁时的手势表现。", "bounded-caller-contract-available"),
        ("RAM-08", "通知授权状态", [13], "notifications/authorization",
         "保留 authorization 不可用返回 null，granted/denied/not-determined 的精确映射和错误传播。",
         "独立 OS 通知授权查询桥；公开通知展示接口不证明能读取同一授权状态。",
         "目标平台授权 API、bridge 源码与实际状态映射；不从能显示通知推导授权结果。",
         "以合成通知场景核对全部授权状态、不可用和异常，不更改个人通知设置。", "bounded-mapping-contract-available"),
        ("RAM-09", "屏幕光标能力", [14], "cursor-capabilities",
         "保留能力为 true 才建立 controller 的工厂条件。",
         "平台坐标/权限能力探测器；getCursorScreenPoint 只是坐标 getter。",
         "平台能力条件与独立探测 provider；当前 getter 读数不构成跨平台证明。",
         "核对支持/不支持时 controller 建立与清理，以及平台坐标行为。", "bounded-factory-contract-available"),
        ("RAM-10", "浏览器权限 prompt", [15], "browser-permissions",
         "保留 app partition、browser permission handling、prompt 委托、request/check 默认拒绝和相关导航/下载策略。",
         "能提供 prompt 协议及权限状态服务的独立运行时/引擎扩展，或经过行为验证的服务适配。",
         "prompt 参数、响应及生命周期和浏览器服务后效；公开 request handler 不构成同协议实现。",
         "在独立 partition 验证允许/拒绝/关闭、重复请求、过期回复和默认拒绝及相关策略。", "partial-native-prompt-contract"),
        ("RAM-11", "系统字体枚举", [16], "fonts",
         "第一方承担直接查询和结果传递；不凭空填充字体列表或静默兜底。",
         "独立 OS 字体枚举 bridge 或运行时扩展。",
         "返回值格式、字体集合/本地化行为及对应 OS provider 源码和目标 SDK。",
         "在目标平台对照实际枚举结果、排序/命名和失败传播。", "bounded-call-contract-available"),
        ("RAM-12", "浏览器 ownership、adoption 和 clone", [], "browser-ownership",
         "主进程 owner manager 管理 route admission、generation、session/preload、pending 与销毁；可保留同一 live view 的移动方案。",
         "lease 消费/失效和 live clone 仍需引擎 provider 或可证明行为等价的所有权协议；不是生成非空 lease 字符串。",
         "可独立构建的 clone/adoption 实现；原 live clone 的实际历史/页面状态语义；同一 view 移动不能证明复制能力。",
         "核对 window.open、live clone 与 cold restore 各自路径、拒绝/销毁、重复消费；记录历史、表单和堆状态，不假定它们相同。", "ownership-preparation-available; clone-provider-unresolved"),
        ("RAM-13", "受限 Node 网络与 scoped IPC", [], "process-policy",
         "保留端点构造、restricted/unrestricted 分流、relaunch 参数/环境和 open-event 重放；设计独立 broker/权限执行接口。",
         "实际执行限制的运行时扩展或独立进程/OS 边界；普通 Node permission flags 不能作为已满足的 provider。",
         "能拒绝通用网络和越界 IPC、允许声明端点的执行机制、平台策略与可构建实现；不是 permission.has 的返回值。",
         "允许端点正例、网络及越界 IPC 负例和重启重放实际通过；保留旧探针仅覆盖本地 TCP/Unix socket 的范围。", "bounded-policy-contract-available; enforcement-provider-unresolved"),
        ("RAM-14", "普通更新与 managed relaunch", [], "updates",
         "普通 transport 与 nullable managed-policy 分离；保留 schema、策略监听、notice/deadline/重试与初始化失败语义。",
         "Sparkle 是 macOS 更新依赖候选；其 SPM 是预编译路线。managed policy 需独立 provider，运行时 linkedBinding 不是 npm 包。",
         "独立签名/更新 feed/安装配置、平台 updater 以及 managed-policy 事件/注销；Sparkle 来源不覆盖 Owl binding。",
         "分别验证 null policy、有效策略、getter 错误、普通安装和强制安装；source-build 与 precompiled 路线分别标明。", "bounded-consumer-contract-available; provider-unresolved"),
        ("RAM-15", "四类特权浏览器设置", [], "browser-settings",
         "保留 contactInfo/passwordManager/extensions/siteSettings，kind/host/capability、partition、mountId、theme、导航和过期响应清理。",
         "独立运行时提供 WebUI/backing services，或独立设置 UI 加等价服务适配；原生服务不能由页面占位补齐。",
         "四类页面的底层数据/服务行为、独立 provider 与构建来源；固定 stock guest 已拒绝八个目标 URL。",
         "四类操作、独立分区、挂载/卸载、历史/主题和底层服务行为逐项验证；不能仅以页面加载验收。", "bounded-caller-contract-available; backing-services-unresolved"),
    ]
    additional = {
        "RAM-03": [ref("runtime-feature-policy-contracts.json", "/maintenanceDecision"), ref("runtime-feature-policy-contracts.json", "/unresolvedNativeEffects")],
        "RAM-05": [ref("runtime-capability-decisions.json", "/decisions/0")],
        "RAM-12": [ref("runtime-capability-decisions.json", "/decisions/2"), ref("browser-ownership-contracts.json", "/implementationDecision"), ref("public-history-duplicate-comparison.json", "")],
        "RAM-13": [ref("runtime-capability-decisions.json", "/decisions/3"), ref("public-runtime-comparison.json", "")],
        "RAM-14": [ref("runtime-capability-decisions.json", "/decisions/1"), ref("runtime-distribution.json", "/distributionRecords/3")],
        "RAM-15": [ref("native-browser-settings-comparison.json", "/architectureDecision"), ref("native-browser-settings-comparison.json", "/requiredFamilies")],
    }
    groups = []
    for gid, title, indices, suffix, first, provider, missing, acceptance, prep in specs:
        sources = [ref("runtime-surface-disposition.json", f"/facts/{i}") for i in indices] + additional.get(gid, [])
        groups.append({
            "id": gid, "title": title,
            "surfaceFactIds": [surface["facts"][i]["id"] for i in indices],
            "sourceContracts": sources,
            "firstPartyResponsibility": first, "providerDecision": provider,
            "exactRemainingPrerequisite": missing, "acceptance": acceptance,
            "proposedAdapterPath": "packages/runtime-adapter/src/" + suffix,
            "proposedContractPath": "packages/contracts/src/runtime/" + suffix,
            "foundationTaskIds": ["W02", "W03"],
            "consumerTaskIds": ["T26"] if gid == "RAM-15" else [],
            "consumerJoinQualification": "T26 from the saved privileged-settings owner; other complete feature-consumer joins remain unclaimed.",
            "buildGateIds": ["BG-01", "BG-02", "BG-03", "BG-04"],
            "sourcePreparationStatus": prep, "runtimeAcceptance": "unverified",
            "confidence": "inferred", "mode": "unknown; retained",
            "fullRequirementRetained": True, "thirdPartyImplementationGenerated": False,
        })
    covered = [v for g in groups for v in g["surfaceFactIds"]]
    assert len(covered) == len(set(covered)) == 17
    assert set(covered) == {f["id"] for f in surface["facts"]}
    build = read("build-input-dispositions-v1.json")
    build_gates = [
        {"id": "BG-01", "purpose": "运行时类型与能力合同", "buildInputIds": ["BUILD-001", "BUILD-003", "BUILD-013", "BUILD-015"],
         "decision": "types 必须从选定 provider 的合同产生；声明一个不存在的方法不构成兼容。"},
        {"id": "BG-02", "purpose": "独立获取、启动与源码来源", "buildInputIds": ["BUILD-005", "BUILD-006", "BUILD-011", "BUILD-021"],
         "decision": "runtime-driver 只指向独立依赖/源码构建产物；记录 commit、平台、校验和与 SDK/headers。现未取得完整 Owl 输入。"},
        {"id": "BG-03", "purpose": "原生 ABI 与编译配置", "buildInputIds": ["BUILD-026"],
         "decision": "按目标 runtime headers、NODE_MODULE_VERSION/Node-API 要求、架构与 SDK 重建 native packages。Node 版本、Node-API 10 或本地 Node22 objc load 均不证明 Owl/候选 Electron ABI。"},
        {"id": "BG-04", "purpose": "独立打包、安装和升级", "buildInputIds": ["BUILD-012", "BUILD-017", "BUILD-022", "BUILD-025", "BUILD-027", "BUILD-028", "BUILD-029", "BUILD-030"],
         "decision": "锁定独立 artifact/构建配方、preload/resources/helpers、应用标识/数据根和签名更新配置；新版本重建并验证能力差异，不读取原安装路径。"},
    ]
    all_build = {x["id"] for x in build["decisions"]}
    assert all(set(x["buildInputIds"]) <= all_build for x in build_gates)
    matrix = {
        "schemaVersion": 1, "baselineId": BASE, "recordedAtUtc": NOW,
        "decisionScope": "SD-02 bounded provider/build disposition; 17 saved missing-description paths plus four existing cross-cutting contracts. Not a complete custom-runtime denominator.",
        "routeDecision": {
            "selectedArchitecture": "First-party capability contracts and adapters separate from an independently obtained runtime/native provider.",
            "selectedFullRuntime": None,
            "sourcePreparation": "The listed bounded contracts can inform later implementation. Partial source-owner/consumer items remain internal analysis work; native/provider gaps remain explicit integration gates.",
            "routes": [
                {"id": "ROUTE-OWL", "decision": "保留为取回原能力的候选；当前不能列作已取得的独立依赖。", "missing": ["独立发行URL/版本与archive hash含义", "源码/修改集和适用许可", "types/headers、构建脚本、工具链与锁定输入", "平台/ABI与能力行为验证"], "qualified": False},
                {"id": "ROUTE-STOCK", "decision": "拒绝固定 Electron 42.3.0 直接替换整个 Owl 运行时；公共接口保留为按合同验证的原语。", "basis": ["17个保存路径缺席的声明/实例读数", "clone/adoption和权限差异", "八个特权设置URL在固定guest被拒绝"], "qualified": False},
                {"id": "ROUTE-ADAPTER", "decision": "采用独立能力边界作为维护设计；平台bridge/运行时fork或等价服务实现逐组评估。不是已选定或构建通过的完整运行时。", "missing": "RAM-01至RAM-15的逐组前提；引擎级能力不能仅以JS接口形状或占位实现验收。", "qualified": False},
            ],
            "excludedFallbacks": ["依赖原客户端安装路径", "复制原framework作为已恢复源码", "删除保留能力/放宽权限", "把空函数、页面占位或假lease计为功能完成"],
        },
        "publicProvenanceOverlay": {
            "primaryReview": review_pin,
            "electronSourceCommit": commit,
            "electronDepsNode": "24.15.0", "frozenStaticNode": "24.19.0",
            "versionDifferenceQualification": "Source metadata versus frozen native static structure; neither proves executed runtime identity or binary ABI compatibility/incompatibility.",
            "sparkleSpmRoute": "precompiled-binary-target; source-build-not-proven",
            "upstreamBytesOrBinariesAcquired": False,
        },
        "capabilityGroups": groups, "buildGates": build_gates,
        "nativeDependencyJoins": [
            {"dependencyRefs": [ref("dependency-investigation-actions-v1.json", "/rows/28"), ref("dependency-investigation-actions-v1.json", "/rows/123")], "name": "node-pty", "decision": "沿用已确认修改边界；独立补丁包/适配路线仍需目标运行时构建、PTY创建和释放验证，不能换成普通上游后声称等价。"},
            {"dependencyRefs": [ref("dependency-investigation-actions-v1.json", "/rows/29"), ref("dependency-investigation-actions-v1.json", "/rows/125"), ref("objc-independent-build.json", "/scope")], "name": "objc-js", "decision": "已有独立SDK配方在本地Node22.23.2/x64构建与一次export-only load通过；不抹去该证据，也不扩大成目标Owl/Electron集成通过。"},
            {"dependencyRefs": [ref("runtime-distribution.json", "/distributionRecords/3")], "name": "Sparkle", "decision": "作为独立第三方更新组件管理；SPM binary与源码重建分列；选定runtime的更新bridge、签名/feed和策略provider仍需单独实现。"},
        ],
        "checkedFrozenSpans": checked_spans,
        "remainingInternalAnalysis": [
            {"id": "RI-01", "groupIds": ["RAM-02"], "work": "音频histogram完整生产/消费边界"},
            {"id": "RI-02", "groupIds": ["RAM-04"], "work": "调试页策略启动owner完整条件"},
            {"id": "RI-03", "groupIds": ["RAM-06"], "work": "input-shape消费者和平台条件"},
        ],
        "denominatorLimits": ["212个公开声明路径只具候选资格，未由本矩阵逐一证明兼容。", "4293个未解析名称候选和34个预算受限表达式不在17路径比较范围；名称候选也不是新增功能数。", "其他已记录custom能力（例如setAgentActive）不能因不在17路径中而视为已解决；本矩阵不声称整个运行时盘点关闭。", "所有模式未知项继续保留；未新增ChatGPT排除或功能验收。"],
        "nextInternalAction": {
            "issueId": "SD-05",
            "question": "用已保存的main/globalState/shutdown/provider合同形成数据域到owner、路径来源、写入与恢复边界的映射。",
            "closure": "逐域区分已确认逻辑根、运行有效根未测和认证/原生/后台外部存储；列明具体缺失provider，避免以globalState局部合同证明全域隔离。",
            "authorization": "冻结/保存证据与自有分析脚本；无新增模型、客户端或个人数据操作。",
        },
        "counts": {"capabilityGroups": 15, "savedSurfacePathsAssignedExactlyOnce": 17, "crossCuttingContractGroups": 4,
                   "buildGates": 4, "nativeDependencyFamiliesJoined": 3, "primarySourceReviewObservations": 5,
                   "sourcePreparationGroupsWithExplicitInternalFollowup": 3,
                   "fullRuntimeRoutesQualified": 0, "newRuntimeProbeRuns": 0, "newReaRuns": 0,
                   "newOriginalSourceParses": 0, "newClientLaunches": 0, "newModelSubmissions": 0,
                   "newProductScenarioPasses": 0, "newClientImplementation": 0},
        "currentProductScope": {"featureDefinitions": 373, "restorationTaskGroups": 48, "unexecutedScenarioSpecifications": 1216},
        "inputPins": inputs,
        "fullAnalysisCompleted": False, "independentRuntimeBuildProven": False,
    }
    matrix_pin = publish("runtime-adoption-matrix-v1.json", encode(matrix))
    evidence = []
    for group in groups:
        basis = group["sourceContracts"][0]
        evidence.append({"id": group["id"], "baselineId": BASE,
                         "claim": group["firstPartyResponsibility"] + " " + group["providerDecision"],
                         "sourcePath": basis["path"], "sourceHash": basis["sha256"],
                         "locator": {"jsonPointer": basis["jsonPointer"]}, "method": "inference",
                         "confidence": "inferred", "verificationStatus": "saved-contract-based-maintenance-decision; native-provider-and-runtime-acceptance-unverified"})
    for i, obs in enumerate(review["observations"]):
        evidence.append({"id": obs["id"], "baselineId": BASE, "claim": obs["finding"],
                         "sourcePath": review_pin["path"], "sourceHash": review_pin["sha256"],
                         "locator": {"jsonPointer": f"/observations/{i}", "upstreamUrl": obs["url"], "upstreamLocator": obs["locator"]},
                         "method": "public-primary-source-review", "confidence": "confirmed",
                         "verificationStatus": "bounded-public-document-observation; local-hash-pins-authored-review-only; no-upstream-bytes-or-runtime-measurement"})
    evidence_pin = publish("runtime-adoption-matrix-v1-evidence.jsonl", b"".join((json.dumps(x, ensure_ascii=False) + "\n").encode() for x in evidence))
    text = ["# 独立运行时能力与构建取舍", "",
            "本次决定维护边界与逐组实施前提，尚未取得通过完整资格验证的运行时。固定17个缺席接口全部接入15组职责，另外合并既有clone/adoption、进程权限、更新及特权设置合同。15组是维护分组，不是完整私有接口或产品功能分母。", "",
            "采用第一方能力合同/adapter与独立runtime/native provider分离的结构；普通Electron 42.3.0直接替换整个Owl的路线不成立。独立Owl来源尚未建立；平台bridge/引擎fork或等价服务实现仍按下表验证。", "",
            "|组|职责|具体剩余前提|", "|---|---|---|"]
    for g in groups:
        text.append(f"|{g['id']} {g['title']}|{g['firstPartyResponsibility']}|{g['exactRemainingPrerequisite']}|")
    text += ["", "## 构建与升级决定", "",
             "四组构建门槛已经接到既有BUILD输入和W02/W03：运行时types、独立获取/启动、native ABI/SDK、打包安装升级。拟议目录是维护建议，没有生成客户端实现或第三方实现。", "",
             f"固定Electron候选的完整源码提交为`{commit}`；该提交DEPS记录Node 24.15.0，冻结framework静态结构为24.19.0。这一差异要求按选定目标重建与验证native依赖，不能据此单独断言ABI兼容或不兼容。[官方提交]({commit_url})", "",
             "Node 24.19.0的固定权限文档没有给出所需scoped IPC/网络策略，CLI文档查不到两个flag；结合已有本地传输探针，不接受仅传普通Node permission参数作为已实现的隔离。[权限文档](https://nodejs.org/download/release/v24.19.0/docs/api/permissions.html)、[CLI文档](https://nodejs.org/download/release/v24.19.0/docs/api/cli.html)", "",
             "Sparkle 2.9.1的Swift包使用binaryTarget，属于预编译依赖路线；source build和Owl managed-policy binding仍分别待验收。[Package.swift](https://raw.githubusercontent.com/sparkle-project/Sparkle/2.9.1/Package.swift)", "",
             "node-pty保留已确认的修改边界；objc-js保留已有Node22.23.2/x64独立构建及export-only load证据，目标运行时集成仍未通过。两者均已接到依赖清单，未生成第三方实现副本。", "",
             "## 分析出口与后续工作", "",
             "本轮关闭的是逐组维护/构建处置：每组都有来源、责任、拟议路径、具体缺口和验收。SD-02整体仍开放：完整独立运行时、部分内部消费者/owner及真实native行为未闭合。没有把接口声明、公开原语或局部探针计为完整复刻。", "",
             "下一项内部工作为SD-05数据域职责映射；继续使用保存证据。只有取得新源码、发行物或具体provider时，才重访相应运行时取舍；不重复已完成的接口存在性枚举。373项功能、48任务组和1216条未执行规格保持。", "",
             "[结构化矩阵](runtime-adoption-matrix-v1.json)、[证据](runtime-adoption-matrix-v1-evidence.jsonl)、[公开来源审阅记录](runtime-adoption-primary-review-v1.json)。公开来源记录的哈希只标识本地审阅记录，未冒充上游文件/二进制哈希。", ""]
    summary_pin = publish("runtime-adoption-matrix-v1.md", "\n".join(text).encode())

    # Immutable correction: the older journal used a composite confidence value
    # outside the plan's enum. Keep its bytes and replace the effective view only.
    original = OUT / "association-overlap-decisions-v1-evidence.jsonl"
    corrected = [json.loads(line) for line in original.read_text().splitlines()]
    for row in corrected:
        assert row["confidence"] == "confirmed-for-bounded-source-relations; inferred-task-design"
        row["confidence"] = "inferred"
        row["method"] = "inference"
        row["verificationStatus"] += "; bounded-source-relations-reviewed; task-design-inferred"
    correction_pin = publish("association-overlap-evidence-correction-v1.jsonl", b"".join((json.dumps(x, ensure_ascii=False) + "\n").encode() for x in corrected))
    erratum = {"baselineId": BASE, "recordedAtUtc": NOW, "original": pin(original),
               "effectiveEvidence": correction_pin, "records": 15,
               "reason": "The prior composite confidence was outside the plan enum; each mixed source/design claim is conservatively inferred. Source claims, pointers, hashes and decisions are unchanged.",
               "changedFields": ["confidence", "method", "verificationStatus"], "originalImmutableBytesPreserved": True}
    erratum_pin = publish("association-overlap-evidence-correction-v1.json", encode(erratum))
    overlay = {"matrix": matrix_pin, "summary": summary_pin, "evidence": evidence_pin,
               "primaryReview": review_pin, "counts": matrix["counts"],
               "qualification": "Bounded source/provider/build design decision; no full runtime adopted or built; SD-02 retains internal and external prerequisites.",
               "fullAnalysisCompleted": False}
    state["runtimeAdoptionMatrix"] = copy.deepcopy(overlay)
    state["runtimeDistribution"]["currentAdoptionOverlay"] = copy.deepcopy(overlay)
    state["runtimeCapabilityDecisions"]["currentAdoptionOverlay"] = copy.deepcopy(overlay)
    state["runtimeCapabilityDecisions"]["nextAction"] = {
        "issueId": "SD-02", "question": "按runtime-adoption-matrix-v1逐组取得具体provider/来源或补齐已列内部合同缺口。",
        "closure": "以各组exactRemainingPrerequisite和acceptance为准；不重跑已完成的固定接口存在性比较。",
        "currentThreadNextInternalIssue": "SD-05"}
    state["stageDecisions"]["runtimeAdoptionOverlay"] = copy.deepcopy(overlay)
    state["stageDecisions"]["nextAction"] = copy.deepcopy(matrix["nextInternalAction"])
    state["pending"][1] = "SD-02: 17缺席路径已接入15组能力/构建处置，普通Electron直接替换被拒绝；完整源码commit及Node源版本差异已登记。独立Owl、实际provider/ABI、部分内部owner/consumer及真实native行为仍开放，未取得完整独立运行时资格。"

    def correct_view(node):
        if isinstance(node, dict):
            evidence_ref = node.get("evidence")
            if isinstance(evidence_ref, dict) and evidence_ref.get("sha256") == pin(original)["sha256"]:
                node["evidenceSchemaCorrection"] = {"erratum": erratum_pin, "effectiveEvidence": correction_pin}
            for key, value in list(node.items()):
                if key != "evidenceSchemaCorrection":
                    correct_view(value)
        elif isinstance(node, list):
            for value in node:
                correct_view(value)

    correct_view(state)
    state["updatedAtUtc"] = NOW
    assert state["status"] == "in-progress" and state["fullAnalysisCompleted"] is False
    assert state["latestBehaviorAuthorizationState"]["groupRemaining"] == 0
    state_path.write_bytes(encode(state))
    first = "当前[独立运行时能力与构建取舍](runtime-adoption-matrix-v1.md)已将17缺席路径接入15组责任、来源、构建和验收；固定Electron直接替换不成立，独立Owl/实际provider与部分内部合同仍待闭合。下一内部项为SD-05数据域职责映射。此前[12关联/3重叠决定](association-overlap-decisions-v1.md)保留，3业务父功能和15项集成限制不变；其journal置信度格式已通过独立erratum修正。373功能、48任务、1216未执行规格保持，完整分析未完成。"
    for name in ["report.md", "gaps.md"]:
        path = OUT / name
        _, rest = path.read_text().split("\n\n", 1)
        path.write_text(first + "\n\n" + rest)
    print(json.dumps({"published": overlay, "evidenceSchemaCorrection": erratum_pin, "frozenSpansChecked": len(checked_spans)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
