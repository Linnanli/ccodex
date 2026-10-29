"""Publish three settings control surfaces and extend the finite feature view."""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/settings-operation-batch-02"
RAW = OUT / "raw/settings-operation-batch-02"
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"


def load(p):
    return json.loads(p.read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    return {"path": os.path.relpath(p, OUT), "bytes": len(b), "sha256": sha(b)}


def ref(p, pointer):
    return {**pin(p), "jsonPointer": pointer}


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


artifacts = ["settings-operation-batch-02.json", "settings-operation-batch-02.md", "feature-scope-v9.json",
             "feature-scope-v9.csv", "feature-scope-v9-scenarios.json"]
assert not RAW.exists() and all(not (OUT / n).exists() for n in artifacts)
old = load(OUT / "feature-scope-v8.json")
old_scenarios = load(OUT / "feature-scope-v8-scenarios.json")
before = load(OUT / "analysis-state.json")
assert before["featureScopeCurrentView"]["snapshotVersion"] == 8
assert len(old["features"]) == 58 and len(old_scenarios["scenarios"]) == 260
observations = load(WORK / "isolated-observations.json")
assert observations["counts"] == {"isolatedSourceCases": 29, "passed": 29, "productScenariosExecuted": 0}
assert len({x["caseId"] for x in observations["observations"]}) == 29
executions = load(WORK / "parse-execution.json")
assert len(executions) == 8 and all(x["observedExitCode"] == 0 for x in executions)
programs = {x["outputDirectory"]: load(WORK / x["outputDirectory"] / "source-contracts.json") for x in executions}
source_bytes, spans = {}, set()


def verify(v):
    if isinstance(v, list):
        for x in v:
            verify(x)
    elif isinstance(v, dict):
        if "sourcePath" in v and "sourceHash" in v:
            path = v["sourcePath"]
            if path not in source_bytes:
                source_bytes[path] = (FROZEN / path.removeprefix("app.asar/")).read_bytes()
            b = source_bytes[path]
            assert sha(b) == v["sourceHash"]
            r = v.get("byteRange") or v.get("locator")
            if r and "start" in r and "endExclusive" in r and "spanHash" in v:
                assert sha(b[r["start"]:r["endExclusive"]]) == v["spanHash"]
                spans.add((path, r["start"], r["endExclusive"]))
        for x in v.values():
            verify(x)


for folder, data in programs.items():
    assert data["fullProgramParsed"]
    assert not data.get("unresolved", [])
    verify(data)
    for u in data["units"]:
        assert sha((WORK / folder / u["sourceFilename"]).read_bytes()) == u["spanHash"]
for name in ["materialized-helpers.json", "bounded-initializers.json", "isolated-observations.json"]:
    verify(load(WORK / name))
RAW.mkdir(parents=True)
shutil.copytree(WORK, RAW / "analysis")
shutil.copyfile(OUT / "analysis-state.json", RAW / "analysis-state-before.json")
for name in [Path(__file__).name, "settings_operations_ast.mjs", "git_settings_ast.mjs", "probe_settings_batch_02.cjs"]:
    shutil.copyfile(ROOT / "scripts/analysis" / name, RAW / name)


def unit(folder, name):
    index = next(i for i, u in enumerate(programs[folder]["units"]) if u["name"] == name)
    return ref(RAW / "analysis" / folder / "source-contracts.json", f"/units/{index}")


contract_path, summary_path, scope_path, csv_path, scenarios_path = [OUT / x for x in artifacts]
dispositions = load(OUT / "settings-section-dispositions.json")
visibility = load(OUT / "settings-mode-boundary-contracts.json")
entries = []
for slug, page in [("worktrees", "Worktrees"), ("keyboard-shortcuts", "Keyboard shortcuts"), ("file-type-handlers", "File type handlers")]:
    i, row = next((i, r) for i, r in enumerate(dispositions["entries"]) if r["slug"] == slug)
    review = next(r for r in visibility["settingsSectionReviews"] if r["slug"] == slug)
    entries.append({
        "slug": slug, "page": page, "surfaceId": row["entryId"], "factoryId": row["factoryId"],
        "factoryRef": row["factoryRef"], "sectionRef": row["sectionRef"], "visibilityRef": row["visibilityRef"],
        "routeInstanceRef": ref(OUT / "settings-registry-contracts.json", f"/routeInstances/{row['savedSettingsRouteInstance']}"),
        "staticRouteInstance": row["savedSettingsRouteInstance"], "priorDispositionRef": ref(OUT / "settings-section-dispositions.json", f"/entries/{i}"),
        "accessFamily": row["accessFamily"], "availableInReducedHostList": review["availableInReducedList"],
        "outerConditionRef": row["outerEntryConditionRef"],
        "conditions": ["Preserve selected-host list filtering, access-family calculation and outer loading/error/redirect/render priority.",
                       "Actual host/account/platform/gates, selected service instance and page mounting remain unobserved."],
        "productMode": "unknown", "actualMountObserved": False, "confirmedExclusion": False,
    })
entries[0]["localPredicate"] = "The switch falls through to visible:true,pending:false; access-family and outer entry conditions still apply."
entries[0]["pageBranch"] = "Gate 375130565 and tab=environments select a host/location-keyed lazy LocalEnvironmentsSettingsContent; otherwise xn renders the worktree controls. That content is delegated, not analyzed as a duplicate worktree feature."
entries[0]["delegatedEnvironmentFactoryRef"] = unit("worktrees-01", "assignment-Mn")
entries[1]["localPredicate"] = "visible:true,pending:false in this section's switch case."
entries[1]["presentationBranch"] = "Vt uses explicit presentation==='chatgpt', otherwise selected-mode value==='work', to choose m. Both renderer presentations exist; runtime product-mode ownership is not inferred from labels alone."
entries[2]["localPredicate"] = "Preserve te fields and visible=te.visible || (te.enabled && currentSection==='file-type-handlers')."

mechanisms = {
    "hostPreferenceWrite": {
        "claim": "nga/tft uses shared mg/wjt for literal host local. For other hosts it gets qf, cancels its query, optimistically clones config.desktop[key], then sends config/batchWrite with replace, configWriteTarget.filePath or null, expectedVersion:null and reloadUserConfig:true. Failure restores the prior snapshot. Finally it invalidates three host keys, plus worktree-list/environment-related keys when changing worktreeRoot.",
        "sourceRefs": [unit("initial-01", "nga"), unit("initial-01", "assignment-rga"), ref(OUT / "settings-git-page-contracts.json", "/sharedSettingsPipeline")],
        "scopeQualification": "Static selected host-write contract. Actual remote configuration receiver, file path, durable flush and consumer effects remain unobserved.",
    },
    "worktreeConversationDiscovery": {
        "operationId": "operation:settings-batch-02:SUPPORT-001", "claim": "cn pages nonarchived thread/list with limit100 and rejects repeated nextCursor. sn lists pins then reads each pinned thread. on merges/deduplicates normal lists and pins. an optionally enriches via ln only when a non-special host has threadAttachmentOwners capability, requires connected state for that path, polls every minute and disables retry. ln processes root/owner reads in batches of ten and checks the supplied abort signal between requests; no server-side cancellation is proven.",
        "sourceRefs": [unit("worktrees-01", n) for n in ["an", "cn", "sn", "on", "ln", "pn", "Tn"]],
        "scopeQualification": "This is support for worktree browsing, not an extra user feature. Native cwd links, attached links, pin priority and unpinned subagent filtering are separate rules; it is not an exhaustive owner census.",
    },
    "serializedPreferredViewerWrite": {
        "operationId": "operation:settings-batch-02:SUPPORT-002", "claim": "O7s/Rw chains through a WeakMap keyed by queryClient, reads current preferredViewers when its queued turn starts, merges [host/extensionKey]:viewer and writes through mg/wjt. It stores a caught promise so later work continues after failure, while returning the original rejecting promise to the caller. Independent queryClient instances are not serialized by this selected function.",
        "sourceRefs": [unit("initial-01", "O7s"), ref(RAW / "analysis/bounded-initializers.json", "/0"), unit("shared-01", "assignment-cMt")],
        "scopeQualification": "Queue logic replayed with synthetic reads/writes; actual cache isolation, cross-window races and disk durability remain unobserved.",
    },
    "shortcutEditAndReset": {
        "claim": "Vt sends set-codex-command-keybinding {commandId,update} and reset-codex-command-keybindings. Success seeds the codex-command-keymap-state cache and refreshes it and global-dictation-hotkey-state; hotkey-window state is additionally refreshed for its row and global reset. ve exposes conditional set/append/replace/remove/reset/clear payloads, conflict checks, annotation-mode validation and capture cancel; capability and presentation constrain available actions.",
        "sourceRefs": [unit("keyboard-01", "Vt"), unit("command-row-01", "ve"), unit("command-row-01", "Ce"), unit("command-row-01", "Te"), unit("command-filter-01", "l")],
        "scopeQualification": "The command receiver, physical key capture/normalization, OS registration and durable keymap backend remain explicit boundaries; no actual keybinding is changed.",
    },
}

# Goal granularity groups alternate gestures and parameter values; automatic helpers are support.
specs = [
    (0, "浏览并刷新工作树及关联会话", "worktrees-01", ["xn", "An", "pn", "kn", "Cn", "an"],
     "Open the general worktrees tab or press Refresh.",
     "Worktree query requires available host settings; preserve loading/error/empty states, local-environment-root exclusion, repo grouping and visible conversation rules.",
     "codex-worktrees via git service with hostConfig, operationSource=worktrees_settings_page and worktreesRoot; Refresh runs worktree and conversation refetches in parallel.",
     "Aggregate error is worktree ?? local-environment-roots ?? conversation error. Selected Refresh callback has no local catch; no explicit page-level cancellation control.",
     "query data and host settings", ["worktree-query-01", "h"], ["operation:settings-batch-02:SUPPORT-001"]),
    (0, "设置工作树根目录", "worktrees-01", ["Ht", "$t"],
     "Edit the root input; blur or enabled CmdOrCtrl+S.",
     "$t hides preference controls without host settings. Root edits are ignored while pending; save requires changed draft and !pending, trims it, and accepts empty or the imported valid-path predicate plus host-home-selected path.isAbsolute.",
     "Host-specific nga/tft writes git- worktreeRoot descriptor key git-worktree-root; success clears draft and shows success.",
     "Invalid input makes no request; failure retains draft and shows error. Path scheme is selected from host codexHome, not simply the renderer OS. No explicit cancel action.",
     "host configuration; key git-worktree-root; default empty", None, []),
    (0, "设置创建工作树前刷新上游", "worktrees-01", ["Jt"],
     "Toggle Always fetch upstream before creating worktrees.",
     "Disabled while its mutation is pending; direct onChange maps true to best-effort and false to never without an extra handler guard.",
     "Shared settings writer for upstreamRefreshMode (worktree-upstream-refresh-mode); source initializer $pt=never is pinned, initialization order/runtime effective value unverified.",
     "Error toast on save failure; no operation-level cancel or proof of an actual fetch.",
     "shared setting; descriptor agentAccess hidden", None, []),
    (0, "设置自动清理旧工作树", "worktrees-01", ["Jt", "Yt"],
     "Toggle automatic deletion; confirm when disabling.",
     "Pending checkbox suppressed. Enabling writes true directly; disabling opens a dialog and only confirmation writes false, clears count draft and closes dialog. Cancel closes dialog without writing.",
     "Host-specific writer for worktree-auto-cleanup-enabled, descriptor default true; success feedback reflects submitted boolean.",
     "Failure shows error; no compensating cleanup operation or deletion is performed by this toggle handler.",
     "host configuration", None, []),
    (0, "设置自动清理保留工作树数量", "worktrees-01", ["Jt"],
     "Edit numeric limit; blur or Enter.",
     "Disabled if count mutation or cleanup mutation is pending or cleanup disabled. Trim then parseInt(base10), blank/NaN clear draft, clamp to at least1; unchanged clears draft without writing.",
     "Host-specific writer for worktree-keep-count, descriptor default15 and integer>=1 schema; successful write clears draft.",
     "Failure retains draft and shows error. Page parseInt also accepts a numeric prefix, e.g. 3garbage ->3; HTML numeric input does not replace source-level acceptance rules.",
     "host configuration", None, []),
    (0, "打开工作树关联的会话", "worktrees-01", ["En", "Cn"],
     "Click a visible known conversation row.",
     "Rows use linked data filtered to pinned or non-subagent conversations; loading and empty states are explicit.",
     "Invoke imported imt navigation callback with conversation.id and selected hostId.",
     "Navigation/service failure and later thread loading are delegated; no local error/cancel handler is present in this row callback.",
     "navigation selection; not a saved preference", None, ["operation:settings-batch-02:SUPPORT-001"]),
    (0, "在已有工作树开始新会话", "worktrees-01", ["En"],
     "Click New chat in this worktree.",
     "Shown for local host kind unless the selected source conversation belongs to the excluded local project kind/id condition; disabled while this worktree deletion state is pending.",
     "Invoke imported TU helper with sourceConversationId from the first pinned/non-subagent native conversation, optionally undefined, and workspaceRoot=worktree.dir.",
     "The source supplies workspace reuse intent; actual task creation, first turn, navigation and errors remain behind TU. No automatic first-message submission is proven.",
     "new-conversation preparation/navigation", None, []),
    (0, "删除指定工作树及归档其本地会话", "worktrees-01", ["En", "gn"],
     "Click Delete on a worktree row.",
     "Button disabled while conversations load or a native conversation is pinned. gn separately suppresses repeated work and refreshes pins before any archive/delete.",
     "When unpinned, await all supplied native conversation archives with cleanupWorktree:false and source=worktree_delete, then worktree-delete {hostId,worktree,reason:settings-delete-targeted}, invalidate host list, show success.",
     "Pin presence warns and returns. Exceptions are caught/logged, show danger, and finally release pending. Partial archives or a successful deletion followed by invalidate error are not compensated; no explicit user cancellation or confirmation is added by this selected handler.",
     "archive and git deletion service effects; actual file recovery unobserved", None, ["operation:settings-batch-02:SUPPORT-001"]),
    (1, "搜索可配置的键盘快捷键", "keyboard-01", ["Vt", "Zt"],
     "Search text or switch to keystroke search.",
     "Available command set is filtered by platform, capabilities, feature flags, registered commands and presentation. Text uses command id/title/description; keystroke mode matches complete stroke prefixes, supports a compatible sequence, ignores repeat and bare Escape exits/clears.",
     "Update local search/mode state only; external-browser and number-target rows have separate search visibility rules.",
     "Loading keymap shows loading; no-match state differs from active search auxiliaries. No persistence or backend cancellation is claimed for local search.",
     "transient component state", ["command-filter-01", "l"], []),
    (1, "编辑或恢复单项命令快捷键", "keyboard-01", ["Vt"],
     "Capture a keybinding, append/remove a binding, reset one command or clear it where the presentation permits.",
     "ve disables controls while pending. Sequence and bare-modifier support depend on command kind/id. Conflict checks include fixed Find, registered commands and both directions of sequence-prefix overlap; annotation mode has additional restrictions.",
     "set-codex-command-keybinding {commandId,update}: set/append/replace(previousAccelerator,accelerator)/remove(accelerator)/reset/clear as source branches select. ChatGPT composer Enter can select reset. Success updates/invalidates keymap and related hotkey caches.",
     "Cancel capture clears editor state without writing; conflicts keep editor state and show message. RPC failure is caught by row wrapper and shown inline; later editor-close behavior differs by presentation and preserves newer capture state by identity.",
     "keymap RPC and OS registration/durable store", ["command-row-01", "ve"], []),
    (1, "批量恢复快捷键默认值", "keyboard-01", ["Vt", "Xt"],
     "Click reset/restore defaults and confirm when required.",
     "Suppress while reset busy. Codex presentation opens confirmation then resets all keybindings and, when its preference exists, external-browser modifier in parallel. ChatGPT presentation directly resets eligible customized commands sequentially, limited to the focused customized command if present; the search-filtered result list is not its reset scope.",
     "On complete success close dialog; keep cache refresh behavior of each mutation.",
     "Cancel confirmation writes nothing. Partial failures show an error and release busy; no rollback of successful sibling resets or preference writes. Focus changes the ChatGPT branch scope.",
     "keymap RPC plus shared external-browser preference", None, []),
    (1, "设置数字快捷键切换聊天或标签页", "keyboard-01", ["Lt"],
     "Choose tabs or sidebar.",
     "Number-target row is gated by unified-tab-strip/search conditions. Trigger disabled while saving; same-value selections have no callback equality check. Existing custom-binding conflicts are shown as a notice rather than blocking write.",
     "Shared writer for primary-number-shortcut-target, descriptor default tabs; labels vary with macOS Command/Control vs other platform Control/Alt.",
     "Failure sets inline error and finally clears pending; actual key dispatch and persisted value require separate observation.",
     "shared setting", None, []),
    (1, "设置点击链接时使用系统浏览器的修饰键", "keyboard-01", ["jt", "Vt"],
     "Choose unassigned, primary, alt or primary-shift.",
     "Row requires non-ChatGPT presentation, an available preference and matching search mode/query. Pending disables trigger; selected-equal value is suppressed.",
     "Shared writer for external-browser-link-shortcut, default primary; global Codex reset can also restore its default.",
     "Failure shows inline error; finally releases pending. Actual link opening and OS target remain consumer boundaries.",
     "shared setting", None, []),
    (2, "查看并重试文件类型处理器发现", "file-handlers-01", ["J", "W", "ce"],
     "Open file-type handlers or click Retry.",
     "Normalize extensions by trim/removing leading dots/lowercase, remove empty, deduplicate/sort. Discovery failure includes either query error or any toolsError; initial empty loading, empty success and refetch feedback are distinct.",
     "Retry calls primary refetch and optional auxiliary refetch only when its isEnabled flag is true, in one Promise.all.",
     "Selected retry callback does not catch its returned rejection locally; failed UI offers retry. No preference mutation or explicit cancellation control.",
     "plugin catalog/query providers", None, []),
    (2, "选择文件类型的首选查看器", "file-handlers-01", ["ue"],
     "Choose Built-in/default or one eligible plugin viewer for an extension.",
     "Skip a row if bot cannot form a preference key. Use extension-specific eligible viewers sorted by title; bot/Izi resolve the longest matching suffix and key JSON([hostId,extension]). Row selection accepts default or an available viewer identity; resolver/default policy remains a boundary.",
     "Rw queues a latest-map merge into preferred-file-viewers. Viewer id is JSON([server,tool.name,resourceUri,pluginId??null]); optimistic row selection uses an incrementing request id.",
     "Only the latest row request can set error and clear pending selection; an older failure cannot replace newer feedback. Row is not globally disabled while saving and requests are not cancelled. A write failure is shown inline.",
     "shared setting; hidden agentAccess; default empty map", ["initial-01", "bIa"], ["operation:settings-batch-02:SUPPORT-002"]),
]
assert len(specs) == 15
operations = []
for i, (page_index, name, folder, names, trigger, guard, effect, failure, state_kind, extra, support) in enumerate(specs):
    refs = [unit(folder, n) for n in names] + ([unit(*extra)] if extra else [])
    operations.append({"operationId": f"operation:settings-batch-02:OP-{i+1:03}", "featureId": f"FSC-{59+i:04}",
        "pageIndex": page_index, "name": name, "trigger": trigger, "guard": guard, "effect": effect,
        "failureAndCancellation": failure, "stateAndPersistence": state_kind,
        "sourceRefs": refs, "supportOperationIds": support, "method": "static-code", "confidence": "confirmed",
        "verificationStatus": "selected-source-contract;actual-product-behavior-not-observed", "completeChainProven": False})

scenario_specs = [
    [("view", "Check host query enablement, loading/error/empty/list states, environment exclusions, repository groups and linked conversations."), ("refresh", "Refresh worktree and conversation queries together; observe fetching state and error propagation."), ("links", "Deduplicate native/attached owners, include pinned subagents and exclude unpinned subagents; retain incomplete-owner qualification."), ("host-switch", "Switch selected host/root and verify keyed queries and abort delivery without assuming service-side cancellation.")],
    [("save", "Save empty and valid absolute trimmed roots using host-specific path style; observe the selected local/remote writer."), ("guard", "Invalid/unchanged/pending input submits nothing; pending input edits ignored."), ("failure", "Reject writer; retain draft and show save error with the correct cache rollback boundary."), ("restore", "Observe actual local store flush or remote config persistence, reopen/restart, then verify effective root.")],
    [("mapping", "Map true/false to best-effort/never, disable while pending and show submitted-value feedback."), ("failure", "Reject shared writer and verify error; do not infer that any Git fetch ran."), ("restore", "Verify effective preference after actual flush/reopen and separately observe the creation-time fetch consumer.")],
    [("enable", "Enable directly and verify host-specific true write."), ("confirm-cancel", "Disable opens dialog; cancel writes nothing and confirmation writes false while clearing count draft."), ("failure", "Reject write, show error and release pending without inventing deletion/undo side effects."), ("restore", "Verify actual saved preference and automatic-cleanup consumer under appropriate host conditions.")],
    [("parse", "Exercise blank/NaN, equal15, zero/negative, decimal and numeric-prefix input; record reset/clamp/parseInt outcomes."), ("disabled", "Cleanup disabled or either related mutation pending disables count edits/saves."), ("failure", "Reject write and preserve editable draft with error feedback."), ("restore", "Observe actual config persistence/reopen and verify cleanup count is consumed separately.")],
    [("navigate", "Click a visible linked conversation and observe exact conversationId and hostId delivery to navigation."), ("visibility", "Loading/empty/filtered subagent rows must match source rules."), ("failure-boundary", "Observe delegate failure/loading; selected row adds no local catch or cancel behavior.")],
    [("prepare", "Invoke TU with worktree root and first eligible native source id or undefined; verify workspace reuse without assuming first-turn submission."), ("guard", "Check local/project conditions and deletion-pending disabled state."), ("delegate-outcome", "Observe downstream creation/navigation/failure separately from callback delivery.")],
    [("delete-order", "Await all native archives with cleanupWorktree:false before targeted delete and invalidation."), ("pins", "Initial pinned/loading guard and fresh pinned recheck must suppress deletion, warn and release pending."), ("repeat", "Repeated delete during pending is suppressed."), ("failure", "Inject archive/delete/invalidate failures separately; record partial effects, danger feedback, no compensation and final pending release."), ("recovery", "Inspect actual archived threads, worktree files and recovery capabilities after service completion/restart; source toast is insufficient.")],
    [("text", "Filter eligible commands by id/title/description and preserve conditional auxiliary rows."), ("keys", "Search by complete stroke prefix and compatible sequence; ignore repeats and let bare Escape clear/exit."), ("conditions", "Vary source-defined platform/capability/presentation gates and loading/no-match states; physical key normalization remains separately verified.")],
    [("payloads", "Verify all applicable set/append/replace/remove/reset/clear payloads across command kinds and presentations."), ("validation", "Reject fixed-Find, command and sequence-prefix conflicts and unsupported annotation-mode keys; do not dispatch writes."), ("cancel", "Cancel capture and verify no preference update, editor cleanup and source-defined focus behavior."), ("failure", "Reject update; show inline error, respect pending controls and preserve newer editor state according to presentation."), ("restore", "Verify actual receiver, OS registration, durable keymap and dispatch after reopen/restart.")],
    [("codex-reset", "Confirm global reset and optional external-browser default in parallel; verify each success cache update."), ("chatgpt-scope", "Verify focused customized-command reset or all eligible customized commands sequentially; search text must not silently narrow this scope."), ("cancel", "Cancel Codex confirmation with no reset requests."), ("partial-failure", "Fail one sibling or sequential update; release busy, show error and retain completed effects without invented rollback.")],
    [("select", "Select tabs/sidebar under row conditions; conflict notice must not suppress write and no same-value guard is assumed."), ("failure", "Reject shared write, show inline error and release pending."), ("restore", "Verify stored preference and actual platform-specific number-key consumer after reopen/restart.")],
    [("select", "Choose each supported modifier; selected-equal suppressed, pending trigger disabled and presentation/search visibility preserved."), ("failure", "Reject write and show inline error while releasing pending."), ("restore", "Verify stored preference, reset coupling and actual default-browser link opening separately.")],
    [("catalog", "Normalize, deduplicate and sort extensions; preserve toolsError and query error aggregation."), ("states", "Check initial loading, fetching-with-results, empty success and failed discovery."), ("retry", "Retry primary plus enabled auxiliary query only; observe Promise.all rejection rather than inventing local recovery."), ("host-switch", "Switch host and confirm catalog/query invalidation and cancellation delivery as supported by actual providers.")],
    [("select", "Resolve longest suffix/key, eligible viewer ids and Built-in selection; skip a row lacking a key."), ("concurrency", "Issue two choices; old failure must not replace newer feedback, and same-queryClient queued writes preserve other keys."), ("failure", "Fail a queued write; show latest row error and allow next queued update to proceed; inspect cross-queryClient race separately."), ("restore", "Observe actual settings flush/reopen and file-opening consumer; successful row callback does not prove durable viewer behavior.")],
]
assert len(scenario_specs) == 15
new_scenario_count = sum(map(len, scenario_specs))
counts = {"pageControlSurfaces": 3, "userGoals": 15, "supportOperations": 2, "sourceProgramsParsed": 8,
    "isolatedSourceCasesPassed": 29, "newProductScenarioSpecifications": new_scenario_count,
    "productScenariosExecuted": 0, "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0,
    "confirmedChatGptExclusionsAdded": 0, "delegatedEnvironmentContentNotDuplicated": True}
facts = []
for i, op in enumerate(operations):
    first_ref = op["sourceRefs"][0]
    folder = specs[i][2]
    u = next(x for x in programs[folder]["units"] if x["name"] == specs[i][3][0])
    facts.append({"id": f"SETTINGS-BATCH-02-F{i+1:03}", "baselineId": BASE, "claim": op["effect"],
        "sourcePath": u["sourcePath"], "sourceHash": u["sourceHash"], "locator": {"kind": "byte-range", **u["byteRange"]},
        "spanHash": u["spanHash"], "method": "static-code", "confidence": "confirmed",
        "verificationStatus": "static-selected-control-contract", "operationId": op["operationId"], "sourceRef": first_ref})
contract = {"schemaVersion": "settings-operation-batch/1", "baselineId": BASE,
    "scope": "Selected Worktrees general-tab controls, complete Keyboard shortcuts control module/command row, and File type handlers controls; delegated environment content and external service implementations stay separate.",
    "method": "REA-backed frozen registry and prior named exports, eight full original Program lexical ASTs, selected source review and 29 synthetic function replays.",
    "entries": entries, "operationContracts": operations, "mechanisms": mechanisms, "facts": facts, "counts": counts,
    "descriptorsRef": ref(RAW / "analysis/shared-01/source-contracts.json", "/units"),
    "originalGitDescriptorRef": ref(OUT / "settings-git-page-contracts.json", "/descriptorPropertiesWithoutControlsInThisPage"),
    "sourceCheckedInitializers": pin(RAW / "analysis/bounded-initializers.json"),
    "isolatedObservation": pin(RAW / "analysis/isolated-observations.json"),
    "dependencyBoundary": {"thirdPartyImplementationGenerated": False,
        "applicationResponsibilities": ["worktree settings/query and deletion coordination", "shortcut search/editor/reset orchestration", "plugin file-viewer selection and serialized map updates"],
        "externalBoundaries": ["React/compiler and controls", "query/mutation cache and cancellation", "Git worktree worker, thread/pin services and navigation", "settings/config/RPC receivers and durable backend", "OS hotkey capture/registration", "plugin discovery/resolver policy"],
        "packageIdentityQualification": "This control analysis does not introduce new package-version or complete third-party closure claims; existing dependency investigations remain authoritative."},
    "overlapReviews": [
        {"featureIds": ["FSC-0023", "FSC-0068"], "status": "possible-parameterized-overlap", "reason": "General popup-window shortcut and the parameterized command editor can expose hotkeyWindow-related behavior; exact API/consumer equivalence is unproven. Keep both scoped records pending cross-entry review."},
        {"featureIds": ["FSC-0048", "FSC-0065"], "status": "distinct-observed-source-entry-no-equivalence-claim", "reason": "Worktree TU preparation callback is not proof of ordinary composer creation plus first-turn submission."},
    ],
    "remainingDecisions": ["actual mounting and gate/presentation/product-mode inputs", "actual settings/config and keymap receiver, store flush and restart durability", "actual Git deletion/archive/recovery and navigation/create effects", "physical capture/OS registration, catalog policy and runtime package compatibility", "cross-entry feature overlap and complete dependency/mode closure"],
    "fullAnalysisCompleted": False, "clientImplementationStarted": False}
dump(contract_path, contract)

new_features, new_scenarios = [], []
for i, op in enumerate(operations):
    op_ref = ref(contract_path, f"/operationContracts/{i}")
    entry_ref = ref(contract_path, f"/entries/{op['pageIndex']}")
    ids = []
    for kind, expectation in scenario_specs[i]:
        sid = f"{op['featureId']}:SB02-OP-{i+1:03}:{kind}"
        ids.append(sid)
        new_scenarios.append({"scenarioId": sid, "featureId": op["featureId"], "operationId": op["operationId"], "kind": kind,
            "preconditions": {"pageEntryRef": entry_ref, "guard": op["guard"], "actualValuesObserved": False},
            "trigger": op["trigger"], "expectedEffect": expectation, "sourceRef": op_ref,
            "sourceQualification": "source-derived acceptance specification; synthetic helper replays do not execute this product scenario",
            "executionStatus": "not-executed", "runtimeObservationRefs": [],
            "authorization": "Specification only; no real preference/thread/worktree/OS shortcut modification, model submission or installed-client run."})
    new_features.append({"featureId": op["featureId"], "baselineId": BASE, "name": op["name"], "page": entries[op["pageIndex"]]["page"],
        "definitionStatus": "author-reviewed-scoped-user-goal", "granularityRationale": "One user goal groups parameterized values/gestures; query aggregation and serialized map updates remain support. Scope is finite and possible cross-entry overlap is explicitly retained.",
        "trigger": op["trigger"], "operationMembers": [{"operationId": op["operationId"], "operationType": "settings-control-goal", "trigger": op["trigger"], "parameters": op["effect"], "operationRef": op_ref}],
        "supportOperationIds": op["supportOperationIds"], "sourceRefs": [op_ref, entry_ref],
        "chain": op["effect"], "conditions": entries[op["pageIndex"]]["conditions"] + [op["guard"]],
        "boundaries": [op["stateAndPersistence"], op["failureAndCancellation"]], "mode": "unknown",
        "modeEvidence": "Source presentation/access-family conditions recorded; actual product-mode ownership and complete caller/shared closure remain unestablished.",
        "retentionStatus": "retain-pending-mode-review", "sourceSpecificationStatus": "static-control-and-qualified-service-contract",
        "runtimeStatus": "not-observed-for-this-feature", "isolatedObservationRef": contract["isolatedObservation"],
        "completeChainProven": False, "scenarioIds": ids, "knownGaps": contract["remainingDecisions"],
        "implementationAcceptance": [op["guard"], op["effect"], op["failureAndCancellation"], "Treat actual persistence, OS/service effects and restart recovery as separately observed outcomes."]})

scope = copy.deepcopy(old)
scope["previousScopeRef"] = pin(OUT / "feature-scope-v8.json")
scope["previousScenarioRef"] = pin(OUT / "feature-scope-v8-scenarios.json")
scope["purpose"] = "Finite reviewed user goals extended by three control surfaces, without claiming a complete or globally deduplicated client feature denominator."
scope["newDefinitionIds"] = [x["featureId"] for x in new_features]
scope["features"] += new_features
for key, consumers in [("worktreeConversationDiscovery", list(range(59, 67))), ("serializedPreferredViewerWrite", [73])]:
    mechanism = mechanisms[key]
    scope["supportOperations"].append({"operationId": mechanism["operationId"], "operationRef": ref(contract_path, f"/mechanisms/{key}"),
        "catalogNamespace": "settings-batch-02", "featureIds": [f"FSC-{x:04}" for x in consumers],
        "classificationConfidence": "confirmed", "excludedFromProductScope": False, "operationEquivalenceClaimed": False,
        "actualUiChainObserved": False, "status": "supporting-mechanism", "supportKind": key,
        "reason": mechanism["scopeQualification"], "supportDoesNotExhaustConsumers": True})
scope["rootCandidateDispositions"] += [{"operationId": x["operationId"], "role": "user", "childOperationIds": []} for x in operations]
scope["rootCandidateDispositions"] += [{"operationId": mechanisms[k]["operationId"], "role": "support", "childOperationIds": []} for k in ["worktreeConversationDiscovery", "serializedPreferredViewerWrite"]]
for index, page in enumerate(entries):
    feature_ids = [op["featureId"] for op in operations if op["pageIndex"] == index]
    relation_index = len(scope["pageContainerRelations"])
    scope["pageContainerRelations"].append({"page": page["page"], "legacyEntryId": "ROUTE-0152",
        "supportInstancePointer": f"/registrations/151/staticMapInstances/{page['staticRouteInstance']}",
        "factoryContractId": page["factoryId"], "featureIds": feature_ids,
        "relation": "conditional-route-container-to-factory-to-controls", "confidence": "confirmed-static-association",
        "sourceRefs": [page["routeInstanceRef"], page["factoryRef"], ref(contract_path, f"/entries/{index}")],
        "conditions": page["conditions"], "actualMountObserved": False, "sameOperationClaimed": False, "entryCompletelyResolved": False})
    scope["legacyFeatureRelations"] += [{"featureId": fid, "status": "conditional-container-association", "entryIds": ["ROUTE-0152"], "pageRelationIndices": [relation_index],
        "completeEntryEquivalenceProven": False, "remainingWork": "实际mount、条件值、运行/耐久性、模式及跨入口重叠仍待核对。"} for fid in feature_ids]
scope["legacyEntryCoverage"]["mappingUpdates"][0]["featureIds"] += scope["newDefinitionIds"]
scope["legacyEntryCoverage"]["qualification"] = "67 scoped definitions associate conditionally with one legacy route template across seven page surfaces; no additional legacy entry declared resolved."
scope.setdefault("crossFeatureOverlapReviews", []).append({"sourceRef": ref(contract_path, "/overlapReviews/0"), "status": "pending-equivalence-review"})
c = scope["counts"]
c.update({"scopedFeatureDefinitions": 73, "assignedUserOperations": 77, "supportOperations": 25,
    "allKnownOperationCandidatesAccountedFor": 101, "unexecutedScenarioSpecifications": 260 + new_scenario_count,
    "normalizedBehaviorLeaves": 103, "featuresConditionallyAssociatedWithLegacyContainers": 67,
    "additionalDiscoveredRootCandidates": 30,
    "rootCandidateDispositionCounts": {"user": 76, "support": 23, "pending": 1, "composite": 1},
    "modeCounts": {"unknown": 73, "codex": 0, "chatgpt": 0, "shared": 0},
    "additionalCrossFeatureOverlapReviewsPending": 1})
scenarios = copy.deepcopy(old_scenarios)
scenarios.update({"previousSnapshotRef": pin(OUT / "feature-scope-v8-scenarios.json"),
    "scenarios": old_scenarios["scenarios"] + new_scenarios, "count": 260 + new_scenario_count})
assert scope["features"][:58] == old["features"] and scenarios["scenarios"][:260] == old_scenarios["scenarios"]
assert scope["supportOperations"][:23] == old["supportOperations"]
assert scope["retainedAssociationBacklog"] == old["retainedAssociationBacklog"]
assert scope["operationReviewQueue"] == old["operationReviewQueue"]
assert len(scope["features"]) == 73 and sum(len(f["operationMembers"]) for f in scope["features"]) == 77
assert len(scope["supportOperations"]) == 25
assert len(scope["rootCandidateDispositions"]) == len({x["operationId"] for x in scope["rootCandidateDispositions"]}) == 101
assert dict(collections.Counter(x["role"] for x in scope["rootCandidateDispositions"])) == c["rootCandidateDispositionCounts"]
assert len({x["scenarioId"] for x in scenarios["scenarios"]}) == scenarios["count"]
assert all(x.get("executionStatus", x.get("status")) == "not-executed" for x in scenarios["scenarios"])
assert all(x["mode"] == "unknown" and not x["completeChainProven"] for x in scope["features"])
assert c["normalizedBehaviorLeaves"] == c["assignedUserOperations"] + c["supportOperations"] + c["queuedOperations"]
dump(scope_path, scope)
dump(scenarios_path, scenarios)
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["featureId", "name", "mode", "operationCount", "runtimeStatus", "completeChainProven"])
    writer.writeheader()
    for x in scope["features"]:
        writer.writerow({"featureId": x["featureId"], "name": x["name"], "mode": x["mode"], "operationCount": len(x["operationMembers"]), "runtimeStatus": x["runtimeStatus"], "completeChainProven": x["completeChainProven"]})
