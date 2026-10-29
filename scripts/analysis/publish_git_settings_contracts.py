"""Publish the bounded Git page contract and append scoped features without rewriting history."""
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
WORK = ROOT / ".analysis-local/git-settings-contract-work"
RAW = OUT / "raw/git-settings-page"
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"


def load(p):
    return json.loads(p.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(p):
    data = p.read_bytes()
    return {"path": os.path.relpath(p, OUT), "bytes": len(data), "sha256": digest(data)}


def ref(p, pointer):
    return {**pin(p), "jsonPointer": pointer}


def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


names = ["settings-git-page-contracts.json", "settings-git-page-summary.md", "feature-scope-v8.json",
         "feature-scope-v8.csv", "feature-scope-v8-scenarios.json"]
assert not RAW.exists() and all(not (OUT / n).exists() for n in names)
previous = load(OUT / "feature-scope-v7.json")
previous_scenarios = load(OUT / "feature-scope-v7-scenarios.json")
before_state = load(OUT / "analysis-state.json")
assert before_state["featureScopeCurrentView"]["snapshotVersion"] == 7
assert len(previous["features"]) == 48 and len(previous_scenarios["scenarios"]) == 212
observation = load(WORK / "isolated-observations-02.json")
assert observation["counts"] == {"isolatedSourceCases": 21, "passed": 21, "productScenariosExecuted": 0}
assert len({x["caseId"] for x in observation["observations"]}) == 21
assert all(x["passed"] for x in observation["observations"])

# Verify original bytes and all stored source locators once, before publishing the current view.
sources = {}
validated_spans = set()


def verify_source_tree(value):
    if isinstance(value, list):
        for item in value:
            verify_source_tree(item)
    elif isinstance(value, dict):
        if "sourcePath" in value and "sourceHash" in value:
            key = value["sourcePath"]
            if key not in sources:
                sources[key] = (FROZEN / key.removeprefix("app.asar/")).read_bytes()
            original = sources[key]
            assert digest(original) == value["sourceHash"], key
            span = value.get("byteRange") or value.get("locator")
            if span and "start" in span and "endExclusive" in span and "spanHash" in value:
                start, end = span["start"], span["endExclusive"]
                assert digest(original[start:end]) == value["spanHash"], (key, start, end)
                validated_spans.add((key, start, end))
        for child in value.values():
            verify_source_tree(child)


programs = {}
for folder in ["local-01", "shared-01", "watcher-01", "watcher-02", "classifier-01", "main-01"]:
    data = load(WORK / folder / "source-contracts.json")
    assert data["fullProgramParsed"]
    verify_source_tree(data)
    for unit in data.get("units", []):
        assert digest((WORK / folder / unit["sourceFilename"]).read_bytes()) == unit["spanHash"]
    programs[folder] = data
verify_source_tree(load(WORK / "supplemental-units.json"))
verify_source_tree(load(WORK / "main-01/materialized-providers.json"))
verify_source_tree(observation["loadedSourceUnits"])

RAW.mkdir(parents=True)
shutil.copytree(WORK, RAW / "analysis")
shutil.copyfile(OUT / "analysis-state.json", RAW / "analysis-state-before.json")
for name in [Path(__file__).name, "git_settings_ast.mjs", "settings_page_surface_ast.mjs", "probe_git_settings.cjs"]:
    shutil.copyfile(ROOT / "scripts/analysis" / name, RAW / name)


def unit(folder, name):
    data = programs[folder]
    index = next(i for i, x in enumerate(data["units"]) if x["name"] == name)
    return ref(RAW / "analysis" / folder / "source-contracts.json", f"/units/{index}")


contract_path = OUT / names[0]
summary_path = OUT / names[1]
scope_path = OUT / names[2]
csv_path = OUT / names[3]
scenarios_path = OUT / names[4]
entry = {
    "slug": "git-settings", "surfaceId": "SETTINGS-SURFACE-024", "factoryId": "SETTINGS-PAGE-FACTORY-024",
    "factoryRef": ref(OUT / "settings-registry-contracts.json", "/pageFactoryContracts/23"),
    "routeInstanceRef": ref(OUT / "settings-registry-contracts.json", "/routeInstances/17"),
    "sectionRef": ref(OUT / "settings-registry-contracts.json", "/sectionDataflowContracts/18"),
    "visibilityRef": ref(OUT / "settings-mode-boundary-contracts.json", "/settingsSectionReviews/24"),
    "outerConditionRef": ref(OUT / "settings-feature-entry-conditions.json", "/commonEntryCondition"),
    "priorDispositionRef": ref(OUT / "settings-section-dispositions.json", "/entries/24"),
    "conditions": [
        "The outer selected-host descriptor must permit this section; git-settings is absent from the reduced host list.",
        "The codexLocal access-family result must permit navigation visibility; the local visibility switch falls through to visible:true,pending:false.",
        "Outer loading/error/redirect and render priority remain as specified by the shared entry-condition contract; navigation visibility alone is not a universal rendering guard.",
        "Ce additionally returns null when its imported selector h(O) is false; the actual selector value and product mode are unobserved.",
    ],
    "actualMountObserved": False, "productMode": "unknown", "confirmedExclusion": False,
}
# Entry rows are in review order, not factory-number order.
dispositions = load(OUT / "settings-section-dispositions.json")
entry["priorDispositionRef"] = ref(OUT / "settings-section-dispositions.json", "/entries/" + str(next(
    i for i, row in enumerate(dispositions["entries"]) if row["entryId"] == entry["surfaceId"])))

descriptors = [
    ("branchPrefix", "git-branch-prefix", "codex/", "DN", "read-write"),
    ("alwaysForcePush", "git-always-force-push", False, "TN", "read-write"),
    ("createPullRequestAsDraft", "git-create-pull-request-as-draft", True, "TN", "read-write"),
    ("pullRequestMergeMethod", "git-pull-request-merge-method", "merge", "U([merge,squash])", "read-write"),
    ("commitInstructions", "git-commit-instructions", "", "DN", "read-only"),
    ("pullRequestInstructions", "git-pr-instructions", "", "DN", "read-only"),
    ("reviewMode", "git-review-mode", "full", "U([full,last-turn-only])", "read-write"),
    ("reviewDelivery", "reviewDelivery", "inline", "U([inline,detached])", "read-write"),
    ("pullRequestWatchAutoMerge", "git-pr-watch-auto-merge", False, "TN", "read-only"),
    ("pullRequestWatchInstructions", "git-pr-watch-instructions", "", "DN", "read-only"),
]
descriptor_rows = [{"property": prop, "key": key, "default": default, "schemaExpression": schema,
                    "agentAccess": access, "sourceRef": unit("shared-01", "assignment-cP" if prop == "reviewDelivery" else "assignment-NN")}
                   for prop, key, default, schema, access in descriptors]
shared_pipeline = {
    "reader": "$kn -> uAn keyed by descriptor.key -> VK data.values[key] ?? descriptor.default",
    "query": "VK: host settings.readAll when available, otherwise get-settings; networkMode always, placeholder sAn, five-second staleTime.",
    "writer": "rAn snapshots VK, starts cancel, captures old data, optimistically patches by default, awaits cancel, then awaits oAn; write error restores the entire old snapshot; finally awaits invalidate then calls GG.",
    "nonOptimisticOption": "optimistic:false patches the current cache only after successful write, preserving concurrent unrelated keys in that snapshot.",
    "conditionalProviderErrors": "cancel is awaited before try and invalidate before GG; injected cancel rejection bypasses write/rollback/finally, and injected invalidate rejection skips GG. Real provider failure behavior is not established by this probe.",
    "hostOrFallback": "oAn: e6.settings.write(key,value) when available; otherwise generic set-setting params {key,value}. aAn reads effective directly from host, or fallback response.value ?? default.",
    "mainFallback": "Selected get/set-setting handlers use getSettingValue/setSettingValue. The setter validates/casts through r.F then awaits this.settings.write. Initialization wraps injected T in AL and invokes afterWrite side effects.",
    "durabilityBoundary": "AL.write calls store.set and afterWrite without explicitly awaiting store.flush. AL.writeForAgent enforces descriptor.agentAccess and explicitly flushes. Backing store instance, file path, schedule, durability and actual host-to-main identity remain unobserved.",
    "uiVersusAgentAccess": "agentAccess read-only does not disable these UI controls; it is enforced by writeForAgent, a separate path.",
    "sourceRefs": [unit("shared-01", n) for n in ["$kn", "rAn", "oAn", "aAn", "assignment-VK", "assignment-uAn"]]
                  + [unit("main-01", n) for n in ["handler-get-setting", "handler-get-settings", "handler-set-setting", "method-setSettingValue"]]
                  + [ref(RAW / "analysis/main-01/materialized-providers.json", "")],
    "scopeQualification": "Static selected source paths and synthetic provider replay; no real preferences, filesystem store, service, native host or product run.",
}
autosave = {
    "debounceMs": 3000, "savedFeedbackMs": 3000,
    "mutationScope": "autosaving-instructions-${setting.key}",
    "draft": "A snapshot object records each edit. Reverting to savedValue clears dirty only when no mutation is pending; editing remains allowed while pending.",
    "automatic": "Timer and unmount flush submit only a draft snapshot distinct from last-submitted and last-failed; there is no automatic isPending check. Mutation serialization belongs to the imported provider.",
    "explicit": "Save and CmdOrCtrl+S require draft and !isPending, clear the failed snapshot and submit. The textarea has no blur-save handler and no explicit cancel action.",
    "success": "Clear only the submitted snapshot, preserve newer edits, show saved feedback, call onSaved with the submitted value even when a newer draft exists.",
    "failure": "Retain draft and mark failed snapshot, show danger toast, suppress automatic/unmount retry of that snapshot; explicit save or a new edit permits another attempt.",
    "sourceRefs": [unit("local-01", n) for n in ["be", "me", "he"]],
    "runtimeQualification": "Hook lifecycle, timer, pending state and mutation delivery are substitutes; no React or query/mutation implementation is executed.",
}
watcher = {
    "operationId": "operation:git:GIT-SUPPORT-001", "role": "support",
    "trigger": "De schedules a separate scoped mutation after a preference save, using the submitted value plus the peer preference captured by the current callback.",
    "scope": "pull-request-watch-preferences",
    "selection": "v lists automations; F9n/gM require heartbeat and the exact ## Pull request fix automation: prompt line, status ACTIVE, and the heartbeat continuation marker line D. Other records are skipped.",
    "transformation": "Preserve all prompt lines through marker D, rebuild following lines using C(prefs), trim custom instructions, skip an unchanged prompt.",
    "payload": ["id", "kind=heartbeat", "name", "prompt", "status=ACTIVE", "targetThreadId", "model", "reasoningEffort", "rrule"],
    "effect": "b calls automation-update for existing items; response must satisfy the original heartbeat kind predicate. Promise.all updates are concurrent; the page invalidates list-automations only after the updater resolves.",
    "failures": "Errors propagate to a separate active-watcher error toast. Preference-save success can already have been reported. No compensation of saved preferences or successful sibling watcher updates is present in this selected path.",
    "sourceRefs": [unit("local-01", "De"), *[unit("watcher-02", n) for n in ["v", "b", "C", "assignment-D"]], unit("classifier-01", "F9n"), ref(RAW / "analysis/supplemental-units.json", "")],
    "actualAutomationsReadOrWritten": 0, "productEffectObserved": False,
}

# The feature unit is the user preference goal, not each callback or bundled descriptor.
operation_specs = [
    ("设置新建分支前缀", "Ne", "branch-prefix-input", "Edit raw string; save on blur or enabled CmdOrCtrl+S.",
     "Draft differs from saved and !mutation.isPending; onChange ignored while pending; equal-to-saved clears draft.",
     "Write draft without page-level trimming; success clears draft and reports success.",
     "Write error reports danger and retains draft; shared optimistic rollback applies; no explicit cancel action."),
    ("设置始终强制推送", "Ne", "always-force-push-toggle", "Toggle boolean.",
     "Control disabled and handler suppressed while pending; no same-value guard.",
     "Write submitted boolean, report enabled/disabled success message.", "Write error reports danger; shared rollback applies."),
    ("设置默认创建草稿 PR", "Ne", "draft-pr-toggle", "Toggle boolean.",
     "Control disabled and handler suppressed while pending; no same-value guard.",
     "Write submitted boolean and report success.", "Write error reports danger; shared rollback applies."),
    ("设置 PR 合并方式", "Ne", "merge-method-selector", "Select merge or squash.",
     "Control disabled while pending; callback requires !pending and value !== saved.",
     "Write selected enum and report success.", "Write error reports danger; shared rollback applies."),
    ("设置提交指令", "Ne/be/me/he", "commit-instructions-textarea", "Edit text; autosave, Save, CmdOrCtrl+S, or unmount flush.",
     "Shared autosave snapshot and pending rules apply.", "Save through the common settings writer.", "Shared autosave failure and retry rules apply; no explicit cancel action."),
    ("设置 PR 描述指令", "Ne/be/me/he", "pr-instructions-textarea", "Edit text; autosave, Save, CmdOrCtrl+S, or unmount flush.",
     "Shared autosave snapshot and pending rules apply.", "Save through the common settings writer.", "Shared autosave failure and retry rules apply; no explicit cancel action."),
    ("设置禁用 Git 差异面板", "Ce", "disable-git-diffs-toggle", "Toggle checkbox; true maps to last-turn-only, false to full.",
     "Ce returns null when h(O) is false; no control-level pending or equality guard in this function.",
     "Direct settings writer call for the mapped value.", "Rejected writer promise reports danger; no separate cancel or draft."),
    ("设置代码审查展示位置", "Ae", "review-delivery-selector", "Select inline or detached.",
     "Displayed value falls back to inline; no control-level pending or equality guard in this function.",
     "Direct settings writer call with selected enum.", "Rejected writer promise reports danger; no separate cancel or draft."),
    ("设置监听 PR 自动合并偏好", "De", "watcher-auto-merge-toggle", "Toggle boolean.",
     "Control disabled while preference mutation pending; callback itself directly calls mutate without additional equality/pending guard.",
     "Save preference, schedule active-watcher update using submitted autoMerge and captured current instructions, then report preference success.",
     "Preference failure prevents its success callback. Active-watcher failure is separate and does not roll back saved preference."),
    ("设置监听 PR 的自定义指令", "De/be/me/he", "watcher-instructions-textarea", "Edit text; shared autosave/manual/unmount flow.",
     "Shared autosave snapshot and pending rules apply.",
     "Save preference; onSaved schedules active-watcher update using saved instructions and captured current autoMerge.",
     "Autosave failure retains draft; separate active-watcher failure does not roll back preference. Old success can still apply an older saved snapshot to watchers."),
]
operations = []
for index, spec in enumerate(operation_specs):
    title, component, control, trigger, guard, success, failure = spec
    primary = "Ne" if component.startswith("Ne") else "De" if component.startswith("De") else component
    operations.append({
        "operationId": f"operation:git:GIT-OP-{index + 1:03}", "contractId": f"GIT-OP-{index + 1:03}",
        "featureId": f"FSC-{index + 49:04}", "name": title, "component": component, "control": control,
        "trigger": trigger, "guard": guard, "parameters": descriptor_rows[index],
        "success": success, "failureAndCancellation": failure,
        "chain": f"{component} -> D/read descriptor + F/rAn -> oAn -> host settings.write or set-setting -> selected main AL/write path",
        "sourceRefs": [unit("local-01", primary), descriptor_rows[index]["sourceRef"]],
        "sharedWriterRef": "/sharedSettingsPipeline", "autosaveRef": "/autosave" if index in [4, 5, 9] else None,
        "supportOperationIds": [watcher["operationId"]] if index in [8, 9] else [],
        "persistenceExpectation": "Read effective value on reopening; actual backing path, flush and restart durability require separate observation.",
        "mode": "unknown", "runtimeStatus": "not-observed-for-this-feature", "completeChainProven": False,
    })

counts = {
    "userPreferenceGoals": 10, "supportOperations": 1,
    "completeProgramParseArtifacts": 6, "distinctSourceProgramsParsed": 5,
    "isolatedSourceCasesPassed": 21, "productScenariosExecuted": 0,
    "newScopedFeatureDefinitions": 10, "newRootCandidates": 11,
    "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0, "confirmedChatGptExclusionsAdded": 0,
}
contract = {
    "schemaVersion": "git-settings-page-contracts/1", "baselineId": BASE,
    "scope": "All controls rendered by the selected frozen Git settings page; shared persistence and active-watcher update boundaries are qualified separately.",
    "method": "REA-backed frozen settings registry and named component binding, supplemented by complete original Program lexical ASTs and synthetic execution of selected original function bodies.",
    "entry": entry, "operationContracts": operations, "sharedSettingsPipeline": shared_pipeline,
    "autosave": autosave, "activeWatcherUpdate": watcher,
    "descriptorInventory": descriptor_rows,
    "descriptorPropertiesWithoutControlsInThisPage": ["pullRequestPollIntervalSeconds", "showSidebarPrIcons", "worktreeRoot"],
    "dependencyBoundary": {
        "applicationResponsibilities": ["Git preference controls", "settings descriptors and transport adapter", "autosaving instruction state", "existing PR watcher prompt transformation and update adapter"],
        "externalProviderBoundaries": ["React/compiler hooks and JSX", "query/mutation provider and scoped scheduling", "notification/i18n controls", "host settings/RPC and automation request services"],
        "thirdPartyCodeGenerated": False,
        "qualification": "Boundaries are architecture inputs, not claims that every imported helper is a third-party package or that exact package versions and complete dependency closure are established.",
    },
    "isolatedObservation": pin(RAW / "analysis/isolated-observations-02.json"),
    "earlierObservation": pin(RAW / "analysis/isolated-observations.json"),
    "observationAccounting": "The latest run contains 21 distinct cases; the earlier 18 overlap and are not added to obtain 39. None is an executed product scenario.",
    "parseReproduction": "git_settings_ast.mjs was extended in stages: local closure, selected provider roots/assignments, then main class handlers. Saved semantic results pin original Programs; the archived final recipe supports all three modes. The watcher named-export parse used settings_page_surface_ast.mjs.",
    "counts": counts,
    "remainingDecisions": [
        "Actual mount, gate/selector values, host/account/platform and product-mode ownership.",
        "Actual selected settings service and main instance, backing store/schema/defaults, side effects, write scheduling/flush and restart durability.",
        "Behavioral consumers of these saved preferences: branch creation, push, PR creation/merge, diff filtering and review delivery.",
        "Actual mutation serialization, competing preference updates, watcher list/update service and partial-failure reconciliation.",
    ],
    "fullAnalysisCompleted": False, "clientImplementationStarted": False,
}
dump(contract_path, contract)

# Scenario descriptions preserve separate UI, persistence and service-failure acceptance boundaries.
scenario_specs = [
    [("changed-save", "Edit prefix and blur or press enabled CmdOrCtrl+S; save exact draft, then clear it on success."),
     ("unchanged-or-pending", "Revert to saved prefix or keep a write pending; unchanged/pending save is suppressed and pending input edits are ignored."),
     ("write-error", "Reject write; draft remains available, danger feedback appears and optimistic snapshot is restored when the writer reaches its catch."),
     ("restore", "After a successful durable flush, reopen/restart and verify the effective prefix; actual flush and store path must be observed separately.")],
    [("write", "Toggle force-push and verify submitted boolean plus enabled/disabled success feedback."),
     ("pending", "During a pending write the control is disabled and handler suppresses a call; same-value calls are not separately guarded."),
     ("write-error", "Reject preference write and verify error feedback and shared optimistic rollback."),
     ("restore", "Observe backing-store flush and reopen/restart with the saved boolean.")],
    [("write", "Toggle default draft PR and verify submitted boolean and success feedback."),
     ("pending", "Verify disabled and handler-level pending suppression; no same-value guard is assumed."),
     ("write-error", "Reject preference write and verify error feedback and shared optimistic rollback."),
     ("restore", "Observe backing-store flush and reopen/restart with the saved boolean.")],
    [("write", "Select merge and squash; verify selected enum and success feedback."),
     ("unchanged-or-pending", "A saved-equal selection or pending mutation is suppressed by the callback; pending control is disabled."),
     ("write-error", "Reject write and verify error feedback and shared optimistic rollback."),
     ("restore", "Observe backing-store flush and reopen/restart with the saved merge method.")],
]
instruction_cases = [
    ("autosave", "Edit text; before 3000ms no automatic submission, after 3000ms submit the current snapshot; verify saved feedback expires after 3000ms."),
    ("revert", "Revert to the saved value before submission while not pending; clear dirty state and issue no write."),
    ("retry", "Fail a snapshot; retain draft and suppress automatic/unmount retry of that snapshot; explicit Save retries once not pending."),
    ("newer-edit", "While an older snapshot is pending, edit a new value; older success preserves the newer draft. Explicit pending save is suppressed; automatic scheduling is delegated to the scoped mutation provider."),
    ("unmount", "Unmount with an unsubmitted fresh draft; submit it once. Already submitted or failed snapshots are not automatically duplicated."),
    ("restore", "Observe actual store flush and reopen/restart with the latest accepted preference; a success callback alone does not prove durability."),
]
scenario_specs += [copy.deepcopy(instruction_cases), copy.deepcopy(instruction_cases)]
scenario_specs += [
    [("visibility", "Verify the control is absent when Ce's selector is false and visible when true under permitted page conditions."),
     ("mapping", "Toggle true/false and verify last-turn-only/full writes; this component has no explicit pending or same-value guard."),
     ("write-error", "Reject the direct writer promise and verify danger feedback and common rollback where applicable."),
     ("restore", "Observe actual store flush and reopen/restart with the saved review mode; separately verify the diff-panel consumer.")],
    [("selection", "Verify inline fallback and inline/detached selection; do not assume an equality or pending suppression absent from the callback."),
     ("repeat", "Invoke the same selected value again and record direct writer delivery; provider/UI delivery still requires actual observation."),
     ("write-error", "Reject the writer promise and verify danger feedback and common rollback where applicable."),
     ("restore", "Observe actual store flush and reopen/restart with the saved delivery choice; separately verify review creation behavior.")],
    [("save-and-update", "Save autoMerge, then update matching active watchers with submitted boolean and captured instructions, preserving item identity/schedule/model fields."),
     ("pending", "Verify control disabled during preference write; distinguish direct mutate callback from a second handler-level guard."),
     ("preference-error", "Reject preference write; verify preference error feedback and no success-triggered active update."),
     ("active-update-error", "Allow preference success, fail one active update; verify separate error and retained preference. Observe partial sibling updates and no invented compensation."),
     ("restore", "Observe actual store flush and reopen/restart; separately verify server-held watcher payloads.")],
    [instruction_cases[0], instruction_cases[2], instruction_cases[3], instruction_cases[4],
     ("watcher-payload", "After instruction save, apply submitted text and captured autoMerge; filter by heartbeat, ACTIVE and both exact marker lines, trim custom text, preserve header and other fields, skip unchanged prompts."),
     ("active-update-error", "Allow instruction preference save, fail watcher update or return a non-heartbeat response; retain preference and report separate active-update error."),
     instruction_cases[5]],
]
assert len(scenario_specs) == 10 and sum(map(len, scenario_specs)) == 48
new_scenarios = []
new_features = []
for index, op in enumerate(operations):
    op_ref = ref(contract_path, f"/operationContracts/{index}")
    ids = []
    for kind, expected in scenario_specs[index]:
        sid = f"{op['featureId']}:{op['contractId']}:{kind}"
        ids.append(sid)
        new_scenarios.append({
            "scenarioId": sid, "featureId": op["featureId"], "operationId": op["operationId"], "kind": kind,
            "preconditions": {"pageEntryRef": ref(contract_path, "/entry"), "guard": op["guard"], "actualValuesObserved": False},
            "trigger": op["trigger"], "expectedEffect": expected, "sourceRef": op_ref,
            "sourceQualification": "source-derived product acceptance specification; isolated helper results do not execute this product scenario",
            "executionStatus": "not-executed", "runtimeObservationRefs": [],
            "authorization": "Specification only; no additional model submission, desktop preference change or real automation read/update performed.",
        })
    new_features.append({
        "featureId": op["featureId"], "baselineId": BASE, "name": op["name"], "page": "Git",
        "definitionStatus": "author-reviewed-scoped-user-goal",
        "granularityRationale": "One saved user preference goal; generic autosave and active-watcher application remain supporting mechanisms rather than extra user goals.",
        "trigger": op["trigger"], "operationMembers": [{"operationId": op["operationId"], "operationType": "git-preference-write",
            "trigger": op["trigger"], "parameters": op["parameters"], "operationRef": op_ref}],
        "supportOperationIds": op["supportOperationIds"], "sourceRefs": [op_ref, ref(contract_path, "/entry"), ref(contract_path, "/sharedSettingsPipeline")],
        "chain": op["chain"], "conditions": entry["conditions"] + [op["guard"]],
        "boundaries": ["page control/state", "shared setting cache and transport", "selected host/main store", "backing-store durability and preference consumers"]
                      + (["active watcher service update"] if op["supportOperationIds"] else []),
        "mode": "unknown", "modeEvidence": "Access-family labels, setting names and defaults do not establish product-mode exclusivity or a complete shared dependency closure.",
        "retentionStatus": "retain-pending-mode-review", "sourceSpecificationStatus": "static-control-save-and-qualified-storage-contract",
        "runtimeStatus": "not-observed-for-this-feature", "isolatedObservationRef": pin(RAW / "analysis/isolated-observations-02.json"),
        "completeChainProven": False, "scenarioIds": ids,
        "knownGaps": contract["remainingDecisions"],
        "implementationAcceptance": [op["guard"], op["success"], op["failureAndCancellation"], op["persistenceExpectation"]]
                                  + (["Preference success and active-watcher update success must remain separate outcomes."] if op["supportOperationIds"] else []),
    })

scope = copy.deepcopy(previous)
scope["previousScopeRef"] = pin(OUT / "feature-scope-v7.json")
scope["previousScenarioRef"] = pin(OUT / "feature-scope-v7-scenarios.json")
scope["purpose"] = "Finite reviewed user goals, now including ten Git preferences; not the full-client feature denominator."
scope["newDefinitionIds"] = [x["featureId"] for x in new_features]
scope["features"] += new_features
scope["supportOperations"].append({
    "operationId": watcher["operationId"], "operationRef": ref(contract_path, "/activeWatcherUpdate"), "catalogNamespace": "git",
    "featureIds": ["FSC-0057", "FSC-0058"], "classificationConfidence": "source-supported",
    "excludedFromProductScope": False, "operationEquivalenceClaimed": False, "actualUiChainObserved": False,
    "status": "supporting-mechanism", "supportKind": "apply-saved-preferences-to-active-watchers",
    "reason": "Existing watcher update is an effect of the two preference goals; it is not a separate user-facing setting.",
    "supportDoesNotExhaustConsumers": True,
})
scope["rootCandidateDispositions"] += [{"operationId": x["operationId"], "role": "user", "childOperationIds": []} for x in operations]
scope["rootCandidateDispositions"].append({"operationId": watcher["operationId"], "role": "support", "childOperationIds": []})
scope["pageContainerRelations"].append({
    "page": "Git", "legacyEntryId": "ROUTE-0152", "supportInstancePointer": "/registrations/151/staticMapInstances/17",
    "factoryContractId": entry["factoryId"], "featureIds": scope["newDefinitionIds"],
    "relation": "conditional-route-container-to-factory-to-controls", "confidence": "source-supported-conditional",
    "sourceRefs": [entry["routeInstanceRef"], entry["factoryRef"], ref(contract_path, "/entry"), ref(contract_path, "/operationContracts")],
    "conditions": entry["conditions"], "actualMountObserved": False, "sameOperationClaimed": False, "entryCompletelyResolved": False,
})
for feature in new_features:
    scope["legacyFeatureRelations"].append({"featureId": feature["featureId"], "status": "conditional-container-association",
        "entryIds": ["ROUTE-0152"], "pageRelationIndices": [3], "completeEntryEquivalenceProven": False,
        "remainingWork": "实际mount、条件值、持久化、功能消费者及模式/共享依赖仍待核对。"})
scope["legacyEntryCoverage"]["mappingUpdates"][0]["featureIds"] += scope["newDefinitionIds"]
scope["legacyEntryCoverage"]["qualification"] = "52 scoped definitions share one conditional legacy route template across four pages; no additional old entry declared resolved."
c = scope["counts"]
c.update({"scopedFeatureDefinitions": 58, "assignedUserOperations": 62, "supportOperations": 23,
    "allKnownOperationCandidatesAccountedFor": 84, "unexecutedScenarioSpecifications": 260,
    "normalizedBehaviorLeaves": 86, "featuresConditionallyAssociatedWithLegacyContainers": 52,
    "additionalDiscoveredRootCandidates": 13,
    "rootCandidateDispositionCounts": {"user": 61, "support": 21, "pending": 1, "composite": 1},
    "modeCounts": {"unknown": 58, "codex": 0, "chatgpt": 0, "shared": 0}})
scenarios = copy.deepcopy(previous_scenarios)
scenarios["previousSnapshotRef"] = pin(OUT / "feature-scope-v7-scenarios.json")
scenarios["scenarios"] += new_scenarios
scenarios["count"] = len(scenarios["scenarios"])

# Semantic inheritance, identity and accounting are checked before advancing analysis-state.
assert scope["features"][:48] == previous["features"]
assert scenarios["scenarios"][:212] == previous_scenarios["scenarios"]
assert scope["supportOperations"][:22] == previous["supportOperations"]
assert scope["operationReviewQueue"] == previous["operationReviewQueue"]
assert scope["retainedAssociationBacklog"] == previous["retainedAssociationBacklog"]
assert len(scope["features"]) == c["scopedFeatureDefinitions"] == 58
assert sum(len(x["operationMembers"]) for x in scope["features"]) == c["assignedUserOperations"] == 62
assert len(scope["supportOperations"]) == c["supportOperations"] == 23
assert len(scope["rootCandidateDispositions"]) == c["allKnownOperationCandidatesAccountedFor"] == 84
assert len({x["operationId"] for x in scope["rootCandidateDispositions"]}) == 84
assert dict(collections.Counter(x["role"] for x in scope["rootCandidateDispositions"])) == c["rootCandidateDispositionCounts"]
assert len({x["scenarioId"] for x in scenarios["scenarios"]}) == scenarios["count"] == 260
assert all(x.get("executionStatus", x.get("status")) == "not-executed" for x in scenarios["scenarios"])
assert all(x["mode"] == "unknown" and not x["completeChainProven"] for x in scope["features"])
assert c["normalizedBehaviorLeaves"] == c["assignedUserOperations"] + c["supportOperations"] + c["queuedOperations"]
assert c["completeFeatureDenominator"] is None and not scope["fullAnalysisCompleted"]
dump(scope_path, scope)
dump(scenarios_path, scenarios)
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["featureId", "name", "mode", "operationCount", "runtimeStatus", "completeChainProven"])
    writer.writeheader()
    for feature in scope["features"]:
        writer.writerow({"featureId": feature["featureId"], "name": feature["name"], "mode": feature["mode"],
            "operationCount": len(feature["operationMembers"]), "runtimeStatus": feature["runtimeStatus"],
            "completeChainProven": feature["completeChainProven"]})

