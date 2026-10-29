"""Publish positive and negative observations of the owned public history probe."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/public-runtime-comparison-work"
RAW = OUT / "raw/public-history-duplicate"


def load(path):
    return json.loads(path.read_text())


def pin(name):
    value = (OUT / name).read_bytes()
    return dict(path=name, bytes=len(value), sha256=hashlib.sha256(value).hexdigest())


def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    state = load(OUT / "analysis-state.json")
    assert state["browserCloneRouteQualification"]["path"] == "browser-clone-route-qualification.json"
    assert not RAW.exists()
    successful = WORK / "owned-history-duplicate-02"
    observed = load(successful / "data/runtime-observations.json")
    receipts = [load(WORK / attempt / "receipt.json") for attempt in ["owned-history-duplicate-01", "owned-history-duplicate-02"]]
    assert receipts[0]["exitCode"] == -6 and receipts[1]["exitCode"] == 0
    assert not (WORK / "owned-history-duplicate-01/data/runtime-observations.json").exists()
    assert all(receipt["runtimeIntegrity"]["frameworkMatchesChecksummedArchive"] for receipt in receipts)
    assert observed["counts"]["casesPassed"] == 12 and observed["counts"]["casesFailed"] == 1
    failures = [item for item in observed["cases"] if not item["passed"]]
    assert [item["id"] for item in failures] == ["HD-03"]
    assert failures[0]["actual"]["sourceInput"] == "edited-source-C"
    assert failures[0]["actual"]["destinationInput"] == "initial-C"
    assert observed["errors"] == observed["deniedRequests"] == []
    assert len(observed["cleanup"]) == 2 and all(x["isDestroyed"] for x in observed["cleanup"])
    process_check = load(successful / "process-check.json")
    assert process_check["remainingOwnedProcesses"] == []
    RAW.mkdir()
    for attempt in ["owned-history-duplicate-01", "owned-history-duplicate-02"]:
        source = WORK / attempt
        destination = RAW / attempt
        destination.mkdir()
        for name in ["receipt.json", "stdout.txt", "stderr.txt", "process-check.json", "run_public_electron_probe.py", "probe_public_history_duplicate.cjs"]:
            if (source / name).exists(): (destination / name).write_bytes((source / name).read_bytes())
        if (source / "data/runtime-observations.json").exists():
            (destination / "runtime-observations.json").write_bytes((source / "data/runtime-observations.json").read_bytes())
        if (source / "data/fixtures").exists():
            (destination / "fixtures").mkdir()
            for fixture in (source / "data/fixtures").glob("*.html"):
                (destination / "fixtures" / fixture.name).write_bytes(fixture.read_bytes())
    (RAW / "before-analysis-state.json").write_bytes((OUT / "analysis-state.json").read_bytes())
    (RAW / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    history_doc = ROOT / ".analysis-local/public-runtime-comparison-work/fetch-02/electron-navigation-history-doc.txt"
    expected = "a8d616425fb83011f9fe5a6f2b841ca02d4489b2c1a550ba175cf2af8134b059"
    assert hashlib.sha256(history_doc.read_bytes()).hexdigest() == expected
    (RAW / "electron-navigation-history-doc.txt").write_bytes(history_doc.read_bytes())
    files = sorted(str(path.relative_to(OUT)) for path in RAW.rglob("*") if path.is_file())
    now = datetime.now(timezone.utc).isoformat()
    previous = pin("browser-clone-route-qualification.json")
    result = dict(schemaVersion="public-history-duplicate/1", baselineId=BASE, recordedAtUtc=now,
        previousRouteQualification=previous, owningTask="W03", affectedTransportTask="W04",
        runtimeVersions=observed["versions"],
        officialApi=dict(url="https://github.com/electron/electron/blob/v42.3.0/docs/api/navigation-history.md",
                         snapshot=pin("raw/public-history-duplicate/electron-navigation-history-doc.txt"),
                         guarantee="Best effort navigation-stack and individual-page state restoration; no arbitrary JS-heap cloning guarantee."),
        attempts=[dict(name="owned-history-duplicate-01", receipt=pin("raw/public-history-duplicate/owned-history-duplicate-01/receipt.json"),
                       completeCapabilityProbe=False, exitCode=-6, disposition="No observation file; not evidence of history API success or failure."),
                  dict(name="owned-history-duplicate-02", receipt=pin("raw/public-history-duplicate/owned-history-duplicate-02/receipt.json"),
                       observations=pin("raw/public-history-duplicate/owned-history-duplicate-02/runtime-observations.json"),
                       completeCapabilityProbe=True, exitCode=0, casesPassed=12, casesFailed=1)],
        cases=observed["cases"], candidatePropertyFailures=failures,
        properties=[
            dict(id="HISTORY-P01", status="observed-on-owned-fixtures", finding="Two independent WebContents in one explicit owned session retain three history entries and current index; back/forward/reload work.", cases=["HD-01", "HD-02", "HD-06", "HD-07", "HD-08", "HD-09"]),
            dict(id="HISTORY-P02", status="observed-on-owned-fixtures", finding="Destination edits, divergent navigation and close do not change the source page or its history; source navigation does not move destination.", cases=["HD-05", "HD-10", "HD-11", "HD-12", "HD-13"]),
            dict(id="HISTORY-P03", status="candidate-property-failed", finding="The currently active C entry restored initial-C instead of edited-source-C, while earlier A/B entries restored their saved edited values.", cases=["HD-03", "HD-06", "HD-07"],
                 scope="Programmatic input.value mutations immediately followed by getAllEntries; no native key input or original Owl comparison. This does not establish universal active-page input loss."),
            dict(id="HISTORY-P04", status="observed-on-owned-fixtures", finding="Restored/reloaded pages initialize their scripts again; the public candidate does not preserve the edited JS heap in this run.", cases=["HD-04", "HD-09"],
                 scope="A property of this candidate, not a proven original native-clone requirement."),
        ],
        routeDecision=dict(routeId="CLONE-ROUTE-03", qualification="partial-public-history-primitive; full-clone-equivalence-unproven",
            retainedCapability="Owned source/destination navigation-history independence and first-party controller feasibility.",
            unresolved=["Whether baseline Owl clone has stronger active-page state guarantees", "Active-document state capture if required by original behavior", "Real host/renderer ownership and adoption replacement", "Session partition, preload/security, network pages, popups and full browser capabilities"],
            prohibitedConclusions=["All 13 checks passed", "Direct Owl replacement works", "Original Owl necessarily copies or necessarily discards JS heap", "All active user edits are always lost by the public API", "Whole runtime route is qualified"]),
        processCheck=pin("raw/public-history-duplicate/owned-history-duplicate-02/process-check.json"),
        rawFiles=[pin(name) for name in files],
        counts=dict(publicRuntimeLaunchAttempts=2, completeCapabilityProbes=1, incompleteAttempts=1,
                    candidateChecks=13, checksPassed=12, checksFailed=1, observedSnapshots=13,
                    originalClientRunsAdded=0, modelSubmissionsAdded=0, productScenarioPassesAdded=0,
                    featureDefinitionsAdded=0, clientImplementationAdded=0),
        nextAction="Close this bounded public-history comparison with its positive and failed properties. Continue the already selected ads-controls, archived-chats and data-controls scope contracts; retain runtime residuals as W03-specific acceptance, not a global source-analysis blocker.",
        fullRuntimeRouteSelected=False, fullAnalysisCompleted=False)
    save("public-history-duplicate-comparison.json", result)
    text = """# 公开运行时历史复制的行为对照

