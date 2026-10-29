"""Publish source-backed storage responsibilities; do not inspect live profiles."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
B = ROOT / 'analysis' / BASE
W = ROOT / '.analysis-local/storage-domain-map-work'
F = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
NOW = datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def pin(path):
    p = Path(path)
    if not p.is_absolute():
        p = B / p
    raw = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(raw), 'sha256': sha(raw)}


def reference(name, pointer):
    return {**pin(name), 'jsonPointer': pointer}


def publish(path, data):
    p = B / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as handle:
        handle.write(data)
    p.chmod(0o444)
    return pin(p)


def main():
    assert not (B / 'storage-domain-map-v1.json').exists()
    state_path = B / 'analysis-state.json'
    state = json.loads(state_path.read_text())
    for n in ['analysis-state.json', 'report.md', 'gaps.md']:
        with (W / (n + '.before')).open('xb') as handle:
            handle.write((B / n).read_bytes())
    input_names = ['global-state-storage-origin.json','global-state-storage-observations.json',
                   'main-persistence-policy.json','mode-persistence-receiver.json',
                   'shutdown-persistence.json','shutdown-persistence-observations.json',
                   'auth-boundary.json','host-state-provider-contracts.json',
                   'host-state-di-contracts.json','behavior-stop-restart.json',
                   'runtime-surface-disposition.json','browser-ownership-contracts.json',
                   'implementation-milestones-v9.json','feature-scope-v27.json',
                   'restoration-coverage-v18.json','feature-scope-v24-scenarios.json']
    input_pins = [pin(n) for n in input_names] + [pin(Path(__file__)), pin(ROOT / 'docs/reverse-engineering/analysis-plan.md')]
    units = []
    selections = []
    for name in ['source-selection.json','source-detail.json']:
        receipt = json.loads((W / name).read_text())
        for result in receipt['results']:
            for u in result['units']:
                raw = (F / u['sourcePath'].removeprefix('app.asar/')).read_bytes()
                span = u['byteRange']
                selected = raw[span['start']:span['endExclusive']]
                assert sha(raw) == u['sourceHash'] and sha(selected) == u['spanHash']
                assert selected == (ROOT / u['savedPath']).read_bytes()
                dest = 'raw/storage-domain-map/' + Path(u['savedPath']).name
                u['publishedSelection'] = publish(dest, selected)
                units.append(u)
            selections.append({k:v for k,v in result.items() if k != 'units'})
    lookup = {(Path(u['sourcePath']).name,u['label']):u for u in units}

    def unit(file, label):
        return copy.deepcopy(lookup[(file, label)])

    net = 'application-network-startup-CfAQmSYg.js'
    boot = 'bootstrap-CooIJpZm.js'
    startup = 'startup-requirements-C6B1x9gL.js'
    main_file = 'main-CqEoQDOU.js'
    src = 'src-BJv5Mk7n.js'
    specs = [
        ('SDMF-01', net, 'definition-ot-xr', '同步home解析器xr默认preferWsl为false；回退表达式为process.env.CODEX_HOME ?? path.join(os.homedir(),`.codex`)。该表达式不trim或resolve环境值，空字符串和相对值并未在此被拒绝。'),
        ('SDMF-02', net, 'definition-st-Sr', '异步执行home解析器Sr在win32且preferWsl为true时先await er()，无结果回退到同一CODEX_HOME/用户home表达式；WSL helper和实际返回值未执行。'),
        ('SDMF-03', boot, 'binding-gT', 'gT先以无参数o.ot()确定桌面home，再以该值构造globalState与config.toml settingsStore；runCodexInWsl和可用性确定后，另以o.st({preferWsl})求executionCodexHome。后者没有替换前两个构造路径。'),
        ('SDMF-04', boot, 'binding-oD', 'userData路径候选先trim CODEX_ELECTRON_USER_DATA_PATH并resolve；无覆盖时以appData、build flavor标签和可选agent run ID构造。该规则与CODEX_HOME解析规则不同。'),
        ('SDMF-05', boot, 'set-user-data', 'bootstrap的所选Program顶层调用将oD结果传入app.setPath(`userData`,...)；实际appData、flavor、环境和运行有效路径未读取。'),
        ('SDMF-06', startup, 'definition-l-ki', 'settingsStore的ki构造器保存filePath/globalState、读取ji(filePath)、规范化状态并准备旧设置迁移。set先更新内存与pendingWrites，再尝试persistPendingSettings；configClient为null时不提交后台写入。'),
        ('SDMF-07', startup, 'binding-ji', 'ji仅在文件存在时读取UTF8并解析TOML的desktop部分；错误日志后返回空对象。该选定reader没有文件写入。'),
        ('SDMF-08', main_file, 'settings-config-client-initialization', '所选settingsStore.initialize输入包含config及batchWriteConfigValues回调，回调调用捕获的pt.sendAppServerRequest(`config/batchWrite`,edits)。此调用结构不证明实际pt实例、配置层或最终文件路径。'),
        ('SDMF-09', startup, 'definition-l-ki', 'ki将pending迁移与写入快照转为desktop.<key>、mergeStrategy:replace的batch edits；确认成功后仅移除仍等于快照的pending值并调用Fi清理旧键，失败被记录且pending保留。initialize中配置已存在的项也可直接清理对应pending迁移并调用Fi，不要求一次新增写入。'),
        ('SDMF-10', startup, 'binding-Fi', 'Fi按descriptor.hostStorage.kind清理configuration/global-state旧键或electron persisted-atom对象成员；composerEnterBehavior另有旧项清理。具体descriptor/schema与Pi迁移取值未在本轮展开，不能按键名推定模式。'),
        ('SDMF-11', main_file, 'binding-AJe', 'AJe为基类提供的read/write适配使用globalState的thread assignments、projectless IDs及路径hint键；另可通过writeMembership回调写后台并更新host ID。这个本地副本没有在所选类中创建独立数据库。'),
        ('SDMF-12', src, 'export-binding-U0', 'AJe使用的i.r导出对应U0；U0.flush先等待pendingThreadWrites和pendingCatalogWrite结算，再await pendingWrite。这个方法不调用globalState.flush，等待队列和文件提交必须分开表述。'),
        ('SDMF-13', boot, 'binding-gT', 'gT在桌面home/sqlite下构造prod或带flavor后缀的codex-history-snapshots数据库名，await allSettled清理主文件、-wal、-shm、-journal。该清理不证明所有会话数据库位置或原生恢复机制。'),
        ('SDMF-14', main_file, 'binding-af', 'af按persist:codex-browser-前缀和encodeURIComponent(name)构造逻辑partition名；已保存app session合同使用app名称。实际磁盘session根仍由runtime/session provider决定。'),
        ('SDMF-15', main_file, 'binding-at', 'at按persist:codex-browser-app-route:前缀编码由两个输入以NUL连接的身份元组；该命名规则不能证明实际磁盘根、账号隔离或完整调用方集合。'),
    ]
    facts = []
    for fid, file, label, claim in specs:
        u = unit(file,label)
        facts.append({'id':fid,'baselineId':BASE,'claim':claim,'sourcePath':u['sourcePath'],
                      'sourceHash':u['sourceHash'],'locator':u['byteRange'],'spanHash':u['spanHash'],
                      'method':'static-code','confidence':'confirmed',
                      'verificationStatus':'selected-frozen-source-confirmed; effective-runtime-instance-and-root-unobserved'})
    # Preserve import/export and selected-call provenance for cross-file statements.
    joins = [
        {'id':'SDMJ-01','relationship':'gT o.ot -> application-network export ot -> xr',
         'units':[unit(boot,'binding-gT'),unit(boot,'binding-o'),unit(net,'export-ot'),unit(net,'definition-ot-xr')]},
        {'id':'SDMJ-02','relationship':'gT s.l -> startup-requirements export l -> ki',
         'units':[unit(boot,'binding-gT'),unit(boot,'binding-s'),unit(startup,'export-l'),unit(startup,'definition-l-ki')]},
        {'id':'SDMJ-03','relationship':'main AJe extends i.r -> src export r -> U0',
         'units':[unit(main_file,'binding-AJe'),unit(main_file,'binding-i'),unit(src,'export-r'),unit(src,'export-binding-U0')]},
        {'id':'SDMJ-04','relationship':'partition constructors use same Program rf/$e prefixes',
         'units':[unit(main_file,'binding-af'),unit(main_file,'binding-rf'),unit(main_file,'binding-at'),unit(main_file,'binding-$e')]},
    ]
    for j in joins:
        j['qualification'] = 'Selected Program declaration/export and call structure; no complete caller census or actual provider instance claim.'

    def old(name, key, indices):
        return [reference(name, f'/{key}/{i}') for i in indices]

    domains = []

    def domain(did, name, owner, root, writes, recovery, design, remaining, new_ids, prior):
        domains.append({'id':did,'name':name,'sourceAuthority':owner,'pathRule':root,
                        'writeBoundary':writes,'recoveryOrMigrationBoundary':recovery,
                        'maintenanceDecision':design,'exactRemainingPrerequisite':remaining,
                        'newSourceFactIds':new_ids,'savedContractRefs':prior,
                        'proposedFoundationTasks':['W03','W05','W06'],
                        'taskJoinQualification':'Shared implementation responsibility proposal; not a full per-feature consumer assignment.',
                        'effectiveRootObserved':False,'fullIsolationProven':False,'mode':'unknown; retained',
                        'confidence':'inferred'})

    domain('SDMD-01','Electron profile','bootstrap path policy -> runtime profile provider',
           'oD(env override or appData/build flavor/agent run ID); app.setPath(userData,...)',
           'runtime owns profile/session writes; source setter alone is not a write inventory',
           'profile migration and original-platform defaults unverified',
           '独立应用标识、显式profile根和runtime配置分别管理；不依靠改目录名称证明全部隔离。',
           '选定runtime的有效userData/session路径、helper配置和迁移规则；不读取个人profile。',
           ['SDMF-04','SDMF-05'],old('auth-boundary.json','evidence',[8,9,10]))
    domain('SDMD-02','主进程globalState','gT/uT -> startup Vr -> receiver scopedState',
           'desktopCodexHome/.codex-global-state.json; .bak and same-directory temp',
           'set/update/delete memory-first queues; updateAndPersist main-write-before-memory; flush versus flushOrThrow differ',
           'missing main skips backup; corrupt main may load backup; no selected fsync or main/backup transaction',
           '状态接口、调度队列和JSON后端分离；广播、内存完成和文件完成使用不同合同。',
           '实际有效home、schema/defaults与目标runtime/平台耐久性；旧9个隔离文件场景不证明整个客户端。',
           ['SDMF-01','SDMF-03'],old('global-state-storage-origin.json','records',[5,6,11,13,15,16,23,27,29,30]))
    domain('SDMD-03','桌面设置与旧键迁移','ki local read -> initialized configClient -> app-server config/batchWrite',
           'startup reads desktopCodexHome/config.toml desktop section; effective backend configuration layer/path unresolved',
           'memory/pending maps -> batch desktop.<key> replace edits; failure logs and retains pending; backend acknowledgement is not disk-durability proof',
           'existing authoritative config can retire legacy keys; otherwise acknowledged migration retires still-matching pending values; Fi clears former global-state/atom fields',
           '保留本地启动读取器、设置状态/迁移协调器和后台配置gateway三个边界；不生成直接覆盖TOML的替代写入器。',
           'pt/config provider实际实例与配置层、descriptor/schema/Pi迁移规则、backend写入/失败/恢复语义。',
           ['SDMF-03','SDMF-06','SDMF-07','SDMF-08','SDMF-09','SDMF-10'],old('shutdown-persistence.json','records',[0,6,7]))
    domain('SDMD-04','thread memberships与projectless路径提示','AJe local globalState adapter + U0 queue + optional backend membership callback',
           'globalState key families; backend callback may own additional state, whose effective storage is unresolved',
           'local assignments/projectless/hints through globalState.set/update; membership callback has a separate queue and completion contract',
           'U0.flush waits pending catalog/thread/local writes; does not flush the globalState file; shutdown calls its distinct interface',
           '维护membership队列/后台桥和本地状态适配两个职责；不为flush名称凭空新增数据库，也不省略全局状态文件排空。',
           'writeThreadAssignment/getThreadStartProjectId实际provider、跨后台/本地失败原子性、调用完成与磁盘完成的集成时序。',
           ['SDMF-11','SDMF-12'],old('shutdown-persistence.json','records',[18,19]))
    domain('SDMD-05','history-snapshot启动清理','gT cleanup -> filesystem',
           'desktopCodexHome/sqlite/codex-history-snapshots[[-flavor]].db and three SQLite sidecars',
           'startup awaits allSettled rm(force:true) for the four selected names; no cleanup executed in this analysis',
           'snapshot producer and relation to other thread databases not established',
           '将启动清理作为显式迁移/维护步骤，保留精确文件族；禁止把它扩大到所有SQLite或会话记录。',
           'snapshot生产者、用途、flavor输入和清理后果；迁移测试只可用自有合成文件。',
           ['SDMF-03','SDMF-13'],[])
    domain('SDMD-06','app-server任务与执行状态','selected host transport/CLI/daemon/websocket -> native/backend storage',
           'executionCodexHome is separately resolved; inherited env, WSL, remote websocket or daemon can select another effective authority',
           'backend owns thread/turn state; desktop globalState is not proof of backend file ownership',
           'saved real restart restored an interrupted turn; automatic continuation and internal commit/recovery mechanism unproven',
           'backend运行配置必须携带host/transport/executable/home身份；本地桌面home和后端有效home分别验收。',
           '实际transport/executable、服务有效根/数据库、WSL helper、SIGTERM恢复与任务状态提交规则。',
           ['SDMF-01','SDMF-02','SDMF-03'],old('auth-boundary.json','evidence',[4,5,6,7])+[reference('behavior-stop-restart.json','/outcome')])
    domain('SDMD-07','认证与secret storage','desktop auth request -> app-server/native file/keyring/secret provider',
           'auth.json/keyring and keychain access group are frozen capability/metadata clues; active provider and namespace unresolved',
           'getAuthStatus RPC does not reveal credential storage selection; shell import/child env/secret gate can affect backend identity',
           'credential migration and secret/file/keyring precedence unverified; distinct CODEX_HOME/userData does not establish anonymous isolation',
           '认证仓库、平台密钥命名空间和后台身份作为独立依赖合同；不得将文件目录覆盖当作凭据隔离开关。',
           '可控自有认证环境、明确provider/namespace和迁移选择规则；未读取auth文件、keychain或凭据。',
           [],old('auth-boundary.json','evidence',[0,1,11,14,15,16,17,18,19]))
    domain('SDMD-08','浏览器持久partition','main partition constructors -> runtime session provider',
           'persist:codex-browser- + encoded name; persist:codex-browser-app-route: + encoded two-input NUL tuple',
           'session/browser services own backing data; logical partition names are not filesystem paths',
           'browser profile migration, cookies/IndexedDB/service state and credential linkage not proven by view ownership probes',
           '独立runtime profile和partition身份一起管理；保留app/route身份及permission处理，不复制原浏览器profile。',
           '实际session storage根、所有partition调用方、账号/host绑定与底层服务迁移；privileged settings仍需runtime provider。',
           ['SDMF-14','SDMF-15'],old('runtime-surface-disposition.json','facts',[15])+[reference('browser-ownership-contracts.json','/implementationDecision')])
    domain('SDMD-09','renderer persisted atoms与窗口标签页','renderer bridge -> main atom policy -> globalState object',
           'electron-persisted-atom-state with thread-browser-tabs-v1:/thread-tab-routes-v1: subkeys; not automatically renderer localStorage',
           'owner/filter/cache acceptance and record merging precede main memory set; broadcast can precede file completion',
           'reset/delete/snapshot rules and migration differ; window-local delivery filters are not credential or filesystem isolation',
           'renderer镜像、IPC策略和main状态后端分开；保留primary owner、删除编码和窗口过滤。',
           '实际store/provider实例、MODE初始化/送达和schema比较器；不以键名决定ChatGPT剥离。',
           [],old('main-persistence-policy.json','records',[0,16,17,18,19,20])+old('mode-persistence-receiver.json','records',[0,1,2,3]))
    domain('SDMD-10','共享host对象镜像','hXe sharedObjectRepository -> wee object/Set subscribers',
           'selected main in-memory object and shallow snapshots; no disk path established',
           'set undefined deletes; other values assign then synchronously notify',
           'reconstruction/bootstrap from real providers required; no durable-write contract follows from shared-object snapshot',
           '将此域保留为内存发布仓库；持久化由各真实owner另行承担，不重复保存整个镜像。',
           '完整对象owner/重建顺序和实际provider；不得由一次快照声称可重启恢复。',
           [],old('host-state-provider-contracts.json','facts',[19,20])+old('host-state-di-contracts.json','facts',[0]))
    domain('SDMD-11','退出、日志与tracing排空','quit coordinator -> independent state/settings/backend/log providers',
           'globalState, settingsStore, membership queue, tracing and logger each retain own authority; log paths unresolved here',
           'first allSettled group precedes limited context cleanup; logger finally-flush is not globalState.flush',
           'skip-drain omits settingsStore.flush; synchronous errors can truncate cleanup; neither 5s context timeout nor SIGTERM proves full durable drain',
           '退出协调器按provider记录等待/超时/失败，区分正常退出、强停和断电；不以一个flush标签代表全部域。',
           '真实Electron事件、目标平台helper/native、各provider提交与异常退出行为；既有17个替身场景不作产品通过。',
           [],old('shutdown-persistence.json','records',[6,7,8,9,11,16,17,18,19]))

    mapping = {
        'schemaVersion':1,'baselineId':BASE,'recordedAtUtc':NOW,
        'scope':'Eleven bounded storage responsibility domains from saved contracts plus selected source. Not a complete product storage census or verified effective-root inventory.',
        'sourceFacts':facts,'sourceJoins':joins,'domains':domains,'sourceSelections':units,'analysisPasses':selections,
        'newEngineeringDecisions':[
            'Separate desktop home, execution home and Electron profile inputs; do not collapse them into one appData option.',
            'Separate initial TOML read from app-server configuration mutation and acknowledgement-driven migration cleanup.',
            'Membership local state is layered on globalState while backend/queue completion remains distinct from file flush.',
            'Retain exact startup history-snapshot cleanup family; no blanket SQLite or thread-data migration.',
            'Treat browser partition identity, native credential authority and runtime profile as separate isolation gates.',
        ],
        'existingBehaviorEvidence':[
            {'ref':reference('global-state-storage-observations.json',''),'scope':'9 isolated real-file cases under Node22; schemas/defaults/comparator substituted or unused; no original store/runtime parity.'},
            {'ref':reference('shutdown-persistence-observations.json',''),'scope':'17 substituted event/timer cases; no native, real IO or original app shutdown.'},
            {'ref':reference('behavior-stop-restart.json','/outcome'),'scope':'Saved authorized real stop/restart outcome; interrupted turn restored; not automatic continued execution or proof of an internal storage path.'},
        ],
        'remainingCoverage':[
            'Effective appData/userData/desktop home/execution home and provider identity require an owned runtime observation; no live personal directories were inspected.',
            'WSL home helper, settings descriptor/schema migration, backend native storage and credential selection remain explicit source/provider boundaries.',
            'Plugin/cache/download/update-resume/automation/workspace and remote account-service storage have not received a complete per-store ownership census in this map. Do not count their feature definitions as resolved storage.',
            'No product-wide storage denominator or complete isolation, migration, failure recovery or durability proof is claimed.',
        ],
        'proposedImplementationPaths':[
            'packages/storage-contracts/src/roots.ts','apps/desktop/src/main/persistence/global-state.ts',
            'apps/desktop/src/main/settings/desktop-settings-store.ts','packages/backend-adapter/src/configuration.ts',
            'apps/desktop/src/main/projects/thread-memberships.ts','packages/runtime-adapter/src/profile-and-sessions.ts',
            'packages/backend-adapter/src/auth-storage.ts','apps/desktop/src/main/lifecycle/quit-coordinator.ts',
        ],
        'pathQualification':'Inferred maintenance boundaries, not recovered original paths, added logical-owner records or generated implementation.',
        'inputPins':input_pins,
        'analysisTools':[pin(W/'inspect_storage_boundaries.cjs'),pin(W/'inspect_storage_detail.cjs')],
        'sourceReceiptPins':[pin(W/'source-selection.json'),pin(W/'source-detail.json')],
        'counts':{'boundedResponsibilityDomains':len(domains),'newStaticSourceFacts':len(facts),
                  'selectedSourceUnits':len(units),'selectedSourceBytes':sum(u['bytes'] for u in units),
                  'sourceBindingJoins':len(joins),'fullProgramParsePasses':len(selections),
                  'distinctProgramsParsed':len({x['file'] for x in selections}),
                  'newReaRuns':0,'newRuntimeObservations':0,'newModelSubmissions':0,'newClientLaunches':0,
                  'personalFilesOrCredentialsRead':0,'newProductScenarioPasses':0,'newClientImplementation':0},
        'currentProductScope':{'features':373,'taskGroups':48,'unexecutedSpecifications':1216},
        'nextInternalAction':{'issueId':'SD-06','question':'将现有37个逻辑owner的责任、环境、模式、来源、接口、共享状态、副作用、依赖与拟议路径对照原计划，补齐明确字段与未决边界。',
                              'closure':'以37个既有owner为固定范围；共享来源与历史438发布文件分开，引用现有合同，不新造原工程模块或功能通过项。',
                              'authorization':'保存/冻结证据与自有分析脚本；无新增模型/客户端或个人数据操作。'},
        'completeStorageDenominatorEstablished':False,'fullStorageIsolationProven':False,'fullAnalysisCompleted':False,
    }
    result = publish('storage-domain-map-v1.json',encoded(mapping))
    journal = publish('storage-domain-map-v1-evidence.jsonl',b''.join((json.dumps(x,ensure_ascii=False)+'\n').encode() for x in facts))
    lines = ['# 数据存储职责与隔离边界','',
             '本轮形成11个有边界的数据域映射，并新增15条冻结源码事实。它说明路径输入、写入与恢复责任；尚未建立完整产品存储分母，也未读取运行中的个人目录或凭据。','',
             '桌面Codex home、后台执行home和Electron userData必须作为三个输入。前两者虽有共同回退表达式，执行home还可能经WSL分流；userData覆盖则会trim并resolve。环境、平台及运行返回值仍未观察。','',
             'settingsStore启动读取config.toml的desktop部分，初始化后由config/batchWrite后台接口写入。迁移清理既可由服务配置已存在触发，也可在迁移写入确认后触发。不能替换为简单本地TOML写入器。','',
             'thread assignments本地副本使用globalState，队列/后台写入另有职责；其flush只等待队列，不等于globalState文件flush。启动另会清理指定history-snapshot数据库及三个sidecar，不能扩大为会话数据库统一清理。','',
             '|数据域|路径/权威来源|维护决定|','|---|---|---|']
    for d in domains:
        lines.append(f"|{d['id']} {d['name']}|{d['pathRule']}|{d['maintenanceDecision']}|")
    lines += ['', '## 行为证据及限制','',
              '沿用已有9个隔离文件场景、17个退出替身场景及已授权停止/重启的真实记录；这些各有范围，不能合计为全域隔离或持久化通过。真实重启恢复interrupted任务不证明自动续跑，也不证明内部数据库位置。', '',
              '认证、secret/keyring、远程服务和浏览器session各有独立权威来源。CODEX_HOME/userData不同不足以证明凭据隔离；逻辑partition名不等于磁盘根。', '',
              '本图仍缺完整plugin/cache/download/update-resume/automation/workspace及远端账户服务的逐store盘点；WSL helper、设置schema/迁移、实际provider和有效根等具体缺口见每域。SD-05整体保持开放。', '',
              '下一内部项为SD-06：将已有37个逻辑owner规范成计划要求的模块字段。功能373、任务48、未执行规格1216不变；本轮无客户端启动、模型调用或新的行为通过项。', '',
              '[结构化映射](storage-domain-map-v1.json)、[源码事实](storage-domain-map-v1-evidence.jsonl)。拟议维护路径不是原目录或已生成客户端代码。', '']
    summary = publish('storage-domain-map-v1.md','\n'.join(lines).encode())
    overlay = {'result':result,'summary':summary,'evidence':journal,'counts':mapping['counts'],
               'qualification':'Bounded static responsibility/path and saved-behavior map; effective roots, complete storage census and full isolation remain unproven.',
               'fullAnalysisCompleted':False}
    state['storageDomainMap'] = copy.deepcopy(overlay)
    state['stageDecisions']['storageDomainOverlay'] = copy.deepcopy(overlay)
    state['stageDecisions']['nextAction'] = mapping['nextInternalAction']
    state['pending'][4] = 'SD-05: 已发布11域职责/路径/恢复映射，补齐home解析、config后台写入/迁移、membership队列及snapshot清理的15条源码事实。实际有效根、认证/native provider、部分store完整盘点与异常恢复仍未证明，不宣称全域隔离。'
    state['updatedAtUtc'] = NOW
    assert not state['fullAnalysisCompleted'] and state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
    state_path.write_bytes(encoded(state))
    first = '当前[数据存储职责映射](storage-domain-map-v1.md)覆盖11个有限域，新增15条源码事实：桌面home、执行home和profile分列；设置经后台写入，membership队列与globalState落盘分列，snapshot清理保留精确文件族。有效根、认证/native provider与完整store盘点仍待核实。下一内部项为SD-06既有37逻辑owner字段规范；373功能、48任务、1216未执行规格保持，完整分析未完成。'
    for n in ['report.md','gaps.md']:
        p=B/n
        _,tail=p.read_text().split('\n\n',1)
        p.write_text(first+'\n\n'+tail)
    print(json.dumps({'published':overlay,'sourceFiles':sorted({x['file'] for x in selections})},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