lines = ["# Git 设置页面分析", "",
    "已把冻结 Git 页面中的全部实际控件收束为10项用户偏好和1项支撑操作，并接入[功能台账 v8](feature-scope-v8.json)。有限台账从48项增至58项；新增48条产品验收规格，累计260条，均未执行。完整客户端功能分母仍未建立。", "",
    "| 功能 | 设置键 | 默认值 |", "| --- | --- | --- |"]
for op in operations:
    lines.append(f"| {op['name']} | {op['parameters']['key']} | {json.dumps(op['parameters']['default'], ensure_ascii=False)} |")
lines += ["", "页面工厂、静态路由和控件已有条件关联；实际挂载、入口条件值和产品模式未观测。Git分支不在缩减host列表内，codexLocal是访问分类，不能直接当作产品模式排除证据。禁用Git差异控件还受单独selector控制。", "",
    "分支前缀在失焦或启用的保存快捷键时提交，pending时禁止编辑；合并方式还会跳过相同值。三个指令文本框停止输入3秒后自动提交，也支持保存按钮、快捷键和卸载时提交。失败快照不会自动重复提交，显式保存或新编辑才能重试；旧请求成功不会清掉较新的草稿。其他控件的pending和相等值守卫各不相同，已逐项记录。", "",
    "保存偏好与更新已有PR watcher分成两个结果。后者只筛选ACTIVE heartbeat及两行标记都匹配的记录，保留标记前提示和身份、模型、日程等字段，重建后续文本；提示相同则跳过。多个更新并发，一项失败可能留下部分成功；所选路径没有补偿已保存偏好或已更新的其他watcher。分析未读取或修改真实automation。", "",
    "共享写入默认乐观更新缓存，写入失败时恢复旧快照，随后刷新并通知。底层选择宿主settings服务或set-setting；所选main路径校验值再调用AL.write。AL.write执行store.set和afterWrite，这层没有显式等待flush；writeForAgent则会检查agentAccess并等待flush。因此UI可写的read-only代理设置不应被误禁用，而保存成功不能证明重启耐久性。真实store和磁盘调度保留为独立问题。", "",
    "6份完整Program解析结果覆盖5个不同源码文件。最新隔离回放的21个不同用例全部通过，涵盖缓存回滚、宿主/通用请求选支、自动保存、watcher筛选/更新和UI/代理写入差异；早先18个用例与之重叠，不相加。React、query/mutation调度、真实store和服务均由替身代替，所以这些结果不计作产品场景通过。", "",
    "第三方实现没有生成到独立客户端代码中。本批只保存分析所需原始片段和引用；应用职责建议分为Git控件、偏好描述/传输、自动保存状态和watcher更新适配，外部React及其他provider保留依赖边界，完整包身份/版本闭包仍沿用依赖分析的限定结论。", "",
    "[逐项合同与源码引用](settings-git-page-contracts.json)保留守卫、参数、错误、无显式取消、持久化和消费者缺口。[验收场景](feature-scope-v8-scenarios.json)保持未执行状态；模型授权余0、模式排除0，本批没有新增模型提交或原客户端运行。", "",
    "本页面的控件→处理函数→共享保存/支撑操作→验收规格映射已交付。下一步用同一批已定位页面组件完成剩余设置用户操作台账；Git真实磁盘耐久性和运行消费者进入专门验证队列，不作为继续盘点其他页面的前置阻断。", ""]
