"""Publish the bounded approval result without changing feature denominators."""
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASELINE
WORK = ROOT / ".analysis-local/approval-response-settlement-work"
RAW = OUT / "raw/approval-response-settlement"
NOW = datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(relative):
    return json.loads((OUT / relative).read_text())


def pin(relative):
    data = (OUT / relative).read_bytes()
    return {"path": relative, "bytes": len(data), "sha256": digest(data)}


def write(relative, value):
    target = OUT / relative
    if target.exists():
        raise RuntimeError(f"Preserve existing artifact: {target}")
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    target.chmod(0o444)


result = json.loads((WORK / "probe/observations.json").read_text())
assert result["counts"]["passed"] == 26
assert len(result["units"]) == 25
assert all(case["passed"] for case in result["cases"])
assert result["counts"]["productAcceptanceRuns"] == 0
old_state = (OUT / "analysis-state.json").read_bytes()
state = json.loads(old_state)
scope_before = {name: pin(name) for name in [
    "feature-scope-v11.json", "feature-scope-v11-scenarios.json",
    "restoration-coverage-v2.json", "implementation-plan-v7.md",
    "approval-entry-contracts.json",
]}
assert state["latestBehaviorAuthorizationState"]["groupRemaining"] == 0
assert state["fullAnalysisCompleted"] is False

if RAW.exists():
    raise RuntimeError("Preserve previous raw publication")
shutil.copytree(WORK / "probe", RAW / "probe")
shutil.copytree(WORK / "helpers", RAW / "saved-helper-program-selection")
for name in ["probe_approval_response_settlement.cjs", "publish_approval_response_settlement.py"]:
    shutil.copyfile(ROOT / "scripts/analysis" / name, RAW / name)
for unit in result["units"]:
    body = (RAW / "probe" / unit["sourceFilename"]).read_bytes()
    assert digest(body) == unit["spanSha256"]

unit_index = {unit["name"]: index for index, unit in enumerate(result["units"])}


def evidence(*names):
    return [{"path": "raw/approval-response-settlement/probe/observations.json",
             "jsonPointer": f"/units/{unit_index[name]}"} for name in names]


