#!/usr/bin/env python3
"""Publish bounded decisions for the existing 12 associations and 3 overlaps.

Reads saved contracts and frozen bytes only. It never imports target JavaScript.
The numbered inputs remain immutable; decisions supplement the current view.
"""
import datetime
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"
WORK = ROOT / ".analysis-local/association-overlap-decisions-work"
STEM = "association-overlap-decisions-v1"
INPUTS = {}
SOURCE_BYTES = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    path = path.resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": digest(data)}


def load(name):
    path = OUT / name
    INPUTS[name] = pin(path)
    return json.loads(path.read_text())


def pointer(obj, ptr):
    for key in ptr.lstrip("/").split("/") if ptr else []:
        key = key.replace("~1", "/").replace("~0", "~")
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def ref(name, ptr=""):
    obj = load(name)
    pointer(obj, ptr)
    return {**INPUTS[name], "jsonPointer": ptr}


def source(name, ptr, shared=False):
    obj = pointer(load(name), ptr)
    path = obj.get("sourcePath")
    source_hash = obj.get("sourceHash")
    if shared:
        path = "app.asar/webview/assets/app-shared-8bd9d0399038.js"
        source_hash = "607ad0866dd25ed3764711b4467a9b60708353a599485b5249ff4cbe0e870245"
    if path not in SOURCE_BYTES:
        data = (FROZEN / path.removeprefix("app.asar/")).read_bytes()
        SOURCE_BYTES[path] = data
    data = SOURCE_BYTES[path]
    assert digest(data) == source_hash, path
    loc = obj.get("byteRange", obj.get("range", obj.get("locator")))
    start, end = loc["start"], loc["endExclusive"]
    assert 0 <= start < end <= len(data)
    span_hash = digest(data[start:end])
    expected = obj.get("spanHash", obj.get("spanSha256", obj.get("sha256")))
    if expected:
        assert span_hash == expected, (name, ptr)
    return {"sourcePath": path, "sourceHash": source_hash,
            "byteRange": {"start": start, "endExclusive": end},
            "spanHash": span_hash, "origin": ref(name, ptr)}


def task(task_id, relationship, status="inferred-design-assignment"):
    name = "implementation-milestones-v9.json" if task_id.startswith("W") else "restoration-coverage-v18.json"
    key = "foundationTasks" if task_id.startswith("W") else "taskGroups"
    for i, value in enumerate(load(name)[key]):
        if value["taskId"] == task_id:
            return {"taskId": task_id, "task": ref(name, f"/{key}/{i}"),
                    "relationship": relationship, "status": status,
                    "actualConsumerClosureClaimed": False}
    raise AssertionError(task_id)


def owner(owner_id):
    for i, value in enumerate(load("logical-module-ownership-v1.json")["responsibilityOwners"]):
        if value["ownerId"] == owner_id:
            return {"ownerId": owner_id, "owner": ref("logical-module-ownership-v1.json", f"/responsibilityOwners/{i}"),
                    "relationship": "bounded design support; does not assign every original consumer"}
    raise AssertionError(owner_id)