summary_path.write_text("\n".join(lines))

profile = {"contracts": pin(contract_path), "summary": pin(summary_path), "counts": counts,
           "featureSnapshot": pin(scope_path), "scenarioSnapshot": pin(scenarios_path), "fullAnalysisCompleted": False}
state = copy.deepcopy(before_state)
state["updatedAtUtc"] = datetime.now(timezone.utc).isoformat()
state["settingsGitPageContracts"] = profile
view = state["featureScopeCurrentView"]
view.update({"snapshotVersion": 8, "scope": "Finite reviewed view; 71 original roots plus 13 additional concrete roots; split leaves counted separately.",
    "ledger": pin(scope_path), "csv": pin(csv_path), "scenarios": pin(scenarios_path),
    "reconciliationKind": "git-settings-controls-and-active-watcher-support", "reconciliationArtifact": pin(contract_path),
    "previousLedger": pin(OUT / "feature-scope-v7.json"), "counts": c,
    "entryConditionOverlayQualification": "Existing overlay pins the v7 48-feature/212-scenario snapshot. New Git features and scenarios take their entry conditions from settings-git-page-contracts.json/entry.",
    "settingsSectionDispositionOverlayQualification": "The immutable disposition snapshot predates the Git operation definitions; the Git contract and v8 ledger supersede only its pending Git operation status.",
    "gitSettingsOverlay": pin(contract_path)})
