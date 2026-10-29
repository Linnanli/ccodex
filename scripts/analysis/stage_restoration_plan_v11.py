#!/usr/bin/env python3
"""Consolidate saved design contracts without running target code or services."""
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/restoration-plan-v11-work"
STAGE = WORK / "deliverables"
STAGE.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()
CACHE = {}
PINS = {}


def path(name):
    p = Path(name)
    return p if p.is_absolute() else ROOT / p if p.parts[0] in {"analysis", "docs", "scripts", ".analysis-local"} else OUT / p


def read(name):
    p = path(name)
    if p not in CACHE:
        CACHE[p] = json.loads(p.read_text())
    return CACHE[p]


def pin(name, pointer=None):
    p = path(name)
    if p not in PINS:
        b = p.read_bytes()
        PINS[p] = dict(path=str(p.relative_to(ROOT)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    r = dict(PINS[p])
    if pointer is not None:
        r["jsonPointer"] = pointer
    return r


def resolve(ref):
    x = read(ref["path"])
    for part in ref.get("jsonPointer", "").split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        x = x[int(part)] if isinstance(x, list) else x[part]
    return x


def plain(x):
    if isinstance(x, dict):
        for k in ("values", "value"):
            if k in x:
                return plain(x[k])
    return x


def write(name, value):
    p = STAGE / name
    assert not p.exists(), f"Refuse to replace {p}"
    p.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n")


SCOPE = "feature-scope-v42.json"
SCENARIOS = "feature-scope-v39-scenarios.json"
COVERAGE = "restoration-coverage-v33.json"
ORDER = "restoration-current-ordering-v16.json"
OWNERS = "feature-module-ownership-v8.json"
LEGACY = "legacy-entry-dispositions-v21.json"
inputs = ["docs/reverse-engineering/analysis-plan.md", "implementation-milestones-v10.json", "implementation-plan-v10.md",
          SCOPE, SCENARIOS, COVERAGE, ORDER, OWNERS, LEGACY, "retained-entry-backlog-v8.json",
          "logical-module-contracts-v1.json", "logical-module-ownership-v1.json", "runtime-adoption-matrix-v1.json",
          "input-shape-owner-v1.json", "audio-measurement-owner-v1.json", "debug-chrome-policy-owner-v1.json",
          "runtime-native-consumers-v1.json", "browser-permission-prompt-v1.json", "managed-update-policy-v1.json",
          "protocol-delta-adoption-v1.json", "storage-domain-map-v1.json", "storage-feature-ownership-v1.json",
          "plugin-storage-authority-v1.json", "auth-storage-authority-v1.json",
          "dependency-investigation-actions-v1.json", "dependency-import-decisions.json", "dependencies.csv",
          "build-input-dispositions-v1.json", "chat-branch-decisions.json", "product-flow-ownership.json",
          "analysis-stage-decisions-v5.json", "analysis-stage-decisions-v5-qualification.json", "behavior-stop-restart.json"]
# Storage decisions use their existing immutable names rather than assumed aliases.
state = read("analysis-state.json")
for key, assumed in [("pluginStorageAuthority", "plugin-storage-authority-v1.json"), ("authStorageAuthority", "auth-storage-authority-v1.json")]:
    if not path(assumed).exists():
        item = state[key]
        ref = next(item[k] for k in ("result", "contracts", "path") if k in item)
        replacement = ref["path"] if isinstance(ref, dict) else ref
        inputs[inputs.index(assumed)] = replacement
old = read("implementation-milestones-v10.json")
scope, specs, cov, order, owners = [read(n) for n in (SCOPE, SCENARIOS, COVERAGE, ORDER, OWNERS)]
legacy = read(LEGACY)
logical = read("logical-module-contracts-v1.json")
features = {x["featureId"]: (i, x) for i, x in enumerate(scope["features"])}
cov_features = {x["featureId"]: (i, x) for i, x in enumerate(cov["features"])}
owner_features = {x["featureId"]: (i, x) for i, x in enumerate(owners["features"])}
task_index = {x["taskId"]: (i, x) for i, x in enumerate(cov["taskGroups"])}
spec_index = {fid: [] for fid in features}
for x in specs["scenarios"]:
    for fid in dict.fromkeys([x["featureId"], *x.get("relatedFeatureIds", [])]):
        spec_index[fid].append(x["scenarioId"])
assert len(features) == 463 and len(task_index) == 51 and len(specs["scenarios"]) == 1569
assert Counter(fid for x in cov["taskGroups"] for fid in x["featureIds"]) == Counter(features.keys())
prep = {x["id"]: x["dependsOn"] for x in order["sourcePreparationGraph"]}
integration = {x["id"]: x["dependsOn"] for x in order["integrationGraph"]}

responsibilities = []
logical_by_id = {x["ownerId"]: x for x in logical["records"]}
for i, x in enumerate(owners["responsibilities"]):
    contract = logical_by_id.get(x["ownerId"])
    paths = plain(resolve(x["fields"]["proposedPath"]))
    paths = [paths] if isinstance(paths, str) else paths
    assert isinstance(paths, list), (x["ownerId"], paths)
    joins = [f["featureId"] for f in owners["features"] if x["ownerId"] in f.get("entryAndCallbackOwnerIds", [])]
    responsibilities.append({
        "ownerId": x["ownerId"], "kind": x["kind"], "currentContract": pin(OWNERS, f"/responsibilities/{i}"),
        "fields": copy.deepcopy(x["fields"]), "paths": paths,
        "sourceWitnessIds": x["sourceWitnessIds"], "exclusiveSourceAssignment": False,
        "foundationTaskId": contract["taskOwnership"]["foundation"]["taskId"] if contract else None,
        "conditionalConsumerJoins": copy.deepcopy(contract["taskOwnership"]["conditionalConsumerJoins"]) if contract else [],
        "currentEntryCallbackFeatureIds": joins,
        "currentEntryCallbackTaskIds": sorted({cov_features[fid][1]["taskId"] for fid in joins}),
        "consumerQualification": "Preserve saved conditional joins; no complete consumer or persistent authority claim.",
        "status": "qualified-source-responsibility; implementation-not-started",
    })
feature_items = []
for fid, (i, f) in features.items():
    ci, c = cov_features[fid]
    oi, o = owner_features[fid]
    assert set(f["scenarioIds"]) == set(spec_index[fid])
    feature_items.append({
        "featureId": fid, "name": f["name"], "mode": f["mode"], "taskId": c["taskId"],
        "featureContract": pin(SCOPE, f"/features/{i}"), "acceptanceContract": pin(COVERAGE, f"/features/{ci}"),
        "moduleContract": pin(OWNERS, f"/features/{oi}"), "proposedPath": o["proposedPath"],
        "operationIds": c["operationIds"], "supportOperationIds": c["supportOperationIds"], "scenarioIds": spec_index[fid],
        "sourceWitnessIds": o["sourceWitnessIds"], "entryAndCallbackOwnerIds": o.get("entryAndCallbackOwnerIds", []),
        "stateAuthorityContract": pin(OWNERS, f"/features/{oi}/persistentOrRemoteStateAuthority"),
        "sourcePartitionProven": False, "implementationStarted": False,
    })

tasks = []
for i, t in enumerate(cov["taskGroups"]):
    tid = t["taskId"]
    tasks.append({**copy.deepcopy(t), "currentTaskContract": pin(COVERAGE, f"/taskGroups/{i}"),
                  "sourcePreparationDependsOn": prep[tid], "integrationDependsOn": integration[tid],
                  "scenarioIds": list(dict.fromkeys(sid for fid in t["featureIds"] for sid in spec_index[fid])),
                  "responsibilityIds": [r["ownerId"] for r in responsibilities if tid in r["currentEntryCallbackTaskIds"] or any(j["taskId"] == tid for j in r["conditionalConsumerJoins"])],
                  "sourcePreparationExit": "逐功能保留合同中的入口条件、参数、状态、副作用、失败、取消及恢复；实际权威通过注入接口委托。",
                  "implementationAcceptance": "逐项执行关联规格并验证真实接收方、服务后效及持久化；不以源码准备或 mock 代替。"})

foundation_outputs = {
    "W01": ["84 条限定职责、48 个粗工作流 facade 与 463 项功能的来源映射", "1726 个来源 witness 及 27 条共享处置；逐转换保留十项模块字段"],
    "W02": ["独立 workspace、分进程编译及打包配方", "202 条依赖的引入与精确锁任务、30 条构建输入补齐决定"],
    "W03": ["15 组能力接口及生命周期", "已闭合 JS 策略与独立 provider 边界、四个构建验收关口"],
    "W04": ["按服务区分的 preload、app-host、HTTP、resolver、socket 传输与编解码", "身份、信任、订阅、断连、取消及释放合同"],
    "W05": ["app-server 请求通知适配与两个协议差异采用决定", "预测 fork 和其他服务独立能力接口与不支持状态"],
    "W06": ["11 个存储域与后续选定边界的 driver、根路径及权威注入", "读取、写入、revision、flush、退出、迁移与恢复职责"],
    "W07": ["应用初始化、路由、多窗口与共享 composer/controller", "产品模式、认证家族、执行位置、会话类别及资格的分离状态"],
    "W08": ["51 个业务任务、463 项有限功能及各自界面/控制器/宿主消费者", "500 项操作、118 项支撑和 1569 条规格的实现与验收对应"],
    "W09": ["全范围验收、ChatGPT 专用分支剥离及第三方审计", "干净构建安装、新基线差分、依赖升级与数据迁移备份回退"],
}
foundations = copy.deepcopy(old["foundationTasks"])
for i, f in enumerate(foundations):
    tid = f["taskId"]
    f.update(sourcePreparationDependsOn=prep[tid], integrationDependsOn=integration[tid], dependsOn=integration[tid],
             sourcePreparationOutput=foundation_outputs[tid], priorFoundation=pin("implementation-milestones-v10.json", f"/foundationTasks/{i}"),
             sourcePreparationEntry="源码准备图上游合同可用即可准备接口；真实集成仍须满足集成图和外部输入条件。",
             sourcePreparationExit="已列输出具有来源、调用边界、异常/释放语义和验收条件；不要求本步骤提前取得下游真实能力。",
             implementationAuthorization="future implementation only; analysis/design authorized now")
    f["openArchitectureConditions"] = {
        "W01": ["完整源码模块及消费者分母未知；限定职责与粗 facade 不等于恢复模块。"],
        "W02": ["运行时具体类型及原生构建的最终闭合在 W03 和 BG-01 至 BG-04；W02 先交付 workspace 和配方，不伪造完整构建通过。"],
        "W03": ["完整合格运行时仍为 0；独立来源、构建、ABI 与平台效果待验证。"],
        "W04": ["真实宿主实例、信任及资源释放仍需集成验证。"],
        "W05": ["预测后台、私有服务、decoder/receiver 后效及发行到源码绑定未证明。"],
        "W06": ["完整 store 分母、逐功能权威、实际有效根及全域隔离未证明。"],
        "W07": ["462 项模式 unknown；只移除已有证据的专用分支。"],
        "W08": ["463 为有限定义；保留 78 条命令关联及 772 条来源关联缺口。"],
        "W09": ["原九项分析标准仍未全闭合；M1 至 M7 均为未来实施验收。"],
    }[tid]
    f["evidence"] = [pin(SCOPE), pin(COVERAGE), pin(ORDER), pin(OWNERS)]

runtime_items = copy.deepcopy(old["runtimeCapabilityWorkItems"])
overlays = {
    "RAM-05": ("runtime-native-consumers-v1.json", "选定 Task Manager JS 委托已定位；原生 payload、动作、刷新与关闭仍待验证。"),
    "RAM-08": ("runtime-native-consumers-v1.json", "选定状态查询、设置打开及生命周期已定位；真实授权状态、系统设置与原生失败语义待验证。"),
    "RAM-11": ("runtime-native-consumers-v1.json", "选定字体数据形状、加载和消费者已定位；真实字体枚举、平台差异及底层来源待验证。"),
    "RAM-10": ("browser-permission-prompt-v1.json", "选定 JS 请求/响应及释放已定位；原生提示注入、实际权限裁决及 profile 隔离待验证。"),
    "RAM-14": ("managed-update-policy-v1.json", "选定更新策略及启动/写入消费者已定位；独立更新来源、签名、安装/重启与回退待验证。"),
}
for r in runtime_items:
    if r["id"] in overlays:
        name, remaining = overlays[r["id"]]
        r.update(selectedLaterSourceContract=pin(name), selectedSourceStatus="selected-JS-boundary-delivered",
                 exactRemainingPrerequisite=remaining, remainingProviderCondition=remaining,
                 sourceFollowupQualification="Later selected JS closure supersedes older entry tracing; native/provider acceptance remains open.")
    r["qualifiedFullRuntime"] = False

boundary_rules = [
    {"id": "ARCH-01", "decision": "按进程和权威划分组合根；每条 IPC/RPC 边界使用按服务区分的合同，renderer 不持有原生 provider。", "basis": [pin("logical-module-contracts-v1.json"), pin(OWNERS)]},
    {"id": "ARCH-02", "decision": "现有 84 条职责和 48 个粗 facade 用于目录内职责划分，不为每个 controller 建一个 npm 包。具体拟路径优先于粗工程树；不自动改名 worker/workers 或现有客户端包。", "basis": [pin(OWNERS, "/responsibilities"), pin(OWNERS, "/featureAdapterProposals")]},
    {"id": "ARCH-03", "decision": "共享来源 witness 只作为来源证据；按保存的共享/重叠规则选择实现所有者或注入接口，不能向多个目录复制同一 bundle 范围。", "basis": [pin(OWNERS, "/sharedWitnessDispositions"), pin("logical-module-contracts-v1.json", "/overlapPolicy")]},
    {"id": "ARCH-04", "decision": "W02 先形成 workspace 与构建配方，W03 准备能力类型；运行时和原生输入最终资格由 BG-01 至 BG-04 验收。保留既有两套依赖图，避免把全部构建输入成功误设为 W03 的源码前置。", "basis": [pin(ORDER), pin("build-input-dispositions-v1.json", "/decisions/0"), pin("runtime-adoption-matrix-v1.json", "/buildGates")]},
    {"id": "ARCH-05", "decision": "202 条第三方记录通过依赖、单独补丁或明确 ABI 适配接入；原发布版本证据和新工程选择的精确锁分别保存，不能把未知版本填成推测版本。", "basis": [pin("dependency-investigation-actions-v1.json", "/rows"), pin("dependency-import-decisions.json")]},
    {"id": "ARCH-06", "decision": "只按已证明的 ChatGPT 专用分支剥离；未知模式、共享提交及账户/宿主权威保留。完整客户端验收保持 M1 至 M7，分析完成继续按原九标准。", "basis": [pin("chat-branch-decisions.json"), pin(SCOPE, "/counts/modeCounts"), pin("implementation-milestones-v10.json", "/implementationMilestones")]},
]
plan = copy.deepcopy(old)
plan.update(schemaVersion="restoration-plan-v11", recordedAtUtc=NOW,
    previousSnapshot=pin("implementation-milestones-v10.json"), currentFeatureScope=pin(SCOPE), currentScenarios=pin(SCENARIOS),
    restorationCoverage=pin(COVERAGE), currentCounts={**cov["counts"], "qualifiedResponsibilityRecords": 84,
    "coarseWorkflowFacades": 48, "sourceWitnesses": 1726, "sharedWitnessDispositions": 27,
    "runtimeCapabilityGroups": 15, "storageDomains": 11, "selectedStorageBoundaries": 16, "dependencyRecords": 202,
    "buildInputOccurrences": 30, "fullRuntimeRoutesQualified": 0, "modelSubmissionsRemaining": 0,
    "savedLegacyEntriesWithoutFeatureMapping": 772, "remainingCommandGoalAssociations": 78},
    countPrecedence="v42 features/operations, v39 scenarios, v33 tasks, v16 ordering and v8 ownership are current. Earlier snapshots retain their historical counters.",
    foundationTasks=foundations, restorationTaskGroups=tasks, featureWorkItems=feature_items,
    logicalModuleWorkItems=responsibilities, logicalModuleRequiredFields=owners["requiredModuleFields"],
    coarseWorkflowFacades=[{"ownerId": x["ownerId"], "contract": pin(OWNERS, f"/featureAdapterProposals/{i}"), "status": x["proposalStatus"]} for i, x in enumerate(owners["featureAdapterProposals"])],
    supportWorkItems=[{"operationId": x["operationId"], "contract": pin(SCOPE, f"/supportOperations/{i}"),
                       "moduleLink": pin(OWNERS, f"/supportOperationLinks/{i}")} for i, x in enumerate(scope["supportOperations"])],
    sourceWitnessMap=pin(OWNERS, "/sourceUnits"), sharedWitnessDispositions=pin(OWNERS, "/sharedWitnessDispositions"),
    currentOwnershipBasis=pin(OWNERS), architectureDecisions=boundary_rules,
    sourcePreparationGraph=order["sourcePreparationGraph"], integrationGraph=order["integrationGraph"],
    sourcePreparationLevels=order["sourcePreparationLevels"], integrationLevels=order["integrationLevels"], orderingBasis=pin(ORDER),
    runtimeCapabilityWorkItems=runtime_items,
    currentStorageFeatureOverlay=pin("storage-feature-ownership-v1.json"),
    storageSourceOverlays=[pin(n) for n in inputs if "storage-authority" in n],
    storageRemaining={"earlierDomainRemaining": pin("storage-domain-map-v1.json", "/remainingCoverage"),
                      "currentSelectedBoundaryRemaining": pin("storage-feature-ownership-v1.json", "/remaining"),
                      "qualification": "Later selected boundaries and17 qualified feature links refine saved domains; no full authority/effective-root/durability closure."},
    dependencyWorkItems=[{"dependencyId": x["dependencyId"], "name": x["name"], "contract": pin("dependency-investigation-actions-v1.json", f"/rows/{i}"),
                          "recommendedIntegration": x["recommendedIntegration"], "investigationExecuted": x["investigationExecuted"]} for i, x in enumerate(read("dependency-investigation-actions-v1.json")["rows"])],
    criterionAudit=pin("analysis-stage-decisions-v5.json", "/criteria"), criterionAuditQualification=pin("analysis-stage-decisions-v5-qualification.json"),
    legacySourceRoleStatus={"basis": pin(LEGACY), "counts": legacy["counts"], "qualification": "Reviewed source roles do not establish complete feature identities or behavior."},
    unresolvedScopeRef=pin(COVERAGE, "/unresolvedScope"), retainedAssociationBacklog=pin("retained-entry-backlog-v8.json"),
    unresolvedScopeQualification="Retain all unresolved business, mode, provider and source associations;772 records are not772 proven missing functions.",
    analysisExitPolicy="Analysis/design delivery is separate from client implementation.1569 product specifications belong to later product verification; major behavior comparison and architecture-changing unknowns remain analysis obligations. Unknown counts need not mechanically reach zero.",
    inputPins=[pin(n) for n in inputs], fullAnalysisCompleted=False, implementationStarted=False, independentClientBuildProven=False)
plan["modePolicy"]["counts"] = scope["counts"]["modeCounts"]
for m in plan["analysisMilestones"]:
    m["status"] = "in-progress; no criterion promotion by consolidation"
    m["evidencePaths"] = {"A1": [SCOPE, LEGACY, OWNERS], "A2": ["dependency-investigation-actions-v1.json", "runtime-adoption-matrix-v1.json", "build-input-dispositions-v1.json"], "A3": [OWNERS, COVERAGE, "storage-feature-ownership-v1.json", "protocol-delta-adoption-v1.json"], "A4": ["behavior-stop-restart.json", "analysis-stage-decisions-v5.json"]}[m["id"]]
plan["nextAnalysisAction"] = {
    "issueId": "SD-01", "scope": "Fixed remaining78 command-to-goal associations; no recursive provider investigation.",
    "inputs": [pin(LEGACY), pin("retained-entry-backlog-v8.json"), pin(SCOPE), pin(OWNERS)],
    "deliverable": "一次固定范围关联结论，区分已有功能入口、支撑机制、有限新增目标及确切未解消费者；只由新证据扩展功能。",
    "stopCondition": "对固定记录给出来源、角色/目标去向、责任边界与尚缺的具体输入即关闭本批；不因 native/service 未通过而重开已交付 JS 合同。",
    "authorization": "Saved/frozen source analysis only; no client launch, target evaluation, model/service calls or personal configuration access.",
}
for c in plan["openConditions"]:
    if c["id"] == "PC-01":
        c["evidence"] = [pin(OWNERS, "/remaining"), pin(LEGACY, "/counts"), pin(SCOPE, "/counts/modeCounts")]
    if c["id"] == "PC-04":
        c["evidence"] = [pin("storage-feature-ownership-v1.json", "/remaining")]
    if c["id"] == "PC-05":
        c["evidence"] = [pin("implementation-milestones-v10.json", "/implementationMilestones")]
    if c["id"] == "PC-06":
        c["evidence"] = [pin("behavior-stop-restart.json"), pin("analysis-stage-decisions-v5.json")]
write("implementation-milestones-v11.json", plan)


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *["| " + " | ".join(cell(x) for x in row) + " |" for row in rows]])


