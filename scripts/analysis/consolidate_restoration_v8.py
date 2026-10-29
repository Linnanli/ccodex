"""Publish the current restoration design with separate source/integration gates.

Reads existing analysis only. Does not build or run the original/client runtime.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASELINE
RAW = OUT / "raw" / "restoration-plan-v8"
EXPECTED_STATE = "2026-10-24T10:43:48.647876+00:00"


def read(name):
    return json.loads((OUT / name).read_text())


def pin(name):
    data = (OUT / name).read_bytes()
    return {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def dump(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def check_graph(nodes, edge_key):
    indexed = {node["id"]: node for node in nodes}
    assert len(indexed) == len(nodes)
    finished, active = set(), set()

    def visit(node_id):
        assert node_id in indexed, node_id
        assert node_id not in active, f"cycle: {node_id}"
        if node_id in finished:
            return
        active.add(node_id)
        for dependency in indexed[node_id][edge_key]:
            visit(dependency)
        active.remove(node_id)
        finished.add(node_id)

    for node_id in indexed:
        visit(node_id)


def main():
    state = read("analysis-state.json")
    assert state["updatedAtUtc"] == EXPECTED_STATE, "Reconcile current state before publishing."
    assert not RAW.exists(), "Immutable publication already exists."
    current = state["featureScopeCurrentView"]
    ledger_name = current["ledger"]["path"]
    scenario_name = current["scenarios"]["path"]
    coverage_name = state["restorationCoverage"]["path"]
    ledger, coverage = read(ledger_name), read(coverage_name)
    old = read("implementation-milestones-v7.json")
    counts = coverage["counts"]
    tasks = coverage["taskGroups"]
    task_ids = [task["taskId"] for task in tasks]
    feature_ids = [feature["featureId"] for feature in coverage["features"]]
    assert len(feature_ids) == len(set(feature_ids)) == counts["finiteFeatureDefinitions"] == 274
    assert len(task_ids) == len(set(task_ids)) == 33
    assert {feature["featureId"] for feature in ledger["features"]} == set(feature_ids)
    assert counts["productScenarioSpecifications"] == 919
    assert not state["fullAnalysisCompleted"]

    names = [
        ledger_name, scenario_name, coverage_name, "implementation-milestones-v7.json",
        "implementation-plan-v7.md", "analysis-stage-decisions-v2.json",
        "build-input-dispositions-v1.json", "dependency-import-decisions.json",
        "product-flow-ownership.json", "native-browser-settings-comparison.json",
        "public-runtime-comparison.json", "runtime-capability-decisions.json",
        "browser-ownership-contracts.json", "global-state-storage-origin.json",
        "main-persistence-policy.json", "shutdown-persistence.json",
    ]
    inputs = [pin(name) for name in names]
    for record in [current["ledger"], current["scenarios"], state["restorationCoverage"]]:
        assert pin(record["path"]) == {key: record[key] for key in ("path", "bytes", "sha256")}

    now = datetime.now(timezone.utc).isoformat()
    RAW.mkdir(parents=True)
    for source, target in [
        (OUT / "analysis-state.json", RAW / "before-analysis-state.json"),
        (ROOT / "README.md", RAW / "before-README.md"),
        (OUT / "report.md", RAW / "before-report.md"),
        (OUT / "gaps.md", RAW / "before-gaps.md"),
        (Path(__file__), RAW / Path(__file__).name),
    ]:
        target.write_bytes(source.read_bytes())

    def decision(identifier, title, finding, choice, affected, evidence, verification):
        return dict(id=identifier, title=title, finding=finding, decision=choice,
                    affectedTasks=affected, evidence=[pin(name) for name in evidence],
                    acceptance=verification, implementationStarted=False)

    decisions = [
        decision("RD8-01", "Separate source preparation from integration acceptance",
            "v7 gives W06 a W03 dependency and M2 a whole-M1 dependency. These are valid integration gates, but overconstrain preparation of source contracts and state logic.",
            "Use two scheduling graphs. Source preparation uses evidenced contracts; native/host/product acceptance keeps runtime, provider, persistence and complete-scope gates. Finishing source preparation does not finish its parent milestone.",
            ["W01", "W02", "W04", "W05", "W06", "W07", *task_ids],
            ["implementation-milestones-v7.json", "global-state-storage-origin.json", "shutdown-persistence.json"],
            ["The source graph has no W03 integration prerequisite for W01/W02/W05/W06 preparation.",
             "Real persistence, isolation, permissions, renderer lifecycle and packaging still require the appropriate runtime integration.",
             "M1 through M7 remain future milestones; this publication starts no client implementation."]),
        decision("RD8-02", "Preserve one shared composer implementation",
            "The saved product-flow contract connects the Codex-specific entry and chat/work entries to shared composer/controller bindings; local task routing also has Work consumers.",
            "Place entry policy in home-surface-policy, retain shared home-composer and local-submission, and isolate only evidenced chat-specific render branches. Do not copy the shared composer or drop the primary chunk.",
            ["T03", "W07"], ["product-flow-ownership.json"],
            ["Codex entry reaches the shared controller and local task path with its own entry policy.",
             "Location, authentication family, product mode, session kind and backend eligibility remain distinct values.",
             "Only branch-level exclusions with a checked consumer closure may be removed."]),
        decision("RD8-03", "Give privileged browser settings an explicit runtime and service gate",
            "The fixed public Electron guest probe rejected eight privileged URLs while owned host/guest controls passed; direct URL embedding does not supply the four settings families.",
            "Treat contact information, password manager, extensions and site settings as runtime/service requirements owned by W03 and consumed by T26. Keep both a suitable independent runtime and equivalent first-party UI/service adapters as unqualified alternatives. Reject direct stock embedding as a completed route.",
            ["W03", "T26"], ["native-browser-settings-comparison.json", "public-runtime-comparison.json"],
            ["Each family has actual independent data/service operations, capability and partition checks.",
             "Mount identity, disposal, navigation/history, theme and late-response cleanup match caller contracts.",
             "No route qualifies through a URL substitution, empty page, original installed runtime copy or a fabricated success flag."]),
        decision("RD8-04", "Update final scope dependencies to all current task groups",
            "v7 embeds 103 definitions and W09 names T01 through T16, whereas current coverage contains 274 definitions owned by T01 through T33.",
            "Freeze v17/v8 as this plan's input snapshot, carry all 33 task groups, 64 support operations, six shared-consumer relations and every unresolved-scope record, and make final acceptance depend on all 33 groups plus unresolved scope closure.",
            ["W09", *task_ids], [ledger_name, coverage_name],
            ["Every current feature has exactly one owning task and retains its current source, scenarios and conditions.",
             "The 15 pending settings pages, 968 legacy records, associations and other required capabilities remain in scope.",
             "The 919 unexecuted product specifications and unknown modes are not promoted to passed or excluded."]),
    ]

    # Preparatory edges describe source/interface work, not actual integration.
    source_dependencies = {
        "W01": [], "W02": [], "W03": ["W01", "W02"],
        "W04": ["W01"], "W05": ["W01", "W02"], "W06": ["W01"],
        "W07": ["W01", "W04", "W06"], "W08": ["W04", "W05", "W06", "W07"],
        "W09": ["W08", *task_ids],
    }
    foundations = copy.deepcopy(old["foundationTasks"])
    for task in foundations:
        task["sourcePreparationDependsOn"] = source_dependencies[task["taskId"]]
        task["integrationDependsOn"] = copy.deepcopy(task["dependsOn"])
        task["sourcePreparationStatus"] = "planned-not-implemented"
    foundations[-1]["dependsOn"] = ["W08", *task_ids]
    foundations[-1]["integrationDependsOn"] = ["W08", *task_ids]
    foundations[-1]["additionalAcceptanceGates"] = ["complete-discovered-scope", "all-retained-product-results", "clean-independent-build", "third-party-externalization", "mode-and-shared-closure"]

    source_tasks = []
    for task in tasks:
        source_tasks.append(dict(id=task["taskId"], dependsOn=["W01", "W05", "W06", "W07"],
            status="design-inputs-available-implementation-not-started",
            taskRef={**pin(coverage_name), "jsonPointer": f"/taskGroups/{tasks.index(task)}"},
            qualification="Only the saved source-level contracts can be prepared; actual native/provider/UI behavior remains an integration prerequisite."))
    source_graph = [dict(id=t["taskId"], dependsOn=t["sourcePreparationDependsOn"]) for t in foundations] + source_tasks
    integration_graph = [dict(id=t["taskId"], dependsOn=t["integrationDependsOn"]) for t in foundations]
    integration_graph += [dict(id=t["taskId"], dependsOn=t["dependsOn"]) for t in tasks]
    check_graph(source_graph, "dependsOn")
    check_graph(integration_graph, "dependsOn")

    milestone = copy.deepcopy(old)
    milestone.update(schemaVersion="implementation-milestones/8", recordedAtUtc=now,
        previousSnapshot=pin("implementation-milestones-v7.json"),
        currentFeatureScope=pin(ledger_name), currentScenarios=pin(scenario_name),
        restorationCoverage=pin(coverage_name), foundationTasks=foundations,
        restorationTaskGroups=copy.deepcopy(tasks), unresolvedScope=copy.deepcopy(coverage["unresolvedScope"]),
        supportOperations=copy.deepcopy(coverage["supportOperations"]),
        sharedGoalConsumerRelations=copy.deepcopy(coverage["sharedGoalConsumerRelations"]),
        sourcePreparationTasks=source_tasks, sourcePreparationGraph=source_graph,
        integrationGraph=integration_graph, restorationDecisions=decisions,
        behaviorAuthorization=copy.deepcopy(state["latestBehaviorAuthorizationState"]),
        currentStatus="current-source-design-consolidated-integration-gates-preserved",
        fullAnalysisCompleted=False, implementationCompleted=False,
        currentCounts=copy.deepcopy(counts), originalCriteriaStatusChanged=False)
    # Rewrite current analysis pointers; leave original requirements/exit criteria intact.
    for item in milestone["analysisMilestones"]:
        item["evidencePaths"] = [name for name in item["evidencePaths"] if not name.startswith(("feature-scope-v", "restoration-coverage-v", "implementation-plan-v"))]
        item["evidencePaths"] += [ledger_name, coverage_name]
        if item["id"] == "A1":
            item["currentUnresolved"] = copy.deepcopy(current["counts"])
            item["currentUnresolved"]["pendingSettingsOperationContainers"] = 15
        if item["id"] == "A2":
            item["evidencePaths"] += ["native-browser-settings-comparison.json"]
    milestone["nextAnalysisActions"] = [
        dict(id="NEXT-01", question="Bound the live-history clone requirement using existing caller and ownership contracts, separating required observable behavior from unproved heap-copy assumptions.",
             inputs=["browser-ownership-contracts.json", "public-runtime-comparison.json", "runtime-capability-decisions.json"],
             exit="A requirement/route table states what each candidate actually preserves, rejects false substitutes, and names the exact residual native or original-behavior evidence needed. Reuse selected units; no whole-Program reparse or original-client/model run."),
        dict(id="NEXT-02", question="Finish the 15 already-discovered settings containers and semantic dispositions of saved legacy groups without rescanning settled sources.",
             inputs=[coverage_name, "entry-family-map.json"],
             exit="Every discovered item has a semantic disposition; remaining source selections answer only a named missing contract or mode boundary."),
        dict(id="NEXT-03", question="Reconcile original nine analysis criteria with full scope, source maps, dependencies and major behavior observations.",
             inputs=["analysis-stage-decisions-v2.json", "behavior-stop-restart.json", coverage_name],
             exit="No unverified product scenario is marked passed; architecture-changing gaps stay open, and unknown items retain exact conditions."),
    ]
    dump("implementation-milestones-v8.json", milestone)

    rows = []
    for task in tasks:
        rows.append(f"| {task['taskId']} {task['name']} | {len(task['featureIds'])} | `{task['primaryModule']}` | {', '.join(task['dependsOn'])} |")
    pending = ", ".join(item["slug"] for item in coverage["unresolvedScope"]["pendingSettingsPages"])
    plan = f"""# Codex 独立客户端恢复实施计划草案 版本 8