lines = ["# 设置操作第二批：Worktrees、键盘快捷键、文件类型处理器", "",
    f"本批交付15项用户目标、2项支撑机制和{new_scenario_count}条待执行验收规格。当前[有限功能台账v9](feature-scope-v9.json)包含73项定义、{scenarios['count']}条未执行产品规格；全客户端功能分母、跨入口去重和产品模式分类仍未闭合。", "",
    "| 页面 | 用户目标 |", "| --- | --- |"]
for op in operations:
    lines.append(f"| {entries[op['pageIndex']]['page']} | {op['name']} |")
lines += ["", "Worktrees的根目录、自动清理开关和保留数量采用host专用写入：local走共享设置，其他host通过config/batchWrite更新desktop键，并分别处理缓存回滚和失效。刷新上游偏好仍走共享设置。根目录先trim并检查绝对路径，路径风格由host codexHome选择；保留数量采用parseInt并钳制到至少1，不能用HTML输入属性替代这段逻辑。关闭自动清理需要确认，取消不写入。", "",
    "工作树列表聚合正常线程、pinned线程及条件下的附件owner，去重并过滤未pinned的子代理；并不保证列出所有owner。删除前重新读取pins，先等待所有传入native会话归档，再删除指定工作树并刷新列表；异常最终释放pending。归档部分成功或删除成功后刷新失败都没有补偿，错误反馈不等于所有副作用均未发生。新建和打开会话分别保留TU/导航边界，没有把回调送达当作创建任务或发送首条消息。environments标签委托到独立本地环境内容，保留为另一个页面的分析任务。", "",
    "键盘页按展示模式、平台、能力和开关筛选命令，文本搜索与按键序列搜索分开。行编辑器记录set/append/replace/remove/reset/clear、序列前缀冲突、annotation限制及取消行为。Codex展示的批量重置先确认，再并发重置keymap及可用的链接修饰键；另一展示分支顺序重置符合条件的自定义命令，若有匹配焦点则只处理该项，搜索结果不会自动缩小这个集合。部分失败保留已完成效果。General中的弹窗快捷键与参数化命令编辑可能有重叠，已列专门去重项，未宣称73项是全局唯一功能分母。", "",
    "文件类型处理器按host和最长匹配扩展名选择查看器。每行用请求序号抑制旧请求的错误/清理反馈；共享map写入另按queryClient排队、执行时读取最新map并合并，前项失败不会卡住后续项。两个不同queryClient之间的竞争不由这段代码解决，实际跨窗口和持久化仍需验证。Retry只重试主query和已启用的辅助query。", "",
    "8份完整Program解析和29项隔离源码回放通过；所用hooks、缓存、RPC、线程、pins、删除、viewer resolver及按键解析均有明确替身边界，没有实际读取或修改个人项目、会话、偏好、快捷键或工作树，没有新增模型请求，也没有运行原客户端。隔离回放不计作产品场景实测。", "",
    "[逐项合同、事实和源码引用](settings-operation-batch-02.json)区分控件、委托组件和真实服务后效。第三方实现没有生成到客户端源码；React/compiler、query/mutation、OS与服务依赖保持外部边界，包版本仍按既有依赖调查处理。", "",
    "已定位的45个设置页面容器中，七个页面有功能合同关联，剩余38个继续按页面批次处理。这是控件分析覆盖，不代表这些页面的运行行为已全部验证。下一批优先Notifications、Appearance与Appshots，并与既有General/Agent合同做去重；公共运行和存储缺口继续独立验证。", ""]