contracts = [
    {
        "id": "AR-C01", "owner": "packages/backend-adapter/src/approvals",
        "contract": "回复入口先查找请求、核对方法；找不到或方法不符时不发送。userVerification 的 accept 在此路径直接返回。accept 安全检查失败同步抛错。",
        "evidence": evidence("L7t", "Dfn-replyWithMcpServerElicitationResponse"),
        "probeIds": ["AR-01", "AR-02", "AR-03", "AR-04", "AR-05"],
        "acceptance": "真实卡片与实际 manager 关联后，分别观察失效请求、方法不符、userVerification、accept 与 decline；不能把无操作返回当作审批完成。",
    },
    {
        "id": "AR-C02", "owner": "packages/desktop-transport/src/coordination",
        "contract": "uV 返回 truthy ownerClientId 时，入口调用异步转发并注册失败日志后立即返回；不等待所属窗口确认，也不在本窗口发送或清理。Z7t 的转发函数自身等待 IPC，并把 error envelope 转为拒绝。",
        "evidence": evidence("L7t", "uV", "Z7t"),
        "probeIds": ["AR-06", "AR-15", "AR-16"],
        "wire": {"method": "thread-follower-submit-mcp-server-elicitation-response",
                 "params": ["conversationId", "requestId", "response"], "options": ["targetClientId"]},
        "acceptance": "在自有双窗口夹具中分别观察转发未决、所属窗口拒绝和成功；单独记录发起窗口返回与所属窗口实际处理，不将前者提升为确认。",
    },
    {
        "id": "AR-C03", "owner": "packages/backend-adapter/src/approvals",
        "contract": "等价请求列表先整体执行 accept 安全检查，再顺序发送。选中请求 apply，其余 discard；后一次同步发送失败不会回滚此前已经发生的状态变化。",
        "evidence": evidence("L7t", "G7t", "jj"),
        "probeIds": ["AR-07", "AR-08", "AR-09"],
        "acceptance": "通过实际所属 manager 验证等价列表与发送顺序；注入第二项同步失败，核对第一项状态及剩余待处理项，保留部分失败语义。",
    },
    {
        "id": "AR-C04", "owner": "packages/backend-adapter/src/approvals",
        "contract": "已保存的 Sii 工厂把 sendAppServerResponse 回调传给 Dfn；构造器保存同一注入值，getApprovalActionContext 再把它传给 Z7t。此工厂回调对普通响应调用 Pvn 后没有 return/await；L7t 同样不等待 sender 返回值。因此这一源码分支不提供后台接收确认。",
        "evidence": evidence("Sii", "Sii-sendAppServerResponse", "Dfn-constructor", "Dfn-getApprovalActionContext", "L7t"),
        "probeIds": ["AR-10", "AR-11", "AR-12", "AR-13", "AR-14"],
        "condition": "仅适用于使用该 Sii/Dfn 条件实例链的分支；其他注入 manager、实际 UI scope 和 Pvn 的序列化/宿主接收均未由本批证明。",
        "acceptance": "将实际 RPC manager、发送消息和后台请求 ID 关联；分别观察同步 throw、异步发送失败、后台拒绝和审批通知。调用返回只能记录该调用边界已结束。",
    },
    {
        "id": "AR-C05", "owner": "packages/state-storage/src/conversations",
        "contract": "apply 通过注入 updater 更新会话：尝试投影 completed/action 的 elicitation item，随后从 requests 删除选中 ID。turnId 为空或 lookup 返回无 turn 时仍执行请求删除；传给 lookup 的选项是 synthesizeMissingTurn:false。item 以 mcp-server-elicitation-请求ID 定位，已存在则替换。userVerification 投影清空 challenge。",
        "evidence": evidence("Z7t", "q7t", "U7t", "cB", "sB", "zB", "Km", "rp"),
        "probeIds": ["AR-17", "AR-18", "AR-19", "AR-20"],
        "condition": "探针的 turn lookup、draft-array 识别和 updater 是合成边界；真实 updater 的持久化、重放、Z4t 内部行为及实际会话实例仍待验证。",
        "acceptance": "以真实请求记录关联投影与请求队列；覆盖有/无 turn、空 turnId、已有 item。单独检查持久化与重启，不能把内存删除当作审批已被后台接受。",
    },
    {
        "id": "AR-C06", "owner": "packages/state-storage/src/conversations",
        "contract": "discard 只移除指定 turn 中 type=mcpServerElicitation 且含匹配 requestId 的 item，再删除同 ID 待请求；其他类型、ID 或无 requestId 的 item 保留。单请求查询拒绝 follower；列表查询过滤 z7t 指定的方法。",
        "evidence": evidence("Z7t", "z7t", "cB"),
        "probeIds": ["AR-21", "AR-22"],
        "acceptance": "通过真实会话快照验证类型/ID 保留规则和 follower 查询限制；z7t 的生产常量初始化不由合成过滤常量探针证明。",
    },
    {
        "id": "AR-C07", "owner": "packages/backend-adapter/src/approvals",
        "contract": "n5t 以严格相等比较 connector_id、link_id、auth_reason；任一 connection_consent 非 nullish 则不等价；requested_scopes 按 Set 比较，忽略顺序和重复，缺省等同空集合。G7t 仅在 QB 识别为 connectorAuth 且没有 consent 的情况下寻找其他等价请求。",
        "evidence": evidence("n5t", "G7t", "QB"),
        "probeIds": ["AR-23", "AR-24"],
        "condition": "QB 的 URL/schema/来源验证依赖只做源码检查，不把 n5t 的纯比较结果当作整个连接器授权链成立。",
        "acceptance": "用真实已验证 connectorAuth 请求核对等价列表；改变 connector/link/reason/scopes/consent 中任一关键条件时重新观察，保留 QB 分类前提。",
    },
    {
        "id": "AR-C08", "owner": "packages/backend-adapter/src/approvals",
        "contract": "B8t 对识别出的 executionBound 审批要求 approveDisabled 为 false，并拒绝对象 _meta 中任何非 nullish persist 值。z8t 仅尝试 form/codex_apps 元数据；H8t 要求 tool_params 恰好只有 confirmation_summary 与非空字符串 plan_token 两键。U8t 还检查长度、解析、schema 和规范化相等。",
        "evidence": evidence("B8t", "z8t", "H8t", "U8t", "V8t"),
        "probeIds": ["AR-25", "AR-26"],
        "condition": "B8t 探针注入识别结果。完整 schema、工具常量初始化、W8t/YB 规范化及实际工具执行绑定仍未验证，不能据此宣布安全链完整。",
        "acceptance": "验证实际 schema/工具/规范化来源后，再用有效与无效元数据检查审批禁用和 persist 策略；与后台执行绑定核对。",
    },
]
unknowns = [
    {"id": "APPROVAL-U03", "change": "部分关闭：选定回复入口、所属窗口转发及条件工厂 sender 的返回语义已明确。", "remaining": "实际 capnweb/manager 实例关联、Pvn 序列化与宿主接收、后台确认和卡片最终可见行为。"},
    {"id": "APPROVAL-U04", "change": "部分关闭：会话内存请求删除与 turn item 投影规则已明确。", "remaining": "accepted atom、实际 updater 的存储、耐久性和重启恢复。"},
    {"id": "APPROVAL-U06", "change": "部分关闭：连接器等价比较、局部参数形状和 B8t 条件已明确。", "remaining": "QB/z8t 全部 schema、URL 来源与规范化依赖，以及实际授权/执行绑定。"},
    {"id": "APPROVAL-U01/U02/U05/U07", "change": "保持开放。", "remaining": "生产模式和功能条件、真实实例、其他审批类型，以及卡片异常/卸载/取消/重启。"},
]
artifact = {
    "schemaVersion": 1, "baselineId": BASELINE, "recordedAtUtc": NOW,
    "status": "bounded-source-contracts-closed; runtime-and-complete-approval-coverage-open",
    "purpose": "将审批调用返回、转发、发送与内存状态规则落实到恢复模块；不把异步调用完成提升为后台确认。",
    "sourceSelection": pin("raw/approval-response-settlement/probe/observations.json"),
    "priorContracts": pin("approval-entry-contracts.json"),
    "contracts": contracts, "unknownDisposition": unknowns,
    "recoveryDecision": {
        "existingTaskIds": ["T03", "T04"],
        "taskMappingKind": "cross-cutting approvals consumer contracts; no new complete feature claim",
        "modules": sorted({contract["owner"] for contract in contracts} | {"apps/desktop/src/renderer/features/approvals"}),
        "rendererRule": "保留旧卡片的 pending/settled/error 与 accepted 状态行为；回复 Promise 完成不标注为后台已确认。真实卡片恢复和失败回滚按既有来源另行验收。",
        "thirdPartyRule": "通过依赖引入既有 RPC/schema/state 库；本批只保留第一方契约和分析原片段，不生成第三方实现。",
        "implementationStarted": False,
    },
    "counts": {"sourceContracts": len(contracts), "isolatedCasesPassed": 26, "selectedSourceUnits": 25,
               "productAcceptanceRunsAdded": 0, "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0,
               "featureDefinitionsAdded": 0, "confirmedChatGptExclusionsAdded": 0},
    "existingScopeUnchanged": scope_before,
    "fullAnalysisCompleted": False,
}
write("approval-response-settlement-contracts.json", artifact)
summary = """# 审批回复、转发与状态清理

本批明确了8条可用于恢复实现的源码契约，26项隔离探针通过。审批入口返回、所属窗口处理、后台接收、界面状态和持久化必须分别记录。

条件工厂 `Sii` 把发送回调注入 `Dfn`，构造器保存后由审批 context 使用。该回调调用 `Pvn` 后没有返回或等待其结果；审批入口同样不等待 sender。跟随窗口则发起向所属窗口的异步转发，注册失败日志后立即返回。因此，成功调用这些入口不能证明后台已经接受审批。

等价请求先整体检查，再逐项发送并更新本地状态。后一次同步发送失败会留下此前已完成的更新。`apply` 会尝试更新 turn item，随后删除待请求；turnId 为空或 lookup 返回无 turn 时仍会删除请求。`discard` 只清理匹配类型与请求 ID 的 item。这些是会话内存转换；真实 updater 的持久化没有在本批验证。

连接器等价比较要求 connector/link/reason 相同且没有 consent，scopes 按集合比较。执行绑定审批的局部参数形状和 persist 检查也已核对；完整 schema、URL 分类、规范化和后台执行绑定仍开放。

恢复时由现有 T03/T04 的 approvals 消费者使用三个边界：`packages/backend-adapter/src/approvals` 负责决定与发送编排，`packages/desktop-transport/src/coordination` 负责所属窗口转发，`packages/state-storage/src/conversations` 负责请求与投影状态。路径是维护建议，不是原作者目录恢复。逐条来源、探针与真实验收条件见[合同](approval-response-settlement-contracts.json)。

旧 APPROVAL-U03/U04/U06 仅关闭上述静态部分。真实 manager/RPC 实例、Pvn 序列化和接收方、后台确认、卡片异常及存储恢复仍是局部验收项；其他审批类型与模式归属继续保留。

25个源码单元均有固定文件哈希和字节范围；复用旧 Program 绑定，并对保存的完整工厂函数做了一次局部 AST 选择。探针只运行精确选取的函数/回调，IPC、发送、turn lookup、updater 和 schema 识别均为明确的合成边界。没有启动目标客户端、提交模型任务或增加真实产品通过数。

本批没有新增完整功能定义或重写实施计划。现有120项有限定义、457条待执行产品规格和恢复覆盖表保持原样；8条合同的真实验收条件独立列在合同中，不能算作已通过的功能。
"""
target = OUT / "approval-response-settlement-summary.md"
assert not target.exists()
target.write_text(summary)
target.chmod(0o444)