目标是完整恢复固定基线的 Codex 行为，剥离有证据证明仅供 ChatGPT 使用的分支，并通过独立依赖引入第三方组件。项目须能维护、升级及从干净环境构建打包，运行时无需读取原客户端安装目录。本阶段交付分析与实施依据；客户端实现尚未开始。

本版采用[功能台账 v17]({ledger_name})、[场景台账]({scenario_name})和[恢复覆盖表 v8]({coverage_name})：274项有限定义、278项用户操作、64项支撑、919条未执行产品规格，分别归属33个恢复任务。完整产品分母仍未知。旧版计划中的103项定义及T01至T16排程由本版替代。

## 源码恢复与集成前置条件

源码准备和真实集成分别排程。合同、纯状态转换、请求编码、界面控制器及构建配置设计可依据已有契约进行；运行时选择影响原生驱动、宿主接入、真实持久化、安装和打包。源码准备完成后，所属里程碑仍须通过真实集成验收。

| 工作 | 源码准备的前置条件 | 真实集成的前置条件 |
| --- | --- | --- |
| W01 合同与来源映射 | 固定来源和既有请求、事件及生命周期契约 | 对应真实provider、错误与释放行为 |
| W02 独立构建输入 | 已登记依赖、30项构建输入及来源政策 | 完整精确锁、运行时集成、干净构建和打包 |
| W03 运行时与平台 | W01、W02；逐能力接口及候选路线 | 独立来源、版本、ABI和全部所需能力实测 |
| W04 桌面传输与宿主 | W01；可先恢复编码和生命周期状态机 | W01、W03；真实IPC、身份、信任与端口释放 |
| W05 后台适配 | W01、W02；按已比较的schema与差异设计 | 实际后台版本、provider、服务及通知语义 |
| W06 状态与持久化 | W01；可先恢复schema、revision和保存状态机 | W01、W03；实际文件驱动、原子替换、退出与迁移 |
| W07 应用壳与模式 | W01、W04、W06的接口和状态合同 | W04、W06的真实集成和窗口生命周期 |
| T01至T33 功能恢复 | 对应有来源的界面、状态、后台和存储接口 | 下表所列原有依赖、具体账户条件和逐功能后效 |
| W09 最终剥离与验收 | W08及全部33个任务的设计结果 | 全部任务、完整范围处置、独立构建及实际产品结果 |

