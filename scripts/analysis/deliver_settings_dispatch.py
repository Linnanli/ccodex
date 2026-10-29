#!/usr/bin/env python3
"""Deliver one frozen metadata allowlist; never import or evaluate target code."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "codex-26.1007.30912-c5b273322a83"
SOURCE = ROOT / ".analysis-local/settings-config-dispatch-work"
DEST = ROOT / "analysis" / BASELINE
RAW = DEST / "raw/settings-config-dispatch"
WORK = ROOT / ".analysis-local/settings-config-dispatch-delivery-work"
PINS = {
    "settings-config-dispatch-contracts.json": (130182, "43f762f0bd471f0c2204bc746707adb8197a37adab9b304ed9e0891ee6ca189e"),
    "evidence.jsonl": (49305, "891e48923fa26d8265ad19bf578a40181e90f7889b32916ae4ff3bceeeab6772"),
    "summary.md": (3198, "cd56198498cef94f052ede035155288cdaf9fefc4880a6fff3e65be01290c4a0"),
    "validation.json": (12964, "4c97e05ddc74cb9ef13e209858a4a9d337e475c01ed820b92ef02fed3d42ec7b"),
    "input-receipts.json": (2920, "abfd9bfabc8e3a6a69253e5cc17eeaf4333d26ba02ad604f291c05fcdcc53476"),
    "source-receipts.json": (5538, "b2d25b8685bba043fc49836605cd0c3bd19c774b8b3b3c46d99d0c60a41762c4"),
    "ownpeer/final-review.json": (7704, "3431cda0617749f409a12d7568b62b5beb3b29c42fa1b3679b7a5c9dfe33fa58"),
    "ownpeer/final-review.md": (1275, "3f6d91c2e933b3f366fda0b59cbaff76aa3b2f42c7d120132899e631fb9e5935"),
    "freeze-manifest.json": (58680, "59f02618205990b39f92e69e23350c0af26dd6866bf0a77c485ed8cd9f73f354"),
    "freeze-confirmation.json": (1074, "ba7176255a6a98ec18944d59ce3e6145cd9cda2aa7f4a3417973692c4d7f4dae"),
    "publication-allowlist.json": (1250, "b39ce26e0cf8dac1ff845dd938a8349164723c7562daa0662364b939c1db234b"),
}
ALIASES = {
    "settings-config-dispatch.json": "settings-config-dispatch-contracts.json",
    "settings-config-dispatch-evidence.jsonl": "evidence.jsonl",
    "settings-config-dispatch-validation.json": "validation.json",
    "settings-config-dispatch-peer-review.json": "ownpeer/final-review.json",
}
FORBIDDEN_KEYS = {"ast", "sourcecode", "source_code", "unittext", "unit_text", "functiontext", "function_text", "completeunittext", "completetargetsource", "implementation", "code", "rawtext"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}


def emit_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(0o444)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def metadata_scan(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key.lower() not in FORBIDDEN_KEYS, f"implementation/AST field at {path}/{key}"
            metadata_scan(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            metadata_scan(child, f"{path}/{index}")
    elif isinstance(value, str):
        assert len(value) <= 600, f"unreviewed long metadata string at {path}"


def main():
    # All source reads are the eleven explicitly pinned metadata/control files.
    saved = {name: (SOURCE / name).read_bytes() for name in PINS}
    for name, data in saved.items():
        assert (len(data), digest(data)) == PINS[name], f"changed frozen input: {name}"
        assert stat.S_IMODE((SOURCE / name).stat().st_mode) == 0o444, name
        if name.endswith(".json"):
            metadata_scan(json.loads(data))
        elif name.endswith(".jsonl"):
            metadata_scan([json.loads(line) for line in data.decode().splitlines()])
    allowlist = json.loads(saved["publication-allowlist.json"])
    selected = allowlist["selectedPaths"]
    assert selected == list(PINS)[:-1]
    assert allowlist["baselineId"] == BASELINE
    manifest = json.loads(saved["freeze-manifest.json"])
    confirmation = json.loads(saved["freeze-confirmation.json"])
    indexed = {item["relativePath"]: item for item in manifest["files"]}
    assert len(indexed) == manifest["fileCount"] == confirmation["confirmedClosedFileCount"] == 272
    assert confirmation["manifest"]["bytes"] == PINS["freeze-manifest.json"][0]
    assert confirmation["manifest"]["sha256"] == PINS["freeze-manifest.json"][1]
    assert manifest["safePublicationAllowlist"] == "publication-allowlist.json"
    for name in [*selected[:-2], "publication-allowlist.json"]:
        assert (indexed[name]["bytes"], indexed[name]["sha256"]) == PINS[name]
        assert indexed[name]["mode"] == "0o444"
    core = json.loads(saved["settings-config-dispatch-contracts.json"])
    journal = [json.loads(line) for line in saved["evidence.jsonl"].decode().splitlines()]
    validation = json.loads(saved["validation.json"])
    peer = json.loads(saved["ownpeer/final-review.json"])
    assert core["baselineId"] == manifest["baselineId"] == confirmation["baselineId"] == BASELINE
    assert journal == core["sourceEvidence"] and len(journal) == 40
    assert len({item["id"] for item in journal}) == 40
    assert dict(Counter(item["confidence"] for item in journal)) == {"confirmed": 38, "unresolved": 2}
    assert all(item["mode"] == "unknown" and item["runtimeStatus"] == "not-observed" for item in journal)
    assert core["summary"]["globalJournalAdded"] == core["evidenceJournal"]["globalAdded"] == 0
    assert core["summary"]["confirmedChatGptOnlyExclusions"] == 0
    assert core["summary"]["selectedCompleteSharedUnits"] + core["summary"]["selectedCompleteNativeUnits"] == 19
    assert core["summary"]["selectedNodeVisitsIncludingOverlap"] == 5409
    assert validation["checkCount"] == 3673 and validation["errors"] == []
    assert peer["combinedIndependentChecks"] == 421 and peer["errors"] == []
    assert peer["reusedIndependentSemanticChecks"] == 159 and peer["finalSavedOnlyCheckCount"] == 262
    # Refuse overwrites; every formal product is exclusive to this delivery.
    targets = [RAW / name for name in PINS] + [DEST / name for name in ALIASES]
    targets += [DEST / "settings-config-dispatch-summary.md", DEST / "settings-config-dispatch-peer-review.md", DEST / "settings-config-dispatch-delivery-provenance.json"]
    assert not RAW.exists(), "dedicated raw delivery directory already exists"
    assert all(not target.exists() for target in targets), "formal destination already exists"
    copies = []
    for name, data in saved.items():
        target = RAW / name
        emit_new(target, data)
        copies.append({"kind": "allowlist-metadata" if name != "publication-allowlist.json" else "allowlist-control", "source": str(SOURCE / name), "destination": str(target), "bytes": len(data), "sha256": digest(data)})
    for target_name, source_name in ALIASES.items():
        target = DEST / target_name
        emit_new(target, saved[source_name])
        copies.append({"kind": "formal-exact-copy-alias", "source": str(SOURCE / source_name), "destination": str(target), "bytes": len(saved[source_name]), "sha256": digest(saved[source_name])})
    summary = """# 配置写入与分发路径分析

