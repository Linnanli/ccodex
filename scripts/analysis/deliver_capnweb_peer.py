"""Attach the completed independent review without modifying its reviewed candidate."""
import json
from pathlib import Path

from deliver_frozen_metadata import BASELINE, WORKSPACE, OUT, encode, pin, require, write_new

LOCAL = WORKSPACE / '.analysis-local/capnweb-upstream-candidate-peer-work'


def main():
    raw = (OUT / 'capnweb-upstream-candidate.json').read_bytes()
    require(pin(raw)['sha256'] == '149d1f988fe9e3bdee2f7ea7057b9180a04b44e0523bdce2db48852256f21075', 'reviewed candidate changed')
    review_raw = (LOCAL / 'review.json').read_bytes()
    require(pin(review_raw)['sha256'] == '0cb69a9885731e5b19871af98f948c6639d6fada17e73360e5b919c4e27ed392', 'peer revision changed')
    review = json.loads(review_raw)
    require(review['baselineId'] == BASELINE and review['checkCount'] == 334 and review['errors'] == [], 'peer did not pass')
    require(review['denominators']['records'] == 14 and review['denominators']['memberShapes'] == 18, 'peer scope changed')
    names = ['review.json', 'review.md', 'attempt-03/review.py', 'attempt-03/runner.py',
        'attempt-03/stdout.txt', 'attempt-03/stderr.txt', 'attempt-03/receipt.json',
        'attempt-01/receipt.json', 'attempt-02/receipt.json']
    inputs = {}
    for name in names:
        p = LOCAL / name
        require(not p.is_symlink() and p.stat().st_mode & 0o777 == 0o444, 'selected peer metadata not frozen')
        inputs[name] = p.read_bytes()
    receipts = [json.loads(inputs[n].rstrip(b'\\n')) for n in
        ['attempt-01/receipt.json', 'attempt-02/receipt.json', 'attempt-03/receipt.json']]
    require([r['exitCode'] for r in receipts] == [1, 1, 0], 'actual peer attempt history changed')
    copies = []
    for name, data in inputs.items():
        target = Path('raw/capnweb-upstream-candidate/independent-review') / name
        write_new(OUT / target, data)
        copies.append({'original': str(LOCAL / name), 'published': target.as_posix(), **pin(data)})
    for name, source in [('capnweb-upstream-candidate-peer-review.json', 'review.json'),
                         ('capnweb-upstream-candidate-peer-review.md', 'review.md')]:
        write_new(OUT / name, inputs[source])
        copies.append({'original': str(LOCAL / source), 'published': name, **pin(inputs[source])})
    result = {'schemaVersion': 1, 'baselineId': BASELINE, 'reviewedCandidate': {'path': 'capnweb-upstream-candidate.json', **pin(raw)},
        'independentReview': {'path': 'capnweb-upstream-candidate-peer-review.json', **pin(review_raw), 'checks': 334, 'errors': []},
        'actualPeerAttemptExitCodes': [1, 1, 0], 'copies': copies,
        'scope': 'Independent saved-metadata review only. Archive SRI is a saved author observation, not independently recomputed by this peer.',
        'producerPendingStatusPreserved': True, 'installedVersion': 'unknown', 'fullEquivalence': 'unknown',
        'modifiedStatus': 'unknown', 'runtimeRunsAdded': 0, 'globalRecordsAdded': 0}
    write_new(OUT / 'capnweb-upstream-candidate-review-provenance.json', encode(result))
    print(json.dumps({'status': 'independent-review-delivered', 'checks': 334, 'copies': len(copies), 'runtimeRunsAdded': 0}))


if __name__ == '__main__':
    main()