固定Electron 42.3.0的自建本地页面探针完成13项检查，12项通过、1项候选属性未通过。结果支持独立导航历史这一局部原语；完整Owl克隆等价性仍未证明。[逐项结果](public-history-duplicate-comparison.json)保留全部检查和两次启动记录。

| 行为 | 本次观察 |
| --- | --- |
| 历史复制 | 两个不同WebContents在同一明确指定的自有session中，各自持有A、B、C三条历史，目的页位于C |
| back与forward | 目的页能回到B、A，再前进到B；较早历史页的编辑输入值保留 |
| reload | B的URL、索引和历史长度保持，脚本重新初始化，输入值回到initial-B |
| 页面独立性 | 目的页编辑和新导航不改变源页；目的历史变为A、B、D，源历史仍是A、B、C |
| 释放 | 关闭目的页后源页仍可用；访问已销毁目的页的历史接口会报错；两页最终均已销毁 |
| 当前页输入 | 当前C页的edited-source-C没有复制过去，目的页得到initial-C，此项未通过 |
| JS状态 | 目的页脚本重新初始化，没有复制源页编辑后的JS堆值 |

当前页输入差异来自用代码直接修改input.value、随后立即读取历史的合成场景。本次没有原生键盘输入，也没有运行原Owl；因此不能据此断言所有活动页输入都会丢失，或原Owl一定具有更强保证。该差异作为候选路线的限制保留，不通过修改预期或重复运行消除。

