"""Check the finite ownership overlay against its actual pinned inputs.

Checks identities, finite-set coverage, explicit joins and non-promotion rules;
does not validate product behavior or claim semantic ownership by containment.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"
MENU_FILES = ["application-menu-goals-v1.json", "menu-command-goals-v1.json",
              "menu-thread-actions-v1.json", "menu-panel-actions-v1.json",
              "menu-navigation-actions-v1.json", "menu-navigation-debug-v1.json",
              "menu-native-history-v1.json", "menu-view-remainder-v1.json"]
FIELDS = {"responsibility", "environment", "mode", "sourceRanges", "imports", "exports",
          "sharedState", "sideEffects", "thirdPartyDependencies", "proposedPath"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)


def verify(folder):
    result = json.loads((folder / "feature-module-ownership-v1.json").read_text())
    assert result["baselineId"] == BASE
    raw, parsed, checked_refs = {}, {}, set()
    def path(p):
        p = Path(p)
        return p if p.is_absolute() else (ROOT / p if str(p).startswith(("analysis/", ".analysis-local/", "scripts/")) else OUT / p)
    def read(p):
        p = path(p)
        if p not in raw:
            raw[p] = p.read_bytes()
        return raw[p]
    def load(p):
        p = path(p)
        if p not in parsed:
            parsed[p] = json.loads(read(p))
        return parsed[p]
    def resolve(ref):
        p = path(ref["path"])
        data = read(p)
        assert len(data) == ref["bytes"], ref["path"]
        assert sha(data) == ref["sha256"], ref["path"]
        if "jsonPointer" in ref:
            x = load(p)
            for bit in ref["jsonPointer"].lstrip("/").split("/") if ref["jsonPointer"] else []:
                bit = bit.replace("~1", "/").replace("~0", "~")
                x = x[int(bit)] if isinstance(x, list) else x[bit]
            checked_refs.add((str(p), ref["jsonPointer"]))
            return x
        if "line" in ref:
            checked_refs.add((str(p), ref["line"]))
            return json.loads(data.decode().splitlines()[ref["line"]-1])

    for obj in walk(result):
        if {"path", "sha256", "bytes"} <= obj.keys():
            resolve(obj)
    ledger = load("feature-scope-v35.json")
    coverage = load("restoration-coverage-v26.json")
    old = load("logical-module-contracts-v1.json")
    features = {x["featureId"]: x for x in result["features"]}
    expected = {x["featureId"]: x for x in ledger["features"]}
    assert len(features) == len(result["features"]) == 426
    assert set(features) == set(expected)
    units = {u["id"]: u for u in result["sourceUnits"]}
    for u in units.values():
        p = FROZEN / u["sourcePath"][len("app.asar/"):]
        data = read(p)
        assert sha(data) == u["sourceHash"], p
        a, z = u["byteRange"]["start"], u["byteRange"]["endExclusive"]
        assert 0 <= a < z <= len(data)
        assert sha(data[a:z]) == u["spanHash"], (p, a, z)
        assert u["role"] == "source-witness; not exclusive implementation ownership"
    responsibilities = {x["ownerId"]: x for x in result["responsibilities"]}
    expected_owners = {x["ownerId"] for x in old["records"]} | {"MENU-UNIT-application-menu"}
    menu_joins, provider_joins = {}, {}
    for name in MENU_FILES:
        menu = load(name)
        expected_owners.update(p["id"] for p in menu.get("additionalMaintenanceProposals", []))
        for g in menu["goals"]:
            menu_joins.setdefault(g["featureId"], []).append((g["id"], g["maintenanceUnitIds"]))
    for record in old["records"]:
        for j in record.get("taskOwnership", {}).get("conditionalConsumerJoins", []):
            for fid in j["featureIds"]:
                provider_joins.setdefault(fid, []).append(record["ownerId"])
    assert set(responsibilities) == expected_owners and len(expected_owners) == 54
    for x in responsibilities.values():
        assert set(x["fields"]) == FIELDS
        assert x["sourceWitnessIds"] and set(x["sourceWitnessIds"]) <= units.keys()
        assert not x["exclusiveSourceAssignment"]
    adapter_ids = {x["ownerId"] for x in result["featureAdapterProposals"]}
    assert len(adapter_ids) == len(result["featureAdapterProposals"]) == 48
    for adapter in result["featureAdapterProposals"]:
        assert FIELDS <= adapter.keys()
        assert not adapter["allStateOwnersAssigned"] and not adapter["completeSourcePartitionProven"]
        actual_members = {f["featureId"] for f in features.values() if f["proposedControllerId"] == adapter["ownerId"]}
        assert actual_members == set(adapter["featureIds"])
        operations = {c["operationId"] for fid in actual_members for c in features[fid]["operationContracts"]}
        assert operations == set(adapter["exports"]["workflowOperationIds"])
    nops = 0
    for fid, f in features.items():
        original = expected[fid]
        assert f["mode"] == original["mode"]
        assert resolve(f["featureRef"])["featureId"] == fid
        assert f["sourceWitnessIds"] and set(f["sourceWitnessIds"]) <= units.keys()
        assert [c["operationId"] for c in f["operationContracts"]] == [o["operationId"] for o in original["operationMembers"]]
        for c in f["operationContracts"]:
            assert isinstance(resolve(c["contractRef"]), dict)
            assert c["stateContracts"] or c["effectContracts"] or c["boundaryContracts"], c["operationId"]
        nops += len(f["operationContracts"])
        actual_menu = [(resolve(j["goalRef"])["id"], j["ownerIds"]) for j in f["menuAdapterRelationships"]]
        assert actual_menu == menu_joins.get(fid, []), fid
        assert [j["ownerId"] for j in f["existingProviderRelationships"]] == provider_joins.get(fid, []), fid
        assert f["persistentOrRemoteStateAuthority"]["ownerId"] is None
        assert f["persistentOrRemoteStateAuthority"]["contractRefs"], fid
        assert not f["completeSourcePartitionProven"] and not f["runtimeAcceptanceChanged"]
    assert nops == result["counts"]["userOperations"] == 443
    assert len(coverage["taskGroups"]) == 49
    assert len(result["supportOperationLinks"]) == result["counts"]["supportingMechanismLinks"] == 117
    assert [s["operationId"] for s in result["supportOperationLinks"]] == [s["operationId"] for s in ledger["supportOperations"]]
    for link in result["supportOperationLinks"]:
        source = resolve(link["contractRef"])
        assert link["featureIds"] == source.get("featureIds", [])
        assert not link["authoritativeStateOwnerAssigned"]
        for fid in link["featureIds"]:
            assert link["operationId"] in features[fid]["supportOperationIds"]
    with (folder / "feature-module-ownership-v1.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert [x["featureId"] for x in rows] == [x["featureId"] for x in result["features"]]
    evidence = [json.loads(line) for line in (folder / "feature-module-ownership-v1-evidence.jsonl").read_text().splitlines()]
    ids = {x["id"] for x in evidence}
    assert len(ids) == len(evidence) == 492
    required = {"id", "baselineId", "claim", "sourcePath", "sourceHash", "locator", "method", "confidence", "verificationStatus"}
    for e in evidence:
        assert required <= e.keys()
        assert sha(read(e["sourcePath"])) == e["sourceHash"]
        assert e["baselineId"] == BASE and e["confidence"] == "inferred"
    assert {x["evidenceId"] for x in features.values()} <= ids
    assert len(result["designDecisions"]) == 12
    assert {x["evidenceId"] for x in result["designDecisions"]} <= ids
    assert not result["fullAnalysisCompleted"] and not result["implementationReady"]
    assert not result["boundedClosure"]["completeClientSourcePartitionProven"]
    counts = result["counts"]
    assert counts["featuresWithFrozenSourceWitnesses"] == 426
    assert counts["normalizedSourceWitnesses"] == len(units)
    assert counts["featuresWithExplicitMenuAdapterJoin"] == len(menu_joins)
    assert counts["featuresWithExplicitExistingProviderJoin"] == len(provider_joins)
    assert counts["authoritativePersistentOrRemoteStateAssignments"] == 0
    assert all(value == 0 for key, value in counts.items() if key.startswith("new"))
    return dict(status="passed", baselineId=BASE, featureDefinitions=426, userOperations=nops,
                integratedResponsibilities=54, coarseWorkflowAdapterProposals=48,
                sourceRangesVerified=len(units), referencedFilesChecked=len(raw), pointersChecked=len(checked_refs), evidenceRecords=len(evidence),
                qualification="Identity/finite mapping/explicit joins/non-promotion checks only; no semantic partition, runtime, product or build acceptance.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = verify(args.directory)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