[机器可读里程碑](implementation-milestones-v8.json)保存两套依赖图。M1至M7的原有整体验收条件继续有效；源码准备不会把M1标为完成，也不会替代真实IPC、权限、服务或落盘结果。后续实施可以先恢复证据充分的源码，完整发布必须通过全部集成条件。

## 工程结构与共享边界

按进程、状态所有权及生命周期组织第一方源码；发布chunk仅作来源定位。每个转换记录原文件hash、字节范围、导入导出、副作用、第三方边界、目标模块与验收场景。建议目录为：

```text
apps/desktop/src/main/                 启动、窗口、宿主、系统与退出
apps/desktop/src/preload/              世界隔离、IPC、端口与浏览器注入
apps/desktop/src/renderer/app/         路由、初始化与窗口状态
apps/desktop/src/renderer/features/    功能界面、控制器和状态
apps/desktop/src/workers/              独立生命周期后台工作
apps/desktop/resources/               有来源记录的资源
packages/contracts/src/               DTO、事件、错误和能力合同
packages/desktop-transport/src/        传输、宿主选择、信任和释放
packages/backend-adapter/src/          app-server及其他服务适配
packages/runtime-adapter/src/          独立运行时和原生能力接口
packages/state-storage/src/            schema、revision、保存与迁移
tools/recovery/                        来源映射和可审查转换
tools/build/                           自有构建、生成和打包工具
tests/fixtures/                        合成目录与回归样例
```

