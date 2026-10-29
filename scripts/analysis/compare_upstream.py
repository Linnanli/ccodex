#!/usr/bin/env python3
"""Compare frozen root packages with exact official npm archives without execution.

Archives are read in memory, never extracted or installed. Published outputs contain
paths, hashes, counts, and package metadata differences, not implementation copies.
"""

import argparse
import base64
import hashlib
import io
import json
import tarfile
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


TARGETS = (
    ("better-sqlite3", "12.11.1"),
    ("node-pty", "1.1.0"),
    ("objc-js", "1.5.0"),
    ("tslib", "2.8.1"),
    ("node-addon-api", "8.9.0"),
)
SOURCE_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".h", ".hpp", ".c", ".cc", ".cpp", ".mm"}
NATIVE_SUFFIXES = {".node", ".so", ".dylib", ".dll", ".exe", ".a", ".o", ".obj", ".lib"}
NATIVE_MAGICS = (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce", b"\xca\xfe\xba\xbe", b"MZ")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "registry.npmjs.org" or parsed.username or parsed.password:
        raise ValueError("Only credential-free HTTPS requests to registry.npmjs.org are allowed")


class RegistryRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def cached_download(url, path, limit):
    validate_url(url)
    if path.exists():
        data = path.read_bytes()
        if len(data) > limit:
            raise ValueError("Cached response exceeds static-read size limit")
        return data, "cache"
    opener = urllib.request.build_opener(RegistryRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "ccodex-static-upstream-comparison/1", "Accept": "application/json" if path.suffix == ".json" else "application/octet-stream"})
    with opener.open(request, timeout=30) as response:
        validate_url(response.geturl())
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Response exceeds static-read size limit")
    path.write_bytes(data)
    return data, "network"


def verify_integrity(data, dist):
    integrity = dist.get("integrity")
    if not integrity:
        raise ValueError("dist.integrity absent; archive comparison refused")
    recognized = []
    for token in integrity.split():
        algorithm, separator, digest = token.partition("-")
        if separator and algorithm in {"sha512", "sha384", "sha256", "sha1"}:
            expected = base64.b64decode(digest.split("?", 1)[0], validate=True)
            recognized.append((algorithm, expected))
    if not recognized:
        raise ValueError("No supported dist.integrity digest")
    priority = {"sha512": 4, "sha384": 3, "sha256": 2, "sha1": 1}
    strongest = max(priority[algorithm] for algorithm, _ in recognized)
    selected = [(algorithm, expected) for algorithm, expected in recognized if priority[algorithm] == strongest]
    if not any(hashlib.new(algorithm, data).digest() == expected for algorithm, expected in selected):
        raise ValueError("dist.integrity mismatch")
    shasum = dist.get("shasum")
    if shasum and hashlib.sha1(data).hexdigest() != shasum:
        raise ValueError("dist.shasum mismatch")
    return {"status": "verified", "algorithms": sorted({algorithm for algorithm, _ in selected}), "sha1Verified": bool(shasum)}


def archive_files(data):
    files, other = {}, []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "package":
                raise ValueError("Unexpected npm archive member path: " + member.name)
            relative = str(PurePosixPath(*path.parts[1:]))
            if member.isdir():
                continue
            if not member.isfile():
                other.append({"memberPath": member.name, "kind": "link-or-special", "linkTarget": member.linkname})
                continue
            if relative in files:
                raise ValueError("Duplicate npm archive member: " + member.name)
            if member.size > 100 * 1024 * 1024:
                raise ValueError("Oversized npm member")
            content = archive.extractfile(member).read()
            files[relative] = {"bytes": content, "memberPath": member.name, "mode": oct(member.mode), "sha256": sha256(content)}
    return files, other


def category(path, data):
    pure = PurePosixPath(path)
    suffix = pure.suffix.lower()
    if suffix in NATIVE_SUFFIXES or data.startswith(NATIVE_MAGICS):
        return "native-binary"
    if pure.name == ".codex-native-module-build.json":
        return "generated-build-metadata"
    if "build" in pure.parts or suffix == ".stamp":
        return "generated-build-artifact"
    if suffix in SOURCE_SUFFIXES:
        return "source-or-runtime-code"
    if suffix in {".gyp", ".gypi"}:
        return "build-input"
    if suffix == ".json":
        return "metadata"
    if suffix == ".md" or pure.name.lower().startswith(("license", "copyright", "notice")):
        return "documentation-or-license"
    return "other-resource"