summary_path.write_text("\n".join(lines))
profile = {"contracts": pin(contract_path), "summary": pin(summary_path), "counts": counts,
    "featureSnapshot": pin(scope_path), "scenarioSnapshot": pin(scenarios_path), "fullAnalysisCompleted": False}
state = copy.deepcopy(before)
state["updatedAtUtc"] = datetime.now(timezone.utc).isoformat()
state["settingsOperationBatch02"] = profile
view = state["featureScopeCurrentView"]
view.update({"snapshotVersion": 9, "scope": "Finite reviewed view; 71 original roots plus30 additional candidates; possible cross-entry overlap retained.",
    "ledger": pin(scope_path), "csv": pin(csv_path), "scenarios": pin(scenarios_path), "counts": c,
    "previousLedger": pin(OUT / "feature-scope-v8.json"), "reconciliationKind": "worktrees-keyboard-file-handler-controls",
    "reconciliationArtifact": pin(contract_path), "settingsOperationBatch02Overlay": pin(contract_path),
    "entryConditionOverlayQualification": "Original overlay covers v7; Git additions use its entry contract, and v9 additions use settings-operation-batch-02.json/entries. All original snapshots stay immutable.",
    "settingsSectionDispositionOverlayQualification": "Original disposition snapshot predates Git and batch02 operation definitions; the two later control contracts supersede only those four pending surface dispositions."})