state["stageDecisions"]["latestSubstep"] = profile
for key, value in [("currentFeatureDefinitions", 58), ("currentRootOperationCandidates", 84), ("currentUnexecutedScenarios", 260)]:
    state["stageDecisions"]["counts"][key] = value
state["stageDecisions"]["nextAction"] = {
    "issueId": "SD-01", "completedSubstep": "Git page: 10 user preference goals, one supporting watcher update, 48 acceptance specifications and 21 isolated cases",
    "fixedInput": "剩余41个已解析的设置页面容器；从Worktrees和Keyboard shortcuts等独立、较小页面开始",
    "question": "按现有组件批量收束用户操作合同与验收规格，累积有限功能台账；公共provider或耐久性未知单列，不逐页重复追溯整个基础设施。",
    "closure": "每批交付完整页面的实际操作、参数、条件、失败与持久化边界；全部页面处理后统一审查跨页重复、模式与共享依赖，再刷新阶段决定。",
    "deferredDedicatedVerification": "Git实际store/flush、功能消费者和服务运行行为保持待验证，不阻断其余页面的源码盘点。",
}
assert state["latestBehaviorAuthorizationState"] == before_state["latestBehaviorAuthorizationState"]
assert state["analysisMilestones"] == before_state["analysisMilestones"]
assert not state["fullAnalysisCompleted"]