本批包含 40 条静态源码契约：38 条确认、2 条未决。原分析解析了 19 个完整选定单元，累计 20,501 字节、5,409 个节点（含重叠）。这些是分析规模，不是功能总数。六个 Agent 页面控件复用既有记录，原 65 条页面记录及全局功能、入口和模式分类在本次交付中未被修改；新增全局记录 0，确认 ChatGPT 专属排除 0。

非项目写入通过 `KI(scope, host).sendRequest` 请求 `config/value/write`；项目分支在源码中等待 `projectWrite()`。项目读取/保存路径进入 `$G → yDn → AW.post`，`vscode://codex/` 前缀选择 `AW.sendRequest → Vf.dispatchMessage` 的 `fetch/cancel-fetch` 分支，经 `are/ire` 桥发送。原生 `MMe` 的对应分支调用注入的 `fetchWrapper`。单独的 `Ude` 构造、`fetchHandler` 与注入的接收对象仍是条件候选，尚未证明它们属于同一实际实例，也未核实磁盘写入、运行时取消或协议交付。

取消处理先移除 pending 项与监听器，再同步分发 `cancel-fetch`，显式 Promise 拒绝发生在分发正常返回之后。同步分发抛错会跳过这次拒绝；已取消信号在 Promise executor 中执行与后续事件监听器抛错具有不同结果。桥调用或 `.catch` 注册同步抛错也会跳过后续 CustomEvent。桥返回 Promise 的异步拒绝仅记录日志，不能据此声称 AW 的 pending Promise 已结束。

作者验证为 3,673 项，范围是选定原始字节片段及保存的元数据。独立复核为 421 项（159 项保存文本语义检查与 262 项最终元数据检查）；此前 25 项作者身份推导不计入独立复核。这些计数不相加，不代表实际运行、端到端成功或完整功能覆盖。本次交付只验证冻结元数据、允许发布范围与逐字节复制，未执行原分析器、目标源码、UI、网络或模型任务。