parts = [
    "# Codex 独立客户端恢复实施计划草案 版本 11",
    "恢复固定基线的 Codex 界面、交互、状态、持久化和桌面集成，剥离已证明只供 ChatGPT 使用的分支，第三方实现通过依赖管理接入。工程应能维护、升级，并从干净环境构建打包，运行时独立于原客户端安装路径。当前仍处于分析和设计阶段，客户端实现尚未开始。",
    "当前范围是 463 项有限功能、500 项用户操作、118 项支撑、51 个业务任务及 1569 条未执行产品规格。完整产品分母未知。[机器计划](implementation-milestones-v11.json)逐 ID 连接[功能 v42](feature-scope-v42.json)、[规格 v39](feature-scope-v39-scenarios.json)、[任务 v33](restoration-coverage-v33.json)和[职责 v8](feature-module-ownership-v8.json)。历史 v10 的 373 项范围不再作为当前实施入口。",
    "## 工程边界与依赖方向",
    "发布 chunk 用来定位来源；维护模块按进程、职责、状态权威及副作用划分。拟工程主干如下，具体路径以职责合同为准，保留 app-server-client、storage-contracts、main/persistence 等既有提案，不机械改名或按每个 controller 新建包。",
    "```text\napps/desktop/src/main/               启动、窗口、宿主、系统及退出的组合根\napps/desktop/src/preload/            隔离世界、IPC、端口和受控注入\napps/desktop/src/renderer/app/       初始化、路由、多窗口和模式\napps/desktop/src/renderer/features/  功能界面、控制器及局部状态\napps/desktop/src/workers/            有独立生命周期的工作任务\napps/desktop/resources/              可追踪来源的资源\npackages/                           按合同隔离的协议、后台、运行时及存储适配\ntools/recovery/                     来源映射及可审查转换\ntools/build/                        独立生成、构建和打包\ntests/fixtures/                     合成样例及回归输入\n```",
    "renderer 调用按服务区分的合同；main/preload 的组合根注入传输、后台、存储和运行时 provider。业务控制器不直接绑定某个原安装路径或私有运行时单例。app-server、桌面 HTTP、app-host、resolver、扩展连接及 socket 分别保留接收方身份、错误、断连、取消和释放语义，不能共享一套含糊的消息总线。",
    table(["设计决定", "实施规则"], [(r["id"], r["decision"]) for r in boundary_rules]),
    "## 来源到模块的转换约束",
    "[职责映射](feature-module-ownership-v8.json)包含 84 条限定职责和 48 个粗工作流 facade；它们不等于 132 个已恢复模块。每条限定职责保留 responsibility、environment、mode、sourceRanges、imports、exports、sharedState、sideEffects、thirdPartyDependencies、proposedPath 十项字段。机器计划索引全部职责、功能及操作，不把粗 facade 的历史功能集合擅自扩充为完整权威。",
    "1726 个来源 witness 和 27 条共享处置作为转换证据；原有 19 条逻辑重叠规则继续有效。一个来源范围可以支持多个判断，不能因此在多个目录复制同一实现。转换记录保存基线、源路径/hash/字节范围、变换方式、依赖、拟路径及回归场景。逐功能持久化权威仍有缺口；另列的 17 条限定存储关联不能充抵全部 463 项。",
    "## 源码准备和真实集成顺序",
    "两套[60 节点依赖图](restoration-current-ordering-v16.json)保持现有边和层次。源码准备可以在接口合同可用时推进；真实运行时、服务和持久化集成继续受外部输入及专门验收条件约束。",
    table(["基础任务", "源码准备上游", "真实集成上游", "准备输出"], [(f["taskId"] + " " + f["name"], ", ".join(f["sourcePreparationDependsOn"]) or "无", "W08 和全部 51 个业务任务" if f["taskId"] == "W09" else ", ".join(f["integrationDependsOn"]) or "无", "；".join(f["sourcePreparationOutput"])) for f in foundations]),
    "W02 先交付 workspace、依赖引入和构建配方；W03 再准备运行时能力及类型。BUILD-001 等运行时相关输入的最终成功留给 BG-01 至 BG-04，不把‘所有构建输入已成功’设成 W03 的源码前置，也不因此修改既有依赖图。源码准备出口要求调用与失败语义可实现；真实集成出口要求真实接收方、效果及平台行为通过。",
    "## 业务任务及完整范围",
    table(["任务", "有限功能数", "拟主模块"], [(t["taskId"] + " " + t["name"], len(t["featureIds"]), "`" + t["primaryModule"] + "`") for t in tasks]),
    "机器计划逐项保存 463 个 featureId、500 个操作 ID、118 个支撑 ID、1569 个 scenarioId 与任务的联系。设置、自动化、文件/变更/Git、终端/PTY、远程/云端、浏览器、系统及页面编辑器等已发现能力均保留；共享消费者不重复计数，Pages 等名称本身也不是 ChatGPT 专用的证据。",
    "## 运行时与原生能力",
    "[运行时矩阵](runtime-adoption-matrix-v1.json)采用第一方能力合同与独立 provider 的边界，完整合格路线仍为 0。固定 stock Electron 42.3.0 直接替换整个 Owl 的路线已被保存的接口和特权页对照否定；公共原语须按各组能力单独验收。独立发行或自有 provider 需要来源/版本/完整性、构建输入、ABI、目标平台和升级资格。",
    table(["能力组", "适配路径", "关键未取得条件"], [(r["id"] + " " + r["title"], "`" + r["proposedAdapterPath"] + "`", r["exactRemainingPrerequisite"]) for r in runtime_items]),
    "RAM-02/04/06 的音频、调试策略和 input-shape JS 边界已交付；后续 Task Manager、授权设置、字体、浏览器权限提示及更新策略的选定 JS 合同也已交付。只因原生效果尚未验证，不重开相同入口追踪。node-pty 修改、objc-js 与 Sparkle 分别保留补丁/源码/二进制来源和目标 ABI 验收；本地 Node 构建或导出加载不能替代目标运行时行为。",
    table(["构建关口", "涉及输入", "验收决定"], [(g["id"], ", ".join(g["buildInputIds"]), g["decision"]) for g in plan["runtimeBuildGates"]]),
    "## 后台协议与持久化",
    "[协议采用](protocol-delta-adoption-v1.json)保留 466 个变体比较中的 455 相同与 11 不同：10 个通知变体的可选 nullable model/reasoningEffort 需要容忍和传递，另一个预测 fork 需要匹配语义的后台。预测 fork 不静默降为普通 fork 或新会话；实际 decoder、receiver、通知后效和发行到源码绑定继续验证。",
    "[11 个存储域](storage-domain-map-v1.json)与[后续存储关联](storage-feature-ownership-v1.json)分别保留权威、路径、写入、revision、flush、退出及迁移恢复责任。desktop home、execution home、runtime profile、浏览器 partition、native credential 与远端账户状态分别注入。后续插件和认证权威合同已经提供选定源码边界；完整 store 分母、实际有效根、逐功能权威和全域隔离仍待闭合。",
    "## 第三方依赖与构建输入",
    "[202 条依赖记录](dependency-investigation-actions-v1.json)逐条有调查动作，包含 78 项根声明；有动作不等于精确版本或修改状态均已确定。原发布版本证据与新工程选定版本及精确锁分开保存。React/UI、schema/query、遥测、native/Wasm 和运行时通过依赖引入，第一方封装和策略恢复为维护源码，第三方 bundle 实现不生成进第一方目录。",
    "[30 条构建输入处置](build-input-dispositions-v1.json)涉及 21 个唯一原路径，均有替代方式、依赖任务和验收要求，替代实现仍为 0。TypeScript/Vite/Forge 是构建职责候选；完整工具链锁、资源、运行时及原生输入、签名和更新配置仍须由独立工程实际验证。",
    "## 模式剥离与升级",
    "当前模式为 462 项 unknown、1 项 shared，整功能确认排除为 0。已有[3 组 ChatGPT 专用分支决定](chat-branch-decisions.json)供后续剥离；共享 composer/controller、Codex 提交、账户访问和宿主能力保留。产品模式、认证家族、执行位置、会话类别及后台资格分别建模，不按名称删功能。",
    "每次升级建立新基线，记录来源、版本、hash 和工具参数；对功能入口/条件、协议通知、状态 schema、依赖修改、运行时能力、资源及平台行为做差分。差异回到拟维护模块、影响场景及迁移/备份/回退配方，历史证据不覆盖。",
    "## 实施验收与当前分析出口",
    "M1 至 M7 完整沿用历史验收条件，当前均未实施。源码合同、隔离回放、mock 或占位不能作为真实功能通过。",
    table(["里程碑", "上游", "退出条件"], [(m["id"] + " " + m["name"], ", ".join(m["dependsOn"]) or "无", "；".join(m["exitCriteria"])) for m in plan["implementationMilestones"]]),
    "分析出口按[原九标准与 39 项要求的当前复核](analysis-stage-decisions-v5.md)及[资格说明](analysis-stage-decisions-v5-qualification.json)判断，本次不提升完成状态。1569 条产品规格属于后续产品验收；主要行为对照和会改变工程结构的未知仍是分析义务。78 条命令关联和 772 条来源关联缺口保留，后者不等于 772 个已证明缺失的功能。",
    "已有只读样例完成且可重开；取消样例提前完成，因此执行中取消未测；停止后重启为 interrupted，自动续跑未证明。审批、失败和 PTY 等主要路径仍缺行为对照。最初 1 次及后续 2 次模型授权均已用完，新增模型测试须另有授权；冻结源码与设计工作可继续。",
    "当前计划整合到此交付；后续来源分析限定为现有 78 条命令关联的一次固定范围处置，区分已有功能入口、支撑、有限新目标和确切缺失消费者。已交付 JS 合同只在出现矛盾来源、新保留消费者或具体未解调用目标时重访；外部 provider 缺失进入具名集成关口，不能成为无界递归调查的理由。",
]
write("implementation-plan-v11.md", "\n\n".join(parts) + "\n")
evidence = []
for r in boundary_rules:
    first = r["basis"][0]
    evidence.append(dict(id="RP11-" + r["id"], baselineId=BASE, claim=r["decision"], sourcePath=first["path"],
        sourceHash=first["sha256"], locator={"jsonPointer": first.get("jsonPointer", "")}, method="saved-contract-design-synthesis",
        confidence="inferred", verificationStatus="design only; no runtime/product/build acceptance", additionalBasis=r["basis"][1:]))
outputs = []
for n in ("implementation-plan-v11.md", "implementation-milestones-v11.json"):
    b = (STAGE / n).read_bytes()
    outputs.append(dict(path=str((OUT / n).relative_to(ROOT)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
write("restoration-plan-v11-provenance.json", dict(baselineId=BASE, recordedAtUtc=NOW,
    builder=pin("scripts/analysis/stage_restoration_plan_v11.py"), inputs=plan["inputPins"], outputs=outputs, evidence=evidence,
    counts={"features": 463, "operations": 500, "support": 118, "specifications": 1569, "tasks": 51,
            "graphNodesEach": 60, "responsibilities": 84, "coarseFacades": 48, "sourceWitnesses": 1726,
            "dependencyRecords": 202, "runtimeGroups": 15, "storageDomains": 11, "buildInputs": 30},
    newClientLaunches=0, newModelSubmissions=0, newServiceCalls=0, clientImplementationAdded=0,
    originalCriteriaStatusChanged=False, fullAnalysisCompleted=False))
print(json.dumps({"stagedAt": str(STAGE), "files": len(list(STAGE.iterdir())), "fullAnalysisCompleted": False}))
