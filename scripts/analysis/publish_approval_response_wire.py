"""Publish the response envelope/receiver decision, preserving current scope."""
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASELINE
WORK = ROOT / ".analysis-local/approval-response-wire-work"
RAW = OUT / "raw/approval-response-wire"
NOW = datetime.now(timezone.utc).isoformat()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def pin(path):
    data = (OUT / path).read_bytes()
    return {"path": path, "bytes": len(data), "sha256": sha(data)}


def write(path, value):
    file = OUT / path
    if file.exists():
        raise RuntimeError(f"Preserve existing publication: {file}")
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    file.chmod(0o444)


observed = json.loads((WORK / "probe/observations.json").read_text())
assert len(observed["cases"]) == 20 and all(row["passed"] for row in observed["cases"])
assert len(observed["units"]) == 19
previous_state = (OUT / "analysis-state.json").read_bytes()
state = json.loads(previous_state)
assert state["latestBehaviorAuthorizationState"]["groupRemaining"] == 0
unchanged = {name: pin(name) for name in ["feature-scope-v11.json", "feature-scope-v11-scenarios.json",
    "restoration-coverage-v2.json", "implementation-plan-v7.md", "approval-response-settlement-contracts.json"]}
assert not RAW.exists()
shutil.copytree(WORK / "probe", RAW / "probe")
shutil.copytree(WORK / "probe-attempt-01", RAW / "selection-attempt-01")
for name in ["response_wire_ast.cjs", "probe_approval_response_wire.cjs", "publish_approval_response_wire.py"]:
    shutil.copyfile(ROOT / "scripts/analysis" / name, RAW / name)
index = {unit["name"]: i for i, unit in enumerate(observed["units"])}


def evidence(*names):
    return [{"path": "raw/approval-response-wire/probe/observations.json", "jsonPointer": f"/units/{index[name]}"} for name in names]


contracts = [
    {"id": "AW-C01", "contract": "Pvn 发送 mcp-response，载荷为 hostId/threadId/response；只有 n6 返回跟踪对象时才增加 requestMethod/trace。dispatch 返回的 Promise 不会被等待；同步 throw 会调用 finish(error) 后继续抛出。",
     "evidence": evidence("Pvn"), "probeIds": ["AW-01", "AW-02", "AW-03"]},
    {"id": "AW-C02", "contract": "MMe 的 mcp-response case 先调用 dynamicAppToolResponses.route；命中则停止，未命中则按 hostId 查连接并 await handleClientResponse(response,threadId)。只有 trace 与 requestMethod 同时存在才进入 c.rn 跟踪包装。Uv 用含 ID 类型的键定位 pending，命中后先删除，再 resolve/reject。",
     "evidence": evidence("case-mcp-response", "Uv.route", "Wv", "tee.getConnection", "tee.getMaybeConnection"),
     "probeIds": ["AW-04", "AW-05", "AW-06", "AW-07", "AW-08", "AW-09"]},
    {"id": "AW-C03", "contract": "保存的主机构造链中，hXe 创建 tee 并登记 createAppServerConnection 的本地主机结果；同一 registry 作为 MMe 的第7个实参，由构造器 c 参数保存。hXe.handleMessage 委托该 messageHandler。createAppServerConnection 构造 i.pn；i 的 require 指向 src-BJv5Mk7n.js，pn 的 getter 返回 mB。mB 构造 MR 作为 messageDelivery。",
     "evidence": evidence("hXe.constructor", "hXe.createAppServerConnection", "hXe.handleMessage", "MMe.constructor", "MMe.getAppServerConnection", "export-pn-mB", "mB.constructor", "MR.constructor"),
     "probeIds": [], "verification": "static constructor/injection/export join; constructors not executed",
     "condition": "不证明实际启动采用该实例，也不证明 registry 中所有动态替换项都属于 mB。原生 messageChannel 注册、renderer bridge 实例和实际交付仍沿用既有局部边界。"},
    {"id": "AW-C04", "contract": "mB.handleClientResponse 在 ensureReady 前移除 userVerification、记录 turnCwds 响应并停止自动提问跟踪。ensureReady 失败时广播 fatal error 后直接返回；admission callback 返回 false 时不发送。随后发送的 trace 来自当前上下文，threadId 作为独立参数传给 delivery。",
     "evidence": evidence("mB.handleClientResponse"), "probeIds": ["AW-10", "AW-11", "AW-12", "AW-13", "AW-14"]},
    {"id": "AW-C05", "contract": "MR.sendMessage 对普通 host 将变换/规范化后的响应 JSON.stringify 后传给 connection.send。response 不触发 $L 的 thread/list 参数补充；没有自动添加新的 method 或 jsonrpc 字段。durable 走独立 n.sa 编码，满足 shared 条件时增加 threadId/threadAccess，不能用普通 host 分支覆盖它。",
     "evidence": evidence("MR.sendMessage", "$L", "eR", "kR"), "probeIds": ["AW-15", "AW-16", "AW-17", "AW-18", "AW-19"],
     "condition": "transformOutgoingMessage 可改变响应；durable 编码器内部和真实传输 framing 未在本批验证。"},
    {"id": "AW-C06", "contract": "MR 不等待 connection.send 的返回值，mB 也不等待 delivery 的返回值。底层同步 throw 可使主进程等待的 mB Promise 拒绝；但 readiness 失败被转换为广播并正常返回。即使串联返回也只到本地调用边界，不能当作后台授权或审批确认。",
     "evidence": evidence("Pvn", "case-mcp-response", "mB.handleClientResponse", "MR.sendMessage"),
     "probeIds": ["AW-02", "AW-07", "AW-10", "AW-13", "AW-14", "AW-17", "AW-18", "AW-20"]},
]

