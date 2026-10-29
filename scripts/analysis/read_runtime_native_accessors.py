#!/usr/bin/env python3
"""Read selected Mach-O native accessors; never launch or modify the target."""
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/runtime-native-accessors-work'
OBJDUMP = Path('/Library/Developer/CommandLineTools/usr/bin/llvm-objdump')
FRAMEWORK_SOURCE = 'Contents/Frameworks/Codex Framework.framework/Versions/155.0.8059.40/Codex Framework'
EXPECTED_HASH = '34598d1cd28252b97c5010bd5d82e2ffc6ca71f2661c85cf89eeddfbb1706398'
EXPECTED_BYTES = 296533696
ACCESSOR_STARTS = [0x4a279e0 + ordinal * 0x20 for ordinal in range(9)]
NAPI_START, NAPI_BODY_END, NAPI_NEXT = 0x4b2aa60, 0x4b2aaad, 0x4b2aab0


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def describe(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': file_digest(path)}


def write_json(path, record):
    assert not path.exists(), f'Refuse to overwrite {path}'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


def parse_macho(data):
    header = struct.unpack_from('<8I', data)
    magic, cpu, subtype, filetype, count, command_bytes, flags, reserved = header
    assert magic == 0xfeedfacf and cpu == 0x1000007
    assert 32 + command_bytes <= len(data)
    segments, symbols, commands = [], None, []
    cursor = 32
    for ordinal in range(count):
        command, size = struct.unpack_from('<II', data, cursor)
        assert size >= 8 and cursor + size <= 32 + command_bytes
        commands.append({'ordinal': ordinal, 'command': command, 'fileOffset': cursor, 'bytes': size})
        if command == 0x19:
            item = struct.unpack_from('<II16sQQQQiiII', data, cursor)
            name = item[2].rstrip(b'\0').decode()
            vm, vm_size, file_offset, file_size, maxprot, initprot, section_count, segflags = item[3:]
            assert 72 + section_count * 80 == size and file_offset + file_size <= len(data)
            sections = []
            for index in range(section_count):
                offset = cursor + 72 + index * 80
                section = struct.unpack_from('<16s16sQQIIIIIIII', data, offset)
                sections.append({'name': section[0].rstrip(b'\0').decode(),
                    'segmentName': section[1].rstrip(b'\0').decode(), 'vmAddress': section[2],
                    'vmSize': section[3], 'fileOffset': section[4], 'flags': section[8],
                    'sectionHeaderFileOffset': offset, 'sectionHeaderBytes': 80})
            segments.append({'name': name, 'vmAddress': vm, 'vmSize': vm_size,
                'fileOffset': file_offset, 'fileSize': file_size, 'maxprot': maxprot,
                'initprot': initprot, 'commandFileOffset': cursor, 'commandBytes': size,
                'sections': sections})
        elif command == 2:
            _, _, symoff, nsyms, stroff, strsize = struct.unpack_from('<6I', data, cursor)
            assert symoff + nsyms * 16 <= len(data) and stroff + strsize <= len(data)
            symbols = {'commandFileOffset': cursor, 'commandBytes': size, 'symbolTableFileOffset': symoff,
                'symbolCount': nsyms, 'stringTableFileOffset': stroff, 'stringTableBytes': strsize}
        cursor += size
    assert cursor == 32 + command_bytes and symbols is not None
    selected = {}
    wanted = set(ACCESSOR_STARTS + [NAPI_START, NAPI_NEXT])
    for index in range(symbols['symbolCount']):
        offset = symbols['symbolTableFileOffset'] + index * 16
        strx, n_type, section, description, value = struct.unpack_from('<IBBHQ', data, offset)
        if value not in wanted or not (n_type & 0x0e) == 0x0e:
            continue
        assert strx < symbols['stringTableBytes']
        at = symbols['stringTableFileOffset'] + strx
        end = data.find(b'\0', at, symbols['stringTableFileOffset'] + symbols['stringTableBytes'])
        assert end >= at
        name = bytes(data[at:end]).decode()
        if value in ACCESSOR_STARTS and not name.startswith('__ZN8electron5fuses'):
            continue
        if value == NAPI_START and name != '_napi_get_version':
            continue
        if value == NAPI_NEXT and name != '_napi_create_promise':
            continue
        assert value not in selected
        selected[value] = {'name': name, 'unslidVmAddress': value, 'nlistIndex': index,
            'nlistFileOffset': offset, 'nlistBytes': 16, 'stringFileOffset': at,
            'stringBytesIncludingNull': end + 1 - at, 'nType': n_type, 'sectionIndex': section}
    assert set(selected) == wanted
    return {'magic': magic, 'cpuType': cpu, 'cpuSubtype': subtype, 'fileType': filetype,
            'loadCommandCount': count, 'loadCommandBytes': command_bytes, 'flags': flags,
            'functionStartsCommandPresent': any(c['command'] == 0x26 for c in commands)}, segments, symbols, selected


def map_vm(segments, vm, length=1):
    matching = [s for s in segments if s['vmAddress'] <= vm and vm + length <= s['vmAddress'] + s['fileSize']]
    assert len(matching) == 1
    segment = matching[0]
    offset = segment['fileOffset'] + vm - segment['vmAddress']
    sections = [s for s in segment['sections'] if s['vmAddress'] <= vm and vm + length <= s['vmAddress'] + s['vmSize']]
    return offset, {'segmentName': segment['name'], 'segmentVmAddress': segment['vmAddress'],
        'segmentFileOffset': segment['fileOffset'], 'sectionName': sections[0]['name'] if len(sections) == 1 else None,
        'unslidVmAddress': vm, 'fileOffset': offset, 'bytes': length}


def tool_capture(label, argv, byte_scope=None):
    assert argv[0] == str(OBJDUMP)
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=30, check=False)
    assert completed.returncode == 0 and len(completed.stdout) < 100000 and len(completed.stderr) < 10000
    stdout, stderr = WORK / f'{label}.stdout.txt', WORK / f'{label}.stderr.txt'
    assert not stdout.exists() and not stderr.exists()
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    record = {'label': label, 'argv': argv, 'exitCode': completed.returncode,
        'stdout': describe(stdout), 'stderr': describe(stderr), 'byteScope': byte_scope,
        'toolExecutable': str(OBJDUMP), 'toolResolvedPath': str(OBJDUMP.resolve()),
        'toolSha256': file_digest(OBJDUMP), 'targetApplicationExecuted': False,
        'method': 'LLVM tool reads target bytes as input; target executable is not launched'}
    write_json(WORK / f'{label}.command.json', record)
    return record, completed.stdout.decode()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    assert not (WORK / 'runtime-native-accessors.json').exists()
    baseline_path = ROOT / '.analysis-local/current-baseline.json'
    baseline = json.loads(baseline_path.read_text())
    inventory_path = ROOT / 'analysis' / baseline['baselineId'] / 'files.json'
    inventory = json.loads(inventory_path.read_text())
    fuse_dir = ROOT / '.analysis-local/runtime-fuse-work'
    fuse_path = fuse_dir / 'runtime-fuse-observation.json'
    fuse = json.loads(fuse_path.read_text())
    old_manifest_path = fuse_dir / 'frozen-manifest.json'
    old_manifest = json.loads(old_manifest_path.read_text())
    assert file_digest(old_manifest_path) == '2efce3db6eab91e01263e6ddfaf0a65c807dfc205a51ff8debce03c706a5cadb'
    for record in old_manifest['files']:
        path = ROOT / record['path']
        assert path.stat().st_size == record['bytes'] and file_digest(path) == record['sha256']
    original = next(e for e in inventory['applicationFiles'] if e['sourcePath'] == FRAMEWORK_SOURCE)
    assert original['sha256'] == EXPECTED_HASH and original['bytes'] == EXPECTED_BYTES
    framework = ROOT / fuse['observations'][1]['runtimeCopyPath']
    assert FRAMEWORK_SOURCE == fuse['observations'][1]['sourcePath']
    assert framework.stat().st_size == EXPECTED_BYTES and file_digest(framework) == EXPECTED_HASH
    wire = fuse['observations'][1]['wireCandidates'][0]
    wire_start = wire['byteStart'] + 34
    assert wire_start == 246224818 and wire['wireAscii'] == '010011001'
    evidence = []
    def evidence_for(data, start, end, claim, scope='static bytes confirmed; execution and call-site closure unverified'):
        assert 0 <= start < end <= len(data)
        ident = 'RUNTIME-NATIVE-ACCESSOR-E' + str(len(evidence) + 1).zfill(3)
        evidence.append({'id': ident, 'baselineId': baseline['baselineId'], 'claim': claim,
            'sourcePath': FRAMEWORK_SOURCE, 'sourceHash': EXPECTED_HASH,
            'locator': {'kind': 'byte-range', 'start': start, 'endExclusive': end},
            'spanSha256': digest(bytes(data[start:end])), 'method': 'bounded-read-only-MachO-machine-code-and-address-mapping',
            'confidence': 'confirmed', 'verificationStatus': scope})
        return ident
    with framework.open('rb') as stream:
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            assert digest(data) == EXPECTED_HASH
            header, segments, symtab, symbols = parse_macho(data)
            text = next(s for s in segments if s['name'] == '__TEXT')
            text_section = next(s for s in text['sections'] if s['name'] == '__text')
            map_evidence = [evidence_for(data, 0, 32, 'Mach-O64 little-endian x86_64 header for fixed Framework.'),
                evidence_for(data, 32, 32 + header['loadCommandBytes'], 'Complete selected Mach-O load command table; all commands parsed and no LC_FUNCTION_STARTS command found.'),
                evidence_for(data, text['commandFileOffset'], text['commandFileOffset'] + text['commandBytes'], 'LC_SEGMENT_64 __TEXT VM/file mapping used for selected code and wire addresses.'),
                evidence_for(data, text_section['sectionHeaderFileOffset'], text_section['sectionHeaderFileOffset'] + 80, 'Selected function bytes lie within Mach-O __TEXT,__text section.'),
                evidence_for(data, symtab['commandFileOffset'], symtab['commandFileOffset'] + symtab['commandBytes'], 'LC_SYMTAB declares source coordinates of selected native symbol entries and strings.')]
            for symbol in symbols.values():
                at, count = symbol['nlistFileOffset'], symbol['nlistBytes']
                symbol['nlistEvidenceId'] = evidence_for(data, at, at + count, 'Selected native symbol nlist_64 entry: ' + symbol['name'])
                at, count = symbol['stringFileOffset'], symbol['stringBytesIncludingNull']
                symbol['nameEvidenceId'] = evidence_for(data, at, at + count, 'Exact selected native symbol name including terminating null: ' + symbol['name'])
            wire_evidence = evidence_for(data, wire['byteStart'], wire['byteEndExclusive'], 'Fixed v1 fuse sentinel/header and nine wire bytes; same bytes as prior frozen fuse observation.')
            accessors = []
            for ordinal, vm in enumerate(ACCESSOR_STARTS):
                offset, code_map = map_vm(segments, vm, 17)
                body = bytes(data[offset:offset + 17])
                assert body[:6] == bytes.fromhex('554889e58a05') and body[10:] == bytes.fromhex('3c310f94c05dc3')
                displacement = struct.unpack_from('<i', body, 6)[0]
                rip_next, read_vm = vm + 10, vm + 10 + displacement
                read_offset, read_map = map_vm(segments, read_vm)
                assert read_vm == 0xead17b2 + ordinal and read_offset == wire_start + ordinal
                raw = data[read_offset]
                assert raw == ord(wire['wireAscii'][ordinal])
                code_evidence = evidence_for(data, offset, offset + 17, 'Complete 17-byte fuse accessor loads its RIP-relative wire byte, compares 0x31, sets AL by equality, restores RBP and returns; no other branch or call.')
                value_evidence = evidence_for(data, read_offset, read_offset + 1, 'Exact byte read by native fuse accessor at wire ordinal ' + str(ordinal))
                accessors.append({'ordinal': ordinal, 'officialSchemaName': wire['states'][ordinal]['officialSchemaName'],
                    'nativeSymbol': symbols[vm], 'codeMapping': code_map, 'bodyBytes': 17, 'bodyHex': body.hex(),
                    'codeEvidenceId': code_evidence, 'ripDisplacementSigned': displacement, 'ripDisplacementBytesHex': body[6:10].hex(),
                    'ripNextUnslidVm': rip_next, 'readUnslidVm': read_vm, 'readMapping': read_map,
                    'readWireOrdinal': ordinal, 'rawByte': raw, 'wireAsciiByte': chr(raw), 'byteEvidenceId': value_evidence,
                    'priorFuseEvidenceId': wire['states'][ordinal]['evidenceId'],
                    'staticReturnPredicate': 'AL := (memory[readUnslidVm] == 0x31); ret',
                    'executionVerified': False, 'callerClosureVerified': False, 'startupEnforcementVerified': False})
            napi_offset, napi_map = map_vm(segments, NAPI_START, NAPI_BODY_END - NAPI_START)
            napi_body = bytes(data[napi_offset:napi_offset + 77])
            assert len(napi_body) == 77 and napi_body[:4] == bytes.fromhex('554889e5')
            assert napi_body[0x13:0x19] == bytes.fromhex('c7060a000000') and napi_body[0x2d:0x2f] == bytes.fromhex('5dc3')
            assert napi_body[-2:] == bytes.fromhex('ebe0')
            assert NAPI_START + 0x0e + struct.unpack('<b', napi_body[0x0d:0x0e])[0] == NAPI_START + 0x2d
            assert NAPI_START + 0x13 + struct.unpack('<b', napi_body[0x12:0x13])[0] == NAPI_START + 0x2f
            assert NAPI_BODY_END + struct.unpack('<b', napi_body[-1:])[0] == NAPI_START + 0x2d
            padding_offset, _ = map_vm(segments, NAPI_BODY_END, 3)
            assert bytes(data[padding_offset:padding_offset + 3]) == bytes.fromhex('0f1f00')
            napi = {'nativeSymbol': symbols[NAPI_START], 'codeMapping': napi_map, 'bodyBytes': 77,
                'bodyEndUnslidVmExclusive': NAPI_BODY_END, 'bodyHex': napi_body.hex(),
                'bodyEvidenceId': evidence_for(data, napi_offset, napi_offset + 77, 'Complete bounded _napi_get_version body: three internal conditional/control-flow edges, one return, no call or external jump.'),
                'writeInstructionUnslidVm': NAPI_START + 0x13, 'writeInstructionFileOffset': napi_offset + 0x13,
                'writeInstructionHex': 'c7060a000000', 'storedUint32Immediate': 10, 'destinationRegister': 'rsi',
                'writeEvidenceId': evidence_for(data, napi_offset + 0x13, napi_offset + 0x19, 'The nonzero-RDI/nonzero-RSI branch statically encodes movl $10,(%rsi).'),
                'controlFlow': [{'instructionUnslidVm': NAPI_START + 0x0c, 'kind': 'conditional-equal', 'targetUnslidVm': NAPI_START + 0x2d, 'condition': 'RDI == 0 after test'},
                    {'instructionUnslidVm': NAPI_START + 0x11, 'kind': 'conditional-equal', 'targetUnslidVm': NAPI_START + 0x2f, 'condition': 'RSI == 0 after test'},
                    {'instructionUnslidVm': NAPI_START + 0x4b, 'kind': 'unconditional-short-jump', 'targetUnslidVm': NAPI_START + 0x2d}],
                'returnUnslidVm': NAPI_START + 0x2e, 'followingPaddingBytes': 3,
                'nextNativeSymbol': symbols[NAPI_NEXT], 'executionVerified': False,
                'claimScope': 'Named Node-API accessor statically encodes version value 10; actual execution, Node version, NODE_MODULE_VERSION and native-module ABI are unverified.',
                'rangeBasis': 'Selected symbol start, complete bounded control-flow bytes through the tail backward jump to the shared return, three bytes of padding, and following selected symbol; not an LC_FUNCTION_STARTS table.',
                'externalApiMeaning': 'Official Node documentation describes the result output as the maximum supported Node-API version; this static constant does not establish complete runtime/API compatibility.'}
    tool_records = []
    version_record, version_text = tool_capture('llvm-version', [str(OBJDUMP), '--version'])
    tool_records.append(version_record)
    tool_records.append(tool_capture('fuse-accessors', [str(OBJDUMP), '--disassemble', '--start-address=0x4a279e0', '--stop-address=0x4a27af1', str(framework)], {'startUnslidVm': ACCESSOR_STARTS[0], 'endUnslidVmExclusive': ACCESSOR_STARTS[-1] + 17, 'selectedFunctionCount': 9})[0])
    tool_records.append(tool_capture('napi-get-version', [str(OBJDUMP), '--disassemble', '--start-address=0x4b2aa60', '--stop-address=0x4b2aab0', str(framework)], {'startUnslidVm': NAPI_START, 'endUnslidVmExclusive': NAPI_NEXT, 'selectedFunctionCount': 1, 'paddingBytes': 3})[0])
    inputs = [baseline_path, inventory_path, fuse_path, fuse_dir / 'evidence.jsonl', fuse_dir / 'summary.md', fuse_dir / 'validation.json', old_manifest_path, ROOT / 'scripts/analysis/read_runtime_fuses.py']
    record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'static-code-and-wire-binding-confirmed; execution-caller-and-version-closure-unverified',
        'method': 'Parse Mach-O header/LC_SEGMENT_64/selected LC_SYMTAB entries; decode bounded x86_64 bytes and RIP displacement; LLVM finite disassembly retained without target execution.',
        'sourceInputs': [describe(p) for p in inputs], 'scripts': [describe(Path(__file__).resolve())],
        'sourceBinary': {'sourcePath': FRAMEWORK_SOURCE, 'runtimeCopyPath': str(framework.relative_to(ROOT)), 'bytes': EXPECTED_BYTES, 'sourceHash': EXPECTED_HASH, 'frozenInventoryHashMatch': True},
        'scope': {'selectedBinaryCount': 1, 'selectedFuseAccessorFunctions': 9, 'selectedNodeApiAccessorFunctions': 1,
            'accessorBodyBytes': 9 * 17, 'nodeApiBodyBytes': 77, 'machineCodeBodyBytes': 230,
            'sourceEvidenceRecords': len(evidence), 'completeNativeCallerClosure': False, 'targetApplicationLaunched': False,
            'targetBinaryModified': False, 'fusesChanged': False, 'modelTasksSubmitted': 0, 'networkRequests': 0,
            'broadNativeDisassembly': False, 'actualNodeVersion': 'unknown', 'nodeModuleVersion': 'unknown', 'nativeModulesAbi': 'unknown'},
        'machO': {'header': header, 'segments': segments, 'symbolTable': symtab, 'mappingEvidenceIds': map_evidence, 'addressKind': 'unslid VM addresses; not observed process addresses'},
        'wireBinding': {'priorFuseObservationHash': file_digest(fuse_path), 'priorFuseEvidenceId': wire['evidenceId'],
            'wireFileStart': wire['byteStart'], 'wireByteStart': wire_start, 'wireByteEndExclusive': wire_start + 9,
            'wireAscii': wire['wireAscii'], 'wireEvidenceId': wire_evidence, 'linkedAccessors': 9},
        'fuseAccessors': accessors, 'napiGetVersion': napi, 'toolVersion': version_text, 'toolRuns': tool_records,
        'schemaReferences': [{'url': 'https://nodejs.org/api/n-api.html#napi_get_version',
            'checkedAt': '2026-10-13', 'sourceReview': 'Reviewed by root task; excerpted meaning supplied to this static subtask.',
            'externalPageReportedVersion': 'v26.11.1', 'role': 'External meaning of napi_get_version output as maximum supported Node-API version; not target Node release or a full ABI claim.',
            'abiScope': 'Node-API ABI stability does not cover Node C++ APIs or external libraries; no traditional NODE_MODULE_VERSION conclusion is made.'}],
        'conclusions': {'nativeAccessorReadBinding': 'All nine selected compiled fuse accessors read the corresponding fixed wire byte through RIP-relative addressing and set AL to equality with 0x31 before returning.',
            'nodeApiVersionEncoding': 'The bounded _napi_get_version nonnull-pointer branch statically stores uint32 immediate 10 through RSI.',
            'actualNodeVersion': 'unknown', 'actualElectronCompatibilityVersion': 'unknown', 'nodeModuleVersion': 'unknown', 'nativeModulesAbi': 'unknown',
            'completeNativeCallerClosure': 'unknown', 'startupExecutionAndEnforcement': 'unknown'},
        'limitations': ['Static accessor bodies and byte bindings do not prove callers, startup invocation or runtime enforcement.',
            'Compiled native symbol names identify these selected functions; this is not a full native implementation or caller census.',
            'Node-API version value 10 is a static constant in one named accessor, not a Node release or traditional NODE_MODULE_VERSION/native ABI proof.',
            'The selected Framework path version 155.0.8059.40 and earlier external fuse schema tag are not actual Node/Electron compatibility version claims.',
            'No target executable, Node diagnostic, altered fuse, network or model task was invoked.',
            'The seven earlier archive/unpacked declaration contradictions remain unexplained by these native accessor observations.']}
    write_json(WORK / 'runtime-native-accessors.json', record)
    evidence_path = WORK / 'evidence.jsonl'
    assert not evidence_path.exists()
    evidence_path.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in evidence))
    rows = '\n'.join(f"| {e['ordinal']} | {e['officialSchemaName']} | `{e['nativeSymbol']['unslidVmAddress']:#x}` | `{e['readUnslidVm']:#x}` | {e['readMapping']['fileOffset']} | `{e['wireAsciiByte']}` |" for e in accessors)
    summary = f'''# 选定原生 accessor 与 fuse wire 的静态绑定

基线 `{baseline['baselineId']}`。仅只读一份完整 Framework 的哈希及 Mach-O 元数据，再核对9个 fuse accessor（各17字节）和一个77字节 `_napi_get_version` 函数；共230字节完整函数主体。有限 llvm-objdump 原始输出、命令与哈希另存，未启动目标、改 fuse、联网或提交模型任务。

9个 accessor 均通过 `movb RIP+disp,%al` 读取同一冻结 wire 的对应字节，再 `cmpb $0x31,%al; sete %al; ret`。LC_SEGMENT_64 的 VM→文件映射与位移独立解析，不使用反汇编输出中的邻近装饰符号推断数据身份。当前固定 wire 为 `{wire['wireAscii']}`，此为静态代码与字节绑定，未验证调用点闭包或启动执行效果。

| ordinal | 已记录 fuse 名称 | accessor unslid VM | 读取 unslid VM | 读取 file offset | 固定字节 |
| --- | --- | --- | --- | --- | --- |
{rows}

`_napi_get_version` 主体范围 `[0x4b2aa60,0x4b2aaad)`，条件分支和末尾跳转均在函数内；唯一 `ret` 位于 `0x4b2aa8e`，尾错误分支跳回共同收尾处。随后3字节 padding，再在 `0x4b2aab0` 开始 `_napi_create_promise`。当前 Mach-O 无 LC_FUNCTION_STARTS；范围依据上述机器码控制流、padding和符号边界，未声称来自函数起点表。非零 RDI、非零 RSI 路径的 `0x4b2aa73` 静态编码 `movl $10,(%rsi)`；这是命名 Node-API accessor 的版本常量10，实际调用未执行。

[Node 官方文档](https://nodejs.org/api/n-api.html#napi_get_version)说明此输出代表支持的最高 Node-API 版本；本文只确认静态常量10，未验证实际调用或全部API兼容。该外部文档页自报 `v26.11.1` 不是目标 Node 版本，Node-API 稳定性也不等于 Node C++ API、外部库或传统模块 ABI 的兼容证明。

实际 Node 版本、Electron兼容版本、传统 `NODE_MODULE_VERSION` 和原生模块 ABI 均为 unknown。Framework 路径版本 `155.0.8059.40` 与外部 fuse schema tag 均不是上述版本证明；此补充也不解释7条既有归档声明矛盾。旧 fuse 材料与原脚本逐哈希保持原字节。
'''
    assert not (WORK / 'summary.md').exists()
    (WORK / 'summary.md').write_text(summary)
    print(json.dumps({'work': str(WORK.relative_to(ROOT)), 'fuseAccessors': 9,
        'napiFunctionBodyBytes': 77, 'sourceEvidenceRecords': len(evidence), 'machineCodeBodyBytes': 230,
        'targetApplicationLaunched': False, 'modelTasksSubmitted': 0}))


if __name__ == '__main__':
    main()