state["settingsOperationCoverage"] = {"catalogPageContainersIncludingPriorThree": 45,
    "pageSurfacesWithScopedControlContracts": ["General", "Agent", "Computer use", "Git", "Worktrees", "Keyboard shortcuts", "File type handlers"],
    "remainingPageContainers": 38, "qualification": "Control contracts include explicit external/delegated boundaries; this does not count actual product passes or a full function denominator."}
stage = state["stageDecisions"]
stage["latestSubstep"] = profile
stage["counts"].update({"currentFeatureDefinitions": 73, "currentRootOperationCandidates": 101, "currentUnexecutedScenarios": scenarios["count"]})
stage["nextAction"] = {"issueId": "SD-01", "completedSubstep": "Three page surfaces;15 scoped goals;two support operations;29 isolated cases and56 unexecuted acceptance specifications",
    "fixedInput": "剩余38个已定位设置页面；下一批Notifications、Appearance、Appshots及既有合同重叠核对",
    "question": "继续批量建立用户操作、状态/保存/取消/失败边界与验收规格；把相同偏好或命令的不同入口列为去重关联。",
    "closure": "交付每个页面的操作与委托边界，更新有限台账及覆盖表；页面数、源码回放数不充当功能总数或产品实测通过数。",
    "deferredDedicatedVerification": "实际设置/keymap/config耐久性、Git删除/恢复、OS热键、导航/新建与模式共享闭包独立列队。"}
