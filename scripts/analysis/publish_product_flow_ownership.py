"""Publish bounded product entry ownership and its restoration consequences."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/product-flow-ownership-work"
RAW = OUT / "raw/product-flow-ownership"
EXPECTED_STATE = "2026-10-24T09:55:35.189346+00:00"


def read(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path, relative_to=OUT):
    data = path.read_bytes()
    return {"path": str(path.relative_to(relative_to)), "bytes": len(data), "sha256": digest(data)}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def atomic_text(path, text):
    temporary = path.with_name(path.name + ".product-flow-new")
    with temporary.open("x") as handle:
        handle.write(text)
    temporary.replace(path)


def main():
    state_path = OUT / "analysis-state.json"
    state = read(state_path)
    assert state["updatedAtUtc"] == EXPECTED_STATE, "Reconcile newer authoritative state first"
    assert not RAW.exists(), "Preserve published result"
    contracts = read(WORK / "selected-units/contracts.json")
    observations = read(WORK / "probe-observations.json")
    assert observations["counts"]["cases"] == observations["counts"]["passed"] == 27
    assert observations["counts"]["failed"] == 0
    sources = {}
    for unit in contracts["units"]:
        source = ROOT / ".analysis-local/baselines" / BASE / "extracted" / unit["sourcePath"].removeprefix("app.asar/")
        if unit["sourcePath"] not in sources:
            sources[unit["sourcePath"]] = source.read_bytes()
        data = sources[unit["sourcePath"]]
        assert digest(data) == unit["sourceHash"]
        bounds = unit["byteRange"]
        selected = data[bounds["start"]:bounds["endExclusive"]]
        assert digest(selected) == unit["spanHash"]
        assert selected == (WORK / "selected-units" / unit["sourceFilename"]).read_bytes()
    for fragment in contracts["fragments"]:
        bounds = fragment["byteRange"]
        data = sources[fragment["sourcePath"]][bounds["start"]:bounds["endExclusive"]]
        assert digest(data) == fragment["spanHash"]
        assert data.decode() == fragment["expression"]

    RAW.mkdir(parents=True)
    before = RAW / "before"
    before.mkdir()
    for path in [state_path, ROOT / "README.md", OUT / "report.md", OUT / "gaps.md", OUT / "implementation-plan.md"]:
        shutil.copy2(path, before / path.name)
    shutil.copytree(WORK / "selected-units", RAW / "selected-units")
    for name in ["probe-observations.json", "probe-observations-attempt-01.json"]:
        shutil.copy2(WORK / name, RAW / name)
    for name in ["product_flow_ownership_ast.mjs", "extract_product_flow_units.mjs", "probe_product_flow.cjs", "publish_product_flow_ownership.py"]:
        shutil.copy2(ROOT / "scripts/analysis" / name, RAW / name)

    def refs(*names):
        return [{"artifact": "raw/product-flow-ownership/selected-units/contracts.json", "jsonPointer": f"/units/{next(i for i, u in enumerate(contracts['units']) if u['name'] == name)}"} for name in names]

    facts = [
        {"id": "PF-01", "claim": "The registered / root is a child of dFs. dFs renders OJa, whose saved initialization lazily selects HomeComposerRoute. The 124-byte wrapper exports primary.t; the complete primary Program binds t to wzt.", "sourceRefs": refs("dFs", "kJa", "home-wrapper", "wzt"), "reusedRouteIds": ["ROUTE-0014", "ROUTE-0015"], "limitation": "Static registered/constructed path; initializer execution, actual React mount and account availability are not established."},
        {"id": "PF-02", "claim": "wzt reads the resolved home mode independently of capability signals and the selected product configuration. Route/state/query conditions can override chat/work. Shared-home choice is z || W===chat || te; unresolved effective mode has a loading branch.", "sourceRefs": refs("wzt", "cPt", "vS"), "observationIds": [x["id"] for x in observations["cases"] if x["id"].startswith("HOME:")], "limitation": "No global enum or entire-module product membership follows from these local comparisons."},
        {"id": "PF-03", "claim": "The Codex-specific Tzt branch renders HFt(mode:codex) and M9(isCodexHome:true). Shared Ezt renders M9(homeComposerMode:o) on its ordinary branch, including source chat and work paths. M9 and downstream jRt/NRt are shared source maintenance units.", "sourceRefs": refs("Tzt", "Ezt", "M9", "jRt", "NRt"), "limitation": "Shared-source consumer evidence does not mark every downstream operation or the 237 existing feature modes as classified."},
        {"id": "PF-04", "claim": "In NRt, Qt requires a controller, a non-null mode and chatHomeState. er is work + local execution. ht is the distinct special cloud condition. vr=Qt && l!=null && !er && !ht selects CIt; otherwise the callback selects $X, whose exact wrapper renders rpt.", "sourceRefs": refs("NRt", "$X"), "existingLocalTaskContracts": ["THREAD-START-ENTRY-001", "THREAD-START-ENTRY-003", "THREAD-START-ENTRY-005"], "observationIds": [x["id"] for x in observations["cases"] if x["id"].startswith("SUBMIT:")], "limitation": "Selected callback and source predicates were executed with owned free variables; the complete NRt, real provider, CIt internals and service effects were not executed."},
        {"id": "PF-05", "claim": "VIt explicitly associates work mode with runLocationState.effectiveLocation. Its file-drop target is chatgpt for chat or work-cloud and codex for the other branch. Chat-named state/transport adapters are therefore shared candidates for retained Work flows.", "sourceRefs": refs("VIt", "NRt"), "limitation": "Work-to-requested-Codex scope is not globally equated; retain shared candidates until all actual retained consumers are mapped."},
        {"id": "PF-06", "claim": "cPt controls mode-switch availability; it does not classify whole source files. Ezt carries local-project mapping, current pending submission cancellation, run-location choices and navigation while switching. The caller modes, permission access families, local/cloud execution, agent collaboration mode and backend session kind must remain separate dimensions.", "sourceRefs": refs("cPt", "iPt", "vS", "Ezt", "VIt"), "limitation": "No original storage or mode transition was observed in a real client."},
    ]
    decisions = [
        {"id": "PF-D01", "decision": "retain-shared-entry-and-controller", "sourceUnits": ["dFs", "kJa", "wzt", "Tzt", "Ezt", "M9", "jRt", "NRt"], "proposedPaths": ["apps/desktop/src/renderer/features/home/home-route.tsx", "apps/desktop/src/renderer/features/home/home-surface-policy.ts", "apps/desktop/src/renderer/features/composer/home-composer.tsx"], "reason": "The same source composer receives a Codex-specific entry and shared chat/work entries. Split state/entry policy and rendering responsibility; do not duplicate or delete the primary chunk.", "evidence": ["PF-01", "PF-02", "PF-03"]},
        {"id": "PF-D02", "decision": "retain-local-task-submission", "sourceUnits": ["NRt", "$X"], "taskIds": ["T03"], "featureIds": ["FSC-0048"], "proposedPaths": ["apps/desktop/src/renderer/features/tasks/local-submission.ts", "packages/contracts/src/composer-destination.ts"], "reason": "Codex home and Work-local select the existing rpt/_9e/TJe local task path. Project context with chatGpt names cannot justify removing this task implementation.", "evidence": ["PF-04", "THREAD-START-ENTRY-001", "THREAD-START-ENTRY-003"]},
        {"id": "PF-D03", "decision": "retain-remote-shared-candidate-pending-consumer-coverage", "sourceUnits": ["VIt", "NRt"], "proposedPaths": ["apps/desktop/src/renderer/features/composer/remote-composer-adapter.ts"], "reason": "Chat and ordinary Work-cloud may select CIt; a specific Work-cloud condition selects the local task composer. Do not replace these rules with chat=>remote/work=>local or remove CIt by its name.", "evidence": ["PF-04", "PF-05"], "remaining": "CIt implementation, backend contracts, and all retained Work consumers are local unresolved items; no independent service compatibility is claimed."},
        {"id": "PF-D04", "decision": "separate-chat-only-branches-without-whole-module-exclusion", "sourceUnits": ["wzt", "Ezt", "jRt"], "branches": ["jRt: c===chat && D?.isTemporaryChat renders CFt temporary-chat footer", "Ezt: inline-system-hints and chatgpt variant are explicitly selected for o===chat", "wzt: custom assistant/temporary chat route and query overrides select chat"], "reason": "These branch responsibilities can be isolated from the Codex entry. The whole components and other consumers remain retained/unknown; removing a branch is a later implementation action.", "confirmedWholeModulesExcluded": 0, "confirmedFeatureExclusionsAdded": 0, "evidence": ["PF-02", "PF-03", "PF-06"]},
    ]
    acceptance = [
        "Independent Codex home renders the shared controller and local task composer with Codex policy/utility surfaces.",
        "Retained Work-local, remote project, and any retained Work-cloud destination preserve their real destination rules, project and host identity.",
        "Pending input, mode loading, denied/upgrade states and late provider hydration cannot silently route a task to a different backend.",
        "No selectable Chat mode, custom Chat assistant or temporary-chat entry in the Codex-only profile; retained shared callbacks remain callable where required.",
        "Real cancellation, thread creation/first-turn identities, notifications and restart persistence use the existing T03 product acceptance rather than VM observations.",
        "React and other confirmed third-party implementations are imported as dependencies; proposed first-party modules do not contain their implementation copies.",
    ]
    result = {
        "schemaVersion": 1, "baselineId": BASE, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
        "status": "bounded-source-product-flow-ownership-decided; product-availability-and-full-mode-coverage-pending",
        "inputPins": [pin(OUT / n) for n in ["route-contracts.json", "route-guard-notes.json", "mode-transition-origin.json", "task-composer-entry-contracts.json", "thread-start-entry-contracts.json", "settings-mode-boundary-contracts.json", "feature-scope-v15.json", "restoration-coverage-v6.json"]],
        "sourceUnits": contracts["units"], "sourceContract": pin(RAW / "selected-units/contracts.json"),
        "isolatedObservation": pin(RAW / "probe-observations.json"),
        "failedFixtureAttempt": {**pin(RAW / "probe-observations-attempt-01.json"), "reason": "Six fixture errors: project object omitted its required gizmo.id and SC component marker was absent. Corrected only fixture dependencies; no target source changed.", "counts": {"passed": 21, "failed": 6}},
        "facts": facts, "restorationDecisions": decisions, "productAcceptance": acceptance,
        "upgradeChecks": ["Diff the exact frozen source spans for entry override precedence and render destination predicates.", "Track mode preference, access policy and execution location separately; no implicit enum coercion.", "Compare local/cloud special-case flags, project mapping, pending input adoption and cancellation before changing adapters.", "Re-run synthetic source-contract probes and the separate real-client acceptance suite; neither substitutes for the other."],
        "counts": {"sourceUnits": 14, "sourceBytes": 65682, "newPrimaryProgramsParsed": 1, "initialProgramsReparsed": 0, "sharedProgramsReparsed": 0, "sourceFacts": 6, "restorationDecisions": 4, "isolatedCasesPassed": 27, "sharedSourceMaintenanceUnits": 4, "featureDefinitionsAdded": 0, "featureModesChanged": 0, "wholeModulesExcluded": 0, "productFeaturePassesAdded": 0, "clientImplementationAdded": 0, "originalClientRunsAdded": 0, "modelSubmissionsAdded": 0},
        "sharedSourceMaintenanceUnitNames": ["wzt", "M9", "jRt", "NRt"],
        "thirdPartyPolicy": "No third-party implementation regenerated; selected frozen first-party source is evidence only. Existing version/source gaps and external dependencies retain their prior disposition.",
        "limits": ["Root registration/initialization is static evidence, not observed real UI reachability.", "CIt and entire retained consumer graph remain incomplete.", "The existing 237 feature definitions retain their mode fields and 808 product scenario specifications remain unexecuted.", "The 27 VM cases use synthetic dependency/free-variable values; no real React, IPC, backend, native capability or persistence was exercised.", "Original task/model sample authorization remains exhausted. This result consumes none."],
        "fullAnalysisCompleted": False, "clientImplementationStarted": False,
    }
    assert sum(u["bytes"] for u in contracts["units"]) == result["counts"]["sourceBytes"]
    result_path = OUT / "product-flow-ownership.json"
    assert not result_path.exists()
    write(result_path, result)
    summary_path = OUT / "product-flow-ownership.md"
    summary_path.write_text("""# 首页分流、共享 composer 与模式剥离边界

