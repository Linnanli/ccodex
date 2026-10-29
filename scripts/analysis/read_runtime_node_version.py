#!/usr/bin/env python3
"""Bounded static Mach-O Node-version getter study; target is never executed."""
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/runtime-node-version-work'
OLD = ROOT / '.analysis-local/runtime-native-accessors-work'
OBJDUMP = Path('/Library/Developer/CommandLineTools/usr/bin/llvm-objdump')
APPLE_SCHEMA = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/mach-o/fixup-chains.h')
BASELINE = 'codex-26.1007.30912-c5b273322a83'
SOURCE = 'Contents/Frameworks/Codex Framework.framework/Versions/155.0.8059.40/Codex Framework'
HASH = '34598d1cd28252b97c5010bd5d82e2ffc6ca71f2661c85cf89eeddfbb1706398'
SIZE = 296533696
OLD_MANIFEST_HASH = '72776bbdff059553a0aa10b6167e98c89e765eb2b52b385db0eb6333bd963f25'
SYMBOL_NAME = '_napi_get_node_version'
NEXT_NAME = '_napi_create_async_work'
BODY_HEX = ('554889e5b8010000004885ff74234885f67420488d05a607690c488906'
            '0f57c00f11477848c787880000000000000031c05dc348b90000000001000000'
            '48898f8800000048c7878000000000000000ebe0')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4194304), b''):
            value.update(block)
    return value.hexdigest()


