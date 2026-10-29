"""Qualify clone routes from saved contracts and a bounded offline probe."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
RAW = OUT / "raw/browser-clone-route"


def load(name):
    return json.loads((OUT / name).read_text())


def pin(name):
    value = (OUT / name).read_bytes()
    return dict(path=name, bytes=len(value), sha256=hashlib.sha256(value).hexdigest())


def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    state = load("analysis-state.json")
    assert state["analysisMilestones"]["path"] == "implementation-milestones-v8.json"
    assert not RAW.exists()
    work = ROOT / ".analysis-local/browser-clone-route-work/isolated-observations.json"
    observed = json.loads(work.read_text())
    assert observed["passed"] == 12 and observed["failed"] == 0
    assert observed["newProgramParses"] == observed["nativeCloneBehaviorsVerified"] == 0
    RAW.mkdir()
    for source, name in [
        (work, "isolated-observations.json"),
        (ROOT / "scripts/analysis/probe_browser_clone_contract.cjs", "probe_browser_clone_contract.cjs"),
        (Path(__file__), "publish_browser_clone_route.py"),
        (OUT / "analysis-state.json", "before-analysis-state.json"),
    ]:
        (RAW / name).write_bytes(source.read_bytes())
    contracts = "raw/runtime-decisions/source-01/main-CqEoQDOU/source-contracts.json"
    contract = load(contracts)
    source_refs = [{**pin(contracts), "jsonPointer": f"/units/{index}"} for index in [0, 1, 10]]
    public = load("public-runtime-comparison.json")
    public_history = next(item for item in public["publicMainObservations"] if item["id"] == "public-navigation-history-restore")
    requirements = [
        dict(id="CLONE-R01", requirement="Same-owner command context, source navigation eligibility and history-clone admission must pass before clone.",
             evidence=["BC-01", "BC-02", "BC-03", "BC-04"], status="source-guard-confirmed"),
        dict(id="CLONE-R02", requirement="A live source follows clone and adoption into a newly generated browserTabId; the original source page is not explicitly destroyed by this callable.",
             evidence=["BC-05", "BC-12"], status="source-orchestration-confirmed; actual-native-independence-unverified"),
        dict(id="CLONE-R03", requirement="The destination is announced with clone WebContents ID and lease; requested back/forward/reload is deferred through initialHistoryNavigation.",
             evidence=["BC-05", "browser-ownership-contracts.json:BROWSER-OWNER-008"], status="source-sequence-confirmed; native-navigation-unverified"),
        dict(id="CLONE-R04", requirement="Destroyed or unadoptable destinations and invalid leases must not produce successful destination messages; close/destroy and pending cleanup follow the saved branches.",
             evidence=["BC-06", "BC-07", "BC-08"], status="selected-source-failure-paths-confirmed"),
        dict(id="CLONE-R05", requirement="Only an absent live source plus reload can take the saved cold-restore/fresh path; back/forward cannot silently use it.",
             evidence=["BC-09", "BC-10", "BC-11"], status="source-branch-condition-confirmed"),
        dict(id="CLONE-R06", requirement="Route/host generation, session partition, preload/security preferences, navigation owner and lifecycle admission must remain consistent across the real host.",
             evidence=["browser-ownership-contracts.json"], status="saved-static-requirements; candidate-end-to-end-unverified"),
        dict(id="CLONE-R07", requirement="Source and destination history, back/forward/reload behavior, form state, loading/error behavior and post-clone independence need a candidate-runtime test and an original-behavior comparison where unavailable.",
             evidence=["public-runtime-comparison.json", "browser-ownership-contracts.json"], status="partially-observed-public-primitives; equivalence-unverified"),
        dict(id="CLONE-R08", requirement="Whether Owl native clone copies JS heap, renderer process state or additional session state is unknown from these first-party source units.",
             evidence=["BC-05"], status="unknown-native-property; not-an-established-source-guarantee",
             restriction="A synthetic clone and absence of caller reads do not prove native absence. Public history losing an edited heap value alone neither proves nor disproves required equivalence."),
    ]
    # Resolve the saved receiver fact by its actual identifier, rather than inventing one.
    ownership = load("browser-ownership-contracts.json")
    receiver = next(fact for fact in ownership["facts"] if "did-attach-webview" in fact["claim"])
    requirements[2]["evidence"][1] = {**pin("browser-ownership-contracts.json"), "factId": receiver["id"]}
    routes = [
        dict(id="CLONE-ROUTE-01", route="Unmodified public Electron used as a drop-in Owl runtime",
             disposition="rejected-as-drop-in", reason="Fixed probe lacks clone and Owl adoption lease APIs; existing renderer/native calls cannot run unchanged.",
             evidence=[pin("public-runtime-comparison.json")]),
        dict(id="CLONE-ROUTE-02", route="Move one retained public WebContentsView between owned windows",
             disposition="limited-transfer-primitive; insufficient-for-duplication", reason="The existing positive probe moves the same live WebContents; it does not create the second tab/history required by the clone path.",
             evidence=[pin("browser-ownership-contracts.json")]),
        dict(id="CLONE-ROUTE-03", route="First-party ownership/controller plus a second public WebContents and restored navigation history",
             disposition="retain-for-bounded-feasibility; equivalence-not-proven",
             supports="Existing public probe restored two entries at index zero and an edited form value. First-party source can own message/identity/lifecycle adaptation.",
             residual=["Back/forward/reload and source/destination independence on owned fixtures", "Session/partition/security and real ownership protocol", "Loading/error/form behavior and any additional original native guarantees", "Full browser settings/services and other Owl capabilities remain separate"],
             rule="Do not discard solely because the public history probe lost an edited JS heap value; do not accept solely because it restored a form.",
             evidence=[pin("public-runtime-comparison.json"), pin("browser-ownership-contracts.json")]),
        dict(id="CLONE-ROUTE-04", route="Independently obtainable Owl-compatible runtime or maintained native runtime changes",
             disposition="unqualified-source-and-build-route", reason="Independent distribution/source, target ABI and exact behavior are still unproven; the original installed runtime is not a qualified independent input.",
             evidence=[pin("runtime-capability-decisions.json")]),
    ]
    now = datetime.now(timezone.utc).isoformat()
    document = dict(schemaVersion="browser-clone-route/1", baselineId=BASE, recordedAtUtc=now,
        inputPins=[pin(name) for name in ["implementation-milestones-v8.json", "browser-ownership-contracts.json", "runtime-capability-decisions.json", "public-runtime-comparison.json"]],
        selectedSourceRefs=source_refs, observations=pin("raw/browser-clone-route/isolated-observations.json"),
        probeScript=pin("raw/browser-clone-route/probe_browser_clone_contract.cjs"),
        requirements=requirements, routes=routes, publicHistoryObservation=public_history,
        decision="Retain a bounded public-history adapter feasibility route while rejecting drop-in API compatibility and same-view transfer as a clone. Native Owl heap semantics remain unknown; no product equivalence or full runtime selection is claimed.",
        owner="W03", affectedSourceOwner="W04", fullRuntimeRouteSelected=False,
        counts=dict(selectedExactUnits=3, sourceCasesPassed=12, newProgramParses=0, newNativeRuns=0,
                    productScenarioPassesAdded=0, modelSubmissionsAdded=0, originalClientRunsAdded=0, clientImplementationAdded=0),
        nextAction=dict(question="Can the fixed public runtime's owned duplicate-history candidate preserve source independence and back/forward/reload behavior?",
            limits="Only synthetic local pages and the already acquired public runtime; no original-client launch, personal data, network service or model submission.",
            closure="Record entry/index/URL/form state in both source and destination before and after each navigation, ownership cleanup and failure. Keep unknown original native semantics explicit."),
        fullAnalysisCompleted=False)
    save("browser-clone-route-qualification.json", document)
    text = """# 浏览器历史克隆的合同与候选路线

