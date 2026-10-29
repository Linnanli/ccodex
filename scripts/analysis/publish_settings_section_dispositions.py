"""Reconcile all settings branch types without treating pages as user features."""
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/settings-section-disposition-work"
RAW = OUT / "raw/settings-section-dispositions"
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"


def load(path):
    return json.loads(path.read_text())


def pin(path):
    data = path.read_bytes()
    return {"path": os.path.relpath(path, OUT), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def ref(path, pointer):
    return {**pin(path), "jsonPointer": pointer}


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


target = OUT / "settings-section-dispositions.json"
assert not RAW.exists() and not target.exists()
registry = load(OUT / "settings-registry-contracts.json")
mode = load(OUT / "settings-mode-boundary-contracts.json")
queue = load(WORK / "queue.json")
forwarded = load(WORK / "forwarded-component-queue.json")
first_runs = load(WORK / "parse-execution.json")
follow_runs = load(WORK / "forwarded-parse-execution.json")
observation = load(WORK / "usage-helper-observations.json")
assert len(first_runs) == 46 and len(follow_runs) == 6
assert all(x["exitCode"] == 0 for x in first_runs + follow_runs)
assert observation["counts"] == {"isolatedHelperCases": 60, "passed": 60, "productScenariosExecuted": 0}
assert len(queue["factories"]) == 53 and len(queue["modules"]) == 49

RAW.mkdir(parents=True)
shutil.copytree(WORK, RAW / "analysis")
shutil.copyfile(OUT / "analysis-state.json", RAW / "analysis-state-before.json")
for name in [Path(__file__).name, "settings_page_surface_ast.mjs", "probe_settings_usage_routes.cjs"]:
    shutil.copyfile(ROOT / "scripts/analysis" / name, RAW / name)

programs = {}
for path in sorted((RAW / "analysis").glob("*-source/*/source-contracts.json")) + sorted((RAW / "analysis/source").glob("*/source-contracts.json")):
    data = load(path)
    key = (data["sourcePath"].removeprefix("app.asar/"), data["expectedExport"])
    assert key not in programs and data["fullProgramParsed"]
    original = (FROZEN / key[0]).read_bytes()
    assert hashlib.sha256(original).hexdigest() == data["sourceHash"]
    unit = data["component"]
    fragment = original[unit["byteRange"]["start"]:unit["byteRange"]["endExclusive"]]
    assert hashlib.sha256(fragment).hexdigest() == unit["spanHash"]
    assert (path.parent / unit["sourceFilename"]).read_bytes() == fragment
    programs[key] = {"path": path, "data": data}
assert len(programs) == 52

factories = {x["key"]: (i, x) for i, x in enumerate(registry["pageFactoryContracts"])}
sections = {x["slug"]: (i, x) for i, x in enumerate(registry["sectionDataflowContracts"])}
factory_targets = {x["slug"]: x for x in queue["factories"]}
old_scope = load(OUT / "feature-scope-v7.json")
existing_pages = {"general-settings": "General", "agent": "Agent", "computer-use": "Computer use"}
existing_features = {slug: next(r["featureIds"] for r in old_scope["pageContainerRelations"] if r["page"] == page)
                     for slug, page in existing_pages.items()}
aliases = {"analytics": "analytics", "consumer-view": "consumer-view", "usage-code-review": "code-review"}
special = {
    "work-settings": ("renderer-redirect", "retained-navigation-support", "M6 redirects to /settings/agent with mode=work, preserving hash and explicit navigation state; its WorkSettingsPanel factory is bypassed on this path."),
    "time-management": ("component-redirect", "retained-navigation-support", "SettingsPage checks safety visibility for this path. The component redirects to /settings/safety, preserving quiet-hours/study-hours view or setting view=time-management, and forwards hash and state."),
    "profile": ("standalone-app-route-link", "retained-link-with-target-reachability-pending", "The catalog appRoute is /profile and the saved settings route map explicitly excludes profile. Its M6 factory does not prove that the standalone route mounts this component."),
    "family": ("noncatalog-shared-factory-key", "pending-other-callers", "No section or saved settings route; its predicate is always invisible and its factory is the same cQa binding as General. This establishes shared factory identity, not a distinct user feature or a whole-module exclusion."),
    "environments": ("noncatalog-placeholder-factory", "pending-other-callers", "No section or saved settings route. Its component only presents an external-section heading/subtitle; the text about opening a browser is not evidence of a browser-opening action."),
}
redirect_details = {
    "age": "The forwarded component redirects to /settings/account when !t; otherwise it renders age details. The back action targets /settings/account#age. Selector t remains an access boundary.",
    "cloud-computer": "onepassword_account_id or onepassword_result query presence redirects using {...location, pathname:/settings/passwords}; otherwise it renders the cloud-browser child. No explicit state prop is added to that redirect.",
    "local-environments": "selectedHostId must equal the literal local, gate 375130565 must be true, pathname must be /settings/local-environments, and search must be empty or view=personal-vault. It then redirects to codex-cloud, translating personal-vault into a tab and forwarding hash/state; otherwise renders the host-keyed page.",
    "cloud-environments": "The root shows preferences only with gate 375130565 and tab=preferences; otherwise a list. Nested paths select new/detail/edit, with invalid paths redirecting to the root. These are several operation surfaces within one page container.",
    "cloud-settings": "The outer visibility hook can substitute cloud-environments under gate 375130565. SettingsPage then redirects to the literal /settings/cloud-environments?tab=preferences with explicit state; that redirect string does not append the current hash.",
    "teams": "Without accountId it shows unavailable. A join subpath with teamId becomes an encoded team detail path with join=true and forwards query/hash/state. Other paths select list or detail.",
    "browser-use": "A selected browser whose capability is not enabled can show loading or redirect to the browser-use root; otherwise browser-specific content is selected. Without a selected browser it renders the policy page.",
    "plugins-settings": "The forwarded component contains nested plugin routes and a fallback navigation target rn(); the target helper's complete result is not established here.",
    "usage": "The page reads tab and normalizes pathname/search through St, imported as EA from the same initial module. Visible panels are mounted with hidden/select/polling state; this is not one user operation.",
}

rows = []
for review_index, review in enumerate(mode["settingsSectionReviews"]):
    slug = review["slug"]
    factory_index, factory = factories[slug]
    target_info = factory_targets[slug]
    known = slug in existing_pages
    if known:
        kind, disposition = "existing-feature-page-container", "retained-existing-feature-container"
        explanation = "Already associated with reviewed feature definitions by the preceding entry-condition overlay."
    elif slug in aliases:
        kind, disposition = "usage-tab-alias", "retained-tab-entry"
        explanation = f"M6 redirects to /settings/usage with tab={aliases[slug]}; tab identity is retained and is not assumed to be a duplicate user operation."
    elif slug in special:
        kind, disposition, explanation = special[slug]
    else:
        kind, disposition = "catalog-page-container", "retained-operation-definition-pending"
        explanation = "A concrete named component export is resolved; operations, child boundaries and mode ownership still require their own contracts."
    section_info = sections.get(slug)
    section = section_info[1] if section_info else None
    row = {
        "entryId": "SETTINGS-SURFACE-" + factory["contractId"].rsplit("-", 1)[1],
        "slug": slug, "newBatch": not known, "entryKind": kind, "disposition": disposition,
        "explanation": explanation, "catalogPresent": section is not None,
        "appRoute": section["appRoute"] if section else None,
        "savedSettingsRouteInstance": section["routeInstanceIndex"] if section else None,
        "factoryId": factory["contractId"], "factoryModule": target_info["modulePath"],
        "factoryExport": target_info["exportName"], "accessFamily": review["family"],
        "productMode": "unknown", "confirmedExclusion": False,
        "outerEntryConditionRef": ref(OUT / "settings-feature-entry-conditions.json", "/commonEntryCondition"),
        "factoryRef": ref(OUT / "settings-registry-contracts.json", f"/pageFactoryContracts/{factory_index}"),
        "visibilityRef": ref(OUT / "settings-mode-boundary-contracts.json", f"/settingsSectionReviews/{review_index}"),
        "existingFeatureIds": existing_features.get(slug, []),
        "featureIdentityEstablishedByThisRow": False, "actualMountObserved": False,
    }
    if section_info:
        row["sectionRef"] = ref(OUT / "settings-registry-contracts.json", f"/sectionDataflowContracts/{section_info[0]}")
    if slug in redirect_details:
        row["conditionalRouting"] = redirect_details[slug]
    if slug == "family":
        row["sharedFactoryCanonicalEntry"] = "general-settings"
        row["sharedFactorySourceRef"] = ref(OUT / "settings-registry-contracts.json", f"/pageFactoryContracts/{factories['general-settings'][0]}")
        row["existingGeneralOperationContracts"] = ref(OUT / "settings-general-page-contracts.json", "/operationContracts")
    if not known and slug != "family":
        initial = programs[(target_info["modulePath"], target_info["exportName"])]
        row["namedExportContracts"] = ref(initial["path"], "/exportBinding")
        component = initial
        if initial["data"]["component"]["nodeType"] == "ImportSpecifier":
            hop = next(x for x in forwarded if x["parentExport"] == target_info["exportName"])
            component = programs[(hop["modulePath"], hop["importedExport"])]
            row["forwardedComponentImport"] = hop
            row["forwardedComponentContracts"] = ref(component["path"], "/exportBinding")
        assert component["data"]["component"]["nodeType"] == "FunctionDeclaration"
        row["componentSource"] = ref(component["path"], "/component")
        row["candidateCallBoundaries"] = ref(component["path"], "/rootCalls")
        row["candidateNavigationBranches"] = ref(component["path"], "/navigationProps")
    rows.append(row)

counts = {
    "allSettingsBranches": len(rows), "newlyDispositionedBranches": sum(x["newBatch"] for x in rows),
    "newBatchEntryKinds": dict(collections.Counter(x["entryKind"] for x in rows if x["newBatch"])),
    "allFactoryKeysLinked": 53, "initialUniqueFactoryModuleExports": 49,
    "newModuleProgramsParsed": 52, "forwardedExportHops": 6,
    "isolatedHelperCasesPassed": 60, "newScopedFeatureDefinitions": 0,
    "newProductScenariosExecuted": 0, "confirmedChatGptExclusionsAdded": 0,
    "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0,
}
assert counts["newlyDispositionedBranches"] == 50
assert counts["newBatchEntryKinds"]["catalog-page-container"] == 42
assert {x["slug"] for x in rows} == set(factories)
result = {
    "schemaVersion": 1, "baselineId": BASE,
    "scope": "Entry/page/redirect disposition of all 53 settings visibility branches, especially the remaining 50; not a whole-client feature denominator.",
    "method": "Reuse the REA-backed frozen registry and its qualified bindings; supplement with 52 complete module Program parses, named-export forwarding and isolated original pure-helper execution.",
    "inputPins": {name: pin(OUT / name) for name in ["settings-registry-contracts.json", "settings-mode-boundary-contracts.json", "settings-feature-entry-conditions.json", "feature-scope-v7.json"]},
    "entries": rows, "counts": counts,
    "pureHelperObservation": pin(RAW / "analysis/usage-helper-observations.json"),
    "registryRouteConstructionRef": ref(OUT / "settings-registry-contracts.json", "/registryLookupContracts/routeMap"),
    "rendererBranchSourceRef": ref(OUT / "raw/settings-feature-entry-conditions/usage-routes/source-contracts.json", "/units"),
    "limitations": [
        "Named exports, wrappers, navigation routes, page containers and user features are different objects. None is used as the complete feature denominator.",
        "The work-settings loader is not reached by its M6 branch; other callers and shared dependencies of that loader remain unclassified.",
        "The profile appRoute descriptor does not establish its standalone route component, and the two noncatalog factory keys need other-caller review.",
        "Route helper executions are isolated source-contract evidence. They do not execute React, the installed app, providers, model services or any of the 212 product scenarios.",
        "All product modes remain unknown, and no ChatGPT-only module is excluded by names or access-family labels.",
    ],
    "fullAnalysisCompleted": False, "clientImplementationStarted": False,
}
dump(target, result)

lines = ["# 设置分支的页面与重定向处置", "",
         "剩余50个分支已逐项关联到工厂、具体模块导出和入口类型。结合前批三个页面，53个设置分支均有处置记录；这没有建立完整功能分母，也没有新增可排除的ChatGPT专属功能。", "",
         "| 本批入口类型 | 数量 | 处理方式 |", "| --- | ---: | --- |",
         "| 设置页面容器 | 42 | 保留具体组件、调用边界及控件分析任务 |",
         "| usage 的 tab 别名 | 3 | 转到同页不同 tab，保留各自功能边界 |",
         "| renderer 重定向 | 1 | work-settings → agent?mode=work |",
         "| 组件重定向 | 1 | time-management → safety，转换 view |",
         "| 独立 appRoute 链接 | 1 | profile → /profile；实际独立路由组件仍待连接 |",
         "| 目录外工厂键 | 2 | family 共用 General；environments 是展示占位，其他调用待核对 |", "",
         "46个初始目标模块及6个转发模块均完成原始Program解析，命名导出均落到具体函数。已记录age、cloud-computer、local-environments、cloud-environments、cloud-settings、teams、browser-use、plugins-settings和usage的条件导航；页面存在不代表条件始终满足。", "",
         "冻结源码的MNs/PNs与FNs字面量在隔离VM中执行60个用例，全部通过：53个slug归类及7个查询转换。验证包含tab替换、重复参数保留、URL编码和未知section回退。该结果只证明这些纯函数，不计入212条客户端场景的通过数。", "",
         "| slug | 入口类型 | 模块导出 |", "| --- | --- | --- |"]
for row in rows:
    if row["newBatch"]:
        lines.append(f"| {row['slug']} | {row['entryKind']} | {row['factoryExport']} |")
lines += ["", "结构化逐项记录及源码引用见[分支处置数据](settings-section-dispositions.json)。现有48个功能、212条未执行产品场景和模式分类均保持原状。下一步从保留页面的控件和处理函数建立实际操作合同；Git设置优先接到已有偏好与持久化边界。", ""]
summary = OUT / "settings-section-dispositions.md"
summary.write_text("\n".join(lines))

state = load(OUT / "analysis-state.json")
before = copy.deepcopy(state)
profile = {"contracts": pin(target), "summary": pin(summary), "counts": counts,
           "fullAnalysisCompleted": False}
state["settingsSectionDispositions"] = profile
state["featureScopeCurrentView"]["settingsSectionDispositionOverlay"] = pin(target)
state["stageDecisions"]["latestSubstep"] = profile
state["stageDecisions"]["nextAction"] = {
    "issueId": "SD-01", "completedSubstep": "50 remaining settings branch dispositions; 52 module Programs; 60 isolated route-helper cases",
    "fixedInput": "42个保留设置页面容器及已解析组件；优先GitSettings的控件和偏好更新边界",
    "question": "将页面容器展开为具体用户操作、参数、持久化与失败/取消合同，接入功能台账；保留条件和共享依赖。",
    "closure": "先完成Git页面全部实际控件到处理函数、状态/存储和验收场景的对应；页面数不作功能数。",
}
assert state["featureScopeCurrentView"]["counts"] == before["featureScopeCurrentView"]["counts"]
assert state["latestBehaviorAuthorizationState"] == before["latestBehaviorAuthorizationState"]
dump(OUT / "analysis-state.json", state)
report = OUT / "report.md"
text = report.read_text()
old = "下一项为其余50个设置分支的实际页面/别名/重定向处置，见 analysis-state.json 的 stageDecisions。"
assert text.count(old) == 1
report.write_text(text.replace(old, "[其余50个分支处置](settings-section-dispositions.md)已完成：42个页面容器、3个tab别名、2个重定向、1个appRoute链接及2个目录外工厂键；新增52个模块Program解析和60个隔离纯函数用例。下一项为Git页面控件与实际操作合同，见 analysis-state.json 的 stageDecisions。"))
gaps = OUT / "gaps.md"
text = gaps.read_text()
old = "下一项处理其余50个设置分支的实际页面、别名和重定向处置；SD-01整体仍部分完成。"
assert text.count(old) == 1
gaps.write_text(text.replace(old, "[其余50个设置分支](settings-section-dispositions.md)也已完成入口类型处置，包含42个需展开操作合同的页面容器。60个隔离路由函数用例通过，产品场景实测数不变。下一项展开Git设置的实际控件与偏好更新链；SD-01整体仍部分完成。"))
dump(RAW / "validation.json", {"counts": counts, "originalModuleHashesAndSelectedComponentBytes": "verified-52",
    "allParserProcessesExitedZero": True, "currentFeatureAndScenarioCountsUnchanged": True,
    "modelAuthorizationUnchanged": True, "producer": pin(RAW / Path(__file__).name)})
for path in [target, summary, *RAW.rglob("*")]:
    if path.is_file():
        path.chmod(0o444)
print(json.dumps({"published": str(target), "counts": counts}, ensure_ascii=False))
