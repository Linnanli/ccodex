"""Close one finite settings-to-feature mapping; preserve prior scope and behavior claims."""
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
WORK = ROOT / ".analysis-local/settings-feature-entry-work/usage-routes-01"
RAW = OUT / "raw/settings-feature-entry-conditions"
TARGET = OUT / "settings-feature-entry-conditions.json"


def read(name):
    return json.loads((OUT / name).read_text())


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": os.path.relpath(path, OUT), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def ref(name, pointer):
    return {**pin(OUT / name), "jsonPointer": pointer}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


assert not TARGET.exists() and not RAW.exists(), "Keep published batches immutable"
scope = read("feature-scope-v7.json")
scenarios = read("feature-scope-v7-scenarios.json")
mode = read("settings-mode-boundary-contracts.json")
callers = read("settings-entry-callers-contracts.json")
cua = read("cua-settings-consumer-contracts.json")
routes = json.loads((WORK / "source-contracts.json").read_text())
assert routes["fullProgramParsed"] and not routes["targetCodeExecuted"]
usage_slugs = {x["section"] for x in routes["usageSections"]}
assert usage_slugs == {"usage", "analytics", "consumer-view", "usage-code-review"}
assert {(x["owner"], x["name"]) for x in routes["qualifiedProgramBindingJoins"]} == {
    ("MNs", "FNs"), ("PNs", "FNs"), ("INs", "FNs"), ("M6", "MNs"), ("M6", "PNs")}
assert len(scope["features"]) == 48 and len(scenarios["scenarios"]) == 212
assert scenarios["executed"] == 0
assert all(x.get("executionStatus", x.get("status")) == "not-executed"
           for x in scenarios["scenarios"])
assert len(mode["settingsSectionReviews"]) == 53

RAW.mkdir(parents=True)
shutil.copytree(WORK, RAW / "usage-routes")
shutil.copyfile(OUT / "analysis-state.json", RAW / "analysis-state-before.json")
shutil.copyfile(__file__, RAW / Path(__file__).name)
shutil.copyfile(ROOT / "scripts/analysis/settings_usage_route_ast.mjs", RAW / "settings_usage_route_ast.mjs")

inputs = {name: pin(OUT / name) for name in [
    "feature-scope-v7.json", "feature-scope-v7-scenarios.json",
    "settings-mode-boundary-contracts.json", "settings-entry-callers-contracts.json",
    "settings-registry-contracts.json", "cua-settings-consumer-contracts.json",
]}


def unit_ref(name, units, unit_id):
    index = next(i for i, u in enumerate(units) if u["unitId"] == unit_id)
    return ref(name, f"/selectedUnits/{index}")


common = {
    "conditionId": "SETTINGS-OUTER",
    "selectedHost": "SettingsPage reads selectedHostId; second visibility argument is descriptor.kind === local, not a product-mode flag.",
    "visibilityComposition": {
        "earlyFilter": "If !(a || Ca.includes(slug)), visible/pending/error are all false.",
        "familyAllowed": "r = Ta[slug] == null || He[Ta[slug]]",
        "visible": "o = r && Tt(section).visible",
        "pending": "!o && Tt(section).pending && (r || ee)",
        "error": "Tt(section).error; this is not forced false when family access is false.",
        "ee": "(family === chatGpt || family === chatGptOrCodex) && K && true",
    },
    "routeSelection": {
        "X": "Matching requested section after the cloud-settings alias handling; these three sections do not use that alias.",
        "inaccessible": "At = X != null && !X.visible && !X.pending && !X.error",
        "redirect": "Ft = At || (Y != null && X?.visible === true)",
        "renderContent": "Lt = !X?.pending",
        "caller": "ri returns a redirect when T=Ft; otherwise an access-error panel takes priority over the outlet, and the outlet is built only when E=Lt.",
    },
    "qualifications": [
        "Navigation visibility and route mounting are separate. An error state can prevent fallback even when a section is invisible.",
        "The host descriptor can represent a cloud executor; kind local does not establish physical locality.",
        "Actual selector, host, gate and capability values remain unobserved for these features.",
        "Control-level conditions already present in feature-scope-v7.json remain necessary.",
    ],
    "sourceRefs": [
        unit_ref("settings-entry-callers-contracts.json", callers["selectedUnits"], "SEC-U004"),
        unit_ref("settings-mode-boundary-contracts.json", mode["selectedUnits"], "SMB-U016"),
        ref("settings-mode-boundary-contracts.json", "/facts/19"),
        ref("settings-mode-boundary-contracts.json", "/facts/21"),
    ],
}

