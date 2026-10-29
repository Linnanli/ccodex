"""Integrate frozen feature contracts into a qualified maintenance design.

This produces analysis metadata only. Ranges are witnesses, never exclusive
implementation assignments. Existing task paths are retained as coarse adapter
proposals, not promoted to recovered source modules.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "codex-26.1007.30912-c5b273322a83"
OUT = ROOT / "analysis" / BASE
FROZEN = ROOT / ".analysis-local/baselines" / BASE / "extracted"
MENU_FILES = [
    "application-menu-goals-v1.json", "menu-command-goals-v1.json",
    "menu-thread-actions-v1.json", "menu-panel-actions-v1.json",
    "menu-navigation-actions-v1.json", "menu-navigation-debug-v1.json",
    "menu-native-history-v1.json", "menu-view-remainder-v1.json",
]
FIELDS = ["responsibility", "environment", "mode", "sourceRanges", "imports",
          "exports", "sharedState", "sideEffects", "thirdPartyDependencies", "proposedPath"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pointer(value, ptr):
    for bit in ptr.lstrip("/").split("/") if ptr else []:
        bit = bit.replace("~1", "/").replace("~0", "~")
        value = value[int(bit)] if isinstance(value, list) else value[bit]
    return value


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class Builder:
    def __init__(self):
        self.data = {}
        self.pins = {}
        self.units = {}
        self.unit_keys = {}
        self.source_bytes = {}

    def path(self, name):
        p = Path(name)
        if p.is_absolute():
            return p
        return ROOT / p if str(p).startswith(("analysis/", ".analysis-local/", "scripts/")) else OUT / p

    def pin(self, name):
        p = self.path(name)
        key = str(p.relative_to(ROOT))
        if key not in self.pins:
            raw = p.read_bytes()
            self.pins[key] = dict(path=key, bytes=len(raw), sha256=sha(raw))
        return self.pins[key]

    def load(self, name):
        p = self.path(name)
        if p not in self.data:
            self.pin(name)
            self.data[p] = json.loads(p.read_text())
        return self.data[p]

    def ref(self, name, ptr=""):
        return dict(self.pin(name), jsonPointer=ptr)

    def resolve(self, ref):
        pin = self.pin(ref["path"])
        if "sha256" in ref:
            assert pin["sha256"] == ref["sha256"], ref["path"]
        if "bytes" in ref:
            assert pin["bytes"] == ref["bytes"], ref["path"]
        if "jsonPointer" in ref:
            return pointer(self.load(ref["path"]), ref["jsonPointer"])
        if "line" in ref:
            return json.loads(self.path(ref["path"]).read_text().splitlines()[ref["line"] - 1])
        return None

    def field(self, ref, key):
        assert key in self.resolve(ref), (ref, key)
        return dict(self.pin(ref["path"]), **{k: v for k, v in ref.items() if k not in ("path", "bytes", "sha256", "jsonPointer")},
                    jsonPointer=ref["jsonPointer"] + "/" + key)

    def unit(self, raw, origin):
        path, source_hash = raw.get("sourcePath"), raw.get("sourceHash")
        rng = raw.get("byteRange") or raw.get("locator")
        span_hash = raw.get("spanHash") or raw.get("spanSha256")
        if not path and isinstance(raw.get("source"), dict):
            src = raw["source"]
            absolute = Path(src["path"])
            if absolute.is_relative_to(FROZEN):
                path = "app.asar/" + str(absolute.relative_to(FROZEN))
                source_hash = src["sha256"]
        if not (path and source_hash and isinstance(rng, dict)):
            return None
        if "start" not in rng or "endExclusive" not in rng:
            return None
        assert path.startswith("app.asar/"), path
        if path not in self.source_bytes:
            raw_file = (FROZEN / path[len("app.asar/"):]).read_bytes()
            assert sha(raw_file) == source_hash, path
            self.source_bytes[path] = raw_file
        raw_file = self.source_bytes[path]
        assert sha(raw_file) == source_hash, path
        start, end = rng["start"], rng["endExclusive"]
        assert 0 <= start < end <= len(raw_file), (path, start, end)
        fresh_span_hash = sha(raw_file[start:end])
        if span_hash:
            assert fresh_span_hash == span_hash, (path, start, end)
        span_hash = fresh_span_hash
        key = (path, start, end)
        if key not in self.unit_keys:
            uid = f"FMO-SOURCE-{len(self.units) + 1:04}"
            self.unit_keys[key] = uid
            self.units[uid] = dict(id=uid, sourcePath=path, sourceHash=source_hash,
                                  byteRange=dict(start=start, endExclusive=end), spanHash=span_hash,
                                  role="source-witness; not exclusive implementation ownership", origins=[])
        uid = self.unit_keys[key]
        if origin not in self.units[uid]["origins"]:
            self.units[uid]["origins"].append(origin)
        return uid

    def units_in(self, value, origin):
        return sorted({uid for node in walk(value) if (uid := self.unit(node, origin))})


def dedup_refs(refs):
    return list({(r["path"], r.get("jsonPointer"), r.get("line")): r for r in refs}.values())


def build(destination):
    b = Builder()
    ledger = b.load("feature-scope-v35.json")
    coverage = b.load("restoration-coverage-v26.json")
    legacy = b.load("logical-module-contracts-v1.json")
    diag_name = "raw/analysis-requirement-disposition-v5/feature-owner-range-diagnostic.json"
    diagnostic = b.load(diag_name)
    diag = {x["featureId"]: (i, x) for i, x in enumerate(diagnostic["features"])}
    coverage_by_id = {x["featureId"]: (i, x) for i, x in enumerate(coverage["features"])}
    features_by_id = {x["featureId"]: x for x in ledger["features"]}
    support_links = [dict(operationId=x["operationId"], featureIds=x.get("featureIds", []),
                          contractRef=b.ref("feature-scope-v35.json", f"/supportOperations/{i}"),
                          relationship="inherited supporting mechanism; consumer list not necessarily exhaustive",
                          authoritativeStateOwnerAssigned=False)
                     for i, x in enumerate(ledger["supportOperations"])]
    old_units = {x["id"]: x for x in legacy["sourceUnits"]}
    owners, joins = [], defaultdict(list)
    for i, record in enumerate(legacy["records"]):
        basis = b.ref("logical-module-contracts-v1.json", f"/records/{i}")
        ranges = [b.unit(old_units[u], b.ref("logical-module-contracts-v1.json",
                   f"/sourceUnits/{legacy['sourceUnits'].index(old_units[u])}")) for u in record["sourceRanges"]]
        assert all(ranges)
        owners.append(dict(ownerId=record["ownerId"], kind="existing-qualified-responsibility",
                           contractRef=basis, sourceWitnessIds=sorted(set(ranges)),
                           fields={k: b.field(basis, k) for k in FIELDS},
                           exclusiveSourceAssignment=False))
        for join in record.get("taskOwnership", {}).get("conditionalConsumerJoins", []):
            for fid in join["featureIds"]:
                assert fid in features_by_id
                joins[fid].append(dict(ownerId=record["ownerId"], role="conditional-provider-support",
                                      relationship=join["relationship"], basis=b.field(basis, "taskOwnership"),
                                      actualProviderIdentityProven=False))
    menus, menu_joins = {}, defaultdict(list)
    for file in MENU_FILES:
        menu = b.load(file)
        menus[file] = menu
        for i, proposal in enumerate(menu.get("additionalMaintenanceProposals", [])):
            basis = b.ref(file, f"/additionalMaintenanceProposals/{i}")
            ranges = b.units_in(proposal["sourceRanges"], b.field(basis, "sourceRanges"))
            assert ranges, proposal["id"]
            owners.append(dict(ownerId=proposal["id"], kind="menu-adapter-proposal-integrated",
                               contractRef=basis, sourceWitnessIds=ranges,
                               fields={k: b.field(basis, k) for k in FIELDS}, exclusiveSourceAssignment=False))
        for i, goal in enumerate(menu["goals"]):
            assert goal["featureId"] in features_by_id
            basis = b.ref(file, f"/goals/{i}")
            menu_joins[goal["featureId"]].append(dict(
                goalRef=basis, ownerIds=goal["maintenanceUnitIds"],
                sourceWitnessIds=b.units_in(goal, basis),
                relationship="published menu composition/callback association; not state authority"))
    menu_unit = b.load("native-menu-roles-v1.json")["maintenanceUnits"][0]
    basis = b.ref("native-menu-roles-v1.json", "/maintenanceUnits/0")
    owners.append(dict(ownerId=menu_unit["id"], kind="menu-composition-responsibility-integrated",
                       contractRef=basis, sourceWitnessIds=b.units_in(menu_unit["sourceRanges"], basis),
                       fields={k: b.field(basis, k) for k in FIELDS}, exclusiveSourceAssignment=False))
    owner_ids = {x["ownerId"] for x in owners}
    assert len(owner_ids) == len(owners) == 54
    for relationships in menu_joins.values():
        assert all(set(j["ownerIds"]) <= owner_ids for j in relationships)

    split_rules = defaultdict(list)
    for n in range(2, 16):
        file = f"settings-operation-batch-{n:02}.json"
        data = b.load(file)
        for i, decision in enumerate(data.get("moduleDecisions", [])):
            split_rules[decision["taskId"]].append(dict(decision=decision["decision"],
                     basis=b.ref(file, f"/moduleDecisions/{i}")))

    output_features, evidence = [], []
    for i, feature in enumerate(ledger["features"]):
        fid = feature["featureId"]
        ci, cov = coverage_by_id[fid]
        feature_ref = b.ref("feature-scope-v35.json", f"/features/{i}")
        refs, operation_contracts = [], []
        source_ids = set()
        if fid in diag:
            di, old = diag[fid]
            source_ids.update(b.units_in(old["sourceUnits"], b.ref(diag_name, f"/features/{di}/sourceUnits")))
        for operation in feature["operationMembers"]:
            original_primary = operation.get("sourceContractRef") or operation["operationRef"]
            b.resolve(original_primary)
            primary = dict(original_primary, **b.pin(original_primary["path"]))
            value = b.resolve(primary)
            assert isinstance(value, dict), primary
            refs.append(primary)
            source_ids.update(b.units_in(value, primary))
            # Deliberately follow only direct references from selected contracts,
            # never the whole published metadata file or an unbounded provider graph.
            selected = []
            for obj in walk(operation):
                if "path" in obj and "sha256" in obj and ("jsonPointer" in obj or "line" in obj):
                    target = b.resolve(obj)
                    refs.append(obj)
                    source_ids.update(b.units_in(target, obj))
            for obj in value.get("sourceRefs", []):
                if isinstance(obj, dict) and "path" in obj and "sha256" in obj:
                    target = b.resolve(obj)
                    source_ids.update(b.units_in(target, obj))
                    selected.append(obj)
            def fields(keys):
                return [b.field(primary, k) for k in keys if k in value]
            state = fields(["stateAndPersistence", "parametersAndState", "readContract", "stateSetterCalls",
                            "stateReadCalls", "persistence", "ownership", "inputs"])
            effects = fields(["effect", "behavior", "actionContract", "claim", "selectedSourceChain"])
            boundaries = fields(["failureAndCancellation", "resetErrorCancelContract", "externalBoundaries",
                                  "knownGaps", "sourceLimits", "boundaries"])
            for key, bucket in [("parametersAndStateRef", state), ("selectedSourceChainRef", effects),
                                ("boundaryRef", boundaries)]:
                if key in operation:
                    bucket.append(operation[key])
            for key, bucket in [("parametersAndState", state), ("chain", effects), ("boundaries", boundaries)]:
                if key in feature:
                    bucket.append(b.field(feature_ref, key))
            excerpt = value.get("effect") or value.get("actionContract") or value.get("behavior") or value.get("claim")
            if not isinstance(excerpt, str):
                excerpt = json.dumps(excerpt, ensure_ascii=False)
            operation_contracts.append(dict(operationId=operation["operationId"], contractRef=primary,
                stateContracts=dedup_refs(state), effectContracts=dedup_refs(effects),
                boundaryContracts=dedup_refs(boundaries), selectedSourceRefs=selected,
                boundaryExcerpt=excerpt[:1000],
                stateAuthorityStatus="named in selected contracts where available; authoritative module not inferred from callers"))
        for ref in feature.get("sourceRefs", []):
            target = b.resolve(ref)
            ref = dict(ref, **b.pin(ref["path"]))
            refs.append(ref)
            source_ids.update(b.units_in(target, ref))
        for join in menu_joins[fid]:
            source_ids.update(join["sourceWitnessIds"])
        assert source_ids, (fid, "no frozen source witness")
        source_ids = sorted(source_ids)
        cov_ref = b.ref("restoration-coverage-v26.json", f"/features/{ci}")
        entry_owners = sorted({o for j in menu_joins[fid] for o in j["ownerIds"]})
        local_cases = {
            "FSC-0399": ("MPA-M01", "About-window singleton, normal close and caught load/readiness cleanup"),
            "FSC-0424": ("MVR-M01", "banner visibility, timer refs and subscription lifecycle; windowZoom and actual zoom callbacks are injected"),
            "FSC-0425": ("MVR-M02", "q9s local open boolean and J9s toggle; dialog contents and loader error UI remain delegated"),
        }
        local = None
        if fid in local_cases:
            oid, scope = local_cases[fid]
            local = dict(ownerId=oid, scope=scope, basis=[j["goalRef"] for j in menu_joins[fid]],
                         confidence="inferred-maintenance-assignment-from-confirmed-static-contract")
        known = feature.get("knownGaps", [])
        output_features.append(dict(
            featureId=fid, name=feature["name"], mode=feature["mode"], featureRef=feature_ref,
            taskRef=cov_ref, taskId=cov["taskId"],
            proposedControllerId=f"FMO-ADAPTER-{cov['taskId']}" if cov["taskId"] != "T49" else None,
            proposedPath=cov["module"],
            controllerAssignmentStatus="coarse workflow adapter proposal" if cov["taskId"] != "T49" else "menu composition plus selected callback adapters",
            sourceWitnessIds=source_ids, operationContracts=operation_contracts,
            supportOperationIds=sorted(set(feature.get("supportOperationIds", [])) |
                                       {s["operationId"] for s in support_links if fid in s["featureIds"]}),
            existingProviderRelationships=joins[fid], menuAdapterRelationships=menu_joins[fid],
            entryAndCallbackOwnerIds=entry_owners, selectedLocalStateOwnership=local,
            persistentOrRemoteStateAuthority=dict(ownerId=None, status="unresolved-per-feature",
                contractRefs=dedup_refs([x for c in operation_contracts for x in c["stateContracts"] + c["effectContracts"]]),
                remainingQuestion="Bind the named store/service/native provider in these exact operation contracts to its authoritative state owner; preserve caller-local state separately.",
                inheritedGaps=known),
            consumerHints=dict(values=cov["consumerModules"], basis=b.field(cov_ref, "consumerModules"),
                               status="published planning hints; not verified import/ownership edges"),
            externalDependencies=dict(values=cov["externalDependencies"], basis=b.field(cov_ref, "externalDependencies"),
                                      exactPackageVersionsEstablished=False, generateVendorImplementation=False),
            sourceContractRefs=dedup_refs(refs), evidenceId=f"FMO-FEATURE-{i+1:04}",
            completeSourcePartitionProven=False, runtimeAcceptanceChanged=False))
        evidence.append(dict(id=f"FMO-FEATURE-{i+1:04}", baselineId=BASE,
            claim=f"{fid}: the enumerated operation contracts support the stated coarse workflow adapter proposal and explicit provider/state gaps; no exclusive source partition is claimed.",
            sourcePath=feature_ref["path"], sourceHash=feature_ref["sha256"],
            locator=dict(kind="json-pointer", jsonPointer=feature_ref["jsonPointer"]),
            method="inference-from-pinned-static-contracts", confidence="inferred",
            verificationStatus="contract-and-frozen-range-identities-checked; product-and-authoritative-owner-unverified"))

    adapters = []
    for ti, task in enumerate(coverage["taskGroups"]):
        if task["taskId"] == "T49":
            continue
        members = [x for x in output_features if x["taskId"] == task["taskId"]]
        assert {x["featureId"] for x in members} == set(task["featureIds"])
        basis = b.ref("restoration-coverage-v26.json", f"/taskGroups/{ti}")
        contracts = [c["contractRef"] for x in members for c in x["operationContracts"]]
        adapters.append(dict(ownerId=f"FMO-ADAPTER-{task['taskId']}",
            proposalStatus="coarse first-party workflow facade; not an independently recovered module or package",
            featureIds=task["featureIds"],
            responsibility=dict(value=f"{task['name']}: own the enumerated presentation/action orchestration; delegate authoritative service, storage and native effects.",
                                behaviorContractRefs=dedup_refs(contracts), confidence="inferred"),
            environment=dict(proposed="renderer", sourceWitnessPlacement="see each normalized frozen source range; called helpers may be cross-process", actualMount="unknown"),
            mode=dict(values=dict(Counter(x["mode"] for x in members)), disposition="retain unknown/shared branches under existing mode decisions"),
            sourceRanges=dict(witnessIds=sorted({u for x in members for u in x["sourceWitnessIds"]}),
                              assignment="witness only; embedded helpers and callees do not become this adapter's implementation"),
            imports=dict(operationPortContractRefs=dedup_refs(contracts), completeImportClosure=False),
            exports=dict(workflowOperationIds=[c["operationId"] for x in members for c in x["operationContracts"]],
                         originalEsmExportRecoveryClaimed=False),
            sharedState=dict(perFeatureContracts=[x["featureId"] for x in members], authority="caller-local orchestration only; persisted/remote authorities remain per-feature unresolved edges"),
            sideEffects=dict(operationContracts=dedup_refs(contracts), policy="preserve source ordering/error/cancel semantics; effect invocation does not transfer service ownership"),
            thirdPartyDependencies=dict(planningInputs=task["externalDependencies"], exactPackageVersionsEstablished=False, generateVendorImplementation=False),
            proposedPath=dict(value=task["primaryModule"], basis=b.field(basis, "primaryModule"), originalSourceDirectoryRecovered=False),
            refinementRules=split_rules[task["taskId"]],
            allStateOwnersAssigned=False, completeSourcePartitionProven=False))

    # Report duplicate witnesses to prevent accidental code duplication. The
    # overlap alone is deliberately never used to create a feature/owner edge.
    by_unit = defaultdict(list)
    for owner in owners:
        for uid in owner["sourceWitnessIds"]:
            by_unit[uid].append(owner["ownerId"])
    overlaps = [dict(sourceWitnessId=u, responsibilityIds=ids,
                     decision="shared witness; retain composition/import relationship and original qualified ownership rules; never copy the whole range into every adapter")
                for u, ids in by_unit.items() if len(ids) > 1]
    module_evidence = []
    for i, owner in enumerate(owners):
        ref = owner["contractRef"]
        module_evidence.append(dict(id=f"FMO-RESPONSIBILITY-{i+1:03}", baselineId=BASE,
            claim=f"Integrate {owner['ownerId']} with its existing qualified ten-field contract; witness overlaps do not establish exclusive ownership.",
            sourcePath=ref["path"], sourceHash=ref["sha256"], locator=dict(kind="json-pointer", jsonPointer=ref["jsonPointer"]),
            method="inference-from-pinned-static-contracts", confidence="inferred", verificationStatus="qualified-contract-integrated; no new implementation or runtime acceptance"))
        owner["evidenceId"] = module_evidence[-1]["id"]
    mapped = {x["featureId"]: x for x in output_features}
    decisions = []
    decision_specs = [
        ("D01", "Settings assets/factories/visibility/routes remain registration and composition responsibilities. The 48 workflow facades are coarse caller proposals supported by their enumerated operations, not 48 recovered packages.", ["FSC-0001", "FSC-0029"]),
        ("D02", "MENU-UNIT-application-menu owns menu composition. Integrate all16 callback adapter proposals without assigning the whole CZe function to each feature or transferring service state into main menus.", ["FSC-0374", "FSC-0382", "FSC-0424"]),
        ("D03", "Draft preparation and context selection stay separate from actual thread start/submit/cancel. Conditional manager/provider joins apply only to the five saved consumers; they do not make the provider facade the UI owner.", ["FSC-0035", "FSC-0036", "FSC-0048", "FSC-0386"]),
        ("D04", "Archive presentation aggregates typed local-host, cloud-task and account-conversation sources. Reuse the local archive workflow for its menu alias while preserving distinct state/effect adapters.", ["FSC-0046", "FSC-0280", "FSC-0281", "FSC-0282", "FSC-0283", "FSC-0284"]),
        ("D05", "Keep browser page history, application router history and adjacent-thread list navigation as three separate contracts; a back/forward label does not establish equivalent state ownership.", ["FSC-0411", "FSC-0418", "FSC-0421"]),
        ("D06", "Workspace menu aliases and the later full-view operation reuse MPA-M02. Their appearance in multiple menu batches does not create multiple layout controllers or prove injected layout-provider ownership.", ["FSC-0400", "FSC-0405", "FSC-0409"]),
        ("D07", "MVR-M01 owns the proposed banner/subscription lifecycle; injected actual zoom callbacks remain a separate authority. Preserve page-only numeric accelerators and ordinary page-then-window fallback.", ["FSC-0424"]),
        ("D08", "MVR-M02 owns the proposed local open/toggle controller. The named lazy dialog, mount location and error UI remain explicit dependency boundaries rather than an inferred complete shortcut feature implementation.", ["FSC-0425"]),
        ("D09", "UI preference/config mutation intent is separate from authoritative host/account stores, effective roots and durable flush/migration. Carry these exact operation contracts into SQ-04 rather than inventing persistence in each page.", ["FSC-0001", "FSC-0029", "FSC-0060", "FSC-0341"]),
        ("D10", "Unknown-mode workflows remain in scope. Apply the existing three Chat-only branch decisions at their saved boundaries; names such as chat, archive or account do not justify deleting entire shared workflows.", ["FSC-0046", "FSC-0048", "FSC-0280", "FSC-0387"]),
        ("D11", "Third-party implementations remain package/runtime/adapter dependencies. Generic coverage hints do not choose versions, establish upstream equivalence or authorize copying helper implementations.", ["FSC-0059", "FSC-0425"]),
        ("D12", "Project menu command/dialog orchestration is separate from the existing project domain/provider contracts. Keep project selection, registration and state consumers connected through explicit ports; a same-domain name is not a verified provider join.", ["FSC-0045", "FSC-0105", "FSC-0374"]),
    ]
    for did, claim, fids in decision_specs:
        bases = dedup_refs([r for fid in fids for r in mapped[fid]["sourceContractRefs"]])
        decisions.append(dict(id=did, claim=claim, featureIds=fids, basis=bases, confidence="inferred", completeSourcePartitionProven=False))
        ref = bases[0]
        module_evidence.append(dict(id=f"FMO-{did}", baselineId=BASE, claim=claim,
            sourcePath=ref["path"], sourceHash=ref["sha256"], locator=dict(kind="json-pointer", jsonPointer=ref["jsonPointer"]),
            method="inference-from-pinned-static-contracts", confidence="inferred", verificationStatus="qualified maintenance design; no runtime or complete source partition claim"))
        decisions[-1]["evidenceId"] = f"FMO-{did}"
    b.pin("scripts/analysis/build_feature_module_ownership_v1.py")
    inherited_policies = [b.ref("logical-module-ownership-v1.json"), b.ref("storage-domain-map-v1.json"),
                          b.ref("chat-branch-decisions.json"), b.pin("dependencies.csv")]
    result = dict(schemaVersion=1, baselineId=BASE, recordedAtUtc=datetime.now(timezone.utc).isoformat(),
        scope="Current 426 finite definitions only; not the complete product denominator. Integrate existing responsibilities, preserve per-operation state/effect contracts, and propose coarse caller adapters.",
        requiredModuleFields=FIELDS, responsibilities=owners, featureAdapterProposals=adapters,
        features=output_features, supportOperationLinks=support_links, sourceUnits=list(b.units.values()), sharedWitnessDispositions=overlaps, designDecisions=decisions,
        counts=dict(featureDefinitions=len(output_features), userOperations=sum(len(x["operationContracts"]) for x in output_features),
            supportingMechanismLinks=len(support_links),
            existingResponsibilities=37, menuAdapterProposalsIntegrated=16, menuCompositionResponsibilitiesIntegrated=1,
            integratedResponsibilityRecords=len(owners), coarseWorkflowAdapterProposals=len(adapters),
            featuresWithFrozenSourceWitnesses=sum(bool(x["sourceWitnessIds"]) for x in output_features),
            normalizedSourceWitnesses=len(b.units), frozenSourceFiles=len(b.source_bytes),
            featuresWithExplicitExistingProviderJoin=sum(bool(x["existingProviderRelationships"]) for x in output_features),
            featuresWithExplicitMenuAdapterJoin=sum(bool(x["menuAdapterRelationships"]) for x in output_features),
            selectedLocalStateAssignments=sum(bool(x["selectedLocalStateOwnership"]) for x in output_features),
            authoritativePersistentOrRemoteStateAssignments=0, sharedWitnessDispositions=len(overlaps),
            inheritedRefinementRules=sum(len(x["refinementRules"]) for x in adapters),
            integratedDesignDecisions=len(decisions),
            newFeatureDefinitions=0, newSourceParses=0, newReaRuns=0, newClientLaunches=0,
            newModelSubmissions=0, newServiceCalls=0, newProductScenarioPasses=0, newClientImplementation=0),
        dependencyPolicy=dict(generateVendorImplementation=False, rule="Use package/runtime/explicit adapter boundaries. A dependency planning hint does not establish its installed version or replacement qualification."),
        boundedClosure=dict(currentFiniteFeaturesAllHaveDestinationOrSpecificGap=True,
                           originalSq03StopConditionSatisfied="finite source-to-responsibility/gap mapping only",
                           completeClientSourcePartitionProven=False, completeFeatureDenominatorEstablished=False),
        remaining=["SQ-02 source census beyond the delivered menu interval, including CZe record33 and other menu/command/navigation owners.",
                   "SQ-04 storage-domain/feature authority joins; keep native/backend-internal effects as explicit external boundaries.",
                   "Per-feature authoritative provider identity, actual receiver/postcondition and failure/cancel/restart acceptance.",
                   "Dependency/runtime provenance and independent clean build/package qualification.",
                   "Mode-specific caller/dependency closure; unknown does not permit whole-feature exclusion."],
        inheritedArchitecturePolicies=inherited_policies,
        evidenceFile="feature-module-ownership-v1-evidence.jsonl", inputPins=list(b.pins.values()),
        fullAnalysisCompleted=False, implementationReady=False)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "feature-module-ownership-v1.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (destination / "feature-module-ownership-v1-evidence.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in evidence + module_evidence))
    with (destination / "feature-module-ownership-v1.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["featureId", "name", "taskId", "mode", "proposedControllerId", "proposedPath", "entryAndCallbackOwnerIds", "conditionalProviderOwnerIds", "sourceWitnessCount", "stateAuthority", "evidenceId"])
        for x in output_features:
            writer.writerow([x["featureId"], x["name"], x["taskId"], x["mode"], x["proposedControllerId"], x["proposedPath"],
                ";".join(x["entryAndCallbackOwnerIds"]), ";".join(j["ownerId"] for j in x["existingProviderRelationships"]),
                len(x["sourceWitnessIds"]), "unresolved; see exact per-operation contracts", x["evidenceId"]])
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