固定基线 `codex-26.1007.30912-c5b273322a83`。已将首页注册、Codex 专用入口、Chat／Work 共享入口和本地／远端 composer 的源码连接收束为四项恢复决定。选择了14个原始单位共65,682字节；27个隔离场景通过。客户端实现尚未开始。

`/ → dFs → OJa → HomeComposerRoute → primary.t → wzt` 是已确认的静态注册／构造链。`wzt` 分别选择 Codex 专用 `Tzt` 和共享 `Ezt`；两者都会向 `M9` 传入参数，后者继续调用 `jRt/NRt`。**首页主 composer 必须作为共享第一方模块保留，不能按 ChatGPT 文件名整块删除。** 初始化与真实页面挂载仍未观察。

模式和执行位置分别决定行为。`wzt` 可以依据路径、项目、草稿、共享快照、sketch、临时聊天参数和能力条件覆盖 chat/work。`cPt` 是切换可用性谓词。它们与权限 access family、agent 的 plan/default 模式和会话 kind 分开维护。

| 源码条件 | 已确认的 composer 路径 | 恢复处理 |
| --- | --- | --- |
| Codex 专用 Tzt | M9 → jRt → NRt；普通路径选择 $X → rpt | 保留共享渲染及现有本地任务链 |
| Work + local execution | `er=true`，选择 $X → rpt | 保留项目、host、权限与首 turn 身份 |
| Chat，或普通 Work-cloud | 满足 Qt 且非 er、非 ht 时，选择 CIt | 保留远端共享候选；继续核实消费者与服务契约 |
| 特定 Work-cloud 条件 ht | 可改选 $X → rpt | 保留特殊目的地规则，不能按 work 字面量统一后端 |
| 控制器缺失或模式未定 | 有独立占位／加载处理 | 不自动发送任务或默认为其他服务 |