specs = [
    ("GENERAL-ENTRY", "General", "general-settings", 46,
     {"hostList": "a must be true for this catalog entry; general-settings is absent from Ca.",
      "accessFamily": None,
      "predicate": "visible=true,pending=false, via fall-through to personalization (case 47).",
      "normalNavigationVisible": "a",
      "mode": "unknown; absence of a family restriction does not prove shared product mode."}),
    ("AGENT-ENTRY", "Agent", "agent", 45,
     {"hostList": "Allowed by Ca even when a=false.",
      "accessFamily": "chatGptOrCodex = x || m; selectors represent access, not exclusive product identity.",
      "predicate": "visible = fe || (x && N.isCapable && j.status === allowed); pending = N.isLoading || j.status === loading; error = N.isError",
      "capability": "N is work.cloud-orchestration.preferences; j is c(nt).",
      "normalNavigationVisible": "(x || m) && (fe || (x && N.isCapable && j.status === allowed))",
      "mode": "unknown; keep the outer error/pending behavior rather than equating this visibility formula with every possible mount."}),
    ("CUA-ENTRY", "Computer use", "computer-use", 15,
     {"hostList": "a must be true; computer-use is absent from Ca.",
      "accessFamily": "codexOrWorkLocal = fe",
      "predicate": "visible = Ct; pending = vt.isLoading || y.isLoading",
      "Ct": "a && (vt.available || y.available || bt)",
      "bt": "a && !y.isLoading && !y.allowed",
      "hostQueries": "vt=Ue({hostId:o}); y=jt({hostId:o})",
      "normalNavigationVisible": "a && fe && (vt.available || y.available || bt)",
      "mode": "unknown; availability and access family do not prove ChatGPT-only or Codex-only ownership."}),
]
pages = []
for condition_id, page, slug, review_index, details in specs:
    review = mode["settingsSectionReviews"][review_index]
    assert review["slug"] == slug and slug not in usage_slugs
    pages.append({
        "conditionId": condition_id, "page": page, "slug": slug,
        "outerConditionId": "SETTINGS-OUTER", "conditions": details,
        "usageRedirectGuard": False,
        "guardQualification": "MNs checks only the four FNs usage section values. These three factory lookups do not take the usage-tab redirect. work-settings remains a separate redirect to agent?mode=work.",
        "sourceRefs": [ref("settings-mode-boundary-contracts.json", f"/settingsSectionReviews/{review_index}")],
        "actualMountObserved": False,
    })

subroutes = [
    {"conditionId": "CUA-MAIN", "parentConditionId": "CUA-ENTRY",
     "conditions": ["Vr has not returned a browser route, browser redirect or Messages route.",
                    "Always-allowed applications and sound controls require i.available.",
                    "Locked-computer control additionally requires platform===macOS and n=ae(hn,selectedHostId)."],
     "sourceRefs": [unit_ref("cua-settings-consumer-contracts.json", cua["selectedUnits"], "CUA-CONSUMER-UNIT-011")]},
    {"conditionId": "CUA-MESSAGES", "parentConditionId": "CUA-ENTRY",
     "conditions": ["The outer SettingsPage redirect, loading and access-error behavior still applies.",
                    "Vr selects the Messages match after the browser branches and before the main-view availability guards.",
                    "ei shows loading if s && l==null; redirects if !s && l?.plugin.installed!==true; otherwise renders Ar.",
                    "The loading-with-candidate case reaches Ar; do not replace the source with an unconditional installed-plugin prerequisite."],
     "sourceRefs": [unit_ref("cua-settings-consumer-contracts.json", cua["selectedUnits"], x)
                    for x in ["CUA-CONSUMER-UNIT-011", "CUA-CONSUMER-UNIT-014"]]},
]