[首页分流证据](product-flow-ownership.md)要求保留同一套共享composer和controller。Codex入口策略放入`home-surface-policy`，共享渲染放入`home-composer`，本地任务提交放入`local-submission`。产品模式、认证家族、执行位置、会话类别和后台资格分别建模；不能按`chatgpt`字符串删除本地任务或共享组件。已定位的chat专属渲染分支可先隔离，删除前仍检查全部消费者和依赖。

app-server、桌面HTTP、注入resolver、扩展连接和协调socket各自维护协议及接收方。renderer通过合同调用宿主；不会直接导入main或原生实现。设置保存与实际消费者效果分开验收。

## 运行时路线与发布条件

固定公开Electron 42.3.0的[实测对照](public-runtime-comparison.md)不支持直接替换Owl：任务管理器、更新策略、WebContents clone与lease、Node网络及IPC权限均有差异。公开API或同view移动只支持对应原语，不能据此宣称完整运行时兼容。

[浏览器设置对照](native-browser-settings-comparison.md)又确认：当前guest嵌入拒绝八个特权URL，而自建host和guest正例通过。联系人、密码管理、扩展和站点设置四类能力归W03的运行时及服务接口所有，T26消费这些接口。直接嵌入stock Electron内部URL的路线已被该实测否定；可独立取得的适用运行时、以及具有等价数据服务的第一方设置界面仍是待验证候选。

