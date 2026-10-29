#!/usr/bin/env python3
"""Read back plan identity, all pins, contract joins and both schedules."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
WORK = ROOT / ".analysis-local/restoration-plan-v10-work"
ap = argparse.ArgumentParser()
ap.add_argument("--published", action="store_true")
args = ap.parse_args()
target = OUT if args.published else WORK / "deliverables"


def read(name):
    return json.loads((OUT / name).read_text())


def pointer(data, ptr):
    if ptr == "":
        return data
    assert ptr.startswith("/"), ptr
    for k in ptr[1:].split("/"):
        k = k.replace("~1", "/").replace("~0", "~")
        data = data[int(k)] if isinstance(data, list) else data[k]
    return data


checked = {}
pointers = set()


def check_pin(ref):
    name = ref["path"]
    path = ROOT / name
    if not path.exists():
        path = OUT / name
    if not path.exists() and Path(name).name in ["implementation-plan-v10.md", "implementation-milestones-v10.json"]:
        path = target / Path(name).name
    b = path.read_bytes()
    assert len(b) == ref["bytes"], (name, "bytes")
    assert hashlib.sha256(b).hexdigest() == ref["sha256"], (name, "hash")
    checked[str(path)] = ref["sha256"]
    if "jsonPointer" in ref:
        pointer(json.loads(b), ref["jsonPointer"])
        pointers.add((str(path), ref["jsonPointer"]))


def walk(value):
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"} <= value.keys():
            check_pin(value)
        for v in value.values():
            walk(v)
    elif isinstance(value, list):
        for v in value:
            walk(v)


plan = json.loads((target / "implementation-milestones-v10.json").read_text())
provenance = json.loads((target / "restoration-plan-v10-provenance.json").read_text())
walk(plan)
walk(provenance)
assert plan["baselineId"] == provenance["baselineId"] == BASE
assert plan["fullAnalysisCompleted"] is False and plan["implementationStarted"] is False
assert plan["independentClientBuildProven"] is False and plan["originalCriteriaStatusChanged"] is False
old = read("implementation-milestones-v9.json")
coverage = read("restoration-coverage-v18.json")
features = read("feature-scope-v27.json")["features"]
scenarios = read("feature-scope-v24-scenarios.json")["scenarios"]
ordering = read("restoration-current-ordering-v1.json")
logical = read("logical-module-contracts-v1.json")
runtime = read("runtime-adoption-matrix-v1.json")
storage = read("storage-domain-map-v1.json")
protocol = read("protocol-delta-adoption-v1.json")
build = read("build-input-dispositions-v1.json")
assert plan["implementationMilestones"] == old["implementationMilestones"], "M1-M7 acceptance changed"
assert plan["originalAnalysisCriteria"] == old["originalAnalysisCriteria"]
assert len(plan["foundationTasks"]) == 9
assert len(plan["restorationTaskGroups"]) == 48
assert len(features) == 373 and len(scenarios) == 1216
assert plan["currentCounts"]["userOperations"] == 377
assert plan["currentCounts"]["supportOperations"] == 117
assert plan["currentCounts"]["pendingSettingsPages"] == 0
assert plan["currentCounts"]["savedLegacySourceRolesUnreviewed"] == 0
assert plan["currentCounts"]["savedLegacyEntriesWithoutFeatureMapping"] == 962
fmap = {f["featureId"]: f for f in features}
covered = Counter(fid for t in plan["restorationTaskGroups"] for fid in t["featureIds"])
assert covered == Counter(fmap.keys()), "feature owner lost or duplicated"
scenario_ids = Counter(x["scenarioId"] for x in scenarios)
assert Counter(s for t in plan["restorationTaskGroups"] for s in t["scenarioIds"]) == scenario_ids
assert all(v == 1 for v in scenario_ids.values())
for t, source in zip(plan["restorationTaskGroups"], coverage["taskGroups"]):
    for k in ["taskId", "featureIds", "primaryModule", "consumerModules", "externalDependencies", "productAcceptancePrerequisites"]:
        assert t[k] == source[k], (t["taskId"], k)
    expected_scenarios = Counter(s["scenarioId"] for s in scenarios if s["featureId"] in t["featureIds"])
    assert Counter(t["scenarioIds"]) == expected_scenarios
    assert t["implementationStarted"] is False
    assert t["currentTaskContract"]["jsonPointer"] == f"/taskGroups/{coverage['taskGroups'].index(source)}"

task_ids = {t["taskId"] for t in plan["restorationTaskGroups"]}
node_ids = task_ids | {f["taskId"] for f in plan["foundationTasks"]}
assert len(node_ids) == 57
for graph_key, levels_key in [("sourcePreparationGraph", "sourcePreparationLevels"), ("integrationGraph", "integrationLevels")]:
    assert plan[graph_key] == ordering[graph_key]
    assert plan[levels_key] == ordering[levels_key]
    graph = {x["id"]: x["dependsOn"] for x in plan[graph_key]}
    assert set(graph) == node_ids
    assert set(graph["W09"]) == task_ids | {"W08"}
    done = set()
    for level in plan[levels_key]:
        assert not done.intersection(level)
        for node in level:
            assert set(graph[node]) <= done, (graph_key, node, graph[node])
        done.update(level)
    assert done == node_ids
    for t in [*plan["foundationTasks"], *plan["restorationTaskGroups"]]:
        key = "sourcePreparationDependsOn" if graph_key == "sourcePreparationGraph" else "integrationDependsOn"
        assert t[key] == graph[t["taskId"]]
for new, prior in zip(plan["foundationTasks"], old["foundationTasks"]):
    assert new["exitCondition"] == prior["exitCondition"]
    assert new["sourcePreparationOutput"] and new["sourcePreparationExit"]

assert len(plan["logicalModuleWorkItems"]) == 37
required = {"responsibility", "environment", "mode", "sourceRanges", "imports", "exports", "sharedState", "sideEffects", "thirdPartyDependencies", "proposedPath"}
assert set(plan["logicalModuleRequiredFields"]) == required
for item, contract in zip(plan["logicalModuleWorkItems"], logical["records"]):
    assert item["ownerId"] == contract["ownerId"]
    assert required <= contract.keys()
    assert item["paths"] == contract["proposedPath"]["values"]
    assert item["foundationTaskId"] == contract["taskOwnership"]["foundation"]["taskId"]
    assert item["foundationTaskId"] in node_ids
    assert item["allConsumersAssigned"] is False
    assert len(item["conditionalConsumerJoins"]) == len(contract["taskOwnership"]["conditionalConsumerJoins"])
    for j, inherited in zip(item["conditionalConsumerJoins"], contract["taskOwnership"]["conditionalConsumerJoins"]):
        assert j["taskId"] == inherited["taskId"] and j["taskId"] in task_ids
        assert j["relationship"] == inherited["relationship"]
        assert j["featureIds"] == inherited.get("featureIds", [])
        assert set(j["featureIds"]) <= fmap.keys()
        assert not j["completeChainProven"]
overlaps = pointer(read("logical-module-ownership-v1.json"), plan["logicalModuleOverlapRules"]["jsonPointer"])
assert len(overlaps) == 19

assert len(plan["runtimeCapabilityWorkItems"]) == 15
refined_groups = set()
for item, prior in zip(plan["runtimeCapabilityWorkItems"], runtime["capabilityGroups"]):
    for k in ["id", "proposedAdapterPath", "proposedContractPath", "foundationTaskIds", "consumerTaskIds", "consumerJoinQualification"]:
        assert item[k] == prior[k], (item["id"], k)
    assert item["qualifiedFullRuntime"] is False
    assert set(item["foundationTaskIds"]) <= node_ids and set(item["consumerTaskIds"]) <= task_ids
    if "selectedSourceRefinement" in item:
        refined_groups.add(item["id"])
        source = json.loads((ROOT / item["selectedSourceRefinement"]["path"]).read_text())["decision"]
        assert item["selectedSourceStatus"] == source["status"]
        assert item["firstPartyUnits"] == source["firstPartyUnits"]
assert refined_groups == {"RAM-02", "RAM-04", "RAM-06"}
assert plan["runtimeRouteDecision"] == runtime["routeDecision"]
assert plan["runtimeBuildGates"] == runtime["buildGates"]
assert plan["nativeDependencyJoins"] == runtime["nativeDependencyJoins"]
assert plan["backendAdoptionDecisions"] == protocol["decisions"]
assert Counter(v for d in plan["backendAdoptionDecisions"] for v in d["variants"]) == Counter(v["id"] for v in protocol["variants"])
assert len(plan["storageDomainWorkItems"]) == 11
for item, prior in zip(plan["storageDomainWorkItems"], storage["domains"]):
    assert {k:v for k,v in item.items() if k != "sourceDecision"} == prior
assert plan["storageRemaining"] == storage["remainingCoverage"]
assert plan["buildInputWorkItems"] == build["decisions"] and len(build["decisions"]) == 30
assert not plan["thirdPartyPolicy"]["generateVendorImplementation"]
assert plan["modePolicy"]["counts"] == {"unknown":372, "codex":0, "chatgpt":0, "shared":1}
assert plan["modePolicy"]["unknownRetained"] and plan["modePolicy"]["sharedComposerControllerRetained"]
assert len(plan["openConditions"]) == 6
for x in plan["openConditions"]:
    assert set(x["tasks"]) <= node_ids and x["condition"] and x["evidence"]
assert plan["behaviorAuthorization"]["groupRemaining"] == 0
assert plan["behaviorAuthorization"]["groupConsumed"] == 2
assert all(plan["behaviorAuthorization"][k] == 0 for k in ["newModelSubmissions", "newClientLaunches", "newServiceCalls"])
assert plan["nextAnalysisAction"]["affectedTasks"] == ["W05", "W06", "T17"]

fields = {"id", "baselineId", "claim", "sourcePath", "sourceHash", "locator", "method", "confidence", "verificationStatus"}
assert len(provenance["evidence"]) == 14
for e in provenance["evidence"]:
    assert fields <= e.keys()
    assert e["confidence"] == "inferred" and e["baselineId"] == BASE
    p = ROOT / e["sourcePath"]
    b = p.read_bytes()
    assert hashlib.sha256(b).hexdigest() == e["sourceHash"]
    pointer(json.loads(b), e["locator"]["jsonPointer"])

md = (target / "implementation-plan-v10.md").read_text()
for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", md):
    assert not link.startswith(("http:", "https:")), "No new external-source claim in this synthesis"
    name = link.split("#")[0]
    assert (target / name).exists() or (OUT / name).exists(), name
for t in plan["restorationTaskGroups"]:
    assert f"| {t['taskId']} {t['name']} | {len(t['featureIds'])} |" in md
for r in plan["logicalModuleWorkItems"]:
    assert r["ownerId"] in md and all(p in md for p in r["paths"])
for r in plan["runtimeCapabilityWorkItems"]:
    assert r["id"] in md and r["exactRemainingPrerequisite"] in md
for d in plan["storageDomainWorkItems"]:
    assert d["id"] in md and d["exactRemainingPrerequisite"] in md
assert "1216 条产品规格不自动成为分析阶段全部跑完的前置条件" in md
assert "客户端实现尚未开始" in md
receipt = {
    "status": "passed", "location": "published" if args.published else "staged",
    "checkedPinFiles": len(checked), "checkedJsonPointers": len(pointers),
    "featuresAssignedExactlyOnce": 373, "scenarioIdsAssignedExactlyOnce": 1216,
    "taskGroups": 48, "graphNodesEach": 57, "logicalOwners": 37, "overlapRules": 19,
    "runtimeGroups": 15, "sourceRefinements": 3, "storageDomains": 11,
    "buildInputOccurrences": 30, "backendDeltaVariants": 11,
    "implementationMilestonesUnchanged": 7, "evidenceRecords": 14,
    "qualification": "Saved-file design/readback verification only; no runtime, service, model, product or client build acceptance.",
}
(WORK / ("published-verification.json" if args.published else "staged-verification.json")).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False))