def main():
    WORK.mkdir(exist_ok=True)
    assert not (OUT / f"{STEM}.json").exists(), "Numbered publication already exists"
    scope = load("feature-scope-v27.json")
    assert len(scope["retainedAssociationBacklog"]) == 12
    assert len(scope["crossFeatureOverlapReviews"]) == 3
    assert len(scope["features"]) == 373
    plan_path = ROOT / "docs/reverse-engineering/analysis-plan.md"
    assert digest(plan_path.read_bytes()) == "48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4"
    state_path = OUT / "analysis-state.json"
    before = state_path.read_bytes()
    (WORK / "state-before.json").write_bytes(before)
    state = json.loads(before)
    assert state["legacyEntryDispositions"]["counts"]["entriesAwaitingDisposition"] == 0
    assert state["latestBehaviorAuthorizationState"]["groupRemaining"] == 0
    records = []

    def add(index, classification, decision, refs, sources, tasks, paths, gaps,
            features=(), owners=(), parent="bounded-source-relation", family="association"):
        original = scope["retainedAssociationBacklog" if family == "association" else "crossFeatureOverlapReviews"][index]
        label = f"AO-A{index + 1:02d}" if family == "association" else f"AO-O{index + 1:02d}"
        record = {"id": label, "family": family,
                  "originalItem": ref("feature-scope-v27.json", f"/{'retainedAssociationBacklog' if family == 'association' else 'crossFeatureOverlapReviews'}/{index}"),
                  "operationId": original.get("operationId"), "classification": classification,
                  "status": "source-relation-review-decided; integration-limits-retained",
                  "decision": decision, "featureIds": list(features),
                  "parentFeatureStatus": parent, "evidenceRefs": [ref(n, q) for n, q in refs],
                  "sourceEvidence": sources, "taskJoins": tasks,
                  "existingOwnerSupport": [owner(x) for x in owners],
                  "maintenanceDecision": {"proposedPaths": paths,
                      "pathInterpretation": "new maintenance responsibility proposal; original directory is not recovered",
                      "thirdPartyImplementations": "Keep imported framework/query/state helpers as dependencies; preserve first-party inputs, ordering, guards and cleanup."},
                  "remainingBoundaries": gaps, "mode": "unknown", "retainInScope": True,
                  "allConsumersAssigned": False, "actualUiChainObserved": False,
                  "fullIntegrationCompleted": False, "wholeFeatureEquivalenceClaimed": False}
        records.append(record)

    general = "settings-general-page-contracts.json"
    wsl = "wsl-project-actions-contracts.json"
    pld = "project-local-delegation-v1.json"
    start = "thread-start-entry-contracts.json"
    resume = "resume-provider-resolution.json"
    fork = "thread-fork-entry-contracts.json"
    archive = "thread-archive-entry-contracts.json"
    notification = "turn-notification-state.json"
    bindings = "turn-notification-bindings.json"
    predicate = "project-feature-condition.json"
    runtime_gap = "实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。"

    add(0, "read-only-facet; business-parent-unresolved",
        "Ks 是 General 的只读 Managed 更新策略行，只有 p(wr) 的显示条件，没有更新动作或偏好写入。把呈现交给 T01；保存的证据不足以将其归到某个已有更新业务功能，不能把它算作独立用户操作。",
        [(general, "/operationContracts/16")], [source(general, "/operationContracts/16/sourceCoordinates")],
        [task("T01", "只读更新策略行的呈现与条件")],
        ["apps/desktop/src/renderer/features/settings/general/managed-update-policy.tsx"],
        ["准确未闭合边界是 wr 所代表策略的实际 provider 与更新业务消费者；不以行标题推定父功能。", runtime_gap],
        parent="exact-unresolved-business-parent")
    add(1, "read-only-facet; business-parent-unresolved",
        "Eo 接收 access 并显示摘要/tooltip；Co/wo/To 的模型或账户读取与显示分流不构成启用动作。呈现归 T01，保留 access 输入边界；没有证据证明它就是 FSC-0280 或其他账户能力功能。",
        [(general, "/operationContracts/30")], [source(general, "/operationContracts/30/sourceCoordinates")],
        [task("T01", "访问摘要与 tooltip 的呈现")],
        ["apps/desktop/src/renderer/features/settings/general/access-summary.tsx"],
        ["实际 access provider、账户匹配结果及其业务父功能未闭合；不从 Daybreak 标签推定共享模式或权益。", runtime_gap],
        parent="exact-unresolved-business-parent")
    add(2, "composite-split; project-action-and-connection-navigation",
        "保留 FSC-0045 为 connected host 的远程建项目动作；非 connected host 的 ps 链接目标精确为 /settings/connections/wsl，导航职责接 T19。无 host 只是安装说明。三种分支不合并成一个创建操作，链接到页面不证明页面内连接操作已执行。",
        [(wsl, "/facts/1"), (wsl, "/facts/2"), (wsl, "/facts/4"), (wsl, "/facts/6")],
        [source(wsl, "/sourceUnits/wsl-card"), source(wsl, "/sourceUnits/connections-link"), source(wsl, "/sourceUnits/open-modal-sender")],
        [task("T01", "WSL 提示卡与条件"), task("T05", "FSC-0045 远程建项目入口", "existing-feature-task-membership"), task("T19", "接收 /settings/connections/wsl 导航的页面职责")],
        ["apps/desktop/src/renderer/features/projects/open-remote-project.ts", "apps/desktop/src/renderer/features/connections/wsl-entry.tsx"],
        ["Wuc 的动态门槛、消息真实送达、ht provider 和保存/重开未验证；没有把导航等同连接成功。", runtime_gap],
        features=["FSC-0045"], owners=["LM-BOUNDARY-STRUCT-RWC-PROJECTS"])
    add(3, "supporting-mcp-auxiliary-session; distinct-from-composer-start",
        "旧 TTC-OP-thread-start 与 MCP queryFn 是同一冻结范围，带 ephemeral:true、read-only 权限及 mcp_extension_host 来源。作为按 host/account/user 管理的 MCP 辅助会话保留；不关联为普通 composer 的 FSC-0048，也不增加用户功能。",
        [(start, "/oldVariantRelationship"), (start, "/facts/12"), (start, "/facts/13"), (start, "/facts/14")],
        [source(start, "/sourceUnits/initial-01~1exact-1396493-1397478")],
        [task("T16", "MCP 辅助会话生命周期的设计归属；完整 MCP 消费者未穷尽"), task("W05", "请求、订阅与退休接口支撑")],
        ["apps/desktop/src/renderer/features/mcp/auxiliary-session.ts"],
        ["pending requests/drain、完整 MCP 消费者、实际 ephemeral 与 unsubscribe 后效仍未闭合；本地 retire/abort 检查不证明服务端取消。", runtime_gap])
    add(4, "supporting-raw-resume; distinct-from-page-hydration",
        "用较新的 resume-provider-resolution 纠正旧 backlog 的 unresolved-user-entry：raw resumeThread 已有环境恢复 draft 调用者，参数、返回和状态更新与页面 resumeConversation/hydration 不同。保留为支撑，旧操作排队为0，不新建用户功能或把两接口合并。",
        [(resume, "/operationDisposition"), (resume, "/sourceFacts/5"), (resume, "/sourceFacts/10"), (resume, "/sourceFacts/11")],
        [source(resume, "/sourceUnits/manager-focus-01-class-method-kM-resumeThread"), source(resume, "/sourceUnits/publish-02-binding-It")],
        [task("T03", "环境恢复与会话协调的支撑合同；不宣称全部调用者归属"), task("W05", "保留 raw API 与协调接口的区别")],
        ["packages/app-server-client/src/raw-thread-api.ts", "apps/desktop/src/renderer/features/tasks/environment-recovery.ts"],
        ["KI 实际选择实例、完整 raw API 消费者、服务/通知/持久化及 draft 展示未验证。", runtime_gap],
        owners=["LM-PROVIDER-host-rpc-selector", "LM-PROVIDER-domain-host-registry"])
    add(5, "existing-user-operation; scoped-fork-association",
        "旧 fork 调用保留到已定义 FSC-0047/T03 的源码关联。header/sidebar 经各自条件选择本地或 worktree 分支，创建身份、同步、placement 与导航分别失败；不能把设置后失败当作未创建并自动重试，也不与普通 start 合并。",
        [(fork, "/oldVariantQualification"), (fork, "/facts/0"), (fork, "/facts/1"), (fork, "/facts/4"), (fork, "/implementationDecisions")],
        [source(fork, "/sourceUnits/header-01~1definition-hn"), source(fork, "/sourceUnits/actions-01~1definition-Zda"), source(fork, "/sourceUnits/actions-01~1definition-Qda")],
        [task("T03", "FSC-0047 分支操作", "existing-feature-task-membership"), task("W05", "分支请求/身份与协调接口")],
        ["apps/desktop/src/renderer/features/tasks/fork-thread.ts"],
        ["实际 KI/RPC 到 manager、worktree 创建、client ID 对账、持久 placement/pane 与重启未验收；target-turn 的具体 UI 入口仍未闭合。", runtime_gap],
        features=["FSC-0047"], owners=["LM-PROVIDER-host-rpc-selector"])
    add(6, "supporting-prewarm-cleanup; distinct-from-user-archive",
        "旧 archive 箭头作为 Dfn constructor 注入 Pdn 的 archiveThread；discardPrewarmedThread 对 cloud 与其他预热走不同清理，失败被吞掉。职责归 T03 的预热生命周期；明确不把它当成用户 FSC-0046 归档入口。",
        [(archive, "/facts/16"), (archive, "/oldCandidateRoleCorrection")],
        [source(archive, "/sourceUnits/manager-constructor"), source(archive, "/sourceUnits/prewarm-constructor"), source(archive, "/sourceUnits/prewarm-discard")],
        [task("T03", "预热会话的失效与清理支撑"), task("W05", "保留清理请求及错误边界")],
        ["packages/app-server-client/src/prewarm-lifecycle.ts"],
        ["实际 prewarm 实例、cloud 标志和启动/失效调度仍未知；吞错不构成服务清理成功证明。", runtime_gap])

    reductions = [
        ("thread/started", "unn 调 upsertConversationFromThread(thread,live) 并广播；所选 T7t upsert 区分更新元数据与新建 needs_resume 会话，不能视为已完整 hydrate turns。", 3),
        ("turn/started", "Rnn 处理不存在的 conversation、匹配 turn/current placeholder、新建 turn 和既有终态保护；不能仅因收到 started 名称就无条件覆盖终态。", 4),
        ("turn/completed", "Rnn 先检查 drainBefore；unknown conversation、input buffer 清理、turn 状态/时长和 unread/事件有分别的条件。回放回调不证明真实回放顺序或持久化成功。", 4),
        ("error", "Rnn 的 error 分支添加带 willRetry/codexErrorInfo 的错误项，没有直接写 status=failed；它与 turn/completed 中的 failed 终态保持不同。", 4),
    ]
    for i, (method, meaning, unit) in enumerate(reductions):
        add(7 + i, "shared-lifecycle-state-support; bounded-lexical-chain",
            f"{method} 归 T03 会话/turn 状态支撑。较新的 Program binding 证据确认 Dfn.onNotification→Vnn 及 Vnn→unn/Rnn，替换旧记录中这几条同名边未确认的描述。{meaning}",
            [(notification, f"/findings/reductions/{i}"), (notification, "/findings/routing"), (bindings, "/edges/4"), (bindings, f"/edges/{0 if i == 0 else 1}"), (bindings, "/remainingUnknowns")],
            [source(notification, "/analyses/1", True), source(notification, f"/analyses/{unit}", True)],
            [task("T03", f"{method} 状态归约与通知消费的设计归属"), task("W05", "保留通知路由、buffer 与 manager 接口")],
            ["packages/app-server-client/src/notifications/router.ts", "packages/app-server-client/src/notifications/reducers.ts"],
            ["已确认的词法边不覆盖所有 helper、动态 receiver 或初始化。准确剩余边界为 transport ingress/manager 实例、注入的状态/存储、UI 订阅者、实际到达/回放与持久化。", runtime_gap],
            owners=["LM-PROVIDER-domain-host-registry"])
    add(11, "derived-capability-support; business-parent-unresolved",
        "保留五条件派生 predicate：gate 真值、projectChatGptProvisioning/projects 存在、identity 与 local-projects query data 非空。已连接的读取者是 chatgpt-project-settings-dialog 的 c(rt)，不能把它改写成已确认的 Codex 项目动作、禁用条件或仅凭文件名排除。设计上置于 W06 项目能力接口，实际父功能仍未确定。",
        [(predicate, "/savedSettingsBinding"), (predicate, "/derivedStateContract"), (predicate, "/conditions"), (predicate, "/claims")],
        [source(predicate, "/selectedOriginalRanges/0"), source(predicate, "/selectedOriginalRanges/3"), source(predicate, "/selectedOriginalRanges/32")],
        [task("W06", "项目能力 predicate 的接口设计；尚无已证实的父用户功能")],
        ["packages/projects/src/local-project-capability.ts"],
        ["准确未闭合边界是该 s 值的实际 action/visibility 消费者及 Codex/shared 保留用途；当前37-owner中 Project domain 仅为设计协作，不证明消费者身份。", runtime_gap],
        owners=["LM-BOUNDARY-STRUCT-RWC-PROJECTS"], parent="exact-unresolved-business-parent")

    keyboard = "raw/settings-operation-batch-02/analysis/keyboard-01/source-contracts.json"
    add(0, "related-command; distinct-api-contracts-equivalence-unresolved",
        "FSC-0023 用注入 hotkeyWindowHotkeys.setHotkey(value/null)，处理 success/error/state；FSC-0068 是 commandId 参数化的 set-codex-command-keybinding，支持 set/append/replace/remove/reset/clear。两处均涉及 hotkeyWindow 和 keymap 缓存协调，但不足以证明 setHotkey 的实现等同该 RPC。保留两个目标与各自错误/捕获合同，抽取缓存协调接口；不按标题合并定义。",
        [(general, "/operationContracts/24"), ("settings-operation-batch-02.json", "/operationContracts/9"), ("settings-operation-batch-02.json", "/overlapReviews/0")],
        [source(general, "/operationContracts/24/sourceCoordinates"), source(keyboard, "/units/0")],
        [task("T01", "FSC-0023 专用 General 捕获入口", "existing-feature-task-membership"), task("T08", "FSC-0068 参数化命令编辑器", "existing-feature-task-membership")],
        ["apps/desktop/src/renderer/features/shortcuts/command-keybindings.ts", "apps/desktop/src/renderer/features/settings/general/popout-hotkey.tsx"],
        ["准确等价边界为注入的 hotkeyWindowHotkeys.setHotkey provider 与 command RPC 后端注册/保存实现；原生 registration、持久化及冲突行为未观察。", runtime_gap],
        features=["FSC-0023", "FSC-0068"], family="overlap")
    local = "raw/restoration-plan-v7/local-content-01/source-contracts.json"
    add(1, "shared-remote-entry-subset; distinct-local-picker",
        "FSC-0105 的 Ut: y!=local 时 qe({hostId:y})，local 时 Ke(scope)。完整 import 把 qe→k$t、Ke→j$t；导出把 k$t→B0r。与 FSC-0045 的 General Kr→k$t→B0r 为同一远程弹窗发送者，两入口均不传 setActive。可共用远程 open helper；FSC-0105 的本地 j$t→z0r→目录 picker 路径仍独立，不能据共享子分支合并整个功能。",
        [("settings-operation-batch-04.json", "/operationContracts/1"), (pld, "/facts"), (wsl, "/facts/2"), (wsl, "/facts/6")],
        [source(local, "/units/0"), source(local, "/imports/2"), source(pld, "/selectedSource/6"), source(pld, "/selectedSource/7")],
        [task("T14", "FSC-0105 本地环境双分支入口", "existing-feature-task-membership"), task("T05", "FSC-0045 共用远程发送者", "existing-feature-task-membership"), task("W06", "共享项目合同与 main picker 服务")],
        ["apps/desktop/src/renderer/features/projects/open-remote-project.ts", "apps/desktop/src/main/projects/project-folder-picker.ts"],
        ["共享发送者不证明 Wuc 门槛通过、弹窗挂载、项目创建或相同实际 host。local picker 的注入 manager/provider 与远程 createRemote 仍分开；保存和重开未验证。", runtime_gap],
        features=["FSC-0105", "FSC-0045"], owners=["LM-BOUNDARY-STRUCT-RWC-PROJECTS"], family="overlap")
    ssh = "raw/settings-operation-batch-05/connections/source-contracts.json"
    add(2, "distinct-ssh-deeplink-workflow; shared-domain-interface-candidate",
        "FSC-0154 的 ssh/add 深链先检查 name/alias、绝对 project path、connect，再登记/等待连接和登录，可复用缓存项目，createRemote 传 reuseExisting:true，最后选择并导航到 Codex composer。WSL/环境 Add project 经 B0r 打开交互弹窗。保留 SSH 工作流与其 abort/部分完成语义；createRemote 同名接口只支持项目域协作建议，不证明实际 provider 相同或整个操作重复。",
        [("settings-operation-batch-05.json", "/operationContracts/33"), (wsl, "/facts/7"), (wsl, "/facts/10"), (wsl, "/facts/11")],
        [source(ssh, f"/units/{i}") for i in [0, 14, 39, 79]],
        [task("T19", "FSC-0154 SSH 深链协调", "existing-feature-task-membership"), task("W06", "项目服务接口协作，实际 provider 身份待确认")],
        ["apps/desktop/src/renderer/features/connections/ssh-add-deeplink.ts", "packages/projects/src/contracts.ts"],
        ["projects.createRemote 的实际注入对象、连接服务、缓存/持久化和重开未验证。abort 抑制后续工作不回滚已经创建的 host/project。", runtime_gap],
        features=["FSC-0154", "FSC-0045", "FSC-0105"], owners=["LM-BOUNDARY-STRUCT-RWC-PROJECTS"], family="overlap")

    assert len(records) == 15
    assert len({r["id"] for r in records}) == 15
    task_coverage = load("restoration-coverage-v18.json")
    task_features = {r["taskId"]: set(r["featureIds"]) for r in task_coverage["taskGroups"]}
    for record in records:
        for feature in record["featureIds"]:
            assert feature in {x["featureId"] for x in scope["features"]}
        for join in record["taskJoins"]:
            if join["status"] == "existing-feature-task-membership":
                assert set(record["featureIds"]) & task_features[join["taskId"]]
    counts = {"associationReviewDecisions": 12, "overlapReviewDecisions": 3,
              "unreviewedItemsInFixed15": 0, "unresolvedBusinessParentItems": 3,
              "recordsRetainingIntegrationLimits": 15, "sharedRemoteSenderSubsetsConfirmed": 1,
              "staleResumeRoleCorrected": 1, "notificationAssociationsUsingNewerLexicalEvidence": 4,
              "newFeatureDefinitions": 0, "featureModesChanged": 0, "newModuleOwnersClaimed": 0,
              "newReaRuns": 0, "newFullProgramParses": 0, "newModelSubmissions": 0,
              "newClientLaunches": 0, "newServiceCalls": 0, "newProductScenarioPasses": 0,
              "newClientImplementation": 0}
    next_action = {"issueId": "SD-02",
        "question": "Decide the independent runtime/source/build or adapter route for retained Owl capabilities using existing capability and distribution evidence.",
        "fixedInput": "runtime-distribution.json, runtime-capability-decisions.json, runtime-surface-disposition.json, browser-ownership-contracts.json and existing dependency investigation actions. Reuse existing probes; do not repeat interface existence enumeration.",
        "closure": "Per retained capability group: identify source/distribution, build/ABI inputs and provider, or an exact missing external prerequisite; distinguish source preparation from full-runtime acceptance. Preserve all retained capability requirements.",
        "authorization": "Saved/frozen evidence and read-only public primary sources only; no client/model/service invocation or personal data."}
    document = {"schemaVersion": 1, "baselineId": BASE,
        "recordedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Fixed 12 retained associations and 3 overlap reviews from feature v27; no new feature discovery.",
        "status": "bounded-source-relation-decisions; analysis-in-progress",
        "plan": pin(plan_path), "records": records, "counts": counts,
        "interpretation": [
            "A reviewed source relation is separate from business-parent identity and actual integration. A01/A02/A12 retain exact unresolved business parents.",
            "Task and proposed path assignments are design decisions, except explicitly verified existing feature/task membership. They do not assert actual provider identity or all-consumer closure.",
            "The immutable feature v27, task v18 and scenario v24 definitions remain unchanged. Current state supplements old backlog review statuses through this overlay.",
            "No mode/exclusion conclusion follows from filenames, method names, empty data, shared cache keys or a source fallback.",
            "Keep first-party ordering, guards, lifecycle and error boundaries; import third-party implementations instead of generating them.",
            "The fixed source-review queue is decided; all original integration, mode and full-analysis obligations remain visible."],
        "nextAction": next_action, "inputPins": list(INPUTS.values()) + [pin(Path(__file__))],
        "fullAnalysisCompleted": False, "implementationReady": False}
    output = OUT / f"{STEM}.json"
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    evidence = []
    for record in records:
        origin = record["evidenceRefs"][0]
        evidence.append({"id": record["id"], "baselineId": BASE, "claim": record["decision"],
            "sourcePath": origin["path"], "sourceHash": origin["sha256"],
            "locator": {"kind": "json-pointer", "jsonPointer": origin["jsonPointer"]},
            "method": "saved-source-contract-and-frozen-byte-review; design-assignments-qualified",
            "confidence": "confirmed-for-bounded-source-relations; inferred-task-design",
            "verificationStatus": "source-review-decided; actual-integration-and-mode-unverified"})
    evidence_path = OUT / f"{STEM}-evidence.jsonl"
    evidence_path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in evidence))
    lines = ["# 既有关联与重叠的源码决定", "",
        "固定处理 feature v27 的12项关联与3项重叠，15项均已给出有边界的源码决定。A01/A02/A12的业务父功能仍未确定；15项均保留实际集成限制。373项功能、48任务、1216条未执行规格和模式分类不变。", "",
        "|编号|决定|任务设计归属|", "|---|---|---|"]
    for record in records:
        lines.append(f"|{record['id']}|{record['classification']}|{', '.join(x['taskId'] for x in record['taskJoins'])}|")
    lines += ["", "以下路径都是新的维护职责建议，不表示恢复原工程目录或生成客户端实现。", ""]
    for record in records:
        lines += [f"## {record['id']}", "", record["decision"], "",
            "维护位置：" + "、".join(f"`{x}`" for x in record["maintenanceDecision"]["proposedPaths"]) + "。", "",
            "剩余边界：" + "；".join(record["remainingBoundaries"]), ""]
    lines += ["完整引用、原始字节范围、任务和既有职责归属见同名 JSON；证据15行按九字段发布。", "",
        "下一项为 SD-02 独立运行时采用决定：复用已有能力差异与发行来源证据，明确每组保留能力的来源、构建输入、provider或准确外部缺口。完整分析尚未完成。", ""]
    summary = OUT / f"{STEM}.md"
    summary.write_text("\n".join(lines))
    for path in [output, evidence_path, summary]:
        path.chmod(0o444)
    overlay = {"result": pin(output), "summary": pin(summary), "evidence": pin(evidence_path),
        "counts": counts, "replacesBacklogReviewStatusOnly": True,
        "qualification": "12 source-association decisions and 3 overlap decisions; 3 unresolved business parents and 15 integration-limited records remain. No whole-feature merge, exclusion or runtime acceptance.",
        "fullAnalysisCompleted": False}
    state["associationOverlapDecisions"] = overlay
    state["stageDecisions"]["associationOverlapOverlay"] = overlay
    state["stageDecisions"]["nextAction"] = next_action
    state["featureScopeCurrentView"]["associationOverlapDecisionOverlay"] = overlay
    state["restorationCoverageCurrentOverlay"]["associationOverlapDecisionOverlay"] = overlay
    state["logicalModuleInventory"]["associationOverlapRefinement"] = overlay
    current_counts = state["featureScopeCurrentView"]["counts"]
    current_counts["additionalCrossFeatureOverlapReviewsPending"] = 0
    current_counts["crossFeatureOverlapDecisionsWithIntegrationLimits"] = 3
    current_counts["associationRelationsAwaitingSourceReview"] = 0
    current_counts["associationRelationsWithBoundedSourceDecision"] = 12
    current_counts["associationBusinessParentsUnresolved"] = 3
    state["pending"][0] = "SD-01: 已保存968条来源角色待分类0；12关联/3重叠均有源码关系决定，3项业务父功能仍未确定。真实provider/模式与完整功能身份仍有缺口；源码关系审阅完成不等于集成完成。45设置容器局部合同已全部交付。"
    state["updatedAtUtc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    paragraph = ("当前[12关联与3重叠的源码决定](association-overlap-decisions-v1.md)已发布：确认WSL/本地环境共用远程发送者，区分SSH、本地picker与快捷键接口，更新resume支撑角色及4项通知词法关联。3项业务父功能与15项集成限制保留；373功能、48任务、1216未执行规格不变。下一项为SD-02独立运行时采用决定，完整分析未完成。")
    for name in ["report.md", "gaps.md"]:
        path = OUT / name
        text = path.read_text()
        (WORK / f"{name}.before").write_text(text)
        _, tail = text.split("\n\n", 1)
        path.write_text(paragraph + "\n\n" + tail)
    print(json.dumps({"publication": str(output), "counts": counts,
        "uniqueFrozenSourceFiles": len(SOURCE_BYTES), "inputPins": len(document["inputPins"]),
        "nextIssue": "SD-02", "fullAnalysisCompleted": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