运行时资格须同时覆盖功能、来源、版本、ABI、构建、升级和第三方边界。空页面、改URL、复制原安装中的Owl或删启动guard均不能满足资格。live-history clone的必要可观察行为须从调用合同与实际证据界定；公开探针未保留JS堆值这一事实，不能单独证明原clone承诺保留JS堆。

运行时未取得资格时，相关集成与发布保持未通过；其他已有契约的源码准备保留独立排程。未选择最终运行时，不宣称完整独立构建已经可行。

## 功能恢复任务

下表列出全部当前所有者。具体操作、支撑、来源、条件、场景及六项共享消费者关系保留在[恢复覆盖表]({coverage_name})；同一功能不会因多个入口而重复恢复。

| 任务 | 定义数 | 第一方主模块 | 真实集成依赖 |
| --- | --- | --- | --- |
{chr(10).join(rows)}

General与Agent偏好须接上实际配置消费者；任务生命周期分别检查后台接受、流式事件、审批、取消、终态、导航和持久化。本地环境保存成功后激活失败仍保留独立结果；Hooks保留来源、管理层和信任；MCP、插件、技能与连接保留共享管理器和OAuth生命周期。导入检测、同步、历史和后置设置分别调用自己的服务。终端、文件与变更、浏览器所有权、云端和系统能力的既有合同继续属于完整恢复范围。

## 第三方依赖与构建输入

[依赖清单](dependencies.csv)的202项记录、78项根声明及其版本依据继续保留。原发布包仅6项根路径安装版本已确认；新工程生成自己的精确锁，并分别记录原版本证据、新选版本及兼容结果。未确认的内嵌实现不会作为第一方源码导出。React及UI、query/schema、遥测、capnweb、native和Wasm按明确接口引入；上游修改用受维护依赖、补丁或第一方适配分别处理。

[30项构建输入](build-input-dispositions-v1.json)已有处置但替代实现为0。TypeScript、Vite和Forge作为来源支持的构建职责候选，自行建立工作区、分进程构建和打包配置；具体版本与最终运行时集成在新工程锁中确定。原monorepo脚本不必逐字恢复，其类型生成、资源、诊断、原生构建和打包职责必须由独立工具承担。普通包锁、native ABI和私有运行时输入分别验收，不能互相代替。

