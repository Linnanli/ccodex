"""Independent artifact receipt/pointer/range validation. No original target access."""
from pathlib import Path
from collections import Counter
import hashlib,json
OUT=Path('/Users/nallylin/Documents/code/ccodex/.analysis-local/request-entry-reconciliation-work')
BASE='analysis/codex-26.1007.30912-c5b273322a83'
checks=0;errors=[]
def check(value,label):
    global checks
    checks+=1
    if not value:errors.append(label)
def digest(raw):return hashlib.sha256(raw).hexdigest()
receipt=json.loads((OUT/'input-receipts.json').read_text())
sources={}
for x in receipt['inputs']:
    raw=Path(x['snapshotPath']).read_bytes();original=Path(x['originPath']).read_bytes()
    check(digest(raw)==x['sha256'] and len(raw)==x['bytes'],'snapshot pin '+x['originRelativePath'])
    check(raw==original,'saved origin unchanged '+x['originRelativePath'])
    check(x['originalTargetSourceRead'] is False,'artifact-only receipt')
    sources[x['originRelativePath']]=raw
def load(name):return json.loads(sources[name])
def resolve(obj,path):
    for bit in path[1:].split('/') if path else []:
        bit=bit.replace('~1','/').replace('~0','~');obj=obj[int(bit)] if isinstance(obj,list) else obj[bit]
    return obj
by_origin={x['originPath']:x for x in receipt['inputs']}
def witness(x):
    r=by_origin[x['artifactPath']]
    check(x['artifactSha256']==r['sha256'] and x['snapshotPath']==r['snapshotPath'],'witness artifact pin')
    parsed=json.loads(sources[r['originRelativePath']]) if x['jsonPointer'] else None
    return resolve(parsed,x['jsonPointer']) if x['jsonPointer'] else None
wrapper=load(BASE+'/request-wrapper-contracts.json');ledger=load(BASE+'/functional-entry-ledger.json')
main=json.loads((OUT/'reconciliation.json').read_text());journal=[json.loads(s) for s in (OUT/'journal.jsonl').read_text().splitlines()]
check(main['baselineId']==ledger['baselineId']==wrapper['baselineId'],'baseline identity')
check(len(main['candidates'])==len(journal)==len(wrapper['calls'])==375,'375 complete candidates and journal')
check(len(set(x['id'] for x in journal))==375,'journal unique IDs')
check(len(ledger['entries'])==968 and len(ledger['deferredCandidates'])==337 and len(ledger['supportNodes'])==176,'independent legacy denominators')
check(Counter(x['methodKind'] for x in wrapper['calls'])=={'single-literal':353,'dynamic-or-conditional':22},'independent AST denominator')
for x in ledger['sourceArtifacts']:
    raw=sources[x['path']];check(digest(raw)==x['sha256'] and len(raw)==x['bytes'],'14 ledger source pins')
check(len(ledger['sourceArtifacts'])==receipt['ledgerSourceArtifactsVerified']==14,'14 source denominator')
old_validation=load('.analysis-local/entry-ledger-work/validation.json')
check(old_validation['ledgerSha256']==digest(sources[BASE+'/functional-entry-ledger.json']),'old independent ledger pin')
check(old_validation['targetCodeReadParsedExecuted'] is False and old_validation['spanBytesRehashed'] is False,'old validation scope retained')
check('not-located' in main['legacyValidation']['wrapperStandaloneValidation'] and 'not-claimed' in main['legacyValidation']['currentPublicationWrapperInclusion'],'wrapper validation/run limitations')

