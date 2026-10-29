"""Reconcile frozen saved artifacts. Never read/parse/evaluate original target source."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib,json

OUT=Path('/Users/nallylin/Documents/code/ccodex/.analysis-local/request-entry-reconciliation-work')
BASE='analysis/codex-26.1007.30912-c5b273322a83'
receipts=json.loads((OUT/'input-receipts.json').read_text())
pins={x['originRelativePath']:x for x in receipts['inputs']}
def sha(b): return hashlib.sha256(b).hexdigest()
def read(relative):
    pin=pins[relative];raw=Path(pin['snapshotPath']).read_bytes()
    assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],relative
    return raw
def load(relative): return json.loads(read(relative))
def witness(relative,pointer):
    p=pins[relative]
    return {'artifactPath':p['originPath'],'snapshotPath':p['snapshotPath'],'artifactSha256':p['sha256'],'jsonPointer':pointer}
def pointer(obj,where):
    for bit in where.strip('/').split('/') if where else []:
        key=bit.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

wr_path=BASE+'/request-wrapper-contracts.json';led_path=BASE+'/functional-entry-ledger.json'
wrapper=load(wr_path);ledger=load(led_path)
wr_journal=BASE+'/request-wrapper-evidence.jsonl';raw=read(wr_journal);lines=raw.splitlines(keepends=True)
evidence={}
for i,line in enumerate(lines):
    item=json.loads(line);assert item['id'] not in evidence
    evidence[item['id']]={'item':item,'line':i+1,'rawLineSha256':sha(line)}
assert len(evidence)==wrapper['evidence']['recordCount']==1787
assert len(wrapper['calls'])==375 and len(wrapper['candidateLinks'])==337
assert len(ledger['entries'])==968 and len(ledger['supportNodes'])==176 and len(ledger['deferredCandidates'])==337
assert wrapper['baselineId']==ledger['baselineId']

manifest=load(next(x['path'] for x in ledger['sourceArtifacts'] if x['artifactId']=='manifest'))
inventory={x['sourcePath']:x for x in manifest['archiveFiles']}
source_receipts=[]
for file in wrapper['files']:
    src=inventory[file['sourcePath']]
    assert file['sourceHash']==src['sha256'] and file['bytes']==src['bytes']
    source_receipts.append({**file,'pinBasis':'saved wrapper file inventory equals saved frozen archive inventory',
       'inventoryWitness':witness(next(x['path'] for x in ledger['sourceArtifacts'] if x['artifactId']=='manifest'),'/archiveFiles/'+str(manifest['archiveFiles'].index(src))),
       'targetSourceBytesRead':False,'targetSpanBytesRehashed':False})
assert len(source_receipts)==37 and sum(x['astSendRequestCount'] for x in source_receipts)==375

old_records={}
for category,key in [('entries','entryId'),('supportNodes','nodeId'),('deferredCandidates','candidateId')]:
    for i,row in enumerate(ledger[category]):
        old_records[(category,i)]={'row':row,'id':row[key],'pointer':'/'+category+'/'+str(i)}
old_ids=defaultdict(list)
for (category,i),record in old_records.items():
    row=record['row']
    for e_id in set(row.get('evidenceIds',[])+([row['primaryEvidenceId']] if row.get('primaryEvidenceId') else [])):
        old_ids[e_id].append({'category':category,'index':i,'recordId':record['id'],'pointer':record['pointer']})
deferred_by_id={x['sourceCoordinates']['evidenceId']:(i,x) for i,x in enumerate(ledger['deferredCandidates'])}
assert len(deferred_by_id)==337
links=defaultdict(list)
for i,link in enumerate(wrapper['candidateLinks']):links[link['astCallEvidenceId']].append((i,link))
assert len(links)==337 and all(len(v)==1 for v in links.values())
assert {x['publishedEvidenceId'] for x in wrapper['candidateLinks']}==set(deferred_by_id)

def coords(obj,path=''):
    if isinstance(obj,dict):
        if obj.get('sourcePath') and obj.get('sourceHash') and isinstance(obj.get('byteRange'),dict):
            yield path,obj
        for k,v in obj.items(): yield from coords(v,path+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):yield from coords(v,path+'/'+str(i))
coordinate_index=defaultdict(list)
coordinate_count=0
for (category,i),record in old_records.items():
    for relative,coordinate in coords(record['row']):
        rng=coordinate['byteRange']
        if rng.get('kind')!='byte-range' or not isinstance(rng.get('start'),int) or not isinstance(rng.get('endExclusive'),int):continue
        coordinate_count+=1
        coordinate_index[(coordinate['sourcePath'],coordinate['sourceHash'])].append({
            'category':category,'recordId':record['id'],'recordIndex':i,'coordinatePointer':record['pointer']+relative,
            'primaryCoordinate':relative=='/sourceCoordinates','coordinate':coordinate})

results=[];journal=[];refresh=[];unaligned=[];counts=Counter();spatial=Counter()
for i,call in enumerate(wrapper['calls']):
    call_id=call['callEvidenceId'];saved=evidence[call_id];ast=saved['item'];loc=ast['locator']
    assert call['sourcePath']==ast['sourcePath'] and call['sourceHash']==ast['sourceHash']
    inv=inventory[call['sourcePath']];assert call['sourceHash']==inv['sha256']
    assert 0<=loc['start']<loc['endExclusive']<=inv['bytes']
    a,z=loc['start'],loc['endExclusive'];exact_primary=[];exact_secondary=[];contexts=[]
    for hit in coordinate_index[(call['sourcePath'],call['sourceHash'])]:
        c=hit['coordinate'];b,y=c['byteRange']['start'],c['byteRange']['endExclusive']
        if a==b and z==y:
            relation='same-complete-saved-byte-range'
        elif b<=a and z<=y:
            relation='wrapper-call-contained-in-old-record-coordinate'
        elif a<=b and y<=z:
            relation='old-record-coordinate-contained-in-wrapper-call'
        else:continue
        item={'recordCategory':hit['category'],'recordId':hit['recordId'],'primaryCoordinate':hit['primaryCoordinate'],
              'relation':relation,'witness':witness(led_path,hit['coordinatePointer']),
              'oldCoordinates':c,'identityClaim':False,'featureAssociation':False}
        if relation=='same-complete-saved-byte-range':
            (exact_primary if hit['primaryCoordinate'] else exact_secondary).append(item)
        else:contexts.append(item)
    direct_id_membership=old_ids.get(call_id,[])
    association=None
    if call_id in links:
        li,link=links[call_id][0];di,old=deferred_by_id[link['publishedEvidenceId']];coordinate=old['sourceCoordinates'];old_range=coordinate['byteRange']
        assert coordinate['sourcePath']==call['sourcePath'] and coordinate['sourceHash']==call['sourceHash']
        assert a<=old_range['start']<old_range['endExclusive']<=z
        assert (a,z)!=(old_range['start'],old_range['endExclusive'])
        assert link['sourcePath']==call['sourcePath'] and link['kind']==call['kind'] and link['contractId']==call['contractId']
        # Label equality is a metadata assertion after ID/range association, never a join key.
        assert old['displayLabel']==call['method']==link['method']
        rpc=load(old['sourceArtifact']['path']);rpc_row=pointer(rpc,old['sourceArtifact']['jsonPointer'])
        assert rpc_row['evidenceId']==link['publishedEvidenceId'] and rpc_row['sourcePath']==call['sourcePath'] and rpc_row['callForm']=='sendRequest'
        ref=next(x for x in ledger['evidenceReferences'] if x['evidenceId']==link['publishedEvidenceId'])
        j_path=ref['evidenceJournal']['path'];j_lines=read(j_path).splitlines(keepends=True);j_line=j_lines[ref['evidenceJournal']['line']-1];j_item=json.loads(j_line)
        assert j_item['id']==link['publishedEvidenceId'] and j_item['sourcePath']==call['sourcePath'] and j_item['sourceHash']==call['sourceHash']
        assert j_item['locator']==old_range
        association={'status':'registered-in-old-deferred-denominator','recordCategory':'deferredCandidates','recordId':old['candidateId'],
             'groupId':old['groupId'],'oldEvidenceId':link['publishedEvidenceId'],'relation':'old-lexical-span-strictly-contained-in-unique-wrapper-complete-call',
             'oldCoordinates':coordinate,'explicitLinkWitness':witness(wr_path,'/candidateLinks/'+str(li)),
             'ledgerWitness':witness(led_path,'/deferredCandidates/'+str(di)),
             'oldSourceArtifactWitness':witness(old['sourceArtifact']['path'],old['sourceArtifact']['jsonPointer']),
             'oldJournalWitness':{**witness(j_path,''),'line':ref['evidenceJournal']['line'],'rawLineSha256':sha(j_line)},
             'sameSpan':False,'operationIdentity':False,'featureIdentity':False,'mode':'unknown','runtime':'unknown'}
        verdict='registered-deferred-via-explicit-saved-link';counts['registeredDeferred']+=1
        if call['kind']!='unresolved':
            refresh.append({'callEvidenceId':call_id,'ledgerCandidateId':old['candidateId'],'ledgerPointer':'/deferredCandidates/'+str(di),
                 'savedWrapperKind':call['kind'],'savedWrapperContractId':call['contractId'],
                 'action':'review annotation freshness only; preserve deferred role and no feature/protocol/runtime promotion'})
    elif exact_primary:
        verdict='exact-old-row-primary-source-range';counts['exactPrimaryRegistered']+=1
    elif direct_id_membership:
        verdict='old-record-direct-evidence-id-membership';counts['directIdRegistered']+=1
    else:
        verdict='not-aligned-to-old-callsite-registration';counts['notAligned']+=1
        reason=('Dynamic/conditional AST call is outside the old literal lexical-callsite denominator; no saved explicit old candidate link or exact primary coordinate/ID match.'
            if call['methodKind']=='dynamic-or-conditional' else
            'Literal AST call has no saved explicit old candidate link or exact primary coordinate/ID match. Saved artifact scope difference does not prove omission; method spelling is not used for identity.')
        unaligned.append({'callEvidenceId':call_id,'wrapperPointer':'/calls/'+str(i),'sourcePath':call['sourcePath'],'sourceHash':call['sourceHash'],
             'byteRange':loc,'methodKind':call['methodKind'],'methodDisplayOnly':call['method'],'savedWrapperKind':call['kind'],
             'reason':reason,'proposedAction':'candidate reconciliation review; no automatic ledger insertion or new feature claim',
             'confirmedOmission':False})
    spatial['samePrimaryRanges']+=len(exact_primary);spatial['sameSecondaryRanges']+=len(exact_secondary);spatial['scopeContextRelationships']+=len(contexts)
    result={'candidateIndex':i,'callEvidenceId':call_id,'wrapperWitness':witness(wr_path,'/calls/'+str(i)),
        'sourcePath':call['sourcePath'],'sourceHash':call['sourceHash'],'completeCallRange':loc,'spanSha256':ast['spanSha256'],
        'spanVerification':'retained prior evidence hash; original target bytes not rehashed in this batch',
        'methodKind':call['methodKind'],'methodDisplayOnly':call['method'],'wrapperClassification':call['kind'],'wrapperContractId':call['contractId'],
        'registrationStatus':verdict,'deferredAssociation':association,'exactPrimaryRangeMatches':exact_primary,
        'exactSecondaryRangeMatches':exact_secondary,'directEvidenceIdMembership':direct_id_membership,'savedScopeContexts':contexts,
        'scopeContextMeaning':'Spatial provenance only; containment does not register the wrapper call or prove same operation/feature.',
        'unresolvedIdentity':verdict=='not-aligned-to-old-callsite-registration','confirmedOmission':False,'featureId':None,'mode':'unknown','runtime':'unknown'}
    results.append(result)
    journal.append({'id':'REQUEST-ENTRY-RECONCILIATION-'+str(i+1).zfill(5),'baselineId':wrapper['baselineId'],
       'method':'frozen-artifact-reconciliation','confidence':'confirmed','claimScope':'Saved artifact identity/coordinates/link reconciliation only; no new original-source/runtime observation',
       'verificationStatus':'artifact-pins-and-record-association-checked; original-target-source-not-read',
       'callEvidenceId':call_id,'sourcePath':call['sourcePath'],'sourceHash':call['sourceHash'],'locator':loc,
       'retainedSpanSha256':ast['spanSha256'],'wrapperWitness':result['wrapperWitness'],
       'callJournalWitness':{**witness(wr_journal,''),'line':saved['line'],'rawLineSha256':saved['rawLineSha256']},
       'registrationStatus':verdict,'deferredAssociation':association,'mainJsonPointer':'/candidates/'+str(i)})

denominator={'wrapperCompleteASTCalls':375,'wrapperSingleLiteral':353,'wrapperDynamicOrConditional':22,
    'wrapperSelectedParsedFiles':37,'oldLedgerEntries':968,'oldLedgerPrimaryEntries':868,'oldLedgerAuxiliaryEntries':100,
    'oldDeferredLiteralWrapperRows':337,'oldSupportNodes':176,'oldDirectAppServerCallCandidates':91,
    'featureCensusDenominator':'unknown','wholeClientCoverageClaimed':False}
assert Counter(x['methodKind'] for x in results)=={'single-literal':353,'dynamic-or-conditional':22}
assert counts['registeredDeferred']==337 and counts['notAligned']==38
assert len(refresh)==95
summary={'denominators':denominator,'registrationCounts':dict(counts),'spatialCounts':dict(spatial),
   'registeredDeferredBySavedWrapperKind':dict(Counter(x['wrapperClassification'] for x in results if x['deferredAssociation'])),
   'notAlignedByMethodKind':dict(Counter(x['methodKind'] for x in unaligned)),
   'annotationReviewCandidates':len(refresh),'confirmedOmissions':0,'newFeaturesClaimed':0,
   'scopeCoordinateOccurrencesScanned':coordinate_count,'sourceReceiptCount':len(source_receipts)}
main={'schemaVersion':1,'baselineId':wrapper['baselineId'],'archiveSha256':wrapper['archiveSha256'],
      'status':'bounded-saved-artifact-reconciliation-complete; feature-census-and-runtime-unknown',
      'method':'Exact saved IDs, pinned artifact pointers, qualified source hashes and explicit original byte-range relations. Names are display-only metadata.',
      'inputs':receipts['inputs'],'inputReceiptsFile':'input-receipts.json','sourceReceiptsFile':'source-receipts.json',
      'legacyValidation':{'ledger':witness('.analysis-local/entry-ledger-work/validation.json',''),
          'wrapperStandaloneValidation':receipts['wrapperStandaloneValidation'],'wrapperStandaloneManifest':receipts['wrapperStandaloneManifest'],
          'wrapperEmbeddedEvidencePin':wrapper['evidence'],'currentPublicationWrapperInclusion':'not-claimed; current run does not separately list wrapper main'},
      'scanScope':{'ledgerRecordCounts':{'entries':968,'supportNodes':176,'deferredCandidates':337},
          'coordinates':'All saved sourcePath/sourceHash/byteRange coordinate objects recursively within those records; exact primary and secondary ranges distinguished.',
          'evidenceIdentityMembership':'Direct primaryEvidenceId/evidenceIds membership in each saved row; no name-based joins.',
          'originalTargetSourceRead':False,'targetSourceSpanRehashed':False},
      'summary':summary,'candidates':results,'notAlignedCandidatesForReview':unaligned,
      'existingDeferredAnnotationReviewCandidates':refresh,'confirmedOmissionCandidates':[],
      'unknowns':['No alignment is not proof of absence from broader implementation or of an omitted feature.',
          'Source containment is spatial provenance; it is not same span or shared operation identity.',
          'Saved wrapper receiver classification does not establish app-server protocol membership, mode, server reachability or feature success.',
          'Ledger feature-census denominator remains unknown; no new feature total or completeness claim.',
          'Only saved artifact coordinates were checked; original target source/span hashes were not freshly verified.'],
      'journalFile':'journal.jsonl','targetSourceRead':False,'targetExecuted':False,'cliExecuted':False,'uiUsed':False,'modelInvoked':False,'networkUsed':False}
(OUT/'source-receipts.json').write_text(json.dumps(source_receipts,ensure_ascii=False,indent=2)+'\n')
(OUT/'reconciliation.json').write_text(json.dumps(main,ensure_ascii=False,indent=2)+'\n')
(OUT/'journal.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in journal))
(OUT/'summary.md').write_text('''# AC-02 request entry reconciliation

仅对保存产物做范围对齐：375 个完整 AST wrapper call = 353 literal + 22 dynamic/conditional。旧台账的 968 entry、337 deferred 和 176 support 是不同角色的分母；337 deferred 来源是旧 literal 词法候选，不是整个客户端功能总数。

337 个 wrapper call 通过已保存 candidateLink 的 FEATURE ID、精确 artifact pin/JSON pointer、相同 sourcePath/hash 和唯一范围包含关系，对应全部 337 个旧 deferred。旧词法范围严格位于完整 AST call 内，337 个匹配均不属于 same span，不能由此推导同一操作或功能身份。方法/名称仅作一致性检查，从未作为身份键。

剩余 38 个 AST call（16 literal、22 dynamic）没有已保存的旧候选关联或完整主坐标/直接 evidence ID 对齐证据，逐条列于 notAlignedCandidatesForReview。记录为“未对齐”，不自动判作未登记或漏项。台账的所有记录下保存坐标也逐一检查，并把外围包含关系留作空间范围证据；它们不能替代调用登记或功能关联。已证实漏项清单为空；全功能分母继续 unknown。

已对齐的 337 项中，95 项保存 wrapper 分类（5 extension connection、66 host-manager selector、1 resolver facade、23 manager facade），242 项仍 unresolved。95 项只列为旧 deferred 注释复核候选，不更改角色、不升级协议/feature/mode/runtime，也不修改任何旧账本。

所有输入保存在 inputs，27 个 input receipt 含旧 ledger 的 14 份 sourceArtifacts pin；37 份源码 receipt 仅核对已保存 wrapper/files 与 frozen inventory 元数据，没有读取原始目标源码或重哈希目标 span。本批不执行目标、CLI、UI、网络或模型。旧 ledger 独立 validation/manifest 已保存；未找到独立 wrapper validation/manifest，不借命名或未列 wrapper 的发布 run 宣称覆盖。历史审计 snapshot 按实际 hash 独立记录。

独立核验结果和最终产品 pins 写于 validation.json，实际分析脚本、stdout/stderr 和 exit receipt 保留于 attempts/v1。新增 journal 每个候选一行，仅记录 artifact reconciliation；所有 original-source/runtime 结论维持旧范围。
''')
print(json.dumps(summary,ensure_ascii=False))