def semantic_diff(before, after, pointer=""):
    changes = []
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(before.keys() | after.keys()):
            child = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                changes.append({"pointer": child, "status": "shipped-added", "shipped": after[key]})
            elif key not in after:
                changes.append({"pointer": child, "status": "shipped-removed", "upstream": before[key]})
            else:
                changes.extend(semantic_diff(before[key], after[key], child))
    elif before != after:
        changes.append({"pointer": pointer or "/", "status": "changed", "upstream": before, "shipped": after})
    return changes


def frozen_files(name, extracted, inventory):
    prefix = "node_modules/" + name + "/"
    included, excluded = {}, []
    for item in inventory["archiveFiles"]:
        path = item.get("archivePath", "")
        if not path.startswith(prefix) or item.get("kind") != "asar-file":
            continue
        relative = path[len(prefix):]
        if "node_modules" in PurePosixPath(relative).parts or ".bin" in PurePosixPath(relative).parts:
            excluded.append({"relativePath": relative, "sourcePath": item["sourcePath"], "sha256": item.get("sha256"), "reason": "nested-install-or-bin-artifact"})
            continue
        data = (extracted / path).read_bytes()
        observed = sha256(data)
        if observed != item["sha256"]:
            raise ValueError("Frozen inventory hash mismatch: " + item["sourcePath"])
        included[relative] = {"bytes": data, "sourcePath": item["sourcePath"], "sha256": observed, "inventoryHashVerified": True, "unpacked": item.get("unpacked", False)}
    if "package.json" not in included:
        raise ValueError("Frozen root package metadata missing: " + name)
    return included, excluded