## 未完成范围与分析出口

本版冻结的是计划输入快照，完整目标继续保留。45个设置容器中30个已有局部合同，以下15个仍待操作归属：{pending}。968条旧入口记录、12项关联待办、跨功能重叠与其他能力缺口完整沿用覆盖表；不能把入口数当作用户功能数，也不能把未展开条目视为不存在。

274项定义的模式仍为unknown，确认ChatGPT整项排除为0。unknown表示判定待补，先保留；它不使已有合同失效，也不允许删除该能力。最终剥离须逐分支证明模式条件和共享依赖闭包。新发现的基线能力仍登记并影响完整验收。

下一项先核对live-history clone的真实合同与候选路线：复用已有caller和ownership选择，区分必要后效与未经证明的堆复制假设，形成逐要求的来源、候选支持和残余证据表。随后完成已知待定容器与旧入口语义处置。只有会改变功能、共享边界、依赖或独立构建决定的问题才扩大源码选择；已闭合的定位不重新解析。

## 行为验收与升级

既有只读样例已完成并可重新打开；执行中停止再重启得到interrupted，尚无自动续跑证明；取消前任务提前完成，执行中取消仍待验证。原授权的1加2次模型样例全部用完。本版新增模型提交、原客户端运行和真实服务调用均为0。919条产品规格仍为未执行；隔离源码测试只证明所选逻辑。

最终验收覆盖每个保留功能的正常、失败、取消、恢复和具体条件，核对真实状态、服务后效与持久化；mock或占位不计完成。干净构建、安装、打包、独立标识及存储路径不得读取原安装。升级建立新基线，比较功能、入口条件、协议、schema、依赖修改、资源和平台行为；每项差异映射到模块、回归场景及迁移回退。