by_feature = {}
for relation in scope["pageContainerRelations"]:
    page_id = {"General": "GENERAL-ENTRY", "Agent": "AGENT-ENTRY", "Computer use": "CUA-ENTRY"}.get(relation["page"])
    if page_id is None:
        assert "computer" in relation["page"].lower()
        page_id = "CUA-ENTRY"
    for feature_id in relation["featureIds"]:
        assert feature_id not in by_feature
        by_feature[feature_id] = page_id
assert len(by_feature) == 42

features = []
for index, feature in enumerate(scope["features"]):
    fid = feature["featureId"]
    condition_id = by_feature.get(fid)
    ids = ["SETTINGS-OUTER", condition_id] if condition_id else []
    if fid in {f"FSC-{i:04}" for i in range(38, 41)}:
        ids.append("CUA-MAIN")
    elif fid in {f"FSC-{i:04}" for i in range(41, 45)}:
        ids.append("CUA-MESSAGES")
    features.append({
        "featureId": fid, "name": feature["name"],
        "featureRef": ref("feature-scope-v7.json", f"/features/{index}"),
        "conditionIds": ids,
        "mappingStatus": "conditional-settings-entry-mapped" if ids else "outside-settings-page-map",
        "qualification": ("This maps the existing General/dialog entry only; other project entry paths are not ruled out."
                          if fid == "FSC-0045" else
                          "Keep existing operation/control preconditions; this is a source-level entry path, not proof of actual mounting."
                          if ids else
                          "Conversation/composer/thread action; no settings page relation exists in the reviewed ledger. Retain its existing entry contract and unresolved legacy identity."),
        "productMode": feature["mode"], "actualValuesObserved": False,
    })

feature_index = {x["featureId"]: i for i, x in enumerate(features)}
scenario_bindings = [{
    "scenarioId": scenario["scenarioId"], "featureId": scenario["featureId"],
    "existingScenarioRef": ref("feature-scope-v7-scenarios.json", f"/scenarios/{i}"),
    "entryMappingPointer": f"/featureEntryMappings/{feature_index[scenario['featureId']]}",
    "application": "Use as conditional entry-path setup; preserve all existing preconditions and alternate entry paths.",
    "executionStatus": scenario.get("executionStatus", scenario.get("status")),
    "originalExecutionStatusField": "executionStatus" if "executionStatus" in scenario else "status",
} for i, scenario in enumerate(scenarios["scenarios"])]

page_by_slug = {x["slug"]: x["conditionId"] for x in pages}
section_rows = [{
    "slug": row["slug"], "family": row["family"],
    "reviewRef": ref("settings-mode-boundary-contracts.json", f"/settingsSectionReviews/{i}"),
    "mappedPageConditionId": page_by_slug.get(row["slug"]),
    "disposition": "mapped-to-current-feature-page" if row["slug"] in page_by_slug else "outside-current-three-page-feature-mapping",
    "qualification": "Unmapped here does not mean excluded, redundant or unimplemented.",
} for i, row in enumerate(mode["settingsSectionReviews"])]

counts = {"settingsBranchesAccountedFor": 53, "mappedPageBranches": 3,
          "otherSectionBranchesRetained": 50, "featureDefinitionsAccountedFor": 48,
          "featuresWithConditionalSettingsEntry": 42, "featuresOutsideSettingsMap": 6,
          "existingScenarioBindings": 212, "newFeatures": 0, "newExecutedScenarios": 0,
          "newProductModeClassifications": 0, "newChatGptExclusions": 0,
          "modelSubmissionsAdded": 0, "originalClientRunsAdded": 0}