assert state["latestBehaviorAuthorizationState"] == before["latestBehaviorAuthorizationState"]
assert state["analysisMilestones"] == before["analysisMilestones"]
assert not state["fullAnalysisCompleted"]
report_path, gaps_path = OUT / "report.md", OUT / "gaps.md"
report, gaps = report_path.read_text(), gaps_path.read_text()
old_text = "下一项批量收束其余41个设置页面，真实持久化/消费者另列验证，见 analysis-state.json 的 stageDecisions。"
assert report.count(old_text) == 1
report = report.replace(old_text, f"[设置操作第二批](settings-operation-batch-02.md)交付Worktrees、键盘与文件处理器15项用户目标，29项隔离回放通过；当前[台账v9](feature-scope-v9.json)含73项有限定义、{scenarios['count']}条未执行规格。其余38个页面继续按批处理，运行/去重缺口独立列队。")
old_text = "下一项批量展开其余41个设置页面；这些运行缺口不作为源码盘点前置阻断，SD-01整体仍部分完成。"
assert gaps.count(old_text) == 1
gaps = gaps.replace(old_text, f"[设置操作第二批](settings-operation-batch-02.md)又交付三个页面15项目标、2项支撑、29项隔离回放；当前73项有限定义／{scenarios['count']}条未执行规格，新增快捷键跨入口重叠待查。剩余38个页面按批继续，真实持久化/服务/模式缺口不阻断源码盘点；SD-01整体仍部分完成。")
dump(RAW / "validation.json", {"sourcePrograms": len(programs), "sourceFiles": len(source_bytes), "verifiedDistinctSpans": len(spans),
    "originalSavedUnitBytesMatch": True, "allParseExitsZero": True, "old58FeaturesAnd260ScenariosPreserved": True,
    "originalQueueAndBacklogPreserved": True, "newCounts": counts, "scopeCounts": c,
    "modelAuthorizationUnchanged": True, "historicalMilestonesUnchanged": True,
    "producer": pin(RAW / Path(__file__).name), "artifacts": [pin(OUT / n) for n in artifacts]})
dump(OUT / "analysis-state.json", state)
report_path.write_text(report)
gaps_path.write_text(gaps)
for p in [*(OUT / n for n in artifacts), *RAW.rglob("*")]:
    if p.is_file():
        p.chmod(0o444)
print(json.dumps({"published": str(contract_path), "counts": counts, "scopeCounts": c}, ensure_ascii=False))