第一方恢复可继续评估“自有所有权控制器加第二个公开WebContents及历史恢复”的路线。现有证据同时排除两种过度结论：普通Electron不能直接运行Owl的clone及adoption调用；一次公开历史恢复成功也不能证明完整克隆等价。[逐要求和逐路线记录](browser-clone-route-qualification.json)列出资格及残余条件。

复用已保存的三个精确源码单元，12项隔离用例全部通过。调用方先检查owner、导航资格和admission，再克隆、创建lease、登记新tab并发送消息；失败路径关闭或销毁目的对象。没有live source时，只有reload可进入冷恢复或fresh分支。历史back/forward/reload动作经pending记录交给接收生命周期执行。实际原生克隆与导航没有由这些合成对象验证。

调用方没有直接读取JS堆，也没有在这些单元中规定堆快照语义。Owl内部究竟复制哪些状态仍未知。此前公开探针恢复了两条历史和编辑后的表单，但没有保留编辑后的JS堆值；后一差异不能单独否定所有第一方适配方案，也不能说明原Owl一定不保留堆。

| 路线 | 当前处置 | 关键条件 |
| --- | --- | --- |
| 普通Electron直接替换Owl | 直接兼容路线已排除 | 缺少clone和adoption接口 |
| 移动同一个WebContentsView | 仅支持窗口转移原语 | 不产生第二个tab或独立历史 |
| 自有控制器加第二个WebContents及历史恢复 | 保留局部可行性验证 | 导航、源与目的独立性、会话分区、安全和生命周期 |
| 独立兼容运行时或原生修改 | 尚未取得资格 | 来源、版本、构建、ABI和实际语义 |

