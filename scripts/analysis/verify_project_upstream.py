#!/usr/bin/env python3
"""Verify the finite project predicate review without parsing or executing JS.

JSONL pointers address an ordered array of physical, zero-based record rows.
Source files are read only from the fixed extracted baseline for byte hashes.
The checks establish provenance and byte integrity, not JS name resolution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


BASELINE = "codex-26.1007.30912-c5b273322a83"
ROOT = Path(__file__).resolve().parents[2]
EXTRACTED = ROOT / ".analysis-local" / "baselines" / BASELINE / "extracted"
WORK = Path(".analysis-local/project-upstream-work")
ORIGIN_KINDS = {
    "fresh-fragment-ast", "reused-frozen-evidence", "export-specifier-lookup"
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_hash(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def walk(value: Any, pointer: str = ""):
    yield pointer, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, pointer + "/" + escape_pointer(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + "/" + str(index))


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("expected an RFC 6901 JSON pointer")
    node = document
    for raw in pointer[1:].split("/"):
        i = 0
        while i < len(raw):
            if raw[i] == "~":
                if i + 1 >= len(raw) or raw[i + 1] not in "01":
                    raise ValueError("invalid JSON pointer escape")
                i += 1
            i += 1
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            node = node[token]
        elif isinstance(node, list):
            if not token.isascii() or not token.isdigit() or (
                    len(token) > 1 and token.startswith("0")):
                raise ValueError("invalid ordered-array index")
            node = node[int(token)]
        else:
            raise ValueError("pointer traverses a scalar")
    return node


def normalized_source(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid sourcePath")
    if value.startswith("app.asar/"):
        value = value[len("app.asar/"):]
    parts = value.split("/")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in parts):
        raise ValueError("sourcePath must be relative without traversal")
    return str(path)


def compatible_coordinates(record: Any) -> dict[str, Any] | None:
    """Read saved evidence conventions, including a boolean endExclusive flag."""
    if not isinstance(record, dict):
        return None
    source = record.get("sourcePath")
    source_hash = record.get("sourceHash", record.get("sourceSha256"))
    span_hash = record.get("spanHash", record.get("spanSha256"))
    coordinate = record.get("range", record.get("byteRange", record.get("locator")))
    if not isinstance(coordinate, dict) or source is None or source_hash is None:
        return None
    start = coordinate.get("start")
    end = coordinate.get("endExclusive")
    if end is False:
        raise ValueError("inclusive legacy ranges are not an accepted coordinate convention")
    if end is True or end is None:
        end = coordinate.get("end")
    if not is_integer(start) or not is_integer(end):
        return None
    return {"sourcePath": normalized_source(source), "sourceHash": source_hash,
            "range": {"start": start, "endExclusive": end}, "spanHash": span_hash}


class Verification:
    def __init__(self):
        self.errors: list[dict[str, str]] = []
        self.documents: dict[str, Any] = {}
        self.sources: dict[str, bytes] = {}
        self.declared_sources: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, dict[str, Any]] = {}
        self.source_artifact_cache: dict[str, Any] = {}
        self.report: dict[str, Any] = {
            "schemaVersion": 1, "baselineId": BASELINE,
            "method": "stdlib JSON/reference/hash verification; no AST or target execution",
            "scope": {
                "selectedFunctions": 6,
                "sourceRoot": str(EXTRACTED.relative_to(ROOT)),
                "jsonlPointerConvention": "ordered array, /<zero-based physical record index>",
                "wholeInitialModuleLexicalBinding": "unknown",
                "semanticClaims": "not independently re-established",
                "runtime": "unverified",
            },
            "artifacts": {}, "inputChecks": [], "sourceFileChecks": [],
            "sourceArtifactChecks": [], "evidenceChecks": [],
            "evidenceReferenceChecks": [], "functionChecks": [], "bindingChecks": [],
            "reproductionChecks": [],
            "scriptPinChecks": [], "sourceInputPinChecks": [],
        }

    def error(self, location: str, message: str):
        self.errors.append({"location": location, "message": message})

    def local_path(self, value: Any) -> Path:
        if not isinstance(value, str) or not value:
            raise ValueError("expected a nonempty workspace file path")
        path = Path(value)
        path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("file path escapes workspace root")
        return path

    def artifact(self, value: Any, label: str) -> tuple[Path, bytes] | None:
        try:
            path = self.local_path(value)
            data = path.read_bytes()
            self.report["artifacts"][label] = {
                "path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha256(data)
            }
            return path, data
        except (OSError, ValueError) as exc:
            self.error(label, str(exc))
            return None

    def parse(self, data: bytes, path: Path, location: str) -> Any:
        if path.suffix == ".jsonl":
            rows = []
            for index, line in enumerate(data.decode("utf-8").splitlines()):
                try:
                    if not line.strip():
                        raise ValueError("blank JSONL row makes the pointer convention ambiguous")
                    rows.append(json.loads(line))
                except (ValueError, json.JSONDecodeError) as exc:
                    self.error(location + "/" + str(index), str(exc))
                    rows.append(None)
            return rows
        return json.loads(data.decode("utf-8"))

    def load_inputs(self, review: dict[str, Any]):
        inputs = review.get("inputs")
        if not isinstance(inputs, list):
            self.error("/inputs", "expected an array")
            return
        seen = set()
        seen_paths = set()
        for index, item in enumerate(inputs):
            loc = "/inputs/" + str(index)
            if not isinstance(item, dict):
                self.error(loc, "expected an input object")
                continue
            key = item.get("key")
            if not isinstance(key, str) or not key or key in seen:
                self.error(loc + "/key", "missing or duplicate input key")
                continue
            seen.add(key)
            loaded = self.artifact(item.get("path"), "input:" + key)
            if loaded is None:
                continue
            path, data = loaded
            if path in seen_paths:
                self.error(loc + "/path", "duplicate canonical input path")
            seen_paths.add(path)
            actual = {"sha256": sha256(data), "bytes": len(data)}
            passed = is_hash(item.get("sha256")) and item["sha256"] == actual["sha256"]
            passed = passed and is_integer(item.get("bytes")) and item["bytes"] == len(data)
            self.report["inputChecks"].append({
                "key": key, "path": str(path.relative_to(ROOT)),
                "expected": {"sha256": item.get("sha256"), "bytes": item.get("bytes")},
                "actual": actual, "passed": passed,
            })
            if not passed:
                self.error(loc, "input hash or byte length mismatch")
            if path.suffix in (".json", ".jsonl"):
                try:
                    self.documents[key] = self.parse(data, path, loc)
                except (UnicodeError, ValueError) as exc:
                    self.error(loc, "cannot parse pinned input: " + str(exc))

    def load_sources(self, review: dict[str, Any]):
        entries = review.get("sourceFiles")
        if not isinstance(entries, list):
            self.error("/sourceFiles", "expected an array")
            return
        for index, item in enumerate(entries):
            loc = "/sourceFiles/" + str(index)
            try:
                if not isinstance(item, dict):
                    raise ValueError("expected a source object")
                name = normalized_source(item.get("sourcePath"))
                if name in self.declared_sources:
                    raise ValueError("duplicate canonical sourcePath")
                self.declared_sources[name] = item
                path = (EXTRACTED / name).resolve()
                if not path.is_relative_to(EXTRACTED.resolve()):
                    raise ValueError("source symlink escapes fixed extracted root")
                data = path.read_bytes()
                self.sources[name] = data
                passed = is_hash(item.get("sourceHash")) and item["sourceHash"] == sha256(data)
                passed = passed and is_integer(item.get("bytes")) and item["bytes"] == len(data)
                self.report["sourceFileChecks"].append({
                    "sourcePath": item["sourcePath"], "canonicalSourcePath": name,
                    "expectedSourceHash": item.get("sourceHash"), "actualSourceHash": sha256(data),
                    "expectedBytes": item.get("bytes"), "actualBytes": len(data), "passed": passed,
                })
                if not passed:
                    self.error(loc, "frozen source hash or byte length mismatch")
            except (OSError, ValueError) as exc:
                self.error(loc, str(exc))

    def source_artifact(self, ref: Any, location: str) -> Any:
        if location in self.source_artifact_cache:
            return self.source_artifact_cache[location]
        result = {"location": location, "passed": False}
        self.report["sourceArtifactChecks"].append(result)
        self.source_artifact_cache[location] = None
        try:
            if not isinstance(ref, dict):
                raise ValueError("expected sourceArtifact {key,jsonPointer}")
            key, pointer = ref.get("key"), ref.get("jsonPointer")
            result.update({"key": key, "jsonPointer": pointer})
            if not isinstance(key, str) or key not in self.documents:
                raise ValueError("sourceArtifact key has no parsed pinned input")
            node = resolve_pointer(self.documents[key], pointer)
            encoded = json.dumps(node, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8")
            result.update({"passed": True, "resolvedType": type(node).__name__,
                           "resolvedCanonicalJsonSha256": sha256(encoded)})
            if isinstance(node, dict):
                result["resolvedId"] = node.get("id", node.get("evidenceId"))
            self.source_artifact_cache[location] = node
            return node
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            self.error(location, "unresolved sourceArtifact: " + str(exc))
            return None

    def check_range(self, value: Any, location: str) -> dict[str, int] | None:
        if (not isinstance(value, dict) or not is_integer(value.get("start"))
                or not is_integer(value.get("endExclusive"))
                or value["start"] < 0 or value["endExclusive"] <= value["start"]):
            self.error(location, "expected a nonempty zero-based, end-exclusive integer range")
            return None
        return {"start": value["start"], "endExclusive": value["endExclusive"]}

    def load_evidence(self, rows: Any):
        if not isinstance(rows, list) or not rows:
            self.error("evidence", "expected a nonempty JSONL record array")
            return
        for index, row in enumerate(rows):
            loc = "evidence/" + str(index)
            check = {"rowIndex": index, "passed": False}
            self.report["evidenceChecks"].append(check)
            before = len(self.errors)
            if not isinstance(row, dict):
                self.error(loc, "expected an evidence object")
                continue
            eid = row.get("id")
            check["id"] = eid
            if not isinstance(eid, str) or not eid or eid in self.evidence:
                self.error(loc + "/id", "missing or duplicate evidence ID")
            else:
                self.evidence[eid] = row
            if row.get("baselineId") != BASELINE:
                self.error(loc + "/baselineId", "unexpected evidence baseline")
            coordinate = self.check_range(row.get("range"), loc + "/range")
            check["range"] = coordinate
            for field in ("claim", "method", "confidence", "verificationStatus"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    self.error(loc + "/" + field, "missing standard journal field")
            locator = row.get("locator")
            if (not isinstance(locator, dict) or locator.get("kind") != "byte-range"
                    or self.check_range(locator, loc + "/locator") != coordinate):
                self.error(loc + "/locator", "standard locator differs from the canonical range")
            if row.get("spanSha256") != row.get("spanHash"):
                self.error(loc + "/spanSha256", "standard spanSha256 differs from spanHash")
            check["standardJournalFieldsChecked"] = True
            try:
                name = normalized_source(row.get("sourcePath"))
                if name not in self.sources:
                    raise ValueError("evidence source is absent from sourceFiles")
                data = self.sources[name]
                check.update({"sourcePath": row["sourcePath"], "canonicalSourcePath": name,
                              "sourceHash": row.get("sourceHash"),
                              "expectedSpanHash": row.get("spanHash")})
                if row.get("sourceHash") != sha256(data):
                    self.error(loc + "/sourceHash", "evidence source hash mismatch")
                if not is_hash(row.get("spanHash")):
                    self.error(loc + "/spanHash", "invalid SHA256")
                if coordinate is not None:
                    if coordinate["endExclusive"] > len(data):
                        raise ValueError("evidence range exceeds frozen source")
                    span = data[coordinate["start"]:coordinate["endExclusive"]]
                    span.decode("utf-8", errors="strict")
                    actual = sha256(span)
                    check.update({"actualSpanHash": actual, "utf8BoundariesVerified": True})
                    if row.get("spanHash") != actual:
                        self.error(loc + "/spanHash", "frozen UTF-8 span SHA256 mismatch")
            except (UnicodeError, ValueError) as exc:
                self.error(loc, str(exc))
            origin = row.get("origin")
            if not isinstance(origin, dict) or origin.get("kind") not in ORIGIN_KINDS:
                self.error(loc + "/origin", "unknown evidence origin kind")
            else:
                check["originKind"] = origin["kind"]
                ref = origin.get("sourceArtifact")
                if ref is not None:
                    upstream = self.source_artifact(ref, loc + "/origin/sourceArtifact")
                    if origin["kind"] == "reused-frozen-evidence" and upstream is not None:
                        try:
                            old = compatible_coordinates(upstream)
                            new = compatible_coordinates(row)
                            if old is None or new is None:
                                raise ValueError("reused origin lacks complete source coordinates")
                            if upstream.get("id", upstream.get("evidenceId")) != eid:
                                raise ValueError("reused evidence ID differs from its upstream row")
                            if old != new:
                                raise ValueError("reused evidence coordinates or hashes differ")
                            check["reusedCoordinatesMatched"] = True
                        except (ValueError, TypeError) as exc:
                            self.error(loc + "/origin", str(exc))
                elif origin["kind"] != "fresh-fragment-ast":
                    self.error(loc + "/origin", "reused/export evidence requires sourceArtifact")
            check["passed"] = before == len(self.errors)

    def references(self, value: Any, prefix: str):
        for pointer, node in walk(value, prefix):
            if not isinstance(node, dict):
                continue
            if "sourceArtifact" in node and node["sourceArtifact"] is not None:
                self.source_artifact(node["sourceArtifact"], pointer + "/sourceArtifact")
            elif "key" in node and "jsonPointer" in node:
                self.source_artifact(node, pointer)
            for field, target in node.items():
                single = field == "evidenceId" or field.endswith("EvidenceId")
                plural = field == "evidenceIds" or field.endswith("EvidenceIds")
                if not single and not plural:
                    continue
                loc = pointer + "/" + escape_pointer(field)
                if target is None or target == "" or target == []:
                    continue
                targets = target if plural and isinstance(target, list) else [target]
                if plural and not isinstance(target, list):
                    self.error(loc, "expected an evidence ID array")
                for index, eid in enumerate(targets):
                    ref_loc = loc + "/" + str(index) if plural else loc
                    passed = isinstance(eid, str) and eid in self.evidence
                    self.report["evidenceReferenceChecks"].append({
                        "location": ref_loc, "evidenceId": eid, "passed": passed,
                    })
                    if not passed:
                        self.error(ref_loc, "nonempty evidence reference is not in the journal")

    def functions(self, review: dict[str, Any]):
        functions = review.get("functions")
        if not isinstance(functions, list):
            self.error("/functions", "expected a function array")
            return
        if len(functions) != 6:
            self.error("/functions", "finite scope requires exactly six functions")
        fragment = review.get("scope", {}).get("fragment", {})
        fragment_range = self.check_range(fragment.get("range"), "/scope/fragment/range")
        fragment_row = self.evidence.get(fragment.get("evidenceId"))
        if fragment_row is None or fragment_range != fragment_row.get("range"):
            self.error("/scope/fragment", "fragment range/ID does not match its journal record")
        function_ids = {f.get("evidenceId") for f in functions if isinstance(f, dict)}
        seen_ids, seen_names, seen_calls = set(), set(), set()
        for index, function in enumerate(functions):
            loc = "/functions/" + str(index)
            before = len(self.errors)
            if not isinstance(function, dict):
                self.error(loc, "expected a function object")
                continue
            eid, name = function.get("evidenceId"), function.get("name")
            if eid in seen_ids or name in seen_names or not isinstance(name, str) or not name:
                self.error(loc, "duplicate function evidence/name or invalid function name")
            seen_ids.add(eid)
            seen_names.add(name)
            row = self.evidence.get(eid)
            coordinate = self.check_range(function.get("range"), loc + "/range")
            if row is None or coordinate != row.get("range"):
                self.error(loc, "function range/ID does not match its journal record")
            elif fragment_range is not None and fragment_row is not None and coordinate is not None:
                if (normalized_source(row["sourcePath"]) != normalized_source(fragment_row["sourcePath"])
                        or row["sourceHash"] != fragment_row["sourceHash"]
                        or coordinate["start"] < fragment_range["start"]
                        or coordinate["endExclusive"] > fragment_range["endExclusive"]):
                    self.error(loc, "selected function is outside the declared finite fragment")
            calls = function.get("calls")
            if not isinstance(calls, list):
                self.error(loc + "/calls", "expected a complete selected-call array")
                calls = []
            checked_calls = []
            for call_index, call in enumerate(calls):
                call_loc = loc + "/calls/" + str(call_index)
                call_before = len(self.errors)
                if not isinstance(call, dict):
                    self.error(call_loc, "expected a call object")
                    continue
                call_id = call.get("evidenceId")
                if call_id in seen_calls:
                    self.error(call_loc, "duplicate selected call evidence ID")
                seen_calls.add(call_id)
                call_row = self.evidence.get(call_id)
                call_range = self.check_range(call.get("range"), call_loc + "/range")
                if call_row is None or call_range != call_row.get("range"):
                    self.error(call_loc, "call range/ID does not match its journal record")
                elif row is not None and coordinate is not None and call_range is not None:
                    if (normalized_source(call_row["sourcePath"]) != normalized_source(row["sourcePath"])
                            or call_row["sourceHash"] != row["sourceHash"]
                            or call_range["start"] < coordinate["start"]
                            or call_range["endExclusive"] > coordinate["endExclusive"]):
                        self.error(call_loc, "selected call is outside its function source/range")
                binding = call.get("localFragmentBinding")
                binding = binding if isinstance(binding, dict) else {}
                target = binding.get("targetFunctionEvidenceId")
                asserted = target not in (None, "", [])
                target_passed = (not asserted or isinstance(target, str)
                                 and target in function_ids and target in self.evidence)
                self.report["bindingChecks"].append({
                    "location": call_loc + "/localFragmentBinding", "evidenceId": call_id,
                    "declaredStatus": binding.get("status"),
                    "targetFunctionEvidenceId": target, "assertedTarget": asserted,
                    "explicitTargetReferencePassed": target_passed,
                    "originalModuleScope": binding.get("originalModuleScope", "unknown"),
                    "nameBasedBindingInferred": False,
                    "semanticBindingValidation": "not re-parsed",
                })
                if not target_passed:
                    self.error(call_loc + "/localFragmentBinding", "explicit target is not a selected function ID")
                if binding.get("originalModuleScope", "unknown") != "unknown":
                    self.error(call_loc + "/localFragmentBinding", "finite fragment cannot claim original module scope")
                checked_calls.append({
                    "evidenceId": call_id, "range": call_range,
                    "calleeKind": call.get("calleeKind"), "calleeName": call.get("calleeName"),
                    "sourcePath": call_row.get("sourcePath") if call_row else None,
                    "sourceHash": call_row.get("sourceHash") if call_row else None,
                    "passed": call_before == len(self.errors),
                })
            self.report["functionChecks"].append({
                "name": name, "evidenceId": eid, "range": coordinate,
                "sourcePath": row.get("sourcePath") if row else None,
                "sourceHash": row.get("sourceHash") if row else None,
                "calls": checked_calls, "passed": before == len(self.errors),
            })

    def reproduction(self, review: dict[str, Any]):
        reproduction = review.get("reproduction", {})
        for prefix in ("script", "parser"):
            path_key, hash_key = prefix + "Path", prefix + "Sha256"
            if path_key not in reproduction:
                continue
            try:
                value = reproduction[path_key]
                path = Path(value)
                if prefix == "script":
                    path = self.local_path(value)
                if not path.is_absolute():
                    path = ROOT / path
                data = path.read_bytes()
                passed = is_hash(reproduction.get(hash_key)) and sha256(data) == reproduction[hash_key]
                self.report["reproductionChecks"].append({
                    "kind": prefix, "path": value, "expectedSha256": reproduction.get(hash_key),
                    "actualSha256": sha256(data), "bytes": len(data), "passed": passed,
                    "executed": False,
                })
                if not passed:
                    self.error("/reproduction/" + hash_key, "reproduction file hash mismatch")
            except (OSError, TypeError, ValueError) as exc:
                self.error("/reproduction/" + path_key, str(exc))

    def declared_file_pins(self, review: dict[str, Any]):
        for field, report_key in (("scripts", "scriptPinChecks"),
                                  ("sourceInputs", "sourceInputPinChecks")):
            entries = review.get(field)
            if not isinstance(entries, list) or len(entries) != 2:
                self.error("/" + field, "expected exactly two explicit file pins")
                continue
            seen = set()
            for index, item in enumerate(entries):
                loc = "/" + field + "/" + str(index)
                try:
                    if not isinstance(item, dict):
                        raise ValueError("expected a pin object")
                    path = self.local_path(item.get("path"))
                    if path in seen:
                        raise ValueError("duplicate canonical pin path")
                    seen.add(path)
                    if field == "sourceInputs":
                        name = normalized_source(item.get("sourcePath"))
                        expected_path = (EXTRACTED / name).resolve()
                        if (not path.is_relative_to(EXTRACTED.resolve())
                                or path != expected_path or name not in self.sources):
                            raise ValueError("source input is not its declared fixed extracted source")
                        data = self.sources[name]
                        source = self.declared_sources[name]
                        if item.get("sha256") != source.get("sourceHash") or item.get("bytes") != source.get("bytes"):
                            raise ValueError("sourceInputs/sourceFiles identities differ")
                    else:
                        data = path.read_bytes()
                    passed = is_hash(item.get("sha256")) and sha256(data) == item["sha256"]
                    passed = passed and is_integer(item.get("bytes")) and item["bytes"] == len(data)
                    self.report[report_key].append({
                        "path": item["path"], "expectedSha256": item.get("sha256"),
                        "actualSha256": sha256(data), "expectedBytes": item.get("bytes"),
                        "actualBytes": len(data), "passed": passed, "executed": False,
                    })
                    if not passed:
                        self.error(loc, "explicit file hash or byte length mismatch")
                except (OSError, ValueError) as exc:
                    self.error(loc, str(exc))
            if field == "scripts" and Path(__file__).resolve() not in seen:
                self.error("/scripts", "explicit script pins omit the verifier itself")
            if field == "sourceInputs":
                expected = {(EXTRACTED / name).resolve() for name in self.sources}
                if seen != expected:
                    self.error("/sourceInputs", "sourceInputs do not exactly cover sourceFiles")

    def summary(self, review: dict[str, Any], rows: list[Any]):
        selected_calls = sum(len(f.get("calls", [])) for f in review.get("functions", [])
                             if isinstance(f, dict) and isinstance(f.get("calls"), list))
        origins = Counter(row["origin"].get("kind") if isinstance(row.get("origin"), dict)
                          else "invalid" for row in rows if isinstance(row, dict))
        if selected_calls != 7:
            self.error("/functions", "finite scope requires exactly seven selected calls")
        actual = {"selectedFunctions": len(review.get("functions", [])),
                  "selectedCalls": selected_calls, "evidenceRecords": len(rows),
                  "freshEvidenceRecords": sum(v for k, v in origins.items() if k != "reused-frozen-evidence"),
                  "reusedEvidenceRecords": origins.get("reused-frozen-evidence", 0)}
        declared = review.get("summary", {})
        for key, value in actual.items():
            if declared.get(key) != value or not is_integer(declared.get(key)):
                self.error("/summary/" + key, "declared denominator differs from verified records")
        fragment = review.get("scope", {}).get("fragment", {})
        coordinate = fragment.get("range", fragment)
        if isinstance(coordinate, dict) and is_integer(coordinate.get("start")) and is_integer(coordinate.get("endExclusive")):
            actual["fragmentBytes"] = coordinate["endExclusive"] - coordinate["start"]
            if declared.get("fragmentBytes") != actual["fragmentBytes"]:
                self.error("/summary/fragmentBytes", "fragment byte denominator mismatch")
        self.report["denominators"] = {
            **actual, "inputPins": len(self.report["inputChecks"]),
            "sourceFiles": len(self.report["sourceFileChecks"]),
            "originKinds": dict(origins),
            "sourceArtifactReferenceOccurrences": len(self.report["sourceArtifactChecks"]),
            "evidenceReferenceOccurrences": len(self.report["evidenceReferenceChecks"]),
            "uniqueReferencedEvidenceIds": len({r["evidenceId"] for r in self.report["evidenceReferenceChecks"] if isinstance(r["evidenceId"], str)}),
            "assertedFragmentFunctionTargets": sum(r["assertedTarget"] for r in self.report["bindingChecks"]),
            "callsWithNoAssertedFunctionTarget": sum(not r["assertedTarget"] for r in self.report["bindingChecks"]),
            "standardJournalRows": len(self.report["evidenceChecks"]),
            "explicitScriptPins": len(self.report["scriptPinChecks"]),
            "explicitSourceInputPins": len(self.report["sourceInputPinChecks"]),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", default=str(WORK / "review.json"))
    parser.add_argument("--evidence", default=str(WORK / "evidence.jsonl"))
    parser.add_argument("--output", default=str(WORK / "validation.json"))
    parser.add_argument("--expected-review-sha256", help="independent frozen review hash")
    parser.add_argument("--expected-evidence-sha256", help="independent frozen journal hash")
    args = parser.parse_args()
    check = Verification()
    own = Path(__file__).resolve().read_bytes()
    check.report["verifier"] = {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                                "sha256": sha256(own), "bytes": len(own)}
    loaded_review = check.artifact(args.review, "review")
    loaded_evidence = check.artifact(args.evidence, "evidence")
    check.report["freezePinsAsserted"] = bool(args.expected_review_sha256 and args.expected_evidence_sha256)
    for label, expected in (("review", args.expected_review_sha256),
                            ("evidence", args.expected_evidence_sha256)):
        if expected is not None:
            actual = check.report["artifacts"].get(label, {}).get("sha256")
            matched = is_hash(expected) and actual == expected
            check.report["artifacts"].setdefault(label, {}).update({
                "expectedSha256": expected, "independentPinMatched": matched,
            })
            if not matched:
                check.error(label, "independent freeze hash mismatch")
    review, rows = {}, []
    try:
        if loaded_review:
            review = check.parse(loaded_review[1], loaded_review[0], "review")
        if loaded_evidence:
            rows = check.parse(loaded_evidence[1], loaded_evidence[0], "evidence")
        if not isinstance(review, dict):
            raise ValueError("review must be an object")
        if review.get("baselineId") != BASELINE:
            check.error("/baselineId", "unexpected review baseline")
        check.load_inputs(review)
        check.load_sources(review)
        check.load_evidence(rows)
        check.references(review, "review")
        check.references(rows, "evidence")
        check.functions(review)
        check.reproduction(review)
        check.declared_file_pins(review)
        check.summary(review, rows)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        check.error("verification", str(exc))
    check.report["errors"] = check.errors
    check.report["passed"] = not check.errors
    check.report["status"] = "passed" if not check.errors else "failed"
    check.report["limitations"] = [
        "Pinned input provenance, source bytes and references are verified without a new JS AST.",
        "An existing fragment binding assertion is checked by explicit evidence ID only; same-name imports are not linked.",
        "Pointer-only artifact links establish an addressable frozen record, not additional runtime or binding semantics.",
        "Consumer/guard checks cover saved selected records; they do not establish complete initial-module caller coverage.",
    ]
    output = check.local_path(args.output)
    if output in {check.local_path(args.review), check.local_path(args.evidence)}:
        raise ValueError("output must not overwrite review or evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(check.report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.write_bytes(encoded)
    print(json.dumps({"status": check.report["status"], "errors": len(check.errors),
                      "denominators": check.report.get("denominators", {}),
                      "verifierSha256": sha256(own), "validationSha256": sha256(encoded),
                      "output": str(output.relative_to(ROOT))}, ensure_ascii=False))
    return 0 if not check.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