def compare_package(name, version, extracted, inventory, raw):
    registry_url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="") + "/" + version
    cache = raw / (name.replace("/", "__") + "@" + version)
    cache.mkdir(parents=True, exist_ok=True)
    metadata_path = cache / "registry.json"
    metadata_bytes, metadata_fetch = cached_download(registry_url, metadata_path, 2 * 1024 * 1024)
    metadata = json.loads(metadata_bytes)
    if metadata.get("name") != name or metadata.get("version") != version:
        raise ValueError("Registry exact-version metadata identity mismatch")
    dist = metadata["dist"]
    tarball_url = dist["tarball"]
    tarball_path = cache / "package.tgz"
    tarball_bytes, tarball_fetch = cached_download(tarball_url, tarball_path, 100 * 1024 * 1024)
    integrity = verify_integrity(tarball_bytes, dist)
    archive_hash = sha256(tarball_bytes)
    upstream, special_members = archive_files(tarball_bytes)
    shipped, excluded = frozen_files(name, extracted, inventory)
    shipped_metadata = json.loads(shipped["package.json"]["bytes"])
    upstream_metadata = json.loads(upstream["package.json"]["bytes"])
    if shipped_metadata.get("name") != name or shipped_metadata.get("version") != version or upstream_metadata.get("name") != name or upstream_metadata.get("version") != version:
        raise ValueError("Tarball or frozen package identity mismatch")
    package_diff = semantic_diff(upstream_metadata, shipped_metadata)
    rows = []
    for path in sorted(upstream.keys() | shipped.keys()):
        upstream_item, shipped_item = upstream.get(path), shipped.get(path)
        if upstream_item and shipped_item:
            status = "byte-identical" if upstream_item["sha256"] == shipped_item["sha256"] else "different"
        else:
            status = "upstream-only" if upstream_item else "shipped-only"
        content = (shipped_item or upstream_item)["bytes"]
        row = {"relativePath": path, "category": category(path, content), "comparisonStatus": status}
        if upstream_item:
            row["upstream"] = {"url": tarball_url, "archiveSha256": archive_hash, "memberPath": upstream_item["memberPath"], "sha256": upstream_item["sha256"], "bytes": len(upstream_item["bytes"]), "mode": upstream_item["mode"]}
        if shipped_item:
            row["shipped"] = {"sourcePath": shipped_item["sourcePath"], "sha256": shipped_item["sha256"], "bytes": len(shipped_item["bytes"]), "inventoryHashVerified": True, "unpacked": shipped_item["unpacked"], "locator": {"type": "byte-range", "start": 0, "end": len(shipped_item["bytes"])}}
        if row["category"] == "native-binary":
            row["interpretation"] = "Binary comparison only; source provenance, ABI, build reproducibility, and runtime behavior remain unverified."
        elif status == "upstream-only":
            row["interpretation"] = "Absent from frozen root package; release cropping candidate, not evidence of a source edit."
        elif status == "shipped-only" and row["category"] == "generated-build-artifact":
            row["interpretation"] = "Additional build output; not automatically an upstream source modification."
        rows.append(row)
    counts = Counter(row["comparisonStatus"] for row in rows)
    common_source = [row for row in rows if row["category"] == "source-or-runtime-code" and row["comparisonStatus"] in {"byte-identical", "different"}]
    modification_candidates = [row["relativePath"] for row in rows if row["category"] in {"source-or-runtime-code", "build-input"} and row["comparisonStatus"] in {"different", "shipped-only"}]
    native_rows = [row for row in rows if row["category"] == "native-binary" and "shipped" in row]
    native_build_metadata = None
    native_metadata_item = shipped.get(".codex-native-module-build.json")
    if native_metadata_item:
        declared = json.loads(native_metadata_item["bytes"])
        checks = []
        for path, declared_hash in declared.get("artifactHashes", {}).items():
            observed = shipped.get(path)
            checks.append({"relativePath": path, "declaredSha256": declared_hash, "observedSha256": observed["sha256"] if observed else None, "matches": bool(observed and observed["sha256"] == declared_hash)})
        native_build_metadata = {"sourcePath": native_metadata_item["sourcePath"], "sourceSha256": native_metadata_item["sha256"], "declared": declared, "artifactHashChecks": checks, "verificationStatus": "metadata-and-artifact-hashes-only", "limitations": "Self-declared build metadata is not proof of reproducible source provenance, runtime ABI compatibility, or the meaning of the signature fields."}
    labels = []
    if common_source and all(row["comparisonStatus"] == "byte-identical" for row in common_source) and not modification_candidates:
        labels.append("source-match")
    if modification_candidates:
        labels.append("source-modification-candidates")
    if package_diff:
        labels.append("metadata-modified")
    elif shipped["package.json"]["sha256"] != upstream["package.json"]["sha256"]:
        labels.append("metadata-reformatted")
    if counts["upstream-only"]:
        labels.append("cropped")
    if native_rows:
        labels.append("native-unverified")
    return {
        "name": name, "version": version, "status": "compared", "modificationStatus": labels,
        "provenance": {"registryUrl": registry_url, "registryMetadataSha256": sha256(metadata_bytes), "registryCachePath": str(metadata_path.resolve()), "registryFetch": metadata_fetch, "tarballUrl": tarball_url, "tarballCachePath": str(tarball_path.resolve()), "tarballFetch": tarball_fetch, "tarballSha256": archive_hash, "distIntegrity": dist["integrity"], "distShasum": dist.get("shasum"), "integrityVerification": integrity},
        "counts": {"upstreamRegularFiles": len(upstream), "shippedRootRegularFiles": len(shipped), "unionRegularFiles": len(rows), "commonRegularFiles": counts["byte-identical"] + counts["different"], "byteIdenticalCommonFiles": counts["byte-identical"], "differentCommonFiles": counts["different"], "upstreamOnlyFiles": counts["upstream-only"], "shippedOnlyFiles": counts["shipped-only"], "excludedNestedInstallFiles": len(excluded), "upstreamSpecialMembers": len(special_members), "commonSourceOrRuntimeFiles": len(common_source), "byteIdenticalCommonSourceOrRuntimeFiles": sum(row["comparisonStatus"] == "byte-identical" for row in common_source), "shippedNativeBinaries": len(native_rows)},
        "packageJsonSemanticDifferences": package_diff,
        "nativeBuildMetadata": native_build_metadata,
        "countsByCategory": {kind: dict(Counter(row["comparisonStatus"] for row in rows if row["category"] == kind)) for kind in sorted({row["category"] for row in rows})},
        "sourceOrBuildInputModificationCandidates": modification_candidates,
        "excludedShippedFiles": excluded, "upstreamSpecialMembers": special_members, "files": rows,
        "limitations": ["source-match applies only to the compared common source/runtime files, not to every original repository file or dependency.", "Release cropping and missing build inputs do not prove the package can be rebuilt.", "Native binaries have not been loaded or rebuilt, even if their archive bytes match.", "This root-package comparison excludes nested dependencies and does not validate bundle copies or client behavior."],
    }