# Reuse the previous complete protocol comparison; verify the exact response files now.
protocol = json.loads((OUT / "exported-protocol-comparison.json").read_text())
comparisons = []
schema_files = []
schema_dir = RAW / "schema"
schema_dir.mkdir()
for mode in ["stable", "experimental"]:
    item = protocol["comparisons"][mode]
    row_index = next(i for i, row in enumerate(item["fileComparisons"]) if row["file"] == "McpServerElicitationRequestResponse.json")
    row = item["fileComparisons"][row_index]
    assert row["referencedContract"]["status"] == "equal"
    schema_bytes = []
    for origin, key in [("public", "publicSchemaRoot"), ("frozen", "frozenSchemaRoot")]:
        source = Path(item[key]) / "McpServerElicitationRequestResponse.json"
        data = source.read_bytes()
        assert sha(data) == row[origin + "File"]["sha256"]
        schema_bytes.append(data)
        target = schema_dir / f"{mode}-{origin}-McpServerElicitationRequestResponse.json"
        target.write_bytes(data)
        schema_files.append(pin(str(target.relative_to(OUT))))
    assert schema_bytes[0] == schema_bytes[1]
    schema = json.loads(schema_bytes[0])
    assert schema["required"] == ["action"]
    assert schema["definitions"]["McpServerElicitationAction"]["enum"] == ["accept", "decline", "cancel"]
    variant_index = next(i for i, row in enumerate(item["variantContracts"]) if row["union"] == "ServerRequest.json" and row["method"] == "mcpServer/elicitation/request")
    assert item["variantContracts"][variant_index]["effectiveContract"]["status"] == "equal"
    comparisons.append({"mode": mode,
        "responseRef": {"path": "exported-protocol-comparison.json", "jsonPointer": f"/comparisons/{mode}/fileComparisons/{row_index}"},
        "serverRequestRef": {"path": "exported-protocol-comparison.json", "jsonPointer": f"/comparisons/{mode}/variantContracts/{variant_index}"},
        "responseFileBytesEqual": True, "effectiveRequestContract": "equal"})

# Persist only relevant constructor-call and require joins, not the complete AST indices.
main = json.loads((WORK / "main-program/source-contracts.json").read_text())
joins = {"newExpressions": [x for x in main["newExpressions"] if x["callee"] in ["tee", "MMe", "i.pn"]],
         "requires": [x for x in main["requires"] if x["module"] == "./src-BJv5Mk7n.js"],
         "qualification": "Source-level lexical and constructor argument evidence. Runtime execution/registration remains unobserved."}
assert {x["callee"] for x in joins["newExpressions"]} == {"tee", "MMe", "i.pn"}
assert len(joins["requires"]) == 1
write("raw/approval-response-wire/source-instance-joins.json", joins)