def metadata(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': file_sha(path)}


def write_json(path, item):
    assert not path.exists(), f'Refuse overwrite: {path}'
    path.write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n')


def parse_macho(data):
    magic, cpu, subtype, filetype, count, total, flags, reserved = struct.unpack_from('<8I', data)
    assert magic == 0xfeedfacf and cpu == 0x1000007 and 32 + total <= len(data)
    segments, symtab, fixups, commands = [], None, None, []
    cursor = 32
    for ordinal in range(count):
        tag, length = struct.unpack_from('<II', data, cursor)
        assert length >= 8 and cursor + length <= 32 + total
        commands.append({'ordinal': ordinal, 'command': tag, 'fileOffset': cursor, 'bytes': length})
        if tag == 0x19:
            item = struct.unpack_from('<II16sQQQQiiII', data, cursor)
            name = item[2].rstrip(b'\0').decode()
            vm, vm_size, offset, size, maxprot, initprot, section_count, segflags = item[3:]
            assert 72 + section_count * 80 == length and offset + size <= len(data)
            sections = []
            for index in range(section_count):
                at = cursor + 72 + index * 80
                row = struct.unpack_from('<16s16sQQIIIIIIII', data, at)
                sections.append({'name': row[0].rstrip(b'\0').decode(), 'vmAddress': row[2],
                    'vmSize': row[3], 'fileOffset': row[4], 'flags': row[8], 'headerFileOffset': at})
            segments.append({'name': name, 'vmAddress': vm, 'vmSize': vm_size,
                'fileOffset': offset, 'fileSize': size, 'commandFileOffset': cursor,
                'commandBytes': length, 'sections': sections})
        elif tag == 2:
            _, _, offset, number, strings, strings_size = struct.unpack_from('<6I', data, cursor)
            assert offset + number * 16 <= len(data) and strings + strings_size <= len(data)
            symtab = {'commandFileOffset': cursor, 'commandBytes': length,
                'symbolTableFileOffset': offset, 'symbolCount': number,
                'stringTableFileOffset': strings, 'stringTableBytes': strings_size}
        elif tag == 0x80000034:
            _, _, offset, size = struct.unpack_from('<4I', data, cursor)
            assert offset + size <= len(data)
            fixups = {'commandFileOffset': cursor, 'commandBytes': length,
                'dataFileOffset': offset, 'dataBytes': size}
        cursor += length
    assert cursor == 32 + total and symtab and fixups
    selected = {}
    for index in range(symtab['symbolCount']):
        at = symtab['symbolTableFileOffset'] + index * 16
        string_index, symbol_type, section, description, vm = struct.unpack_from('<IBBHQ', data, at)
        assert string_index < symtab['stringTableBytes']
        name_at = symtab['stringTableFileOffset'] + string_index
        end = data.find(b'\0', name_at, symtab['stringTableFileOffset'] + symtab['stringTableBytes'])
        assert end >= name_at
        name = bytes(data[name_at:end]).decode()
        if name in {SYMBOL_NAME, NEXT_NAME}:
            assert symbol_type & 0xe == 0xe and name not in selected
            selected[name] = {'name': name, 'unslidVmAddress': vm, 'nlistIndex': index,
                'nlistFileOffset': at, 'nlistBytes': 16, 'stringFileOffset': name_at,
                'stringBytesIncludingNull': end + 1 - name_at, 'nType': symbol_type, 'sectionIndex': section}
    assert set(selected) == {SYMBOL_NAME, NEXT_NAME}
    return {'magic': magic, 'cpuType': cpu, 'cpuSubtype': subtype, 'fileType': filetype,
        'loadCommandCount': count, 'loadCommandBytes': total,
        'functionStartsCommandPresent': any(c['command'] == 0x26 for c in commands)}, segments, symtab, fixups, selected


def map_vm(segments, vm, length):
    candidates = [s for s in segments if s['vmAddress'] <= vm and vm + length <= s['vmAddress'] + s['fileSize']]
    assert len(candidates) == 1
    segment = candidates[0]
    sections = [s for s in segment['sections'] if s['vmAddress'] <= vm and vm + length <= s['vmAddress'] + s['vmSize']]
    assert len(sections) == 1 and sections[0]['flags'] & 0xff not in {1, 12, 18}
    offset = segment['fileOffset'] + vm - segment['vmAddress']
    return offset, {'unslidVmAddress': vm, 'fileOffset': offset, 'bytes': length,
        'segmentName': segment['name'], 'segmentVmAddress': segment['vmAddress'],
        'segmentFileOffset': segment['fileOffset'], 'sectionName': sections[0]['name'],
        'sectionHeaderFileOffset': sections[0]['headerFileOffset']}


def capture(label, argv, scope):
    assert argv[0] == str(OBJDUMP)
    run = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=30, check=False)
    assert run.returncode == 0 and len(run.stdout) < 100000 and len(run.stderr) < 10000
    stdout, stderr = WORK / f'{label}.stdout.txt', WORK / f'{label}.stderr.txt'
    assert not stdout.exists() and not stderr.exists()
    stdout.write_bytes(run.stdout)
    stderr.write_bytes(run.stderr)
    record = {'label': label, 'argv': argv, 'exitCode': run.returncode,
        'stdout': metadata(stdout), 'stderr': metadata(stderr), 'scope': scope,
        'toolExecutable': str(OBJDUMP), 'toolResolvedPath': str(OBJDUMP.resolve()),
        'toolSha256': file_sha(OBJDUMP), 'targetExecuted': False,
        'method': 'LLVM reads target file as data; the target binary is never launched'}
    write_json(WORK / f'{label}.command.json', record)
    return record, run.stdout.decode()


