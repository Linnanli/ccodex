#!/usr/bin/env python3
"""Independently check saved design identities, references and unchanged gates."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/codex-26.1007.30912-c5b273322a83"
WORK = ROOT / ".analysis-local/restoration-plan-v11-work"
PUBLISHED = "--published" in sys.argv
TARGET = OUT if PUBLISHED else WORK / "deliverables"
NAMES = ["implementation-plan-v11.md", "implementation-milestones-v11.json", "restoration-plan-v11-provenance.json"]
CACHE = {}
CHECKED = set()
POINTERS = set()


def locate(name):
    p = Path(name)
    if p.is_absolute():
        return p
    if not PUBLISHED and p.name in NAMES:
        return TARGET / p.name
    return ROOT / p if p.parts[0] in {"analysis", "docs", "scripts", ".analysis-local"} else OUT / p


def load(name):
    p = locate(name)
    if p not in CACHE:
        b = p.read_bytes()
        CACHE[p] = (b, hashlib.sha256(b).hexdigest(), json.loads(b) if p.suffix == ".json" else None)
    return CACHE[p]


def data(name):
    return load(name)[2]


def pointer(name, ptr):
    x = data(name)
    for k in ptr.split("/")[1:]:
        k = k.replace("~1", "/").replace("~0", "~")
        x = x[int(k)] if isinstance(x, list) else x[k]
    POINTERS.add((name, ptr))
    return x


def walk(x):
    if isinstance(x, list):
        for value in x:
            walk(value)
    elif isinstance(x, dict):
        if {"path", "sha256"} <= x.keys():
            b, digest, _ = load(x["path"])
            assert digest == x["sha256"], (x["path"], "hash")
            if "bytes" in x:
                assert len(b) == x["bytes"], (x["path"], "bytes")
            CHECKED.add(x["path"])
            if "jsonPointer" in x:
                pointer(x["path"], x["jsonPointer"])
        for value in x.values():
            walk(value)


plan = data("implementation-milestones-v11.json")
provenance = data("restoration-plan-v11-provenance.json")
old = data("implementation-milestones-v10.json")
scope = data("feature-scope-v42.json")
coverage = data("restoration-coverage-v33.json")
ownership = data("feature-module-ownership-v8.json")
ordering = data("restoration-current-ordering-v16.json")
specs = data("feature-scope-v39-scenarios.json")
walk(plan)
walk(provenance)
assert plan["implementationMilestones"] == old["implementationMilestones"]
assert plan["originalAnalysisCriteria"] == old["originalAnalysisCriteria"]
assert len(plan["originalAnalysisCriteria"]) == 9
assert not any(plan[k] for k in ("fullAnalysisCompleted", "implementationStarted", "independentClientBuildProven", "originalCriteriaStatusChanged"))
assert plan["behaviorAuthorization"] == old["behaviorAuthorization"]
assert plan["modePolicy"]["counts"] == scope["counts"]["modeCounts"] == {"unknown": 462, "codex": 0, "chatgpt": 0, "shared": 1}
assert plan["completeFeatureDenominator"] is None
for key in ("sourcePreparationGraph", "integrationGraph", "sourcePreparationLevels", "integrationLevels"):
    assert plan[key] == ordering[key], key
for key in ("sourcePreparationGraph", "integrationGraph"):
    graph = {x["id"]: set(x["dependsOn"]) for x in plan[key]}
    assert len(graph) == 60
    done = set()
    while len(done) < len(graph):
        ready = {k for k, v in graph.items() if k not in done and v <= done}
        assert ready, (key, "cycle or missing node")
        done |= ready

fids = [x["featureId"] for x in scope["features"]]
assert len(fids) == len(set(fids)) == 463
assert [x["featureId"] for x in plan["featureWorkItems"]] == fids
assert Counter(fid for t in plan["restorationTaskGroups"] for fid in t["featureIds"]) == Counter(fids)
assert len(plan["restorationTaskGroups"]) == 51
assert [x["taskId"] for x in plan["restorationTaskGroups"]] == [x["taskId"] for x in coverage["taskGroups"]]
scenario_ids = {x["scenarioId"] for x in specs["scenarios"]}
assert len(scenario_ids) == len(specs["scenarios"]) == 1569
by_feature = {fid: set() for fid in fids}
for s in specs["scenarios"]:
    for fid in {s["featureId"], *s.get("relatedFeatureIds", [])}:
        by_feature[fid].add(s["scenarioId"])
assert {s for t in plan["restorationTaskGroups"] for s in t["scenarioIds"]} == scenario_ids
for p, f, c, o in zip(plan["featureWorkItems"], scope["features"], coverage["features"], ownership["features"]):
    assert p["featureId"] == f["featureId"] == c["featureId"] == o["featureId"]
    assert set(p["scenarioIds"]) == set(f["scenarioIds"]) == set(c["scenarioIds"]) == by_feature[p["featureId"]]
    assert p["operationIds"] == c["operationIds"]
    assert p["sourceWitnessIds"] == o["sourceWitnessIds"]
    assert not p["implementationStarted"] and not p["sourcePartitionProven"]
assert len({op for f in plan["featureWorkItems"] for op in f["operationIds"]}) == 500
assert [x["operationId"] for x in plan["supportWorkItems"]] == [x["operationId"] for x in scope["supportOperations"]]
assert len(plan["supportWorkItems"]) == 118
for p, s in zip(plan["supportWorkItems"], ownership["supportOperationLinks"]):
    assert p["operationId"] == s["operationId"]
    assert pointer(p["moduleLink"]["path"], p["moduleLink"]["jsonPointer"])["operationId"] == p["operationId"]

assert len(plan["logicalModuleWorkItems"]) == 84
assert len(plan["coarseWorkflowFacades"]) == 48
for p, o in zip(plan["logicalModuleWorkItems"], ownership["responsibilities"]):
    assert p["ownerId"] == o["ownerId"] and p["fields"] == o["fields"]
    assert set(p["fields"]) == set(ownership["requiredModuleFields"]) and len(p["fields"]) == 10
    assert p["sourceWitnessIds"] == o["sourceWitnessIds"] and not p["exclusiveSourceAssignment"]
    for f in p["currentEntryCallbackFeatureIds"]:
        entry = next(x for x in ownership["features"] if x["featureId"] == f)
        assert p["ownerId"] in entry["entryAndCallbackOwnerIds"]
assert len(ownership["sourceUnits"]) == 1726 and len(ownership["sharedWitnessDispositions"]) == 27
assert plan["logicalModuleOverlapRules"] == old["logicalModuleOverlapRules"]
assert [x["ownerId"] for x in plan["coarseWorkflowFacades"]] == [x["ownerId"] for x in ownership["featureAdapterProposals"]]
assert len(plan["runtimeCapabilityWorkItems"]) == 15
assert plan["runtimeRouteDecision"] == old["runtimeRouteDecision"]
assert all(not r["qualifiedFullRuntime"] for r in plan["runtimeCapabilityWorkItems"])
for key in ("runtimeBuildGates", "nativeDependencyJoins", "storageDomainWorkItems", "backendAdoptionDecisions", "buildInputWorkItems"):
    assert plan[key] == old[key], key
assert len(plan["storageDomainWorkItems"]) == 11 and len(plan["buildInputWorkItems"]) == 30
assert sum(len(x["variants"]) for x in plan["backendAdoptionDecisions"]) == 11
dep = data("dependency-investigation-actions-v1.json")["rows"]
assert len(plan["dependencyWorkItems"]) == 202
for p, d in zip(plan["dependencyWorkItems"], dep):
    assert p["dependencyId"] == d["dependencyId"] and p["name"] == d["name"]
    assert p["recommendedIntegration"] == d["recommendedIntegration"]
    assert p["investigationExecuted"] == d["investigationExecuted"]
assert not plan["thirdPartyPolicy"]["generateVendorImplementation"]
required = {"id", "baselineId", "claim", "sourcePath", "sourceHash", "locator", "method", "confidence", "verificationStatus"}
for e in provenance["evidence"]:
    assert required <= e.keys() and e["confidence"] == "inferred"
    assert load(e["sourcePath"])[1] == e["sourceHash"]
    pointer(e["sourcePath"], e["locator"]["jsonPointer"])

md = (TARGET / "implementation-plan-v11.md").read_text()
assert md.startswith("# Codex 独立客户端恢复实施计划草案 版本 11\n")
assert "373 项范围不再作为当前实施入口" in md
for value in ("463", "500", "118", "1569", "51", "84", "48", "1726", "202", "30", "462", "78", "772"):
    assert value in md, value
for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", md):
    assert (OUT / target.split("#")[0]).is_file() or (TARGET / target.split("#")[0]).is_file(), (label, target)
receipt = {"scope": "Saved design references, identity coverage and unchanged acceptance gates only.",
           "publishedReadback": PUBLISHED, "filesWithVerifiedPins": len(CHECKED), "verifiedJsonPointers": len(POINTERS),
           "features": 463, "operations": 500, "support": 118, "uniqueSpecifications": 1569,
           "sharedRelatedFeatureScenarioLinksPreserved": sum(len(s.get("relatedFeatureIds", [])) for s in specs["scenarios"]),
           "tasks": 51, "graphNodesEach": 60, "responsibilities": 84, "coarseFacades": 48,
           "sourceWitnessesReferenced": 1726, "dependencyRows": 202, "runtimeGroups": 15, "buildInputs": 30,
           "originalCriteriaPromoted": False, "runtimeProductOrBuildAcceptance": False, "status": "passed"}
name = "published-verification.json" if PUBLISHED else "verification.json"
(WORK / name).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False))