固定版本的[官方历史接口说明](https://github.com/electron/electron/blob/v42.3.0/docs/api/navigation-history.md)将逐页状态恢复定义为best effort，并建议在新WebContents尚未导航时调用。接口适合评估历史重建，但文档与本次探针均未保证任意活动文档或JS堆快照。其历史导航能力也不提供Owl的renderer adoption协议。

第一次启动在生成观察文件前以SIGABRT退出；该次不计能力检查。相同探针在沙箱外的第二次启动完成，运行时主程序及framework与此前校验的官方归档一致。两次启动均已确认无自有残留进程。全部13份页面快照、失败属性、代码和原始回执按hash保存；模型提交、原客户端运行及产品通过数均增加0。

此批关闭公开历史原语的限定对照：保留其导航与独立性证据，将当前文档状态、真实host接入、安全分区及原Owl语义留在W03/W04的具体验收项。下一步继续已有源码选择的Ads controls、Archived chats和Data controls操作归属；完整运行时选择和完整功能范围仍未关闭。
"""
    with (OUT / "public-history-duplicate-comparison.md").open("x") as stream:
        stream.write(text)
    overlay = dict(result=pin("public-history-duplicate-comparison.json"), summary=pin("public-history-duplicate-comparison.md"),
                   counts=result["counts"], fullRuntimeRouteSelected=False)
    state["publicHistoryDuplicateComparison"] = overlay
    state["analysisMilestones"]["currentScopeOverlay"]["publicHistoryDuplicateOverlay"] = overlay
    state["stageDecisions"]["publicHistoryDuplicateOverlay"] = overlay
    state["analysisMilestones"]["currentAnalysisPriority"] = "A1/A3-bounded-scope-with-local-runtime-residuals"
    state["stageDecisions"]["nextAction"] = dict(issueId="SD-01/SD-06", completedSubstep="Public owned history comparison closed: 12/13 properties pass, current programmatically edited active form not copied; complete clone equivalence remains unproven.",
        fixedInput="Current v17/v8 and already captured .analysis-local/settings-data-batch11-work selections; no repeated public history run without a new requirement.",
        question="Which finite actions, shared consumers and account/conversation/local-thread boundaries belong to ads-controls, archived-chats and data-controls?",
        closure="Publish source contracts, operation ownership and explicit local integration/mode residuals for these three known containers; preserve current full-scope backlog and actual failed candidate property.",
        deferredDedicatedVerification="W03/W04 retain active-document state, original native guarantees, real adoption, session/security and full browser capabilities. Remaining model authorization is zero.")
    state["updatedAtUtc"] = now
    (OUT / "analysis-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    for name in ["report.md", "gaps.md"]:
        target = OUT / name
        lines = target.read_text().splitlines()
        paragraph = "[公开历史复制对照](public-history-duplicate-comparison.md)已完成：13项候选检查中12项通过，当前页程序化编辑值未复制这一项保留失败；历史导航、页面独立性与关闭清理有实测。首次启动失败及完整结果均保留，完整Owl等价性未证明。"
        target.write_text(lines[0] + "\n\n" + paragraph + "\n\n" + "\n".join(lines[1:]).lstrip() + "\n")
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