def main():
    assert not WORK.exists(), 'Refuse existing output directory; immutable output is not overwritten'
    WORK.mkdir(parents=True)
    baseline_path = ROOT / '.analysis-local/current-baseline.json'
    inventory_path = ROOT / 'analysis' / BASELINE / 'files.json'
    old_result_path = OLD / 'runtime-native-accessors.json'
    old_manifest_path = OLD / 'frozen-manifest.json'
    assert file_sha(old_manifest_path) == OLD_MANIFEST_HASH
    old_manifest = json.loads(old_manifest_path.read_text())
    for item in old_manifest['files']:
        path = ROOT / item['path']
        assert path.stat().st_size == item['bytes'] and file_sha(path) == item['sha256']
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baselineId'] == BASELINE
    inventory = json.loads(inventory_path.read_text())
    row = next(r for r in inventory['applicationFiles'] if r['sourcePath'] == SOURCE)
    assert row['bytes'] == SIZE and row['sha256'] == HASH
    previous = json.loads(old_result_path.read_text())
    framework = ROOT / previous['sourceBinary']['runtimeCopyPath']
    assert framework.stat().st_size == SIZE and file_sha(framework) == HASH
    schema_bytes = APPLE_SCHEMA.read_bytes()
    schema_path = WORK / 'apple-fixup-chains.h'
    schema_path.write_bytes(schema_bytes)
    schema_ranges = []
    for start_token, end_token in [
        (b'struct dyld_chained_fixups_header', b'// these values are set'),
        (b'// values for dyld_chained_starts_in_segment.pointer_format', b'// DYLD_CHAINED_PTR_ARM64E'),
        (b'struct dyld_chained_ptr_64_rebase', b'// DYLD_CHAINED_PTR_ARM64E_USERLAND24')]:
        start = schema_bytes.index(start_token)
        end = schema_bytes.index(end_token, start)
        schema_ranges.append({'start': start, 'endExclusive': end,
            'spanSha256': sha(schema_bytes[start:end])})
    assert b'DYLD_CHAINED_PTR_64                     =  2' in schema_bytes
    assert b'next      : 12,    // 4-byte stride' in schema_bytes
    evidence = []
    def cite(data, start, end, claim):
        assert 0 <= start < end <= len(data)
        ident = 'RUNTIME-NODE-VERSION-E' + str(len(evidence) + 1).zfill(3)
        evidence.append({'id': ident, 'baselineId': BASELINE, 'claim': claim,
            'sourcePath': SOURCE, 'sourceHash': HASH,
            'locator': {'kind': 'byte-range', 'start': start, 'endExclusive': end},
            'spanSha256': sha(bytes(data[start:end])),
            'method': 'bounded-read-only-MachO-symbol-CFG-RIP-and-chained-pointer-analysis',
            'confidence': 'confirmed', 'verificationStatus': 'static source bytes confirmed; no target execution or complete caller closure'})
        return ident
    with framework.open('rb') as stream:
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            assert sha(data) == HASH
            header, segments, symtab, fixups, symbols = parse_macho(data)
            refs = [cite(data, 0, 32, 'Frozen Framework Mach-O64 x86_64 header.'),
                cite(data, 32, 32 + header['loadCommandBytes'], 'Complete Mach-O load-command table; selected mappings and chained-fixups command parsed, LC_FUNCTION_STARTS absent.'),
                cite(data, symtab['commandFileOffset'], symtab['commandFileOffset'] + 24, 'LC_SYMTAB coordinates used for exact selected symbol names and nlist entries.'),
                cite(data, fixups['commandFileOffset'], fixups['commandFileOffset'] + 16, 'LC_DYLD_CHAINED_FIXUPS payload location and size.')]
            for name, symbol in symbols.items():
                at = symbol['nlistFileOffset']
                symbol['nlistEvidenceId'] = cite(data, at, at + 16, 'Exact nlist_64 entry for ' + name)
                at = symbol['stringFileOffset']
                symbol['nameEvidenceId'] = cite(data, at, at + symbol['stringBytesIncludingNull'], 'Exact null-terminated symbol name ' + name)
            start = symbols[SYMBOL_NAME]['unslidVmAddress']
            next_start = symbols[NEXT_NAME]['unslidVmAddress']
            assert start == 0x4b42f60 and next_start == start + 96
            body = bytes.fromhex(BODY_HEX)
            assert len(body) == 81
            offset, mapping = map_vm(segments, start, 81)
            assert bytes(data[offset:offset + 81]) == body
            body_ref = cite(data, offset, offset + 81, 'Complete bounded napi_get_node_version body includes both parameter-error branches and tail jump to shared return; no call or external branch.')
            padding_offset, _ = map_vm(segments, start + 81, 15)
            padding = bytes(data[padding_offset:padding_offset + 15])
            assert padding.hex() == '6666666666662e0f1f840000000000'
            padding_ref = cite(data, padding_offset, padding_offset + 15, 'Fifteen-byte NOP padding separates full body from next actual symbol.')
            for delta, target in [(0xc, 0x31), (0x11, 0x33), (0x4f, 0x31)]:
                assert delta + 2 + struct.unpack_from('<b', body, delta + 1)[0] == target
            displacement = struct.unpack_from('<i', body, 0x16)[0]
            struct_vm = start + 0x1a + displacement
            assert struct_vm == 0x111d3720
            struct_offset, struct_map = map_vm(segments, struct_vm, 24)
            raw_struct = bytes(data[struct_offset:struct_offset + 24])
            major, minor, patch, alignment, encoded_pointer = struct.unpack('<IIIIQ', raw_struct)
            assert (major, minor, patch, alignment) == (24, 19, 0, 0)
            getter = {'nativeSymbol': symbols[SYMBOL_NAME], 'nextNativeSymbol': symbols[NEXT_NAME],
                'codeMapping': mapping, 'bodyBytes': 81, 'bodyEndUnslidVmExclusive': start + 81,
                'bodyHex': body.hex(), 'bodyEvidenceId': body_ref, 'followingPaddingBytes': 15,
                'paddingHex': padding.hex(), 'paddingEvidenceId': padding_ref,
                'instructionCount': 19, 'returnUnslidVm': start + 0x32,
                'controlFlow': [{'instructionUnslidVm': start + 0xc, 'kind': 'conditional-equal', 'targetUnslidVm': start + 0x31, 'condition': 'RDI == 0'},
                    {'instructionUnslidVm': start + 0x11, 'kind': 'conditional-equal', 'targetUnslidVm': start + 0x33, 'condition': 'RSI == 0'},
                    {'instructionUnslidVm': start + 0x4f, 'kind': 'unconditional-short-jump', 'targetUnslidVm': start + 0x31}],
                'leaInstructionUnslidVm': start + 0x13, 'leaInstructionFileOffset': offset + 0x13,
                'leaInstructionHex': body[0x13:0x1a].hex(), 'ripDisplacementSigned': displacement,
                'ripNextUnslidVm': start + 0x1a, 'directStructureUnslidVm': struct_vm,
                'leaEvidenceId': cite(data, offset + 0x13, offset + 0x1a, 'RIP-relative LEA obtains unslid static version-structure address.'),
                'outputStoreInstructionUnslidVm': start + 0x1a,
                'outputStoreInstructionHex': body[0x1a:0x1d].hex(),
                'outputStoreEvidenceId': cite(data, offset + 0x1a, offset + 0x1d, 'Nonnull RDI/RSI path stores direct structure address into memory at RSI.'),
                'rangeBasis': 'Exact selected nlist symbol start, complete bounded internal CFG including tail error branch, fifteen-byte NOP, following selected symbol; no function-starts table.',
                'executionVerified': False, 'callerClosureVerified': False}
            for name in ['__TEXT', '__DATA_CONST']:
                segment = next(s for s in segments if s['name'] == name)
                refs.append(cite(data, segment['commandFileOffset'], segment['commandFileOffset'] + segment['commandBytes'], 'LC_SEGMENT_64 ' + name + ' file-backed VM mapping for selected function/data/chain.'))
            for selected in [mapping, struct_map]:
                refs.append(cite(data, selected['sectionHeaderFileOffset'], selected['sectionHeaderFileOffset'] + 80, 'Selected ' + selected['segmentName'] + ',' + selected['sectionName'] + ' section mapping.'))
            fix_base = fixups['dataFileOffset']
            version, starts_delta, imports_delta, strings_delta, imports_count, imports_format, strings_format = struct.unpack_from('<7I', data, fix_base)
            assert version == 0
            starts_base = fix_base + starts_delta
            segment_count = struct.unpack_from('<I', data, starts_base)[0]
            assert segment_count == len(segments)
            segment_offsets = list(struct.unpack_from('<' + 'I' * segment_count, data, starts_base + 4))
            seg_index = next(i for i, s in enumerate(segments) if s['name'] == '__DATA_CONST')
            segment_info = starts_base + segment_offsets[seg_index]
            info_size, page_size, fmt, segment_vm_offset, max_pointer, page_count = struct.unpack_from('<IHHQIH', data, segment_info)
            assert fmt == 2 and page_size == 4096 and segment_vm_offset == segments[seg_index]['vmAddress']
            assert 22 + 2 * page_count <= info_size and segment_info + info_size <= fix_base + fixups['dataBytes']
            pointer_vm = struct_vm + 16
            page_index, in_page = divmod(pointer_vm - segment_vm_offset, page_size)
            assert page_index < page_count
            page_entry_offset = segment_info + 22 + page_index * 2
            page_start = struct.unpack_from('<H', data, page_entry_offset)[0]
            assert page_start < 0x8000
            page_base = segment_vm_offset + page_index * page_size
            chain = []
            current = page_base + page_start
            while True:
                assert page_base <= current <= pointer_vm and len(chain) < 1024
                at, pointer_map = map_vm(segments, current, 8)
                value = struct.unpack_from('<Q', data, at)[0]
                entry = {'unslidVmAddress': current, 'fileOffset': at, 'rawUint64': value,
                    'rawHex': bytes(data[at:at + 8]).hex(), 'nextStrideUnits': (value >> 51) & 0xfff,
                    'bind': value >> 63}
                chain.append(entry)
                if current == pointer_vm:
                    break
                assert entry['nextStrideUnits'] > 0
                current += entry['nextStrideUnits'] * 4
            assert len(chain) == 229 and chain[-1]['rawUint64'] == encoded_pointer
            target_low = encoded_pointer & ((1 << 36) - 1)
            high8 = (encoded_pointer >> 36) & 0xff
            reserved = (encoded_pointer >> 44) & 0x7f
            bind = encoded_pointer >> 63
            assert high8 == reserved == bind == 0
            release_vm = target_low | (high8 << 56)
            assert release_vm == 0xf69f978
            release_offset, release_map = map_vm(segments, release_vm, 5)
            release = bytes(data[release_offset:release_offset + 5])
            assert release == b'node\0'
            region_offset, _ = map_vm(segments, page_base + page_start, pointer_vm + 8 - (page_base + page_start))
            chain_refs = [cite(data, fix_base, fix_base + 28, 'Selected dyld chained-fixups payload header, version zero and starts offset.'),
                cite(data, starts_base, starts_base + 4 + 4 * segment_count, 'dyld_chained_starts_in_image gives segment index mapping.'),
                cite(data, segment_info, segment_info + 22, 'Selected __DATA_CONST chain header: pointer format 2, 4096-byte pages and segment offset.'),
                cite(data, page_entry_offset, page_entry_offset + 2, 'Selected page-start entry identifies chain start used to prove release field membership.'),
                cite(data, region_offset, chain[-1]['fileOffset'] + 8, 'Bounded selected-page bytes support complete 229-pointer chain walk from declared start through release field.')]
            pointer_ref = cite(data, struct_offset + 16, struct_offset + 24, 'Release field is a format-2 chained rebase pointer, bind zero, target low36 0xf69f978, high8 zero, reserved zero, next stride two.')
            release_ref = cite(data, release_offset, release_offset + 5, 'Chained-pointer decoded release target contains exact null-terminated string node.')
            fixup_result = {'command': fixups, 'header': {'fixupsVersion': version, 'startsOffset': starts_delta,
                'importsOffset': imports_delta, 'symbolsOffset': strings_delta, 'importsCount': imports_count,
                'importsFormat': imports_format, 'symbolsFormat': strings_format},
                'startsInImageFileOffset': starts_base, 'segmentCount': segment_count,
                'segmentInfoOffsets': segment_offsets, 'selectedSegmentIndex': seg_index,
                'selectedSegmentInfoFileOffset': segment_info, 'selectedSegmentInfoBytes': info_size,
                'pageSize': page_size, 'pointerFormat': fmt, 'pointerFormatName': 'DYLD_CHAINED_PTR_64',
                'segmentVmOffset': segment_vm_offset, 'maxValidPointer': max_pointer, 'pageCount': page_count,
                'bytesAfterDeclaredPageStartArray': info_size - (22 + 2 * page_count),
                'bytesAfterDeclaredPageStartArrayMeaning': 'not interpreted; selected page uses a single direct start',
                'selectedPageIndex': page_index, 'selectedPageEntryFileOffset': page_entry_offset,
                'selectedPageStart': page_start, 'selectedPageUnslidVm': page_base,
                'chainWalkCount': len(chain), 'chainWalk': chain, 'mappingEvidenceIds': chain_refs,
                'releasePointerUnslidVm': pointer_vm, 'releasePointerFileOffset': struct_offset + 16,
                'encodedPointerUint64': encoded_pointer, 'encodedPointerHex': raw_struct[16:].hex(),
                'targetLow36': target_low, 'high8': high8, 'reserved': reserved, 'bind': bind,
                'nextStrideUnits': (encoded_pointer >> 51) & 0xfff, 'strideBytes': 4,
                'decodedUnslidVmAddress': release_vm, 'pointerEvidenceId': pointer_ref,
                'scope': 'Only selected page chain through this release field; not all dyld fixups or actual loaded-process pointers.'}
            version_data = {'mapping': struct_map, 'structureBytes': 24, 'rawHex': raw_struct.hex(),
                'structureEvidenceId': cite(data, struct_offset, struct_offset + 24, 'Directly returned static version structure: uint32 fields 24/19/0, four alignment bytes, eight-byte release chained pointer.'),
                'layout': [{'field': 'major', 'offset': 0, 'bytes': 4, 'type': 'uint32_t', 'value': major},
                    {'field': 'minor', 'offset': 4, 'bytes': 4, 'type': 'uint32_t', 'value': minor},
                    {'field': 'patch', 'offset': 8, 'bytes': 4, 'type': 'uint32_t', 'value': patch},
                    {'field': 'alignmentPadding', 'offset': 12, 'bytes': 4, 'value': alignment},
                    {'field': 'release', 'offset': 16, 'bytes': 8, 'type': 'const char*', 'encoding': 'Mach-O DYLD_CHAINED_PTR_64 rebase'}],
                'major': major, 'minor': minor, 'patch': patch, 'release': release[:-1].decode(),
                'encodedVersion': f'{major}.{minor}.{patch}', 'releaseMapping': release_map,
                'releaseBytesIncludingNull': 5, 'releaseHex': release.hex(), 'releaseEvidenceId': release_ref,
                'structureLayoutBasis': 'Parent-reviewed official Node-API napi_get_node_version/napi_node_version schema, x86_64 uint32 and pointer layout; not an executed API result.'}
    tool_runs = []
    version_run, tool_version = capture('llvm-version', [str(OBJDUMP), '--version'], {'targetInput': False})
    tool_runs.append(version_run)
    bounded_run, disassembly = capture('napi-get-node-version', [str(OBJDUMP), '--disassemble',
        '--start-address=0x4b42f60', '--stop-address=0x4b42fc0', str(framework)],
        {'startUnslidVm': start, 'endUnslidVmExclusive': next_start, 'bodyBytes': 81, 'paddingBytes': 15})
    tool_runs.append(bounded_run)
    matches = re.findall(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )+)', disassembly, re.M)
    assert len(matches) == 20
    with framework.open('rb') as stream:
        for address, octets in matches:
            vm = int(address, 16)
            raw = bytes.fromhex(octets)
            file_at, _ = map_vm(segments, vm, len(raw))
            stream.seek(file_at)
            assert stream.read(len(raw)) == raw
    inputs = [baseline_path, inventory_path, old_result_path, old_manifest_path]
    record = {'baselineId': BASELINE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'selected-native-getter-static-version-confirmed; execution-and-traditional-ABI-unverified',
        'sourceInputs': [metadata(path) for path in inputs],
        'sourceArtifacts': [metadata(schema_path),
            metadata(ROOT / '.analysis-local/runtime-node-version-attempt-01/failure-record.json'),
            metadata(ROOT / '.analysis-local/runtime-node-version-attempt-01/producer-attempt.py'),
            metadata(ROOT / '.analysis-local/runtime-node-version-attempt-02/failure-record.json'),
            metadata(ROOT / '.analysis-local/runtime-node-version-attempt-02/producer-attempt.py')],
        'scripts': [metadata(Path(__file__).resolve())],
        'sourceBinary': {'sourcePath': SOURCE, 'runtimeCopyPath': str(framework.relative_to(ROOT)),
            'bytes': SIZE, 'sha256': HASH, 'inventoryPath': str(inventory_path.relative_to(ROOT)),
            'identityScope': 'Packaged Framework path version 155.0.8059.40 is not a Node/Electron release or ABI inference.'},
        'method': 'Exact actual nlist lookup, bounded full getter CFG, RIP direct data reference, declared chained-fixups page membership, local primary header decoding and fixed byte-span hashes.',
        'machO': {'header': header, 'segments': segments, 'symbolTable': symtab,
            'mappingEvidenceIds': refs, 'addressKind': 'unslid VM and file coordinates; process addresses not observed'},
        'getter': getter, 'versionStructure': version_data, 'releasePointerFixup': fixup_result,
        'toolVersion': tool_version.strip(), 'toolRuns': tool_runs,
        'schemaReferences': [{'url': 'https://nodejs.org/api/n-api.html#napi_get_node_version',
            'checkedAt': '2026-10-13', 'reviewedBy': 'root', 'sourceReview': 'Parent supplied reviewed official Node-API document schema; this subtask made no network request.',
            'externalPageReportedVersion': 'v26.11.1', 'externalSourceArchived': False,
            'layout': 'uint32_t major; uint32_t minor; uint32_t patch; const char* release;',
            'role': 'Structure/API meaning only; external document version is not target version. API output points to Node own static version info; no free required.'},
            {'url': 'https://raw.githubusercontent.com/nodejs/node/v24.19.0/src/node_api_types.h',
            'checkedAt': '2026-10-13', 'reviewedBy': 'root', 'externalTag': 'v24.19.0',
            'externalSourceArchived': False, 'lineStart': 38, 'lineEnd': 43,
            'layout': 'uint32_t major; uint32_t minor; uint32_t patch; const char* release;',
            'role': 'Fixed official Node tag header confirms field order/types; target values independently come from fixed Framework bytes, not this external tag.'},
            {'role': 'Local Apple SDK primary Mach-O chained-fixup format schema; host SDK is not claimed as target SDK.',
            'originalPath': str(APPLE_SCHEMA), 'resolvedOriginalPath': str(APPLE_SCHEMA.resolve()),
            'originalBytes': len(schema_bytes), 'originalSha256': sha(schema_bytes),
            'snapshot': metadata(schema_path), 'byteRanges': schema_ranges,
            'checkedAt': '2026-10-13', 'pointerFormat': 2, 'name': 'DYLD_CHAINED_PTR_64',
            'definition': 'target36/high8 8/reserved7/next12 with 4-byte stride/bind1; format2 target is VM address'}],
        'summary': {'newEvidenceCount': len(evidence), 'selectedSymbols': 2,
            'getterBodyBytes': 81, 'getterInstructionCount': 19, 'internalControlFlowEdges': 3,
            'versionStructureBytes': 24, 'releaseCStringBytes': 5, 'selectedChainPointerCount': 229,
            'encodedNodeVersion': '24.19.0', 'release': 'node'},
        'conclusions': {'selectedFrameworkNativeStaticVersion': '24.19.0', 'selectedFrameworkNativeStaticRelease': 'node',
            'directGetterToStructureBinding': 'confirmed', 'releaseFixupChainMembershipAndTarget': 'confirmed',
            'observedExecutedNodeVersion': 'unknown', 'actualElectronCompatibilityVersion': 'unknown',
            'nodeModuleVersion': 'unknown', 'nativeModulesAbi': 'unknown',
            'completeNativeCallerClosure': 'unknown', 'startupExecutionAndEnforcement': 'unknown'},
        'executionScope': {'targetPrograms': 0, 'probes': 0, 'appStarts': 0, 'fuseModifications': 0,
            'credentialReads': 0, 'networkRequests': 0, 'newModelTasks': 0,
            'commandsAllowed': 'Only owned Python analysis and LLVM bounded file-data disassembly/version'},
        'limitations': ['Static structure referenced by selected getter is not an observed executed version query.',
            'No traditional NODE_MODULE_VERSION value is directly proven by this getter, its version structure or release string; no NAPI/Chromium/dependency inference.',
            'External Node document v26.11.1 and host Apple SDK metadata are schema references, not target runtime identities.',
            'Only two exact target symbol names selected; no full native caller closure or whole-library raw string scan.',
            'Only declared selected-page fixup chain through release field decoded; all other fixups and actual loader effects unverified.',
            'Earlier frozen runtime-fuse/native-accessor outputs preserved; this new observation does not rewrite their time-scoped unknowns.',
            'Earlier archive/unpacked declaration contradictions remain unexplained.']}
    (WORK / 'evidence.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in evidence))
    write_json(WORK / 'runtime-node-version.json', record)
    (WORK / 'summary.md').write_text(
        '# 选定原生 Node 版本静态结构\n\n'
        '固定 Framework 中 `_napi_get_node_version` 的完整有界函数直接引用静态结构，'
        '其 `major/minor/patch` 为 **24.19.0**，`release` 为 **node**。这是所选原生接口所引用的静态发行版本结构；未执行查询。\n\n'
        f'- 基线：`{BASELINE}`；Framework `{SIZE:,}` 字节，SHA256 `{HASH}`。\n'
        '- 实际符号 VM/file `0x4b42f60`；完整主体 81 字节、19 条指令、3 条内部控制流边；'
        '15 字节 NOP 后下一实际符号位于 `0x4b42fc0`。函数在 RDI/RSI 非空路径把结构指针写到 RSI。\n'
        '- RIP-relative LEA 直接指向结构 VM/file `0x111d3720`，24 字节：3 个 uint32、4 字节对齐、8 字节 release 字段。\n'
        '- release 字段原始 `78f9690f00001000` 是 chained rebase 编码，不是裸指针。'
        '实际 `LC_DYLD_CHAINED_FIXUPS` 声明 format 2；只沿选定页的 229 个指针到该字段，'
        '确认 bind/reserved/high8 为 0、target VM/file `0xf69f978`，读取 `node\\0`。\n'
        f'- 新增 {len(evidence)} 条原始字节证据，符号、映射、函数、结构、选定链和字符串均记录完整 span/hash；'
        '原始有限 LLVM 输出、命令、退出码、工具身份均保留。\n\n'
        '结构含义采用父级已核对的[官方 Node-API 文档](https://nodejs.org/api/n-api.html#napi_get_node_version)；'
        '该外部网页自报 v26.11.1，不是目标版本；[官方固定 tag 结构头](https://raw.githubusercontent.com/nodejs/node/v24.19.0/src/node_api_types.h)'
        '也已由父级核对字段顺序/类型，目标值独立来自二进制。指针格式依据本机 Apple 官方 SDK `fixup-chains.h` 原字节快照；'
        '主机 SDK 版本也不作为目标 SDK 结论。\n\n'
        '目标、探针、app、网络、凭证与模型均未执行或读取；旧冻结产物保持原字节。'
        '实际执行后的 Node 版本、Electron 兼容发行版、`NODE_MODULE_VERSION`、传统原生 ABI、完整调用点闭包与启动执行效果仍未知。'
        '不从 Node-API=10、Chromium、开发依赖或路径版本推算传统 ABI；不解释既有 archive/unpacked 声明矛盾。\n')
    print(json.dumps({'status': 'generated', 'output': str(WORK.relative_to(ROOT)),
        'newEvidenceCount': len(evidence), 'summary': record['summary'],
        'main': metadata(WORK / 'runtime-node-version.json'), 'evidence': metadata(WORK / 'evidence.jsonl')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
