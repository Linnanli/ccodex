#!/usr/bin/env python3
"""Stage the current restoration design from saved analysis; never run a client."""
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/restoration-plan-v10-work"
STAGE = WORK / "deliverables"
STAGE.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()


def read(name):
    return json.loads((OUT / name).read_text())


def pin(name, pointer=None):
    p = ROOT / name if name.startswith(("analysis/", "docs/", "scripts/", ".analysis-local/")) else OUT / name
    b = p.read_bytes()
    r = {"path": str(p.relative_to(ROOT)), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    if pointer is not None:
        r["jsonPointer"] = pointer
    return r


def dump(name, value):
    p = STAGE / name
    assert not p.exists(), f"Refuse to replace staged output: {p}"
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


inputs = [
    "docs/reverse-engineering/analysis-plan.md", "implementation-plan-v9.md",
    "implementation-milestones-v9.json", "feature-scope-v27.json",
    "feature-scope-v24-scenarios.json", "restoration-coverage-v18.json",
    "restoration-current-ordering-v1.json", "logical-module-contracts-v1.json",
    "logical-module-ownership-v1.json", "runtime-adoption-matrix-v1.json",
    "input-shape-owner-v1.json", "audio-measurement-owner-v1.json",
    "debug-chrome-policy-owner-v1.json", "protocol-delta-adoption-v1.json",
    "storage-domain-map-v1.json", "build-input-dispositions-v1.json",
    "dependency-investigation-actions-v1.json", "dependency-import-decisions.json",
    "dependencies.csv", "legacy-entry-dispositions-v5.json",
    "association-overlap-decisions-v1.json", "chat-branch-decisions.json",
    "archive-mode-ownership.json", "product-flow-ownership.json",
    "analysis-stage-decisions-v4.json", "behavior-stop-restart.json",
    "environment-extension-contracts.json",
]
pins = [pin(n) for n in inputs]
old = read("implementation-milestones-v9.json")
scope = read("feature-scope-v27.json")
scenarios = read("feature-scope-v24-scenarios.json")
coverage = read("restoration-coverage-v18.json")
ordering = read("restoration-current-ordering-v1.json")
logical = read("logical-module-contracts-v1.json")
runtime = read("runtime-adoption-matrix-v1.json")
storage = read("storage-domain-map-v1.json")
protocol = read("protocol-delta-adoption-v1.json")
build = read("build-input-dispositions-v1.json")
legacy = read("legacy-entry-dispositions-v5.json")
associations = read("association-overlap-decisions-v1.json")
stage = read("analysis-stage-decisions-v4.json")
dependency_actions = read("dependency-investigation-actions-v1.json")

feature_by_id = {x["featureId"]: (i, x) for i, x in enumerate(scope["features"])}
task_by_id = {x["taskId"]: (i, x) for i, x in enumerate(coverage["taskGroups"])}
scenario_by_feature = {fid: [] for fid in feature_by_id}
for x in scenarios["scenarios"]:
    scenario_by_feature[x["featureId"]].append(x["scenarioId"])
assert len(feature_by_id) == 373 and len(task_by_id) == 48
assert sum(map(len, scenario_by_feature.values())) == 1216
assert Counter(x for t in coverage["taskGroups"] for x in t["featureIds"]) == Counter(feature_by_id.keys())
assert all(set(f["scenarioIds"]) == set(scenario_by_feature[fid]) for fid, (_, f) in feature_by_id.items())

prep = {x["id"]: x["dependsOn"] for x in ordering["sourcePreparationGraph"]}
integration = {x["id"]: x["dependsOn"] for x in ordering["integrationGraph"]}
work_specs = {
    "W01": {
        "sourcePreparationOutput": ["按服务命名空间拆开的 DTO、错误、通知和生命周期接口", "原文件/hash/字节范围到维护模块的转换清单", "37 个既有职责及 19 条重叠规则的导入边界"],
        "sourcePreparationExit": "每个准备转换的范围有原位置、依赖合同、导入导出/副作用和回归场景；重叠范围只保留一个实现所有者。",
        "openArchitectureConditions": ["完整源码模块分母及所有消费者尚未建立；37 是已保存职责集合。"],
    },
    "W02": {
        "sourcePreparationOutput": ["工作区及分进程 TypeScript/Vite/Forge 构建职责配置", "202 条依赖的来源/新选版本/引入方式清单与新工程精确锁策略", "30 条缺失输入的独立补齐任务和资源来源清单"],
        "sourcePreparationExit": "每条构建输入有负责人、生成/获取方式和验证命令；第三方实现不会生成到第一方源码。",
        "openArchitectureConditions": ["实际完整锁、运行时 artifact/SDK、原生目标构建和签名/更新输入尚未取得资格。"],
    },
    "W03": {
        "sourcePreparationOutput": ["15 组运行时能力的类型、生命周期和错误合同", "RAM-02/04/06 已核实的 JS 策略及适配接口", "逐平台 provider 选择和 BG-01 至 BG-04 的构建验收定义"],
        "sourcePreparationExit": "每组明确第一方策略与底层 provider 责任；保留 unsupported、异常和释放语义。",
        "openArchitectureConditions": ["没有完整合格运行时；独立来源/构建/ABI/特权服务及平台效果仍影响路线。"],
    },
    "W04": {
        "sourcePreparationOutput": ["preload、app-host、HTTP、resolver、扩展连接和 socket 各自的编解码器", "身份/信任、订阅、断连、取消和资源释放状态机"],
        "sourcePreparationExit": "真实传输接口被明确注入；端口、身份、owner 和 disposal 不跨服务混用。",
        "openArchitectureConditions": ["真实宿主实例及全部接收方身份未闭合；原生消息/IPC 与能力释放需运行验证。"],
    },
    "W05": {
        "sourcePreparationOutput": ["按实际 provider 选择的 app-server 请求及通知适配器", "10 项可选通知字段的容忍边界", "预测 fork 的独立能力接口与不支持状态", "环境扩展、命令后台和私有服务的分离接口"],
        "sourcePreparationExit": "保留原参数、错误及通知语义；预测 fork 不降级为普通 fork 或新会话。",
        "openArchitectureConditions": ["匹配的预测后台、公开 npm 到源码 commit 绑定及真实 decoder/receiver/通知后效未证明。"],
    },
    "W06": {
        "sourcePreparationOutput": ["11 个已分析存储域的根路径配置与 driver 接口", "schema/revision/并发写/原子替换、退出和迁移恢复状态机", "desktop home、execution home、runtime profile 与认证存储的分别注入"],
        "sourcePreparationExit": "每域有读取/写入/flush/迁移/恢复责任；membership 队列与文件 flush 不互相代替。",
        "openArchitectureConditions": ["全量 store 分母、认证/native/backend 存储及实际有效根仍未闭合。"],
    },
    "W07": {
        "sourcePreparationOutput": ["应用初始化、路由与多窗口壳", "模式/认证家族/执行位置/会话类别/资格的独立状态", "共享首页 composer/controller 与 Codex 本地提交策略"],
        "sourcePreparationExit": "共享组件和 provider 生命周期被保留；只剥离有证据的三组 Chat 专用分支。",
        "openArchitectureConditions": ["372 项 unknown 功能的完整模式/共享消费者闭包未建立，不据名称删除。"],
    },
    "W08": {
        "sourcePreparationOutput": ["48 个任务的界面、控制器与宿主消费者", "终端/文件与变更/Git/远程/云端/系统能力的委托实现清单", "每功能正常、失败、取消和恢复场景与条件"],
        "sourcePreparationExit": "373 项现有定义逐项有实现所有者；其他已发现委托能力及未知范围仍在表内。",
        "openArchitectureConditions": ["373 是当前有限定义，不是已证明完整产品分母；部分业务父功能/消费者仍未知。"],
    },
    "W09": {
        "sourcePreparationOutput": ["全范围验收表、剥离清单及第三方审计", "新基线差分、依赖升级及数据迁移/备份/回退配方", "干净安装/构建/打包/升级与原安装路径独立性检查"],
        "sourcePreparationExit": "所有 T01 至 T48 和 W08 的设计结果可追踪到验收；未决能力保留失败/待验证状态。",
        "openArchitectureConditions": ["原九项分析标准尚未全部完成，实施里程碑 M1 至 M7 均未执行。"],
    },
}
work_refs = {
    "W01": ["logical-module-contracts-v1.json", "logical-module-ownership-v1.json"],
    "W02": ["build-input-dispositions-v1.json", "dependency-investigation-actions-v1.json", "dependency-import-decisions.json", "dependencies.csv"],
    "W03": ["runtime-adoption-matrix-v1.json", "input-shape-owner-v1.json", "audio-measurement-owner-v1.json", "debug-chrome-policy-owner-v1.json"],
    "W04": ["logical-module-contracts-v1.json"],
    "W05": ["protocol-delta-adoption-v1.json", "environment-extension-contracts.json"],
    "W06": ["storage-domain-map-v1.json"],
    "W07": ["product-flow-ownership.json", "chat-branch-decisions.json", "archive-mode-ownership.json"],
    "W08": ["restoration-coverage-v18.json", "legacy-entry-dispositions-v5.json", "association-overlap-decisions-v1.json"],
    "W09": ["feature-scope-v27.json", "feature-scope-v24-scenarios.json", "restoration-coverage-v18.json"],
}
foundations = []
for i, f in enumerate(old["foundationTasks"]):
    f = copy.deepcopy(f)
    tid = f["taskId"]
    f.update(work_specs[tid])
    f["sourcePreparationDependsOn"] = prep[tid]
    f["integrationDependsOn"] = f["dependsOn"] = integration[tid]
    f["sourcePreparationEntry"] = "所需来源合同可定位，且源码准备图的上游输出可用；不要求上游已通过真实集成。"
    f["implementationAuthorization"] = "future implementation only; current goal authorizes analysis/design"
    f["priorFoundation"] = pin("implementation-milestones-v9.json", f"/foundationTasks/{i}")
    f["evidence"] = [pin(n) for n in work_refs[tid]]
    foundations.append(f)

logical_items = []
for i, r in enumerate(logical["records"]):
    tid = r["taskOwnership"]["foundation"]["taskId"]
    assert tid in prep
    joins = []
    for j in r["taskOwnership"]["conditionalConsumerJoins"]:
        tj, task = task_by_id[j["taskId"]]
        assert set(j.get("featureIds", [])) <= set(feature_by_id)
        joins.append({
            "taskId": j["taskId"], "featureIds": j.get("featureIds", []),
            "currentTask": pin("restoration-coverage-v18.json", f"/taskGroups/{tj}"),
            "relationship": j["relationship"], "confidence": j.get("confidence", "inferred"),
            "actualUiReceiverIdentityProven": j.get("actualUiReceiverIdentityProven", False),
            "completeChainProven": False,
        })
    logical_items.append({
        "ownerId": r["ownerId"], "contract": pin("logical-module-contracts-v1.json", f"/records/{i}"),
        "responsibility": r["responsibility"]["value"], "paths": r["proposedPath"]["values"],
        "foundationTaskId": tid, "conditionalConsumerJoins": joins,
        "taskJoinQualification": r["taskOwnership"]["foundation"]["relationship"],
        "remaining": r["taskOwnership"]["remaining"],
        "allConsumersAssigned": False, "mode": r["mode"]["value"],
        "status": "source-contract-available; implementation-not-started",
    })

refinement_files = {"RAM-06": "input-shape-owner-v1.json", "RAM-02": "audio-measurement-owner-v1.json", "RAM-04": "debug-chrome-policy-owner-v1.json"}
runtime_items = []
for i, group in enumerate(runtime["capabilityGroups"]):
    r = copy.deepcopy(group)
    r["sourceDecision"] = pin("runtime-adoption-matrix-v1.json", f"/capabilityGroups/{i}")
    if r["id"] in refinement_files:
        name = refinement_files[r["id"]]
        refined = read(name)["decision"]
        r["selectedSourceRefinement"] = pin(name, "/decision")
        r["selectedSourceStatus"] = refined["status"]
        r["firstPartyUnits"] = refined["firstPartyUnits"]
        r["acceptance"] = "；".join(refined.get("acceptance", refined.get("resolutionBuckets", {}).get("implementationVerification", [])))
        r["sourceFollowupQualification"] = "Later selected source decision supersedes the old JS-owner followup only; all native/platform/provider acceptance stays open."
        r["remainingProviderCondition"] = {
            "RAM-02": "真实 histogram 生产、delta/reset/configured-set、多 reader/平台语义及独立 bridge 来源。",
            "RAM-04": "真实特权页/策略作用范围、profile/guest 边界及可构建 provider。",
            "RAM-06": "原生能力、setInputShape/hit-testing、坐标/DPI 及真实 RPC/平台效果。",
        }[r["id"]]
        # Preserve older wording only in its pinned source, not as current open JS work.
        r["exactRemainingPrerequisite"] = r["remainingProviderCondition"]
    r["qualifiedFullRuntime"] = False
    runtime_items.append(r)

storage_items = []
for i, d in enumerate(storage["domains"]):
    r = copy.deepcopy(d)
    r["sourceDecision"] = pin("storage-domain-map-v1.json", f"/domains/{i}")
    storage_items.append(r)

tasks = []
for i, t in enumerate(coverage["taskGroups"]):
    tid = t["taskId"]
    fids = t["featureIds"]
    tasks.append({
        **copy.deepcopy(t),
        "currentTaskContract": pin("restoration-coverage-v18.json", f"/taskGroups/{i}"),
        "sourcePreparationDependsOn": prep[tid], "integrationDependsOn": integration[tid],
        "scenarioIds": [sid for fid in fids for sid in scenario_by_feature[fid]],
        "sourcePreparationOutput": [t["primaryModule"], *t["consumerModules"]],
        "sourcePreparationExit": "按该任务的来源合同恢复控制器/状态/委托接口；逐功能保留入口条件、异常、取消及恢复分支。",
        "implementationAcceptance": "每个 featureId 对应场景经真实接收方、服务后效及持久化验证；当前规格均未执行。",
        "logicalOwnerIds": [x["ownerId"] for x in logical_items if any(j["taskId"] == tid for j in x["conditionalConsumerJoins"])],
        "ownerJoinQualification": "Only existing conditional contract joins are listed; no name-based assignment or complete-consumer claim.",
        "origin": "Current v18 coverage; v10 scheduling consolidation, implementation not started.",
    })

analysis_ms = copy.deepcopy(old["analysisMilestones"])
for a in analysis_ms:
    a.pop("currentUnresolved", None)
    a["evidencePaths"] = {
        "A1": ["feature-scope-v27.json", "legacy-entry-dispositions-v5.json", "association-overlap-decisions-v1.json", "chat-branch-decisions.json"],
        "A2": ["dependency-investigation-actions-v1.json", "runtime-adoption-matrix-v1.json", "build-input-dispositions-v1.json"],
        "A3": ["logical-module-contracts-v1.json", "storage-domain-map-v1.json", "protocol-delta-adoption-v1.json", "restoration-coverage-v18.json"],
        "A4": ["behavior-checks.md", "behavior-stop-restart.json", "analysis-stage-decisions-v4.json"],
    }[a["id"]]
    a["status"] = "in-progress; no criterion promotion by this consolidation"

open_conditions = [
    {"id": "PC-01", "class": "architecture-affecting-analysis", "tasks": ["W01", "W07", "W08"], "condition": "完整功能/模块分母和消费者闭包；模式未明项保留，不能据名称剥离。", "evidence": [pin("logical-module-contracts-v1.json", "/remaining"), pin("legacy-entry-dispositions-v5.json", "/counts"), pin("association-overlap-decisions-v1.json", "/counts")]},
    {"id": "PC-02", "class": "external-input-or-provider-development", "tasks": ["W02", "W03", "W04"], "condition": "独立运行时来源/版本/构建输入/ABI 和 15 组能力，三类原生依赖的目标环境构建。", "evidence": [pin("runtime-adoption-matrix-v1.json", "/routeDecision"), pin("runtime-adoption-matrix-v1.json", "/nativeDependencyJoins")]},
    {"id": "PC-03", "class": "external-input-or-provider-development", "tasks": ["W05"], "condition": "匹配预测语义的后台及私有服务；公开候选到实际分发版本的来源绑定。", "evidence": [pin("protocol-delta-adoption-v1.json", "/decisions/1")]},
    {"id": "PC-04", "class": "architecture-affecting-analysis", "tasks": ["W05", "W06"], "condition": "未覆盖 store 的权威 owner、根路径/认证/backend 边界及迁移责任；实际有效根另列运行验收。", "evidence": [pin("storage-domain-map-v1.json", "/remainingCoverage")]},
    {"id": "PC-05", "class": "implementation-verification", "tasks": ["W03", "W04", "W05", "W06", "W08", "W09"], "condition": "真实传输/decoder/通知/持久化和逐平台能力；完整构建安装、升级和回退。", "evidence": [pin("implementation-milestones-v9.json", "/implementationMilestones")]},
    {"id": "PC-06", "class": "behavior-analysis-with-authorization-limit", "tasks": ["W08"], "condition": "主要失败/审批/PTY及执行中取消仍缺行为对照，自动续跑未证明；已有模型授权余 0。", "evidence": [pin("behavior-stop-restart.json"), pin("analysis-stage-decisions-v4.json", "/remainingIssues/3")]},
]
next_action = {
    "issueId": "SD-05", "scope": "plugin storage authority only; no repeated complete census",
    "question": "从已保存插件合同和冻结源码定位插件配置/安装状态/cache 的 owner、写入接口及根路径来源，区分桌面本地存储与后台权威。",
    "affectedTasks": ["W05", "W06", "T17"],
    "whyArchitectureRelevant": "决定插件状态 driver 应属于客户端还是 app-server/provider，避免把多个 home/profile 根或远端状态合并。",
    "stopCondition": "交付选定插件域的调用/存储边界、原位置与未取得的 provider；不扩展为全产品存储或完整模式结论。",
    "authorization": "冻结/保存证据和自有分析脚本；不启动客户端、服务或模型，不读写个人配置。",
}
current_counts = copy.deepcopy(coverage["counts"])
current_counts.update({
    "logicalResponsibilityOwners": len(logical_items), "overlapRules": 19,
    "runtimeCapabilityGroups": len(runtime_items), "storageDomains": len(storage_items),
    "dependencyRecords": 202, "buildInputOccurrences": 30,
    "savedLegacySourceRolesUnreviewed": legacy["counts"]["entriesAwaitingDisposition"],
    "savedLegacyEntriesWithoutFeatureMapping": legacy["counts"]["entriesWithoutFeatureMapping"],
    "fullRuntimeRoutesQualified": 0, "modelSubmissionsRemaining": 0,
})
plan = {
    "schemaVersion": "restoration-plan-v10", "baselineId": BASE, "recordedAtUtc": NOW,
    "scope": old["scope"], "currentAuthorizationScope": "Analysis, design and saved-source verification only; client implementation is future work.",
    "previousSnapshot": pin("implementation-milestones-v9.json"),
    "originalPlan": pin("docs/reverse-engineering/analysis-plan.md"),
    "currentFeatureScope": pin("feature-scope-v27.json"),
    "currentScenarios": pin("feature-scope-v24-scenarios.json"),
    "restorationCoverage": pin("restoration-coverage-v18.json"),
    "currentCounts": current_counts,
    "countPrecedence": "Feature/operation/scenario identities come from v27/v24/v18; source-role status comes from v5 and 15 association decisions. Historical counters embedded in old snapshots are not current role/mode/consumer closure.",
    "completeFeatureDenominator": None,
    "analysisMilestones": analysis_ms, "originalAnalysisCriteria": old["originalAnalysisCriteria"],
    "criterionAudit": pin("analysis-stage-decisions-v4.json", "/criteria"),
    "originalCriteriaStatusChanged": False,
    "implementationMilestones": old["implementationMilestones"],
    "foundationTasks": foundations, "restorationTaskGroups": tasks,
    "sourceMappingRequiredFields": old["sourceMappingRequiredFields"],
    "logicalModuleRequiredFields": logical["requiredFields"],
    "logicalModuleWorkItems": logical_items,
    "logicalModuleOverlapRules": logical["overlapPolicy"],
    "sourcePreparationGraph": ordering["sourcePreparationGraph"],
    "integrationGraph": ordering["integrationGraph"],
    "sourcePreparationLevels": ordering["sourcePreparationLevels"],
    "integrationLevels": ordering["integrationLevels"],
    "orderingBasis": pin("restoration-current-ordering-v1.json"),
    "runtimeRouteDecision": runtime["routeDecision"], "runtimeCapabilityWorkItems": runtime_items,
    "runtimeBuildGates": runtime["buildGates"], "nativeDependencyJoins": runtime["nativeDependencyJoins"],
    "storageDomainWorkItems": storage_items, "storageImplementationPaths": storage["proposedImplementationPaths"],
    "storageBoundaryDecisions": storage["newEngineeringDecisions"],
    "storageRemaining": storage["remainingCoverage"],
    "backendAdoptionDecisions": protocol["decisions"],
    "backendAdoptionBasis": pin("protocol-delta-adoption-v1.json"),
    "thirdPartyPolicy": {
        "dependencyActions": pin("dependency-investigation-actions-v1.json"),
        "importDecisions": pin("dependency-import-decisions.json"),
        "dependencyInventory": pin("dependencies.csv"),
        "generateVendorImplementation": False,
        "rules": ["保留原发布版本证据与新工程选定版本/精确锁两套身份。", "公开包按依赖引入，bundle 内嵌实现不导出为第一方代码。", "修改的 node-pty、objc-js 与 Sparkle 各自保留源码/补丁/预编译和目标 ABI 验收。", "第一方封装与策略恢复为可维护源码；运行时和原生实现须有独立来源或独立开发路线。"],
    },
    "buildInputWorkItems": build["decisions"],
    "buildInputBasis": pin("build-input-dispositions-v1.json"),
    "modePolicy": {
        "counts": scope["counts"]["modeCounts"], "confirmedWholeFeatureExclusions": 0,
        "chatOnlyBranchDecisionGroups": 3, "branchDecisions": pin("chat-branch-decisions.json"),
        "unknownRetained": True, "sharedComposerControllerRetained": True,
        "qualification": "产品模式与认证家族、执行位置、会话类型和 build flavor 分别建模；不按名称剥离。",
    },
    "legacySourceRoleStatus": {"basis": pin("legacy-entry-dispositions-v5.json"), "counts": legacy["counts"], "qualification": "来源角色审阅完成不代表 968 项完整功能身份或行为闭合。"},
    "associationDecisionStatus": {"basis": pin("association-overlap-decisions-v1.json"), "counts": associations["counts"], "qualification": "12 关联和 3 重叠已审阅，3 业务父功能未知；不重开已解决的源码关系。"},
    "unresolvedScopeRef": pin("restoration-coverage-v18.json", "/unresolvedScope"),
    "unresolvedScopeQualification": "Retain delegated control families and other required capabilities; current legacy status is the v5/association overlay above, not older embedded pending counts.",
    "openConditions": open_conditions,
    "behaviorAuthorization": {"groupMaximum": 2, "groupConsumed": 2, "groupRemaining": 0, "initialOneConsumed": True, "basis": pin("behavior-stop-restart.json"), "newModelSubmissions": 0, "newClientLaunches": 0, "newServiceCalls": 0},
    "upgradePolicy": ["新输入版本使用新基线，记录来源/版本/哈希及工具参数。", "比较功能/条件、协议/通知、状态 schema、运行时能力、依赖修改、资源及平台行为。", "每项差异回到来源模块、受影响功能/场景与迁移/备份/回退；保存旧证据，不覆盖历史快照。"],
    "analysisExitPolicy": "Analysis/design delivery is separate from complete client implementation. All 1216 product specifications belong to later product verification; major behavior comparison and architecture-changing unknowns remain analysis obligations. Unknown counts need not mechanically reach zero.",
    "nextAnalysisAction": next_action,
    "inputPins": pins,
    "fullAnalysisCompleted": False, "implementationStarted": False,
    "independentClientBuildProven": False,
}
dump("implementation-milestones-v10.json", plan)


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |", *["| " + " | ".join(cell(x) for x in row) + " |" for row in rows]])


parts = [
    "# Codex 独立客户端恢复实施计划草案 版本 10",
    "目标是完整恢复固定基线的 Codex 界面、交互、状态、持久化和桌面集成，剥离有证据证明仅供 ChatGPT 使用的分支，通过依赖管理引入第三方实现。项目须可维护、升级、从干净环境构建打包，运行时不依赖原客户端安装路径。本轮仍为分析与实施依据，客户端实现尚未开始。",
    "当前依据：[功能台账 v27](feature-scope-v27.json)、[场景台账 v24](feature-scope-v24-scenarios.json)、[覆盖表 v18](restoration-coverage-v18.json)。373 项有限功能定义、377 项用户操作、117 项支撑、1216 条未执行产品规格，全部归入 T01 至 T48。373 不是已证明完整产品分母。45 个已发现设置容器均有局部合同；没有新增整功能排除或行为通过项。",
    "[机器可读计划](implementation-milestones-v10.json)保留每个任务的来源、完整 featureId/scenarioId、模块、外部依赖和验收条件。旧 v9 及其他编号快照保留历史含义；当前来源角色状态采用[逐 ID 处置 v5](legacy-entry-dispositions-v5.json)：968 条已保存入口的来源角色待审阅为 0，962 条无功能映射，完整功能身份闭合为 0。不得用角色盘点充抵功能验证。",
    "## 源码准备与真实集成分别排程",
    "以下输出是后续实施工作包，当前阶段只形成设计。源码接口/控制器可依照已保存合同准备；真实运行时、宿主、后台与存储集成继续受各自条件约束。源码准备成功不会把集成里程碑标为通过。",
    table(["任务", "源码准备上游", "真实集成上游", "可交付输出与准备出口"], [(f["taskId"] + " " + f["name"], ", ".join(f["sourcePreparationDependsOn"]) or "无", ", ".join(f["integrationDependsOn"]) if f["taskId"] != "W09" else "W08、T01 至 T48", "；".join(f["sourcePreparationOutput"]) + "。" + f["sourcePreparationExit"]) for f in foundations]),
    "两套依赖图均有 57 个节点，直接采用[当前排序图](restoration-current-ordering-v1.json)。源码准备从 W01/W02 开始，随后 W03/W04/W05/W06，再 W07、T01 至 T48/W08、W09；真实集成则在 W03 后才接 W04/W06。同层只表示合同依赖允许并行，不代表外部输入已取得。每个任务另保留具体账户、平台、服务、原生与持久化前置条件。",
    "## 由职责和来源决定工程结构",
    "发布 chunk 只用于来源定位，不按文件名自动拆业务模块。进程主干沿用 main/preload/renderer/worker；实际职责路径由下表与来源合同确定。原文件 hash、字节范围、转换方式、导入导出、共享状态、副作用、第三方边界与场景必须一起保留。",
    "```text\napps/desktop/src/main/              启动、窗口、宿主、系统和退出\napps/desktop/src/preload/           世界隔离、IPC、端口和注入\napps/desktop/src/renderer/app/      路由、初始化、多窗口和模式\napps/desktop/src/renderer/features/ 功能界面、控制器和状态\napps/desktop/src/workers/           独立生命周期后台工作\napps/desktop/resources/             有来源记录的资产\npackages/contracts/src/             按服务分开的 DTO/事件/错误\npackages/desktop-transport/src/     宿主、传输、信任和释放\npackages/backend-adapter/src/       app-server 与其他服务适配\npackages/runtime-adapter/src/       运行时和原生能力接口\npackages/state-storage/src/         状态、revision、保存和迁移\ntools/recovery/                     来源映射和可审查转换\ntools/build/                        自有构建、生成和打包\ntests/fixtures/                     合成目录和回归样例\n```",
    "这个主干不覆盖或重命名下面的具体职责路径，例如 app-server-client、storage-contracts 和 main 内持久化实现仍按相应证据保留。[37 个逻辑模块合同](logical-module-contracts-v1.json)各有计划要求的十项字段、251 个唯一来源范围和[19 条重叠规则](logical-module-ownership-v1.json)。37 只是既有职责集合；438 个发布文件不能充当源码模块分母。",
    table(["既有逻辑职责", "基础任务", "拟维护路径"], [(r["ownerId"] + "：" + r["responsibility"], r["foundationTaskId"], "；".join("`" + p + "`" for p in r["paths"])) for r in logical_items]),
    "条件消费者只沿用已有合同中的 taskId/featureId 连接；机器计划更新到当前覆盖表引用，并保留 inferred、实际实例未证明及不完整消费者集合的限制。不会按 Voice、Pets、Browser 或 Debug 名称自动归入 T28/T32/T26/T31。",
    "[首页分流](product-flow-ownership.md)保留同一套共享 composer/controller，将 Codex 入口策略、共享渲染和本地提交分别维护。产品模式、认证家族、执行位置、会话类别和后台资格独立建模。app-server、桌面 HTTP、注入 resolver、扩展连接和协调 socket 保持各自协议/接收方；renderer 通过合同调用宿主。",
    "## 运行时采用和原生输入",
    "[运行时采用矩阵](runtime-adoption-matrix-v1.md)选择第一方能力合同加独立 provider 的维护边界，尚未选出完整合格运行时。固定 stock Electron 42.3.0 直接替换路线已被接口及特权 URL 对照否定；公开 API、同 view 移动或普通历史复制只证明对应原语。完整资格必须覆盖独立来源/版本/校验和、构建输入、ABI、功能、目标平台和升级。",
    table(["能力组", "第一方适配路径", "当前未取得的关键条件"], [(r["id"] + " " + r["title"], "`" + r["proposedAdapterPath"] + "`", r["exactRemainingPrerequisite"]) for r in runtime_items]),
    "RAM-02 的[音频 owner](audio-measurement-owner-v1.md)、RAM-04 的[调试页策略](debug-chrome-policy-owner-v1.md)、RAM-06 的[input-shape owner](input-shape-owner-v1.md)已经解决选定 JS 生产/消费、启动/写入条件和交互合同。缺少 native provider 不重开这些源码问题；真实 histogram、特权页策略及 hit-testing/平台效果继续开放。15 组能力与历史 17 条缺失 API 路径是不同分母。",
    table(["构建关口", "覆盖原输入", "采用条件"], [(g["id"] + " " + g["purpose"], ", ".join(g["buildInputIds"]), g["decision"]) for g in runtime["buildGates"]]),
    "node-pty 的已确认修改保留补丁/适配边界，仍须目标环境 PTY 创建和释放；objc-js 的本地 Node 22 构建及 export-only load 不证明目标 Owl/Electron ABI；Sparkle 的 SPM binary 路线与源码重建分列。不能复制原安装 Owl/原生库充当恢复源码，也不能删除 guard、返回恒真能力、伪造 lease 或用空页面替代真实能力。live clone、cold restore 和 window.open 分别验证，原 clone 是否承诺 JS 堆保留仍按调用与行为证据判断。",
    "## 后台协议采用",
    "[11 个已保存差异变体](protocol-delta-adoption-v1.md)已经逐一有采用决定，维持原 466 变体比较的分母：455 相同、11 不同。无需重新全量发现协议。",
    table(["决定", "范围", "实现边界与验收"], [(d["id"], str(len(d["variants"])) + " 个变体", d["decision"] + "；" + "；".join(d["implementationChecks"])) for d in protocol["decisions"]]),
    "10 个通知差异是 subAgentActivity 的可选 nullable model/reasoningEffort；保留容忍与字段传递，既有 required 不变。实际 decoder/clone/store/通知顺序仍需验证。预测 fork 的 experimentalPredictionMode 与 ephemeral/excludeTurns、禁止 fresh-thread fallback 的合同保留；公开候选尚未具备预测语义资格，版本门槛通过、未知字段被忽略或普通 fork 成功均不能替代。实际 provider/receiver、私有服务与 npm 到源码 commit 绑定继续开放。",
    "## 存储域、隔离与恢复",
    "[11 域映射](storage-domain-map-v1.md)给出来源权威、路径规则、写入和恢复边界；实际有效根和完整全域隔离尚未证明。desktop home、execution home 与 Electron profile 分别注入；浏览器 partition、native credential 和远端账户服务另有权威。",
    table(["存储域", "职责与路径", "维护决定及所缺条件"], [(d["id"] + " " + d["name"], d["sourceAuthority"] + "；" + d["pathRule"], d["maintenanceDecision"] + "；" + d["exactRemainingPrerequisite"]) for d in storage_items]),
    "配置启动 TOML 读取与 app-server config/batchWrite、成功确认后的迁移清理分开；membership 本地状态、后台队列完成与 globalState 文件 flush 分开。snapshot 清理只保留已核实的 DB/-wal/-shm/-journal 家族，不扩大成任意 SQLite/会话迁移。拟路径保留 storage-contracts、main/persistence、settings store、backend config/auth、project membership、runtime profile 和 quit coordinator；全量 plugin/cache/download/update/automation/workspace/remote store 仍有缺口。",
    "## 全部当前功能任务与委托范围",
    "下表 48 个任务完整保留 373 项现有定义。具体 featureId、场景、输入、支撑、来源、消费者、外部依赖及逐项验收见机器计划和[覆盖表 v18](restoration-coverage-v18.json)。共享消费者不重复计算功能。",
    table(["任务", "定义数", "第一方主模块", "真实集成上游"], [(t["taskId"] + " " + t["name"], len(t["featureIds"]), "`" + t["primaryModule"] + "`", ", ".join(t["integrationDependsOn"])) for t in tasks]),
    "General/Agent 设置须接上实际消费者；任务提交、后台接受、流式通知、审批、取消、终态、导航及持久化分别验证。本地环境保存后激活失败保留独立结果；Hooks 保留管理层、来源和信任；MCP/插件/技能/连接保留共享管理器和 OAuth 生命周期。导入检测/同步/历史/后置设置与终端、文件变更、Git/PTY/worker、浏览器所有权、远程/云端和系统能力的既有委托合同仍在完整恢复范围，不能仅恢复设置页面。",
    "## 第三方依赖、构建与模式剥离",
    "[依赖清单](dependencies.csv)有 202 条记录、78 项根声明，[逐项调查动作](dependency-investigation-actions-v1.json)覆盖全部 202 条。沿用原来源/版本/许可证/修改证据，新工程独立选版本并生成精确锁；原声明范围不等于实际安装版本。React/UI、query/schema、遥测、capnweb、native/Wasm 和运行时从依赖引入，第一方封装单独恢复。修改库采用受维护依赖、独立补丁或明确适配，未知内嵌代码不作为业务源码输出。",
    "[30 条缺失构建输入](build-input-dispositions-v1.json)对应 21 个唯一原路径，逐条已有补齐决定、依赖任务及验收条件，替代实现仍为 0。TypeScript/Vite/Forge 是来源支持的构建职责候选，完整版本锁和最终运行时集成尚未完成。原 monorepo 脚本无须逐字还原，但类型生成、资源、诊断、原生编译、启动和打包职责必须由独立输入承担。",
    "当前 shared 1、unknown 372，Codex/ChatGPT 整功能正向分类为 0；这不表示未发现 Codex 分支。已明确[3 组 Chat 专用分支](chat-branch-decisions.md)，整功能排除仍为 0。共享归档、首页提交、账户访问及其他 Codex 依赖保留。12 关联/3 重叠的源码关系均已审阅，3 项业务父功能未知；不能为了清零未知而合并或删除。",
    "## 里程碑验收和仍需分析的条件",
    "M1 至 M7 完整沿用 v9 的开始条件、交付、验收与失败动作，机器计划逐字保留。主流程样例或源码隔离检查不能替代它们。",
    table(["里程碑", "上游", "完整退出条件"], [(m["id"] + " " + m["name"], ", ".join(m["dependsOn"]) or "无", "；".join(m["exitCriteria"])) for m in plan["implementationMilestones"]]),
    table(["未完成条件", "性质", "影响与证据"], [(c["id"], c["class"], ", ".join(c["tasks"]) + "：" + c["condition"]) for c in open_conditions]),
    "分析出口继续按[九标准/39 要求复核](analysis-stage-decisions-v4.md)审计；本次不提升原四项记录义务/五项部分完成的状态。1216 条产品规格不自动成为分析阶段全部跑完的前置条件；主要行为对照、足以指导实现的功能/模块关系和会改变架构的未知仍是本阶段义务。未知模式无需机械清零，缺口也不能默默移走。",
    "## 行为证据、授权与升级",
    "已有只读样例完成且可重开；停止后重启观察为 interrupted，自动续跑未证明；取消前任务提前完成，执行中取消未测。失败/审批/PTY 等主要路径仍缺对照。最初 1 次及后续最多 2 次模型样例授权均已耗尽，余 0；本次新增模型、服务、客户端启动和产品场景执行均为 0。不得从 1216 条规格或源码隔离用例推导产品通过。",
    "完整实现须逐功能验证真实服务后效、状态、失败/取消/恢复和落盘；mock、占位或未决 provider 不计完成。干净环境安装/构建/打包须使用独立应用标识、各数据根、认证来源、资产和更新配置，不读原安装路径；source-build 与预编译依赖分别列明。升级建立新基线，比较入口/条件、协议/通知、schema、依赖修改、运行时能力、资产和平台行为；每项差异回到模块、回归场景及迁移/备份/回退。",
    "下一项定向分析限定为 SD-05 插件配置/安装状态/cache 的权威与根路径，影响 W05/W06/T17：从保存合同及冻结源码分清桌面本地 driver 和 app-server/provider 写入。交付选定域的调用与存储边界、原位置和明确缺失的 provider 即停止该子步；不再重复已经完成的运行时 JS owner 或全量协议盘点。完整目标保持进行中。",
]
(STAGE / "implementation-plan-v10.md").write_text("\n\n".join(parts) + "\n")

claims = [
    ("SCOPE", "restoration-coverage-v18.json", "/counts", "373 项有限功能和 48 任务的当前数量及未实现状态。"),
    ("ORDER", "restoration-current-ordering-v1.json", "/sourcePreparationGraph", "源码准备和集成分别沿用当前 57 节点依赖图。"),
    ("LOGICAL", "logical-module-contracts-v1.json", "/records", "37 个既有职责合同作为维护工作包输入，不代表完整源码模块分母。"),
    ("RUNTIME", "runtime-adoption-matrix-v1.json", "/routeDecision", "采用能力适配边界，尚无完整合格运行时。"),
    ("INPUT", "input-shape-owner-v1.json", "/decision", "选定 input-shape 源码问题已解决，native/平台集成仍开放。"),
    ("AUDIO", "audio-measurement-owner-v1.json", "/decision", "选定音频 JS 生产/消费合同已解决，真实数据 provider 仍开放。"),
    ("DEBUG", "debug-chrome-policy-owner-v1.json", "/decision", "选定调试策略启动/写入和消费者已解决，原生策略仍开放。"),
    ("BACKEND", "protocol-delta-adoption-v1.json", "/decisions", "11 个差异变体的两类采用决定保留，预测 fork 不静默降级。"),
    ("STORAGE", "storage-domain-map-v1.json", "/domains", "11 个存储域按权威/路径/写入恢复分别维护，实际全域隔离未证明。"),
    ("BUILD", "build-input-dispositions-v1.json", "/decisions", "30 个缺失输入有处置但替代实现未完成。"),
    ("VENDOR", "dependency-investigation-actions-v1.json", "/rows", "全部 202 条依赖记录有调查动作，实施通过依赖引入第三方实现。"),
    ("ROLE", "legacy-entry-dispositions-v5.json", "/counts", "968 个保存入口的来源角色待审阅为 0；不等于功能身份完整。"),
    ("MODE", "chat-branch-decisions.json", "", "三组专用分支取舍与未知/共享依赖保留分别处理。"),
    ("GATES", "implementation-milestones-v9.json", "/implementationMilestones", "完整 M1 至 M7 验收保留，源码准备不充抵真实集成。"),
]
evidence = []
for label, name, ptr, claim in claims:
    s = pin(name)
    evidence.append({"id": "RP10-" + label, "baselineId": BASE, "claim": claim,
                     "sourcePath": s["path"], "sourceHash": s["sha256"],
                     "locator": {"jsonPointer": ptr}, "method": "saved-analysis-synthesis",
                     "confidence": "inferred", "verificationStatus": "design-synthesis; not runtime or product acceptance"})
outputs = []
for name in ["implementation-plan-v10.md", "implementation-milestones-v10.json"]:
    b = (STAGE / name).read_bytes()
    outputs.append({"path": str((OUT / name).relative_to(ROOT)), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
dump("restoration-plan-v10-provenance.json", {
    "baselineId": BASE, "recordedAtUtc": NOW, "publisher": pin("scripts/analysis/publish_restoration_plan_v10.py"),
    "inputs": pins, "outputs": outputs, "evidence": evidence,
    "derivation": "Saved-contract design consolidation; no original source extraction, new REA run, runtime launch, model/service call or client implementation.",
    "counts": {"features": 373, "tasks": 48, "scenarios": 1216, "graphNodesEach": 57, "logicalOwners": 37, "runtimeGroups": 15, "storageDomains": 11, "buildInputOccurrences": 30, "backendDeltaVariants": 11},
    "fullAnalysisCompleted": False, "originalCriteriaStatusChanged": False,
})
print(json.dumps({"stagedAt": str(STAGE), "outputs": outputs, "fullAnalysisCompleted": False}, ensure_ascii=False))