# Verify every source locator against the frozen source, independently of probes.
frozen = ROOT / ".analysis-local/baselines" / BASELINE / "extracted/webview/assets/app-shared-8bd9d0399038.js"
source = frozen.read_bytes()
assert digest(source) == result["source"]["sha256"]
for unit in result["units"]:
    span = unit["byteRange"]
    assert digest(source[span["start"]:span["endExclusive"]]) == unit["spanSha256"]
for contract in contracts:
    assert contract["acceptance"] and contract["owner"]
    assert set(contract["probeIds"]) <= {case["id"] for case in result["cases"]}
    for ref in contract["evidence"]:
        index = int(ref["jsonPointer"].split("/")[-1])
        assert 0 <= index < len(result["units"])
for name, before in scope_before.items():
    assert pin(name) == before

validation = {"baselineId": BASELINE, "sourceSpansVerified": 25, "contractsVerified": 8,
              "isolatedCasesPassed": 26, "oldScopeFilesUnchanged": len(scope_before),
              "productAcceptanceRunsAdded": 0, "modelSubmissionsAdded": 0,
              "fullAnalysisCompleted": False}
write("raw/approval-response-settlement/validation.json", validation)
contract_pin = pin("approval-response-settlement-contracts.json")
summary_pin = pin("approval-response-settlement-summary.md")
state["approvalResponseSettlement"] = {
    "contracts": contract_pin, "summary": summary_pin,
    "validation": pin("raw/approval-response-settlement/validation.json"),
    "counts": artifact["counts"], "fullAnalysisCompleted": False,
}
state["stageDecisions"]["latestSubstep"] = state["approvalResponseSettlement"]
state["stageDecisions"]["nextAction"] = {
    "issueId": "SD-03/SD-06",
    "completedSubstep": "Eight approval reply/forwarding/sender/state contracts dispositioned to existing modules;26 isolated cases pass. Current120/457 scope unchanged.",
    "fixedInput": "Existing ordinary lifecycle contracts, saved Sii/Dfn bindings and approval-response-settlement-contracts.json. Reuse completed selections.",
    "question": "What concrete response envelope and host receiver does Pvn use for MCP elicitation replies, and is that contract covered by the selected public backend adapter?",
    "closure": "Trace only this unresolved response serializer and actual registered host handler; disposition wire fields, failure semantics and adapter acceptance. Do not reanalyze settled sender return or memory cleanup rules.",
    "deferredDedicatedVerification": "Actual manager/RPC identity, backend delivery, complete approval kinds, card errors, persistence/restart and full mode/shared coverage remain feature-specific acceptance gaps.",
}
state["updatedAtUtc"] = NOW
temp = OUT / ".analysis-state.approval-settlement.tmp"
temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
temp.replace(OUT / "analysis-state.json")

