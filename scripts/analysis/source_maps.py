#!/usr/bin/env python3
"""Scan all frozen JS/CSS/JSON and map files, distinguishing real comments.

Uses Babel on every JavaScript containing a sourceMappingURL marker. Source
map URLs are resolved only within the frozen input; no URL or app is executed.
"""
import argparse
import base64
import collections
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import unquote_to_bytes, urlsplit


def digest(data):
    return hashlib.sha256(data).hexdigest()


def css_comments(data):
    comments = []
    position = 0
    while position < len(data):
        byte = data[position]
        if byte in (34, 39):
            quote = byte
            position += 1
            while position < len(data):
                if data[position] == 92:
                    position += 2
                elif data[position] == quote:
                    position += 1
                    break
                else:
                    position += 1
        elif data[position:position + 2] == b'/*':
            end = data.find(b'*/', position + 2)
            if end == -1:
                break
            comments.append({'byteStart': position, 'byteEnd': end + 2, 'type': 'CommentBlock'})
            position = end + 2
        else:
            position += 1
    return comments


def map_shape(value):
    return isinstance(value, dict) and value.get('version') == 3 and (isinstance(value.get('sources'), list) and isinstance(value.get('mappings'), str) or isinstance(value.get('sections'), list))


def map_details(value):
    sources = value.get('sources', [])
    contents = value.get('sourcesContent')
    sections = value.get('sections', [])
    section_maps = [map_details(item['map']) for item in sections if isinstance(item, dict) and map_shape(item.get('map'))]
    present = sum(isinstance(content, str) for content in contents) if isinstance(contents, list) else 0
    result = {'version': value.get('version'), 'file': value.get('file'), 'sourceRoot': value.get('sourceRoot'),
              'sources': sources, 'sourceCount': len(sources), 'hasSourcesContent': isinstance(contents, list),
              'sourcesContentEntries': len(contents) if isinstance(contents, list) else 0, 'nonNullSourcesContentEntries': present,
              'sourceContentBytes': sum(len(content.encode()) for content in contents if isinstance(content, str)) if isinstance(contents, list) else 0,
              'sourceContentHashes': [digest(content.encode()) if isinstance(content, str) else None for content in contents] if isinstance(contents, list) else [],
              'sectionCount': len(sections), 'inlineSections': section_maps,
              'unresolvedSectionUrls': [item['url'] for item in sections if isinstance(item, dict) and 'url' in item]}
    result['totalSourceCount'] = len(sources) + sum(item['totalSourceCount'] for item in section_maps)
    result['totalNonNullSourcesContentEntries'] = present + sum(item['totalNonNullSourcesContentEntries'] for item in section_maps)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('--babel-parser', required=True)
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    baseline_path = Path(args.baseline).resolve()
    baseline = json.loads(baseline_path.read_text())
    inventory_path = baseline_path.parent / 'files.json'
    inventory = json.loads(inventory_path.read_text())
    output = Path(args.output).resolve()
    work = Path(args.work).resolve()
    output.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    extensions = {'.js', '.mjs', '.cjs', '.css', '.json', '.map'}
    records = []
    known = {}
    excluded = collections.Counter()
    errors = []
    evidence = []
    scanned = []
    markers = []
    markers_by_path = collections.defaultdict(list)
    json_error_paths = set()
    directive_candidates = []
    json_maps = []
    map_files = []
    marker_pattern = re.compile(rb'sourceMappingURL')
    directive_pattern = re.compile(rb'^[ \t]*[#@][ \t]*sourceMappingURL[ \t]*=[ \t]*(\S+?)[ \t]*(?:\r?\n|$)')

    def ev(record, locator, claim, confidence='confirmed', method='static-source-map-scan'):
        identifier = 'sm-e-' + str(len(evidence) + 1).zfill(5)
        evidence.append({'id': identifier, 'baselineId': baseline['baselineId'], 'claim': claim,
                         'sourcePath': record['sourcePath'], 'sourceHash': record['sha256'], 'locator': locator,
                         'method': method, 'confidence': confidence, 'verificationStatus': 'static-confirmed' if confidence == 'confirmed' else 'needs-verification'})
        return identifier

    for group, key, root in [('asar', 'archiveFiles', Path(baseline['extractedDirectory'])), ('disk', 'applicationFiles', Path(baseline['snapshotApplication']))]:
        for item in inventory[key]:
            relative = item.get('archivePath', item['sourcePath'])
            source_path = 'app.asar/' + relative if group == 'asar' else relative
            if group == 'disk' and '/app.asar.unpacked/' in relative:
                excluded['disk-asar-unpacked-duplicate'] += 1
                continue
            if not item.get('sha256'):
                excluded['symlink-or-non-file'] += 1
                continue
            record = {**item, 'sourcePath': source_path, 'relativePath': relative, 'group': group,
                      'physicalPath': str(root / relative), 'extension': Path(relative).suffix.lower()}
            known[source_path] = record
            if record['extension'] in extensions:
                records.append(record)

    for index, record in enumerate(records):
        try:
            data = Path(record['physicalPath']).read_bytes()
            if digest(data) != record['sha256']:
                raise ValueError('Frozen file hash no longer matches baseline')
        except (OSError, ValueError) as error:
            errors.append({'sourcePath': record['sourcePath'], 'error': str(error)})
            continue
        occurrences = list(marker_pattern.finditer(data))
        scanned.append({'sourcePath': record['sourcePath'], 'sourceHash': record['sha256'], 'bytes': len(data),
                        'extension': record['extension'], 'group': record['group'], 'rawMarkerCount': len(occurrences)})
        for match in occurrences:
            marker = {'sourcePath': record['sourcePath'], 'byteStart': match.start(), 'byteEnd': match.end(), 'classification': 'unclassified'}
            markers.append(marker)
            markers_by_path[record['sourcePath']].append(marker)
        if record['extension'] in ('.js', '.mjs', '.cjs') and occurrences:
            directive_candidates.append({key: record[key] for key in ('sourcePath', 'physicalPath', 'sha256')})
        if record['extension'] in ('.json', '.map'):
            try:
                parsed = json.loads(data)
            except ValueError as error:
                errors.append({'sourcePath': record['sourcePath'], 'error': 'JSON parse: ' + str(error), 'kind': 'json-parse-error'})
                json_error_paths.add(record['sourcePath'])
                continue
            def find_maps(value, pointer=''):
                if map_shape(value):
                    identifier = ev(record, {'jsonPointer': pointer or '/'}, 'JSON source map object exists')
                    json_maps.append({'sourcePath': record['sourcePath'], 'jsonPointer': pointer or '/', 'details': map_details(value), 'evidenceIds': [identifier]})
                    return
                if isinstance(value, dict):
                    for key, child in value.items(): find_maps(child, pointer + '/' + str(key).replace('~', '~0').replace('/', '~1'))
                elif isinstance(value, list):
                    for position, child in enumerate(value): find_maps(child, pointer + '/' + str(position))
            find_maps(parsed)
            if record['extension'] == '.map':
                map_files.append({'sourcePath': record['sourcePath'], 'sourceHash': record['sha256'], 'isSourceMap': map_shape(parsed)})
        if (index + 1) % 5000 == 0:
            print(json.dumps({'scanFiles': index + 1, 'total': len(records)}), flush=True)

    candidate_path = work / 'javascript-candidates.json'
    candidate_path.write_text(json.dumps(directive_candidates) + '\n')
    comment_path = work / 'javascript-comment-classification.jsonl'
    command = [args.node, '--max-old-space-size=4096', str(Path(__file__).with_name('source_map_comments.mjs')), str(candidate_path), str(comment_path), args.babel_parser]
    result = subprocess.run(command)
    if result.returncode:
        raise RuntimeError('Comment classifier failed; partial cache retained, no complete report written')
    comments_by_path = {item['sourcePath']: item for item in (json.loads(line) for line in comment_path.read_text().splitlines())}
    directives = []
    false_positives = []
    unresolved = []
    inline_maps = []
    parser_results = collections.Counter()
    for record in records:
        if record['sourcePath'] not in markers_by_path:
            continue
        data = Path(record['physicalPath']).read_bytes()
        own_markers = markers_by_path[record['sourcePath']]
        if record['extension'] in ('.json', '.map'):
            if record['sourcePath'] in json_error_paths:
                unresolved.append({'sourcePath': record['sourcePath'], 'status': 'unresolved-json-parse-failure', 'rawMarkerCount': len(own_markers)})
                for marker in own_markers: marker['classification'] = 'unresolved-json-parse-failure'
                continue
            for marker in own_markers:
                marker['classification'] = 'json-data-not-source-map-directive'
                false_positives.append({**marker, 'evidenceIds': [ev(record, {'byteStart': marker['byteStart'], 'byteEnd': marker['byteEnd']}, 'sourceMappingURL occurs in JSON data, not a JS/CSS directive comment')]})
            continue
        if record['extension'] == '.css':
            comments = css_comments(data)
            status = 'css-comment-lexed'
        else:
            info = comments_by_path[record['sourcePath']]
            status = info['status']
            parser_results[status] += 1
            comments = info['comments']
            if status == 'parse-failed':
                unresolved.append({'sourcePath': record['sourcePath'], 'parserErrors': info['errors'], 'rawMarkerCount': len(own_markers),
                                   'evidenceIds': [ev(record, {'byteStart': 0, 'byteEnd': len(data)}, 'Babel could not classify sourceMappingURL markers', 'unresolved')]})
                for marker in own_markers: marker['classification'] = 'unresolved-parser-failure'
                continue
        for comment in comments:
            content_start = comment['byteStart'] + 2
            content_end = comment['byteEnd'] - 2 if comment['type'] == 'CommentBlock' else comment['byteEnd']
            content = data[content_start:content_end]
            match = directive_pattern.match(content)
            for marker in own_markers:
                if comment['byteStart'] <= marker['byteStart'] < comment['byteEnd']:
                    marker['classification'] = 'confirmed-directive' if match else 'non-directive-comment-text'
            if not match:
                continue
            raw_url = match.group(1).decode(errors='replace')
            url = raw_url[:-2].rstrip() if raw_url.endswith('*/') else raw_url
            identifier = ev(record, {'byteStart': comment['byteStart'], 'byteEnd': comment['byteEnd']}, 'Actual sourceMappingURL directive comment: ' + (url[:200] if not url.startswith('data:') else 'inline data URL'), method='babel-comment-parser' if status != 'css-comment-lexed' else 'css-comment-lexer')
            item = {'sourcePath': record['sourcePath'], 'sourceHash': record['sha256'], 'locator': {'byteStart': comment['byteStart'], 'byteEnd': comment['byteEnd']},
                    'url': url if not url.startswith('data:') else 'data:[omitted; see urlSha256/byte locator]', 'urlSha256': digest(url.encode()),
                    'urlBytes': len(url.encode()), 'commentClassification': status, 'evidenceIds': [identifier]}
            if url.startswith('data:'):
                try:
                    header, encoded = url.split(',', 1)
                    decoded = base64.b64decode(encoded, validate=True) if ';base64' in header else unquote_to_bytes(encoded)
                    parsed = json.loads(decoded)
                    if not map_shape(parsed): raise ValueError('Decoded data URL is not a source map object')
                    item['resolution'] = 'inline-map-decoded'
                    inline_maps.append({'generatedSourcePath': record['sourcePath'], 'mapSha256': digest(decoded), 'mapBytes': len(decoded),
                                        'details': map_details(parsed), 'evidenceIds': [identifier]})
                except (ValueError, UnicodeError) as error:
                    item['resolution'] = 'inline-map-decode-failed'
                    item['error'] = str(error)
                    unresolved.append(item)
            else:
                parsed_url = urlsplit(url)
                if parsed_url.scheme or parsed_url.netloc:
                    item['resolution'] = 'external-url-not-fetched'
                    unresolved.append(item)
                else:
                    relative = posixpath.normpath(posixpath.join(posixpath.dirname(record['sourcePath']), unquote_to_bytes(parsed_url.path).decode(errors='replace')))
                    target = known.get(relative)
                    item['resolvedSourcePath'] = relative
                    item['resolution'] = 'frozen-map-found' if target else 'missing-from-frozen-input'
                    if target:
                        try:
                            parsed = json.loads(Path(target['physicalPath']).read_bytes())
                            item['mapDetails'] = map_details(parsed) if map_shape(parsed) else None
                            item['mapSourceHash'] = target['sha256']
                        except ValueError as error:
                            item['resolution'] = 'external-map-json-invalid'
                            item['error'] = str(error)
                            unresolved.append(item)
            directives.append(item)
        for marker in own_markers:
            if marker['classification'] in ('unclassified', 'non-directive-comment-text'):
                marker['classification'] = 'string-code-or-regex-not-directive-comment' if marker['classification'] == 'unclassified' else marker['classification']
                false_positives.append({**marker, 'evidenceIds': [ev(record, {'byteStart': marker['byteStart'], 'byteEnd': marker['byteEnd']}, 'sourceMappingURL marker is ' + marker['classification'], method='babel-comment-parser' if status != 'css-comment-lexed' else 'css-comment-lexer')]})

    summary = {'eligibleFiles': len(records), 'scannedFiles': len(scanned), 'readOrHashErrors': sum(item.get('kind') != 'json-parse-error' for item in errors),
               'jsonParseErrors': sum(item.get('kind') == 'json-parse-error' for item in errors),
               'byGroupAndExtension': dict(collections.Counter(item['group'] + ':' + item['extension'] for item in scanned)),
               'rawMarkerOccurrences': len(markers), 'rawMarkerFiles': len(set(item['sourcePath'] for item in markers)),
               'confirmedDirectiveComments': len(directives), 'falsePositiveOccurrences': len(false_positives),
               'unresolvedMarkerOccurrences': sum(item['classification'].startswith('unresolved-') for item in markers),
               'markerClassifications': dict(collections.Counter(item['classification'] for item in markers)),
               'javascriptCommentParsing': dict(parser_results), 'standaloneMapFiles': len(map_files), 'jsonSourceMapObjects': len(json_maps),
               'inlineDecodedMaps': len(inline_maps), 'directiveResolution': dict(collections.Counter(item['resolution'] for item in directives)),
               'sourcesContentMaps': sum(item['details']['totalNonNullSourcesContentEntries'] > 0 for item in inline_maps + json_maps),
               'sourcesContentEntries': sum(item['details']['totalNonNullSourcesContentEntries'] for item in inline_maps + json_maps),
               'excluded': dict(excluded)}
    report = {'baselineId': baseline['baselineId'], 'scope': 'All frozen ASAR and external JS/MJS/CJS/CSS/JSON/map files; ASAR-unpacked disk duplicates excluded',
              'inventory': {'sourcePath': str(inventory_path), 'sourceHash': digest(inventory_path.read_bytes())},
              'method': {'javascript': 'Babel comments from complete file parse', 'css': 'quote-aware CSS comment lexer', 'json': 'Complete JSON traversal for version-3 map objects',
                         'remoteUrls': 'Recorded only; not fetched', 'decodedSourceContents': 'Counts/hashes retained; third-party source text not copied into reports'},
              'tooling': {'babelParserEntry': str(Path(args.babel_parser).resolve()), 'babelParserEntrySha256': digest(Path(args.babel_parser).read_bytes()),
                          'node': args.node, 'commentClassifierCommand': command},
              'summary': summary, 'scannedFiles': scanned, 'directives': directives, 'inlineMaps': inline_maps, 'jsonMaps': json_maps,
              'standaloneMaps': map_files, 'falsePositives': false_positives, 'unresolved': unresolved, 'errors': errors,
              'limitations': ['Released-file source maps do not establish original repository build inputs or upstream modifications.',
                              'No map URLs outside the frozen inventory were downloaded.',
                              'Files outside the listed extensions and compressed archive contents are not scanned for embedded map directives.']}
    (output / 'source-maps.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (output / 'source-map-evidence.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in evidence))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