正式 [契约 JSON](settings-config-dispatch.json)、[证据日志](settings-config-dispatch-evidence.jsonl)、[作者验证](settings-config-dispatch-validation.json)、[独立复核](settings-config-dispatch-peer-review.md) 与 [交付记录](settings-config-dispatch-delivery-provenance.json) 可供后续工程恢复使用。原始元数据在 [raw 快照](raw/settings-config-dispatch/settings-config-dispatch-contracts.json)，其相对路径和原绝对路径保留作者记录的上下文；未引用为新执行证明。完整单元文本、AST、依赖与工具实现未发布。
"""
    peer_reader = """# 配置分发独立复核

保存的独立复核结果为通过且保留范围限制：421 项检查、0 个错误。其中 159 项是保存文本的语义检查，262 项是最终保存元数据检查。作者的 3,673 项选定原始源码验证另列；此前 25 项身份推导为作者输入，不计入独立合计。

复核确认了项目写入等待、队列错误恢复、两次刷新尝试，以及取消和桥分发同步抛错的条件差异。实际 receiver、Ude/fetchHandler 绑定、运行时交付、取消和磁盘效果仍未决。本次交付没有重新执行该复核。

详见 [正式复核 JSON](settings-config-dispatch-peer-review.json)、[原始复核说明](raw/settings-config-dispatch/ownpeer/final-review.md) 与 [原始复核 JSON](raw/settings-config-dispatch/ownpeer/final-review.json)。本页为交付时派生的读者索引；raw 下两份文件为冻结输入的逐字节副本。
"""
    for name, text in [("settings-config-dispatch-summary.md", summary), ("settings-config-dispatch-peer-review.md", peer_reader)]:
        emit_new(DEST / name, text.encode())
    for item in copies:
        observed = pin(Path(item["destination"]))
        assert observed["bytes"] == item["bytes"] and observed["sha256"] == item["sha256"]
    # Re-read only the selected original metadata after delivery to prove stability.
    assert all((SOURCE / name).read_bytes() == data for name, data in saved.items())
    provenance = {
        "schemaVersion": "settings-config-dispatch-delivery-provenance/1",
        "baselineId": BASELINE,
        "status": "delivered-frozen-metadata-with-scope-limits",
        "allowlistMetadataFileCount": 10,
        "allowlistControlFileCount": 1,
        "formalExactCopyAliasCount": 4,
        "exactCopyCount": len(copies),
        "copies": copies,
        "derivedReaders": [pin(DEST / "settings-config-dispatch-summary.md"), pin(DEST / "settings-config-dispatch-peer-review.md")],
        "sourceManifest": pin(SOURCE / "freeze-manifest.json"),
        "sourceConfirmation": pin(SOURCE / "freeze-confirmation.json"),
        "sourceAllowlist": pin(SOURCE / "publication-allowlist.json"),
        "selectedMetadataPinsAndReadonlyModesVerified": True,
        "full272FileManifestClosureRechecked": False,
        "metadataSafety": {"forbiddenImplementationOrAstFieldsFound": 0, "jsonStringLengthLimit": 600, "completeTargetSourceCopied": False, "selectedUnitTextCopied": False, "parserOrDependencyImplementationCopied": False},
        "scope": {"journalRecords": 40, "confidenceCounts": {"confirmed": 38, "inferred": 0, "unresolved": 2}, "originalSelectedUnits": 19, "originalNodeVisitsIncludingOverlap": 5409, "savedAuthorChecks": 3673, "savedIndependentChecks": 421, "checksNotAddedTogether": True, "newParses": 0, "targetExecutions": 0, "runtimeObservations": 0, "globalJournalAdded": 0, "confirmedChatGptOnlyExclusions": 0, "featureCountEstablished": False, "mode": "unknown"},
        "relativeReferences": "Exact copies preserve source-relative and original absolute references; raw layout preserves selected relative peer and journal links. Reader pages are derived, not peer-authored.",
        "limits": ["Only eleven selected metadata/control files rehashed; no full 272-file seal rerun.", "Saved author/peer checks were not re-executed by delivery.", "Actual receiver, Ude/fetchHandler identity, transport, cancellation and write persistence remain unproved."],
        "actualDeliveryExecution": "raw/settings-config-dispatch/delivery-execution-provenance.json",
    }
    emit_new(DEST / "settings-config-dispatch-delivery-provenance.json", json_bytes(provenance))
    result = {"status": provenance["status"], "exactCopyCount": len(copies), "derivedReaderCount": 2, "sourceStableAfterDelivery": True, "formalProducts": [pin(DEST / name) for name in [*ALIASES, "settings-config-dispatch-summary.md", "settings-config-dispatch-peer-review.md", "settings-config-dispatch-delivery-provenance.json"]]}
    emit_new(WORK / "delivery-result.json", json_bytes(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