原九项分析标准保持四项资料或范围义务已有交付、五项部分完成。结构和排程已对齐当前证据；完整功能分母、模式、运行时资格和主要行为缺口继续待关闭。
"""
    with (OUT / "implementation-plan-v8.md").open("x") as stream:
        stream.write(plan)

    validation = dict(baselineId=BASELINE, checkedAtUtc=now,
        inputPinsChecked=len(inputs), featureOwnersChecked=len(feature_ids),
        taskGroupsChecked=len(task_ids), sourceGraphNodes=len(source_graph), integrationGraphNodes=len(integration_graph),
        sourceGraphAcyclic=True, integrationGraphAcyclic=True,
        finalGateCoversAllTaskGroups=True, unresolvedScopePreserved=milestone["unresolvedScope"] == coverage["unresolvedScope"],
        supportOperationsPreserved=milestone["supportOperations"] == coverage["supportOperations"],
        sharedConsumerRelationsPreserved=milestone["sharedGoalConsumerRelations"] == coverage["sharedGoalConsumerRelations"],
        originalMilestoneExitCriteriaPreserved=milestone["implementationMilestones"] == old["implementationMilestones"],
        behaviorAuthorizationPreserved=True, featureDefinitionsAdded=0, productScenarioPassesAdded=0,
        clientImplementationAdded=0, modelSubmissionsAdded=0, originalClientRunsAdded=0,
        originalCriteriaStatusChanged=False, fullAnalysisCompleted=False)
    assert all(validation[key] for key in ["unresolvedScopePreserved", "supportOperationsPreserved", "sharedConsumerRelationsPreserved", "originalMilestoneExitCriteriaPreserved"])
    dump("raw/restoration-plan-v8/validation.json", validation)
    provenance = dict(baselineId=BASELINE, recordedAtUtc=now,
        method="Consolidate existing pinned contracts; split source scheduling from actual integration without changing full-scope acceptance.",
        inputPins=inputs, previousState=pin("raw/restoration-plan-v8/before-analysis-state.json"),
        script=pin("raw/restoration-plan-v8/consolidate_restoration_v8.py"),
        outputs=[pin("implementation-milestones-v8.json"), pin("implementation-plan-v8.md"), pin("raw/restoration-plan-v8/validation.json")],
        counts=counts, fullAnalysisCompleted=False)
    dump("restoration-plan-v8-provenance.json", provenance)

    previous_milestones = copy.deepcopy(state["analysisMilestones"])
    state["analysisMilestones"] = dict(**pin("implementation-milestones-v8.json"),
        plan=pin("implementation-plan-v8.md"), coverage=pin(coverage_name),
        buildInputs=pin("build-input-dispositions-v1.json"), provenance=pin("restoration-plan-v8-provenance.json"),
        previousSnapshot={key: previous_milestones[key] for key in ["path", "bytes", "sha256"]},
        currentAnalysisPriority="A2/A3-runtime-contract-qualification", fullAnalysisCompleted=False,
        currentScopeOverlay=copy.deepcopy(previous_milestones["currentScopeOverlay"]))
    state["stageDecisions"]["latestConsolidation"] = dict(
        plan=pin("implementation-plan-v8.md"), milestones=pin("implementation-milestones-v8.json"),
        coverage=pin(coverage_name), buildInputs=pin("build-input-dispositions-v1.json"),
        provenance=pin("restoration-plan-v8-provenance.json"), validation=pin("raw/restoration-plan-v8/validation.json"),
        finiteFeatureDefinitions=len(feature_ids), productSpecificationsUnexecuted=919,
        restorationTaskGroups=len(task_ids), sourcePreparationAndIntegrationGatesSeparated=True,
        fullAnalysisCompleted=False, clientImplementationStarted=False)
    state["stageDecisions"]["nextAction"] = dict(
        issueId="SD-02/SD-06", completedSubstep="Current 274 definitions and T01-T33 consolidated; source preparation and actual integration now have separate dependency graphs.",
        fixedInput="Existing browser-ownership/runtime contracts and fixed public-runtime probe; preserve v17/v8 full-scope backlog.",
        question=milestone["nextAnalysisActions"][0]["question"],
        closure=milestone["nextAnalysisActions"][0]["exit"],
        deferredDedicatedVerification="Native behavior, independent runtime qualification, actual product scenarios, 15 pending containers and full mode/legacy dispositions remain open. No model authorization remains.")
    state["updatedAtUtc"] = now
    assert state["latestBehaviorAuthorizationState"] == read("analysis-state.json")["latestBehaviorAuthorizationState"]
    assert state["analysisMilestones"]["currentScopeOverlay"] == previous_milestones["currentScopeOverlay"]
    (OUT / "analysis-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    summary = "[当前统一实施计划](implementation-plan-v8.md)已覆盖274项定义和T01至T33，区分源码准备与真实集成的前置条件；最终验收仍包含全部功能、运行时资格、独立构建和模式剥离。15个设置容器及其余完整范围缺口保留。此批没有新增客户端实现、模型提交或产品通过数。"
    for name in ["report.md", "gaps.md"]:
        target = OUT / name
        lines = target.read_text().splitlines()
        target.write_text(lines[0] + "\n\n" + summary + " 当前以[状态文件](analysis-state.json)为准；下文各旧批次描述保留为历史记录。\n\n" + "\n".join(lines[1:]).lstrip() + "\n")
    root_readme = ROOT / "README.md"
    lines = root_readme.read_text().splitlines()
    relative = f"analysis/{BASELINE}/implementation-plan-v8.md"
    root_readme.write_text(lines[0] + f"\n\n当前恢复设计见[实施计划版本8]({relative})：274项定义、33组任务；源码准备与真实集成分别排程，完整范围和最终验收条件保留。\n\n" + "\n".join(lines[1:]).lstrip() + "\n")
    print(json.dumps(validation, ensure_ascii=False))


if __name__ == "__main__":
    main()