decision = {
    "id": "AW-D01", "status": "source-design-supported; actual-backend-acceptance-pending",
    "owner": "packages/backend-adapter/src/approvals",
    "existingTaskIds": ["T03", "T04"],
    "responsibilities": [
        "Expose a server-request reply operation keyed by the original request ID; do not send a new client request named mcpServer/elicitation/request.",
        "Keep desktop host/thread/method/tracing wrapper separate from the backend result body and preserve optional content/_meta.",
        "Preserve dynamic-tool response routing before normal backend delivery and keep ordinary/durable transport branches distinct.",
        "Report local call completion, transport outcome and backend resolution separately; preserve observed ready-failure broadcasts and synchronous-error paths.",
    ],
    "protocolFinding": "The frozen and pinned public codex-cli0.162.0 response schemas are byte-equal in stable and experimental exports; action is required, content/_meta optional. This supports body-shape reuse only.",
    "acceptanceConditions": [
        "Correlate an actual pending request ID across renderer, chosen manager, main receiver, transport and serverRequest/resolved or equivalent observable outcome.",
        "Verify actual bridge registration, host/connection identity and framing/write behavior with owned fixtures.",
        "Observe readiness failure, synchronous transport failure and unknown asynchronous delivery independently from UI settlement.",
        "Verify durable encoder/account/shared-thread behavior before claiming that host path is supported.",
    ],
    "fullPublicBackendCompatibility": False, "clientImplementationStarted": False,
}
artifact = {"schemaVersion": 1, "baselineId": BASELINE, "recordedAtUtc": NOW,
    "status": "response-envelope-and-source-receiver-dispositioned; actual-delivery-pending",
    "sourceContracts": contracts, "protocolComparisons": comparisons,
    "protocolSource": pin("exported-protocol-comparison.json"), "schemaFiles": schema_files,
    "sourceSelection": pin("raw/approval-response-wire/probe/observations.json"),
    "extractionNote": "Main/connection Programs were selected once. The initial utility omitted TemplateLiteral switch labels; the probe reuses the older published complete dispatcher AST case locator. Archived utility includes the later selector correction; no full main reparse was performed.",
    "sourceInstanceJoins": pin("raw/approval-response-wire/source-instance-joins.json"),
    "restorationDecision": decision,
    "localGaps": ["Actual bridge registration and receiver/manager identity", "Real transport framing/write acceptance and backend resolution",
        "Durable encoder and account/shared-thread path", "Complete approval kinds/schema safety/mode closure", "UI and persistence/restart"],
    "counts": {"sourceContracts": 6, "protocolComparisons": 2, "restorationDecisions": 1,
        "selectedSourceUnits": 19, "isolatedCasesPassed": 20, "newFullProgramParses": 3,
        "productAcceptanceRunsAdded": 0, "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0,
        "featureDefinitionsAdded": 0, "confirmedChatGptExclusionsAdded": 0},
    "existingScopeUnchanged": unchanged, "fullAnalysisCompleted": False}
write("approval-response-wire-contracts.json", artifact)

summary = """# 审批响应封装、宿主接收与后台适配

本批把上轮未明确的 `Pvn` 响应封装接到主进程路由、连接和传输接口，交付6条源码契约、stable/experimental两项协议对照和1项后台适配决定。20项隔离探针通过，包含一次合成串联。

响应先形成 `mcp-response` 的桌面包装：hostId、threadId、response；有跟踪对象时再附 requestMethod/trace。主进程先尝试动态工具响应路由；未命中时按 hostId 查连接并调用 `handleClientResponse(response, threadId)`。保存的构造器、参数和导出关系把此条件路径接到 `mB` 连接和 `MR` delivery，真实实例与原生桥注册尚未观察。

`handleClientResponse` 在等待就绪前清理交互跟踪。就绪失败会广播错误并正常返回，未发送响应；成功后向 delivery 传递响应和独立的 threadId。delivery 对普通主机把变换后的响应序列化为 JSON，再调用传输的 send；durable 走自己的编码与 shared-thread 字段。两个发送层都没有等待下层返回的 Promise。因此，主进程调用完成仍不能作为后台审批确认。

后台适配应回复已有服务端请求 ID，保留 result 的 action/content/_meta；桌面的路由包装与后台结果体分开维护。固定的公开 CLI 0.162.0 与冻结 CLI 的响应 schema 在 stable/experimental 下逐字节相同，服务端请求的有效 schema 也与旧比较一致。这支持复用结果体形状，真实授权、执行绑定、通知和 durable 路径仍需验证，不能据此宣布全部后台兼容。

恢复决定与逐条来源、异常和验收条件见[合同](approval-response-wire-contracts.json)。职责仍接到现有 T03/T04 的审批消费者，没有新增完整功能定义，没有生成客户端或第三方实现。当前120项定义、457条待执行产品规格和覆盖表保持原样；本批产品实测、模型提交和原客户端运行均为0。

本子步骤的源码封装与接收问题已有处理决定。真实传输、实例、后台确认、界面和耐久性继续留在所属模块验收中。下一批回到功能分母：复用保存的工厂与页面绑定，展开 plugins-settings、skills-settings、connections 三个尚未完成操作归属的容器；不再重复追踪本批已经明确的返回语义。
"""
target = OUT / "approval-response-wire-summary.md"
assert not target.exists()
target.write_text(summary)
target.chmod(0o444)