result = {
    "schemaVersion": 1, "baselineId": BASE,
    "purpose": "Close SD-01's finite 53-branch/48-definition settings-entry association substep.",
    "inputPins": inputs, "rawSourceContracts": pin(RAW / "usage-routes/source-contracts.json"),
    "commonEntryCondition": common, "pageEntryConditions": pages, "subrouteConditions": subroutes,
    "settingsBranchDispositions": section_rows, "featureEntryMappings": features,
    "scenarioEntryBindings": scenario_bindings, "counts": counts,
    "remainingWork": ["Classify the other 50 setting branches by actual page, redirect, compatibility alias or same-page tab, then establish concrete feature candidates.",
                      "SD-01 overall remains partial: the complete feature denominator and exclusive product-mode dependency closure are not established.",
                      "Real mounting, provider values and behavior/persistence still need separate verification."],
    "fullAnalysisCompleted": False, "clientImplementationStarted": False,
}
dump(TARGET, result)
summary = """# 设置入口条件与现有功能的关联

本批关闭 SD-01 的一个有限子步骤：53 个设置分支均有处置记录；现有 48 个功能逐项有设置入口关联或不属于本批的理由。42 项关联到三个设置页面，6 项属于会话/线程入口。212 条既有场景均接上入口映射，没有增加执行通过数。

| 页面/入口 | 现有功能数 | 已明确的入口条件 |
| --- | ---: | --- |
| General | 29 | 必须进入完整主机设置目录；general-settings 的 switch 分支继承 personalization 的 visible=true。仍保留每个控件的平台和能力条件。 |
| Agent | 6 | 目录允许精简主机；分类与页面 predicate 分别组合。导航不可见不等于所有错误状态下都不能挂载。 |
| Computer use 主视图 | 3 | 外层设置页条件后，主视图要求能力 available；锁屏选项另有 macOS 和 capability 条件。 |
| Computer use / Messages | 4 | 保留外层加载/重定向规则；内部先于主视图分流，再按插件加载/候选/安装状态决定。 |
| 会话与线程入口 | 6 | 不套用设置页面条件；保留既有入口合同和待解决的旧入口身份。 |

新增完整 Program 解析确认 MNs/PNs 使用同一个 FNs 绑定，其四项只涉及 usage、analytics、consumer-view、usage-code-review。因此 General、Agent、Computer use 不会进入该 usage-tab 重定向；work-settings → agent?mode=work 是另一分支。旧台账中的这处条件疑点由本批覆盖说明，历史文件保留。

访问资格、主机 descriptor、平台、capability 与产品模式分别记录。48 项仍为 mode=unknown，确认可排除的 ChatGPT-only 项仍为零。第二个可见性参数来自 descriptor.kind===local，不能当作产品模式，也不能据此认定物理本机。

本批只把静态入口条件关联到原有定义与场景，不证明实际挂载、接收端、持久化或完整构建。其余 50 个设置分支保留待逐项处置；SD-01 整体和完整分析目标均未完成。

对应结构化数据：[入口与场景映射](settings-feature-entry-conditions.json)。现有功能和场景仍以 v7 为定义来源，本批作为关联层，不复制或改写其语义。
"""
(OUT / "settings-feature-entry-conditions.md").write_text(summary)

# Validate the new associations, selected bytes and references before advancing current pointers.
assert collections.Counter(x["mappingStatus"] for x in features) == {
    "conditional-settings-entry-mapped": 42, "outside-settings-page-map": 6}