恢复目录按职责提出：`features/home` 负责入口和 surface policy，`features/composer` 负责共享渲染及远端适配，`features/tasks` 负责本地提交，`packages/contracts` 记录目的地与状态。它们是维护建议，不是原作者目录或已生成的客户端源码。

临时 Chat footer、chat 专用 inline system hints、custom Chat assistant／temporary-chat 入口可以在入口和明确条件分支处隔离。**这些事实没有证明整个 CFt、CIt、项目设置或 chatgpt 命名模块可删除。** 原237项功能的 mode 字段、完整功能分母、808条产品场景及现有第三方依赖决定均保留。

27个场景执行完整 wzt/cPt，以及 NRt 中保存的目的地谓词和选定 render callback；依赖和闭包自由变量使用合成值。它们验证所选源码的控制与渲染分流，不证明完整 React 挂载、真实客户端、后台执行、IPC、原生能力或重启持久化。首次尝试的6个合成环境错误及21个通过结果原样保留，修正 fixture 后27项通过；原源码未改动。

实际产品验收仍须覆盖 Codex 首页、本地任务、需要保留的 Work 目的地、输入接管、取消、首 turn、通知及重启恢复。ChatGPT 专属分支剥离和所有第三方包引入在实施时按这些边界执行。详细事实、来源范围、恢复路径、验收与升级检查见[结构化结果](product-flow-ownership.json)；原始小单位和观察见[证据目录](raw/product-flow-ownership/selected-units/contracts.json)。未新增模型任务或原客户端运行。
""")
    overlay = {"result": pin(result_path), "summary": pin(summary_path), "counts": result["counts"], "taskIds": ["T03"], "featureIds": ["FSC-0048"], "featureModeOverride": False, "fullAnalysisCompleted": False}
    state["productFlowOwnership"] = overlay
    state["stageDecisions"]["productFlowOwnershipOverlay"] = overlay
    state["analysisMilestones"]["currentScopeOverlay"]["productFlowOwnershipOverlay"] = overlay
    state["stageDecisions"]["nextAction"] = {
        "issueId": "SD-01/SD-03",
        "completedSubstep": "Root home construction and shared Codex/chat/work composer source ownership decided; local/cloud destination rules retained and 27 bounded VM cases passed.",
        "question": "What concrete operations and dependency/receiver contracts do the still-pending code-review and codex-cloud settings containers expose?",
        "fixedInput": "Use the frozen factory modules settings-84199bf2f2cf.js:CodeReviewPluginSettings and settings-ae50ba9fa78a.js:CodexCloudSettings, existing entry/access contracts, and current v15/v6.",
        "closure": "Define all user operations in those two containers, connect exact receiver/dependency boundaries and acceptance conditions, and record unresolved imports locally. Do not revisit settled home mode helpers or public browser settings probes.",
        "remainingScope": "All 20 pending settings containers, full candidate/mode coverage, original acceptance criteria, runtime/build/service gaps and zero remaining model samples remain. This ordering does not exclude any original requirement.",
    }
    state["updatedAtUtc"] = result["recordedAtUtc"]
    state["fullAnalysisCompleted"] = False
    write(RAW / "publication.json", {"baselineId": BASE, "previousStateTimestamp": EXPECTED_STATE, "result": pin(result_path), "summary": pin(summary_path), "preservedStateFields": ["featureScopeCurrentView", "restorationCoverage", "latestBehaviorAuthorizationState", "buildInputDispositions"], "sourceSpansVerified": 14, "fragmentSpansVerified": len(contracts["fragments"]), "fullAnalysisCompleted": False})
    state_before = read(before / "analysis-state.json")
    for key in ["featureScopeCurrentView", "restorationCoverage", "latestBehaviorAuthorizationState", "buildInputDispositions"]:
        assert state.get(key) == state_before.get(key), key
    atomic_text(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    paragraph = "已明确[首页分流与共享 composer 边界]({link})：Codex 专用入口和 Chat／Work 入口复用主 composer；本地／远端提交还受执行位置与特殊条件影响。14个源码单位、27个隔离场景支持四项恢复决定；未变更237项功能的模式字段，未新增产品验收或模型任务。\n\n"
    for path in [ROOT / "README.md", OUT / "report.md", OUT / "gaps.md"]:
        text = path.read_text()
        title, body = text.split("\n\n", 1)
        link = f"analysis/{BASE}/product-flow-ownership.md" if path == ROOT / "README.md" else "product-flow-ownership.md"
        atomic_text(path, title + "\n\n" + paragraph.format(link=link) + body)
    plan_path = OUT / "implementation-plan.md"
    plan = plan_path.read_text()
    marker = "## 当前可以决定的工程边界\n\n"
    assert plan.count(marker) == 1
    addition = "[首页分流与共享 composer 决定](product-flow-ownership.md)补充明确：保留 Codex 与 Chat／Work 实际复用的主 composer，在入口 policy 和目的地 adapter 处分离行为。本地任务沿既有 T03 链恢复；远端 composer 的 Work 共享消费者继续调查。仅剥离明确 chat 条件下的专属分支，不能整块删除 ChatGPT 命名组件。路径、验收和升级检查见[机器可读结果](product-flow-ownership.json)。该补充未开始客户端实现，也未改变完整范围。\n\n"
    atomic_text(plan_path, plan.replace(marker, marker + addition))
    for path in RAW.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
    result_path.chmod(0o444)
    summary_path.chmod(0o444)
    print(json.dumps({"stateUpdatedAtUtc": state["updatedAtUtc"], "result": pin(result_path), "counts": result["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