report_path = OUT / "report.md"
report = report_path.read_text()
old = "下一项为Git页面控件与实际操作合同，见 analysis-state.json 的 stageDecisions。"
assert report.count(old) == 1
report = report.replace(old, "[Git页面合同](settings-git-page-summary.md)已交付10项偏好和1项支撑操作，21项隔离用例通过；当前[台账v8](feature-scope-v8.json)含58项有限功能、260条未执行产品规格。下一项批量收束其余41个设置页面，真实持久化/消费者另列验证，见 analysis-state.json 的 stageDecisions。")
gaps_path = OUT / "gaps.md"
gaps = gaps_path.read_text()
old = "下一项展开Git设置的实际控件与偏好更新链；SD-01整体仍部分完成。"
assert gaps.count(old) == 1
gaps = gaps.replace(old, "[Git设置合同](settings-git-page-summary.md)已覆盖10项用户偏好、共享保存和已有watcher更新；21项隔离回放通过，48条新增产品规格均未执行。当前有限功能58项／260规格，真实store/flush、模式与消费者仍待验证。下一项批量展开其余41个设置页面；这些运行缺口不作为源码盘点前置阻断，SD-01整体仍部分完成。")

dump(RAW / "validation.json", {
    "distinctSourceFiles": len(sources), "verifiedDistinctSourceSpans": len(validated_spans),
    "parseArtifacts": len(programs), "allSavedUnitBytesMatch": True,
    "prior48FeaturesAnd212ScenariosUnchanged": True, "priorSupportQueueAndAssociationBacklogPreserved": True,
    "currentCounts": c, "newProductSpecifications": len(new_scenarios), "latestIsolatedCases": 21,
    "productScenariosExecuted": 0, "modelAuthorizationUnchanged": True,
    "historicalMilestoneArtifactsUnchanged": True,
    "newArtifacts": {name: pin(OUT / name) for name in names}, "producer": pin(RAW / Path(__file__).name),
})
# The current-state pointer advances only after all artifacts and semantic checks are ready.
dump(OUT / "analysis-state.json", state)
report_path.write_text(report)
gaps_path.write_text(gaps)
for p in [*(OUT / n for n in names), *RAW.rglob("*")]:
    if p.is_file():
        p.chmod(0o444)
print(json.dumps({"published": str(contract_path), "counts": counts, "scopeCounts": c}, ensure_ascii=False))