assert {x["featureId"] for x in features} == {x["featureId"] for x in scope["features"]}
assert {x["scenarioId"] for x in scenario_bindings} == {x["scenarioId"] for x in scenarios["scenarios"]}
for unit in routes["units"]:
    source = ROOT / ".analysis-local/baselines" / BASE / "extracted" / unit["sourcePath"].removeprefix("app.asar/")
    data = source.read_bytes()[unit["byteRange"]["start"]:unit["byteRange"]["endExclusive"]]
    assert hashlib.sha256(data).hexdigest() == unit["spanHash"]
    saved = RAW / "usage-routes" / unit["sourceFilename"]
    assert saved.read_bytes() == data
for item in inputs.values():
    assert pin(OUT / item["path"]) == item
state = read("analysis-state.json")
previous = copy.deepcopy(state)
next_action = {
    "issueId": "SD-01", "completedSubstep": "53 settings branches / 48 current definitions / 212 scenario entry associations",
    "fixedInput": "其余50个设置可见性分支及现有注册表/页面工厂/路由合同",
    "question": "按真实页面、重定向、兼容别名或同页tab逐项分组，建立具体功能候选与保留/支撑/重复/待定处置。",
    "closure": "50项逐项有来源和处置；不按分类标签排除，不重复调查本批已关闭的三个页面入口。",
}
profile = {"contracts": pin(TARGET), "summary": pin(OUT / "settings-feature-entry-conditions.md"),
           "counts": counts, "sourceScope": "three-page entry association only",
           "fullAnalysisCompleted": False}
state["settingsFeatureEntryConditions"] = profile
state["featureScopeCurrentView"]["entryConditionOverlay"] = pin(TARGET)
state["stageDecisions"]["nextAction"] = next_action
state["stageDecisions"]["latestSubstep"] = profile
assert previous["featureScopeCurrentView"]["counts"] == state["featureScopeCurrentView"]["counts"]
assert previous["latestBehaviorAuthorizationState"] == state["latestBehaviorAuthorizationState"]
dump(OUT / "analysis-state.json", state)

report = OUT / "report.md"
text = report.read_text()
old = "当前下一项是把设置页面使用条件接到48项定义和场景前提，见 analysis-state.json 的 stageDecisions。"
assert text.count(old) == 1
text = text.replace(old, "[设置入口关联](settings-feature-entry-conditions.md)已将42项功能接到三个页面条件，另6项保留非设置入口理由；212条场景均接上条件引用。下一项为其余50个设置分支的实际页面/别名/重定向处置，见 analysis-state.json 的 stageDecisions。")
report.write_text(text)
gaps = OUT / "gaps.md"
text = gaps.read_text()
old = "当前动作是SD-01：将53个设置可见性分支接到当前48个功能定义的页面条件和场景前提，分开访问资格、能力、平台与产品模式；不要求所有 unknown 清零。"
assert text.count(old) == 1
text = text.replace(old, "SD-01的[三个设置页面入口关联](settings-feature-entry-conditions.md)子步骤已关闭：42项功能有条件关联，6项明确不属设置入口，212条场景均有引用。48项模式仍未知，实测数不变。下一项处理其余50个设置分支的实际页面、别名和重定向处置；SD-01整体仍部分完成。")
gaps.write_text(text)
dump(RAW / "validation.json", {"counts": counts, "sourceUnitsRehashed": len(routes["units"]),
    "selectedBindings": len(routes["qualifiedProgramBindingJoins"]), "priorFeatureCountsUnchanged": True,
    "priorModelAuthorizationUnchanged": True, "sourceContracts": pin(RAW / "usage-routes/source-contracts.json"),
    "publisher": pin(RAW / Path(__file__).name), "sourceRecipe": pin(RAW / "settings_usage_route_ast.mjs")})
for path in [TARGET, OUT / "settings-feature-entry-conditions.md", *RAW.rglob("*")]:
    if path.is_file():
        path.chmod(0o444)
print(json.dumps({"published": str(TARGET), "counts": counts}, ensure_ascii=False))