checked = 0
for unit in observed["units"]:
    source = ROOT / ".analysis-local/baselines" / BASELINE / "extracted" / unit["sourcePath"].removeprefix("app.asar/")
    source_bytes = source.read_bytes()
    assert sha(source_bytes) == unit["sourceHash"]
    span = unit["byteRange"]
    expected = source_bytes[span["start"]:span["endExclusive"]]
    assert sha(expected) == unit["spanSha256"]
    assert (RAW / "probe" / unit["sourceFilename"]).read_bytes() == expected
    checked += 1
for name, original in unchanged.items():
    assert pin(name) == original
validation = {"sourceUnitsVerified": checked, "isolatedCasesPassed": 20,
    "byteEqualSchemaPairs": 2, "oldScopeFilesUnchanged": len(unchanged),
    "productAcceptanceRunsAdded": 0, "fullAnalysisCompleted": False}
write("raw/approval-response-wire/validation.json", validation)
entry = {"contracts": pin("approval-response-wire-contracts.json"), "summary": pin("approval-response-wire-summary.md"),
    "validation": pin("raw/approval-response-wire/validation.json"), "counts": artifact["counts"], "fullAnalysisCompleted": False}
state["approvalResponseWire"] = entry
state["stageDecisions"]["latestSubstep"] = entry
state["stageDecisions"]["nextAction"] = {
    "issueId": "SD-01/SD-06",
    "completedSubstep": "Pvn envelope, dynamic/normal host response routing, conditional connection construction and transport-send contract dispositioned;20 isolated probes and2 reused protocol-mode comparisons. Source return/cleanup rules are settled for this bounded path.",
    "fixedInput": "Saved settings section dispositions and named-export/component bindings for plugins-settings, skills-settings and connections; current120/457 feature/acceptance ledgers.",
    "question": "Which user operations, support work, conditions and actual receiver boundaries belong to these three uncovered settings containers?",
    "closure": "Reconcile concrete operations into current feature/support/task/acceptance coverage, preserve mode unknowns and shared dependencies, and reduce the32-container backlog only by pages with scoped operation contracts.",
    "deferredDedicatedVerification": "Approval bridge/manager identity, actual transport/backend confirmation, durable encoding, UI and persistence remain local acceptance gaps; do not repeat settled sender/response-state analyses.",
}
state["updatedAtUtc"] = NOW
temporary = OUT / ".analysis-state.response-wire.tmp"
temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
temporary.replace(OUT / "analysis-state.json")
lead = "[审批响应封装与宿主接收](approval-response-wire-summary.md)已形成6条源码契约和后台适配决定，20项隔离探针通过。普通主机回复现有服务端请求ID，durable保留独立编码；就绪失败可能广播错误后正常返回，调用完成不能充当后台确认。既有两种协议模式的响应schema逐字节相同；真实交付、原生桥实例与完整兼容仍待验收。120/457范围不变，下一批展开plugins、skills、connections三个操作容器。\n\n"
for name in ["report.md", "gaps.md"]:
    file = OUT / name
    heading, rest = file.read_text().split("\n\n", 1)
    file.write_text(heading + "\n\n" + lead + rest)
readme = ROOT / "README.md"
heading, rest = readme.read_text().split("\n\n", 1)
readme.write_text(heading + "\n\n" + "[审批响应封装与后台适配决定](analysis/" + BASELINE + "/approval-response-wire-summary.md)已交付；20项隔离探针通过，真实后台确认仍待验收。下一批展开插件、技能和连接设置。\n\n" + rest)
write("raw/approval-response-wire/publication-receipt.json", {"recordedAtUtc": NOW,
    "previousStateSha256": sha(previous_state), "state": pin("analysis-state.json"), **entry})
for file in RAW.rglob("*"):
    if file.is_file():
        file.chmod(0o444)
print(json.dumps(validation))