下一步使用已取得的固定公开运行时及自建本地页面，核对重复历史后的back、forward、reload和两页独立性。该检查不运行原客户端或提交模型任务。原Owl语义、四类特权浏览器设置及其余运行时能力分别保持未解决；最终独立运行时路线尚未选定。
"""
    with (OUT / "browser-clone-route-qualification.md").open("x") as stream:
        stream.write(text)
    state["browserCloneRouteQualification"] = dict(**pin("browser-clone-route-qualification.json"),
        summary=pin("browser-clone-route-qualification.md"), counts=document["counts"], owner="W03", fullAnalysisCompleted=False)
    overlay = dict(result=pin("browser-clone-route-qualification.json"), summary=pin("browser-clone-route-qualification.md"), fullRuntimeRouteSelected=False)
    state["analysisMilestones"]["currentScopeOverlay"]["browserCloneRouteOverlay"] = overlay
    state["stageDecisions"]["browserCloneRouteOverlay"] = overlay
    state["stageDecisions"]["nextAction"] = dict(issueId="SD-02", completedSubstep=document["decision"],
        fixedInput="Pinned existing public Electron and owned synthetic history pages; reuse saved source selections.",
        question=document["nextAction"]["question"], closure=document["nextAction"]["closure"],
        deferredDedicatedVerification="Native Owl semantics, full runtime qualification, pending scope/mode and product acceptance remain open. No model authorization remains.")
    state["updatedAtUtc"] = now
    (OUT / "analysis-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    for name in ["report.md", "gaps.md"]:
        target = OUT / name
        lines = target.read_text().splitlines()
        paragraph = "[浏览器克隆路线核对](browser-clone-route-qualification.md)将调用方可证明的导航与所有权要求同未知原生堆语义分开；12项新增隔离用例通过。保留公开历史适配的局部验证路线，完整运行时与产品行为尚未通过。"
        target.write_text(lines[0] + "\n\n" + paragraph + "\n\n" + "\n".join(lines[1:]).lstrip() + "\n")
    print(json.dumps(document["counts"]))


if __name__ == "__main__":
    main()