def markdown(result):
    text = ["# 固定版本 npm 上游逐文件比较", "", "基线：`" + result["baselineId"] + "`。状态：`" + result["status"] + "`。", "", "仅比较冻结根包与官方 npm 精确版本归档。归档仅静态读取，不解包安装、不执行脚本；第三方实现保留在 ignored `raw/upstream`，发布结果只有定位、哈希、统计和包元数据差异。", "", "| 包 | 冻结根文件 / 上游文件 | 共同相同 / 共同总数 | 源码相同 / 共同源码 | 上游独有 / 冻结独有 | 修改状态 |", "| --- | --- | --- | --- | --- | --- |"]
    for package in result["packages"]:
        label = package["name"] + "@" + package["version"]
        if package["status"] != "compared":
            text.append("| " + label + " | — | — | — | — | " + package["status"] + " |")
            continue
        counts = package["counts"]
        text.append(f"| {label} | {counts['shippedRootRegularFiles']} / {counts['upstreamRegularFiles']} | {counts['byteIdenticalCommonFiles']} / {counts['commonRegularFiles']} | {counts['byteIdenticalCommonSourceOrRuntimeFiles']} / {counts['commonSourceOrRuntimeFiles']} | {counts['upstreamOnlyFiles']} / {counts['shippedOnlyFiles']} | {', '.join(package['modificationStatus']) or 'no-label'} |")
    text.extend(["", "`source-match` 仅证明共同源码文件字节一致；`metadata-modified` 表示 package.json 语义有差异；`cropped` 表示上游文件未被交付；`native-unverified` 表示原生 ABI、来源及构建仍未验证。共同文件一致不证明整个包未修改、可完整重建或客户端行为兼容。", ""])
    for package in result["packages"]:
        text.append("## " + package["name"] + "@" + package["version"])
        text.append("")
        if package["status"] != "compared":
            text.append(package.get("error", "前一下载或验证失败后未继续执行。"))
            text.append("")
            continue
        provenance = package["provenance"]
        text.append("[官方固定版本元数据](" + provenance["registryUrl"] + ")；[归档](" + provenance["tarballUrl"] + ")。`dist.integrity` 已验证；归档 SHA-256：`" + provenance["tarballSha256"] + "`。")
        text.append("")
        text.append("package.json 语义差异：" + (", ".join("`" + entry["pointer"] + "`" for entry in package["packageJsonSemanticDifferences"]) or "无") + "。")
        text.append("源码或构建输入修改候选：" + (", ".join("`" + path + "`" for path in package["sourceOrBuildInputModificationCandidates"]) or "无") + "。")
        natives = [entry for entry in package["files"] if entry["category"] == "native-binary" and "shipped" in entry]
        text.append("冻结原生文件：" + (", ".join("`" + entry["relativePath"] + "`（" + entry["comparisonStatus"] + "）" for entry in natives) or "无") + "。")
        if package["nativeBuildMetadata"]:
            native_metadata = package["nativeBuildMetadata"]
            text.append("额外 `.codex-native-module-build.json` 已单列为生成构建元数据；所列产物哈希" + ("均匹配" if all(check["matches"] for check in native_metadata["artifactHashChecks"]) else "存在缺失或不匹配") + "。其自报运行时与构建签名未独立验证。")
        text.append("排除嵌套安装文件：" + str(package["counts"]["excludedNestedInstallFiles"]) + "；逐文件来源和分母见 `upstream-comparison.json`。")
        text.append("")
    return "\n".join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw", type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text())
    output = args.output or args.baseline.parent
    raw = args.raw or output / "raw" / "upstream"
    output.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    inventory_path = args.baseline.parent / "files.json"
    inventory = json.loads(inventory_path.read_text())
    if inventory["baselineId"] != baseline["baselineId"]:
        raise ValueError("Baseline inventory identity mismatch")
    result = {"baselineId": baseline["baselineId"], "generatedAtUtc": datetime.now(timezone.utc).isoformat(), "baselineFileSha256": sha256(args.baseline.read_bytes()), "inventorySha256": sha256(inventory_path.read_bytes()), "sourceArchiveSha256": baseline["archiveSha256"], "method": "official npm exact-version metadata and integrity-verified archives; full-file SHA-256 comparison against frozen ASAR inventory", "status": "complete", "expectedPackages": len(TARGETS), "packages": [], "downloadedCodeExecuted": False, "installScriptsExecuted": False, "thirdPartyImplementationsPublished": False}
    stopped = False
    for name, version in TARGETS:
        if stopped:
            result["packages"].append({"name": name, "version": version, "status": "not-attempted-after-failure"})
            continue
        try:
            compared = compare_package(name, version, Path(baseline["extractedDirectory"]), inventory, raw)
            result["packages"].append(compared)
            print(json.dumps({"package": name + "@" + version, "counts": compared["counts"], "modificationStatus": compared["modificationStatus"]}), flush=True)
        except Exception as error:
            stopped = True
            result["status"] = "failed-stopped"
            result["packages"].append({"name": name, "version": version, "status": "failed", "error": type(error).__name__ + ": " + str(error)})
            print(name + "@" + version + ": " + type(error).__name__ + ": " + str(error), flush=True)
    result["comparedPackages"] = sum(package["status"] == "compared" for package in result["packages"])
    save_json(output / "upstream-comparison.json", result)
    (output / "upstream-comparison.md").write_text(markdown(result), encoding="utf-8")
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