lead = "审批回复链新增[8条恢复合同](approval-response-settlement-summary.md)，26项隔离探针通过：条件 sender 与跟随窗口入口的调用返回不等于后台确认；等价请求的顺序发送、部分失败、请求删除和 turn 投影已明确。真实 manager/接收、存储和卡片行为仍待验证。当前120/457范围及恢复覆盖表不变。下一项仅核对 Pvn 响应封装与宿主接收方，不重复分析已明确的返回和内存规则。\n\n"
for name in ["report.md", "gaps.md"]:
    file = OUT / name
    text = file.read_text()
    heading, body = text.split("\n\n", 1)
    file.write_text(heading + "\n\n" + lead + body)
readme = ROOT / "README.md"
text = readme.read_text()
heading, body = text.split("\n\n", 1)
readme.write_text(heading + "\n\n" + "[审批回复与状态清理合同](analysis/" + BASELINE + "/approval-response-settlement-summary.md)已补齐8条恢复规则，26项隔离探针通过；后台接收、真实卡片和存储仍待验证。\n\n" + body)

receipt = {"recordedAtUtc": NOW, "previousStateSha256": digest(old_state),
           "state": pin("analysis-state.json"), "contracts": contract_pin,
           "summary": summary_pin, "validation": pin("raw/approval-response-settlement/validation.json")}
write("raw/approval-response-settlement/publication-receipt.json", receipt)
for file in RAW.rglob("*"):
    if file.is_file():
        file.chmod(0o444)
print(json.dumps(validation, ensure_ascii=False))