wr_raw=sources[BASE+'/request-wrapper-evidence.jsonl'];wr_lines=wr_raw.splitlines(keepends=True)
wr_e={json.loads(raw)['id']:(i+1,raw,json.loads(raw)) for i,raw in enumerate(wr_lines)}
check(len(wr_e)==1787 and digest(wr_raw)==wrapper['evidence']['sha256'],'saved wrapper journal pin/count')
link_by_call={x['astCallEvidenceId']:(i,x) for i,x in enumerate(wrapper['candidateLinks'])}
old_deferred={x['sourceCoordinates']['evidenceId']:(i,x) for i,x in enumerate(ledger['deferredCandidates'])}
check(len(link_by_call)==337 and {x['publishedEvidenceId'] for x in wrapper['candidateLinks']}==set(old_deferred),'legacy/link bijection IDs')
record_counts=Counter();same_span=0;linked_old=set()
for i,candidate in enumerate(main['candidates']):
    call=wrapper['calls'][i];note=journal[i]
    check(candidate['candidateIndex']==i and candidate['callEvidenceId']==call['callEvidenceId']==note['callEvidenceId'],'candidate index/ID')
    check(witness(candidate['wrapperWitness'])==call,'exact wrapper JSON pointer')
    line,raw,e=wr_e[call['callEvidenceId']]
    check((candidate['sourcePath'],candidate['sourceHash'],candidate['completeCallRange'],candidate['spanSha256'])==
          (e['sourcePath'],e['sourceHash'],e['locator'],e['spanSha256']),'retained source locator/hash')
    check((note['sourcePath'],note['sourceHash'],note['locator'],note['retainedSpanSha256'])==
          (e['sourcePath'],e['sourceHash'],e['locator'],e['spanSha256']),'journal retained locator')
    check(note['callJournalWitness']['line']==line and note['callJournalWitness']['rawLineSha256']==digest(raw),'exact wrapper journal line')
    check(note['mainJsonPointer']=='/candidates/'+str(i) and note['registrationStatus']==candidate['registrationStatus'],'journal main pointer/status')
    check(candidate['methodKind']==call['methodKind'] and candidate['methodDisplayOnly']==call['method'],'metadata only method')
    check(candidate['mode']==candidate['runtime']=='unknown' and candidate['featureId'] is None and candidate['confirmedOmission'] is False,'unknown runtime/feature/omission')
    record_counts[candidate['registrationStatus']]+=1
    if call['callEvidenceId'] in link_by_call:
        li,link=link_by_call[call['callEvidenceId']];di,old=old_deferred[link['publishedEvidenceId']];assoc=candidate['deferredAssociation']
        check(assoc is not None and assoc['recordId']==old['candidateId'],'registered deferred exact record')
        check(witness(assoc['explicitLinkWitness'])==link and witness(assoc['ledgerWitness'])==old,'old link/ledger pointer')
        rpc=witness(assoc['oldSourceArtifactWitness']);check(rpc['evidenceId']==link['publishedEvidenceId'],'old source JSON pointer ID')
        old_coord=old['sourceCoordinates'];rng=old_coord['byteRange'];full=e['locator']
        check(old_coord['sourcePath']==e['sourcePath'] and old_coord['sourceHash']==e['sourceHash'],'qualified same source')
        check(full['start']<=rng['start']<rng['endExclusive']<=full['endExclusive'],'old lexical range inside full call')
        same_span+=int(full==rng);linked_old.add(link['publishedEvidenceId'])
        check(assoc['sameSpan'] is False and assoc['operationIdentity'] is False and assoc['featureIdentity'] is False,'no containment identity promotion')
        jw=assoc['oldJournalWitness'];r=by_origin[jw['artifactPath']];old_line=sources[r['originRelativePath']].splitlines(keepends=True)[jw['line']-1];old_ev=json.loads(old_line)
        check(digest(old_line)==jw['rawLineSha256'] and old_ev['id']==link['publishedEvidenceId'],'old exact journal row pin/ID')
        check(old_ev['sourcePath']==e['sourcePath'] and old_ev['sourceHash']==e['sourceHash'] and old_ev['locator']==rng,'old journal coordinates')
        check(note['deferredAssociation']==assoc,'journal exact association')
    else:
        check(candidate['deferredAssociation'] is None and candidate['registrationStatus']=='not-aligned-to-old-callsite-registration','unaligned remains unaligned')
        check(candidate['exactPrimaryRangeMatches']==[] and candidate['exactSecondaryRangeMatches']==[] and candidate['directEvidenceIdMembership']==[],'no exact registered witness claimed')
    for context in candidate['savedScopeContexts']:
        check(witness(context['witness'])==context['oldCoordinates'],'scope context pointer')
        check(context['identityClaim'] is False and context['featureAssociation'] is False,'scope containment is not identity')
check(same_span==0 and len(linked_old)==337,'337 unique strict containments and zero same spans')
check(record_counts=={'registered-deferred-via-explicit-saved-link':337,'not-aligned-to-old-callsite-registration':38},'independent final registration counts')
check(Counter(x['methodKind'] for x in main['notAlignedCandidatesForReview'])=={'single-literal':16,'dynamic-or-conditional':22},'unaligned 16/22 denominator')
check(len(main['existingDeferredAnnotationReviewCandidates'])==95 and len(main['confirmedOmissionCandidates'])==0,'95 annotation reviews and zero proved omissions')
check(main['summary']['spatialCounts']=={'samePrimaryRanges':0,'sameSecondaryRanges':0,'scopeContextRelationships':337},'spatial result counts')
check(main['summary']['denominators']['featureCensusDenominator']=='unknown' and main['summary']['confirmedOmissions']==main['summary']['newFeaturesClaimed']==0,'no feature/omission census upgrade')
for flag in ['targetSourceRead','targetExecuted','cliExecuted','uiUsed','modelInvoked','networkUsed']:check(main[flag] is False,'static only '+flag)
src_receipts=json.loads((OUT/'source-receipts.json').read_text());check(len(src_receipts)==37,'37 source metadata receipts')
for x in src_receipts:
    item=witness(x['inventoryWitness']);check(x['sourcePath']==item['sourcePath'] and x['sourceHash']==item['sha256'] and x['bytes']==item['bytes'],'saved inventory source receipt')
    check(x['targetSourceBytesRead'] is False and x['targetSpanBytesRehashed'] is False,'source metadata no fresh bytes')
check(sum(x['astSendRequestCount'] for x in src_receipts)==375,'375 file AST sum')
attempt=json.loads((OUT/'attempts/v1/run.json').read_text());check(all(x['exitCode']==0 for x in attempt['runs']),'actual attempted commands passed')
for x in attempt['files']:
    raw=Path(x['path']).read_bytes();check(digest(raw)==x['sha256'] and len(raw)==x['bytes'],'attempt source/output pin')
products=[]
for name in ['reconciliation.json','journal.jsonl','summary.md','source-receipts.json','input-receipts.json']:
    p=OUT/name;raw=p.read_bytes();products.append({'path':str(p),'bytes':len(raw),'sha256':digest(raw)})
result={'schemaVersion':1,'baselineId':main['baselineId'],'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,
   'method':'Independent saved-artifact bytes/hash, raw journal lines, ID bijections, exact JSON pointers and qualified byte-range checks; no original target source read',
   'inputCount':len(receipt['inputs']),'ledgerSourcePins':14,'wrapperCandidates':375,'registeredDeferred':337,'notAligned':38,
   'finalProducts':products,'originalTargetSourceRead':False,'targetSourceSpanRehashed':False,'targetExecuted':False,'cliExecuted':False,'uiUsed':False,'modelInvoked':False,'networkUsed':False}
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if not errors else 1)
