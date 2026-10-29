"""Read selected companion indices for report/state and publication inventories."""
import hashlib
import json
from pathlib import Path

PROFILES = [
    ('settingsConfigDispatch', 'settings-config-dispatch-delivery-provenance.json',
     ['settings-config-dispatch-summary.md', 'settings-config-dispatch-peer-review.md'],
     '40 scoped static records; no actual receiver or persistence claim',
     '[设置配置分发](settings-config-dispatch-summary.md)另保存40条记录。选定写入链经AW/Vf、fetch/cancel-fetch与renderer桥到主进程wrapper候选；同步dispatch抛错与Promise rejection分别记录。实际receiver、Ude/fetchHandler实例与写入持久化仍未知。'),
    ('terminalFeatureContracts', 'terminal-feature-contracts-delivery-provenance.json',
     ['terminal-feature-contracts-summary.md'],
     '35 scoped records and 43 saved units; runtime backend not established',
     '[终端操作与接口](terminal-feature-contracts-summary.md)另保存35条记录、43个完整单位及9组操作。panel传workspaceRoot给manager，manager本地绑定workspace并不把该字段传入host create；终端输入、附着、清理和错误分支保持各自条件。独立审查七处修正已落实，真实UI、native PTY与后端实例仍待验证。'),
    ('nodePtyModificationContracts', 'node-pty-modification-contracts-provenance.json',
     ['node-pty-modification-contracts-summary.md'],
     '18 records; package-only independent review, client window author-only',
     '[node-pty修改与第一方调用](node-pty-modification-contracts-summary.md)形成18条记录，两个Windows JS共有9处上游差异。部分kill分支返回等待链，pre-ready只排队；callback rejection回退与同步错误不同。维护方案须明确补丁依赖或等价adapter，不能凭同版本号认定普通包等价。四小package JS的独立100项审查与作者524项坐标检查分列，main caller没有独立语义审查，Windows/native实际行为仍未知。'),
    ('settingsFeatureOperationMapping', 'settings-feature-operation-mapping-provenance.json',
     ['settings-feature-operation-mapping-summary.md'],
     '38 author operation cards; no feature IDs assigned or source independence claimed',
     '[设置逐操作卡](settings-feature-operation-mapping-summary.md)保存General32项操作／展示与Agent6配置控件，共38张卡。选择、reset、可用性、导航与只读展示分别保留参数、状态及四类未执行验收场景；featureId均未分配。General映射作者参与过原源码catalog，未增加独立General源码语义验证。'),
    ('analysisRequirementsReaderReview', 'analysis-requirements-current-audit-reader-peer-provenance.json',
     ['analysis-requirements-current-audit-reader-peer-review.json'],
     '240 checks of the explicitly saved 16-input reader snapshot only',
     '[需求审计读者发布复核](analysis-requirements-current-audit-reader-peer-review.json)完成240项限定检查，核对16份读者输入、9项exact-copy声明和142个本地链接；不覆盖其固定快照之后的新合同发布。'),
    ('fileChangeViewContracts', 'file-change-view-contracts-delivery-provenance.json',
     ['file-change-view-contracts-summary.md', 'file-change-view-contracts-v2.json'],
     '30 inherited contracts with two metadata errata; original journal and delta remain separate',
     '[文件与变更查看](file-change-view-contracts-summary.md)发布30条合同的v2读者，原30行journal与两条fresh勘误分开。C012仅吞掉返回值的Promise rejection，同步错误进入外层catch；C018同步sender抛错与异步rejection的pending清理不同。旧peer保留two-findings状态，限定delta审查未证明实际bridge receiver、持久化或UI。'),
    ('functionalOperationReconciliation', 'functional-operation-reconciliation-provenance.json',
     ['functional-operation-reconciliation-summary.md', 'functional-operation-reconciliation.json'],
     '71 saved operation candidates, 282 confirmed and 29 inferred relations; full denominator unknown',
     '[功能操作与来源关联](functional-operation-reconciliation-summary.md)接上71个已保存操作候选与311条关联，其中282条confirmed、29条作者手选composer支持为inferred。38设置操作的不同表示没有重复计数，36功能组、968旧入口、337 deferred均保持。紧凑读者保留全部操作和关联，完整原件仍归档；完整功能分母、模式及运行验证未增加确认。'),
    ('modeTransitionOrigin', 'mode-transition-origin-provenance.json',
     ['mode-transition-origin-summary.md', 'mode-transition-origin.json'],
     '26 selected transition/initializer/resolver records; full mode domain and runtime unknown',
     '[模式切换来源](mode-transition-origin-summary.md)将Jo/jqn接到真实gS及所选初始化／lPt解析器。gS无值域校验，lPt两处透传persistedMode；7保存单位包含较大导入／导出声明，26合同不等于功能数量。独立解析88、元数据288、补身份23分列；e导入身份据新增保存metadata关闭，存储、运行及Codex归属仍未知，模式排除保持0。'),
    ('objcModificationContracts', 'objc-modification-contracts-provenance.json',
     ['objc-modification-contracts-summary.md', 'objc-modification-contracts.json'],
     '22 source contracts and 29 saved units; no binary provenance or runtime parity claim',
     '[objc-js源码边界](objc-modification-contracts-summary.md)确认所选9文件与官方1.5.0源码一致，差异在已发布native binary，不能据此决定维护源码补丁。22合同与29保存单位经有限独立审查，父278与native210分列；通知回调的正常路径、旧x86_64静态识别与ABI／构建来源缺口分别保留。15场景仍未执行，后续独立构建另批登记。'),
    ('settingsConfigReceiverOrigin', 'settings-config-receiver-origin-provenance.json',
     ['settings-config-receiver-origin-summary.md', 'settings-config-receiver-origin.json'],
     '25 selected source records close constructor injection; actual instance, persistence and nonproject RPC remain unknown',
     '[配置接收链来源](settings-config-receiver-origin-summary.md)保存同一构造函数中$L→Ude→MMe的真实源绑定，项目read-file/config-save处理先mkdir再writeFile。25条记录的三个措辞修正已通过有限独立审查；i.di／i.U实现另批调查，非项目KI/rpc、实际client、消息送达、I/O取消和落盘仍未知，不追溯升级原40条分发合同。'),
    ('objcIndependentBuild', 'objc-independent-build-provenance.json',
     ['objc-independent-build-summary.md', 'objc-independent-build.json'],
     'Local Node 22 x64 SDK recipe built and loaded once; no Owl/ARM, callback or full-client parity claim',
     '[objc-js独立构建](objc-independent-build-summary.md)实际原配方缺ffi.h失败，调整SDK include与系统-lffi后的候选配方构建成功。27个native源文件保持一致；Node22 x64唯一一次模块初始化／导出类型检查成功，未调用加载后的导出原生方法。独立65项metadata和82项日志检查分列；Owl Node24、ARM、ABI、回调及干净环境构建仍未知，旧15场景未升级。',
     {'runtimeRunsAdded': 1, 'runtimeScope': 'One independently built native module initialization and export-type smoke in local Node 22 x64.',
      'nativeModuleLoadsObserved': 1, 'nativeMethodsInvokedAfterModuleInit': 0,
      'originalClientRunsAdded': 0, 'deliveryRuntimeRunsAdded': 0}),
    ('modePreferenceStorageOrigin', 'mode-preference-storage-origin-provenance.json',
     ['mode-preference-storage-origin-summary.md', 'mode-preference-storage-origin.json'],
     '46 static records with required cleanup errata; actual MODE publisher, backend and persistence unknown',
     '[模式偏好与存储来源](mode-preference-storage-origin-summary.md)接上Fu/FJ、fd/Uk、Ch/_I及状态订阅链，保存46条记录与51单位。MODE两参数调用未启用可选coerce/delay；实际ARt publisher、provider/store和耐久后端仍未知。读者必须应用[清理勘误](raw/mode-preference-storage-origin/qualification/cleanup-errata.json)：IJ先调用c，正常返回后才调用l，setup抛错不保证清理旧注册。旧core/journal保留历史字节，附近generic localStorage未证明MODE join；18个真实场景未执行。'),
    ('settingsDiSource', 'settings-di-source-provenance.json',
     ['settings-di-source-summary.md', 'settings-di-source.json'],
     '16 frozen source records and three client delegations; later rX investigation is separate',
     '[文件di与U来源](settings-di-source-summary.md)将getter di接到原Program G，U接到lX。readFile使用第二client实参，mkdir/writeFile使用第三client实参；G不能直接认定为node:fs/promises或真实落盘。16条静态记录的19个保存坐标经有限独立审查，旧快照rX/run边界保持未知，新上下文调查另批登记。实际client、Response、source实参、取消及持久化仍未观察。'),
    ('modeBehaviorObservations', 'mode-behavior-observations-provenance.json',
     ['mode-behavior-observations-summary.md', 'mode-behavior-observations.json'],
     'One Node 22 command ran 20 isolated VM cases of three saved functions with memory substitutes',
     '[模式函数隔离观察](mode-behavior-observations-summary.md)实际执行3小函数共901字节的20个VM场景。gS首setter与FJ publisher同步throw阻止后续写入，返回rejected Promise的所选分支仍继续；lPt两处persisted分支保留对象身份。FJ可选coerce/delay只验证通用工厂，MODE调用未启用。结果只支持明确内存替身下的控制流，真实UI/provider/hI/ARt、存储和Codex归属仍未知；20场景共享一条命令，不升级旧静态合同。',
     {'runtimeRunsAdded': 1, 'runtimeScope': 'One isolated Node 22 VM observation command; synthetic memory providers and three saved functions only.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 20, 'savedFunctionsExecuted': 3,
      'originalClientRunsAdded': 0, 'originalStorageRunsAdded': 0, 'deliveryRuntimeRunsAdded': 0}),
    ('settingsSourceContextOrigin', 'settings-source-context-origin-provenance.json',
     ['settings-source-context-origin-summary.md', 'settings-source-context-origin.json'],
     'Nine source/documentation records; rX/k/node:async_hooks identity closed, actual runtime unobserved',
     '[source-context内置依赖来源](settings-source-context-origin-summary.md)将lX引用接到原Program rX零参数AsyncLocalStorage构造，再接到node:async_hooks require。9条记录、4小单位114字节含重叠，经作者298／独立metadata264／保存解析30分别检查。lX直接return run的条件合同与Node24.19官方候选文档分开；候选note未byte-pin网页，也不证明目标版本或当前实例。维护方案可使用运行时内置API的小型第一方adapter，native callback/run、context值和整fetch仍未知。'),
    ('sourceContextBehaviorObservations', 'source-context-behavior-observations-provenance.json',
     ['source-context-behavior-observations-summary.md', 'source-context-behavior-observations.json'],
     'One local Node22 command ran eight cases of the 36-byte saved wrapper with fresh builtin ALS candidates',
     '[source-context候选观察](source-context-behavior-observations-summary.md)实际执行36字节lX包装函数的8场景：同步返回／抛错、Promise身份与结算、嵌套恢复及异步继承。每场景使用新建本机Node22内置AsyncLocalStorage，未执行目标Node24或实际rX。8场景共用1条命令，不能据此证明真实client/source、native回调或完整fetch；原9／16／25静态快照保持。',
     {'runtimeRunsAdded': 1, 'runtimeScope': 'One local Node22 candidate observation command, using fresh builtin ALS instances and one saved 36-byte wrapper.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 8, 'savedFunctionsExecuted': 1,
      'executedSavedSourceBytes': 36, 'originalClientRunsAdded': 0, 'originalStorageRunsAdded': 0,
      'deliveryRuntimeRunsAdded': 0}),
    ('modePublisherInstantiation', 'mode-publisher-instantiation-provenance.json',
     ['mode-publisher-instantiation.md', 'mode-publisher-instantiation.json'],
     '23 static records, 21 confirmed/one inferred/one unresolved; 13 unexecuted scenarios',
     '[MODE publisher来源](mode-publisher-instantiation.md)在完整Rkc范围内将3处ARt第二参数接到同一局部s，经Ho/Hf/Vf/ire到条件renderer桥，并将bootstrap seed接到实际YRt localStorage读取。23记录中21 confirmed、1 inferred、1 unresolved；13场景未执行。Rkc真实bootstrap caller、gS实际store/provider、native接收器与耐久写入仍未知，模式归属及排除项保持。旧Storage46／MODE26字节不改，长查询零命中与历史检查失败按原限定保留。'),
    ('behaviorInterventions', 'behavior-interventions-provenance.json',
     ['behavior-interventions-summary.md', 'behavior-interventions.json'],
     'Two approved model-task budget: one submitted, one remaining; cancellation and running restart not tested',
     '[获授权行为样例进度](behavior-interventions-summary.md)记录本组授权2次已用1次、余1次。第一条原60秒观察超时，后续同thread/turn UI为completed，取消点击0；模型称无直接只读文件工具，不是独立文件访问审计。2026-10-23恢复冻结应用与CLI后，原项目名称及ID控件均0，第二条未提交；清理退出不算执行中介入，合成README同字节恢复不证明跨会话持久性。',
     {'modelSubmissionsObserved': 1, 'remainingModelSubmissions': 1,
      'newModelSubmissionsOn20261023': 0, 'cancelClicks': 0, 'stopRestartScenarioSignals': 0}),
    ('behaviorStopRestartOutcome', 'behavior-stop-restart-provenance.json',
     ['behavior-stop-restart-summary.md', 'behavior-stop-restart.json'],
     'Completed approved two-submission group; running SIGTERM/restart restored same turn as interrupted through an observed row',
     '[停止／重启实际结果](behavior-stop-restart-summary.md)补齐本组第2次提交，现2/2已用、余0。按后续明确授权对同一合成目录登记一次，新ID核实；原观察器遇额外dialog计数后停下，同一调用稍后完成，未点击信任或重试登记。停止前同thread/turn UI为inProgress，主PID及3个CLI退出；同profile新PID启动后，实际侧栏行绑定同thread/cwd，打开后原turn为interrupted。当前页首次样本未自动恢复，没有观察到继续执行；取消仍未测，不扩大为后端送达／耐久存储证明。',
     {'groupModelSubmissionsObserved': 2, 'remainingModelSubmissions': 0,
      'newModelSubmissionsOn20261023': 1, 'scenarioStopSignals': 1, 'scenarioRestarts': 1,
      'actualTerminalStatus': 'interrupted'}),
    ('modePersistenceReceiver', 'mode-persistence-receiver-provenance.json',
     ['mode-persistence-receiver-summary.md', 'mode-persistence-receiver.json'],
     'Four selected complete ranges, 1235 bytes; 11 source facts and one inferred receiver relation; syntax checked only',
     '[主进程persisted-atom候选](mode-persistence-receiver-summary.md)从旧REA/AST坐标读取4个完整范围1235字节，形成11条来源事实与1条receiver关联推断。选定main分支接到MMe发送／更新方法；owner过滤、旧值广播、recordUpdate回退、delete/属性定义及set后广播分别保留。Node只作包装范围语法检查，没有执行目标代码或做新的独立绑定分析。TY/pR/hR、广播实现、actual globalState与耐久后端仍未知；维护路径仅inferred建议。'),
    ('mainPersistencePolicy', 'main-persistence-policy-provenance.json',
     ['main-persistence-policy-summary.md', 'main-persistence-policy.json'],
     'Eight bounded units, 2486 bytes; 20 static source facts and two inferred relations; no target execution or lexical binding closure',
     '[持久化键策略与广播](main-persistence-policy-summary.md)另保存8个完整范围2486字节、20条来源事实与2条推断。TY为两个标签页前缀；pR为特定缓存键的版本接纳，hR包含条件更新与容量裁剪。普通键或删除广播全部窗口，标签页键非删除只发来源窗口；删除／reset方法与set后广播顺序分别记录。13场景未执行；新范围仅作语法检查，原Program绑定、schema／比较器、窗口和存储实例及落盘仍未知。旧批次未知项保留历史语境，模式排除及全局分母不改。'),
    ('globalStateStorageOrigin', 'global-state-storage-origin-provenance.json',
     ['global-state-storage-origin-summary.md', 'global-state-storage-origin.json', 'global-state-storage-observations.json'],
     '37 static records join startup factory to receiver; one Node22 command observes nine isolated real-file scenarios of 13 saved units',
     '[globalState构造与文件写入](global-state-storage-origin-summary.md)用3个冻结Program的作用域分析接上g.U/gT→uT→Vr→vXe/hXe→MMe，另保存37条源码事实。Vr的atom写入延迟、flush与flushOrThrow、提交前后内存更新、临时文件与备份读取分别记录。1条本机Node22命令在9个隔离场景执行13个保存单位4774字节并使用真实自建文件；主文件缺失不读备份、损坏时回退、错误吞吐及备份失败后主提交保留均已观察。schema/default/archives未执行，原应用实例、Node24/Owl、关闭flush与任务后端恢复仍未知。',
     {'runtimeRunsAdded': 1, 'runtimeScope': 'One local Node22 command executing 13 saved first-party storage units with guarded real file IO and explicitly substituted non-IO dependencies.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 9, 'savedSourceUnitsLoaded': 13,
      'executedSavedSourceBytes': 4774, 'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
      'deliveryRuntimeRunsAdded': 0}),
    ('shutdownPersistence', 'shutdown-persistence-provenance.json',
     ['shutdown-persistence-summary.md', 'shutdown-persistence.json', 'shutdown-persistence-observations.json'],
     '20 static records; one Node22 command with 17 synthetic event/timer scenarios executing eight saved units',
     '[正常退出与保存顺序](shutdown-persistence-summary.md)用冻结main Program接上实际eZe注册、startup状态、vXe facade与hXe清理，保存20条事实和19范围。1条Node22命令在17场景执行8单位3408字节，全部Electron/native/backend与计时器均为显式替身；普通与skip分支、首组无整体5秒限制、同步／异步错误、超时不取消、日志finally和清理截断分别观察。原应用事件送达、settings/backend实际清理、SIGTERM路径及任务恢复机制仍未知；未新增模型提交或模式排除。',
     {'runtimeRunsAdded': 1, 'runtimeScope': 'One local Node22 isolated VM command with synthetic app/native/backend callbacks and an explicit fake timer scheduler.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 17, 'savedSourceUnitsLoaded': 8,
      'executedSavedSourceBytes': 3408, 'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
      'deliveryRuntimeRunsAdded': 0}),
    ('featureScopeLedger', 'feature-scope-ledger-provenance.json',
     ['feature-scope-ledger-summary.md', 'feature-scope-ledger.json', 'feature-scope-ledger.csv', 'feature-scope-scenarios.json'],
     '34 author-reviewed scoped feature definitions; 35 assigned operations, 36 queued; 140 unexecuted acceptance specifications',
     '[细粒度功能与验收映射](feature-scope-ledger-summary.md)为38张设置卡形成34个baseline-local功能定义，35操作已关联；两个只读信息facet和一个WSL多动作卡保持队列，另33个非设置操作待审。选择／reset归于同一目录偏好但不称操作等价，六个配置键保持独立。140条验收规格均未执行；4个冻结Program的169范围与88元数据pointer重核通过。968旧入口仅同一设置容器部分关联，967未映射；34模式unknown、排除0、完整分母仍未知，36旧大组及337 deferred保留。',
     {'scopedFeatureDefinitions': 34, 'assignedOperations': 35, 'queuedOperations': 36,
      'unexecutedScenarioSpecifications': 140, 'newModeAssignments': 0,
      'newConfirmedExclusions': 0, 'originalClientRunsAdded': 0}),
    ('interruptControlFlowObservations', 'interrupt-control-flow-provenance.json',
     ['interrupt-control-flow-summary.md', 'interrupt-control-flow.json',
      'interrupt-control-flow-findings.json', 'interrupt-control-flow-observations.json'],
     'Eight source facts and 17 Program joins; one completed 34-scenario VM suite plus one retained partial failed command; no actual cancel click',
     '[中断函数条件与隔离观察](interrupt-control-flow-summary.md)在完整shared Program中核对Ien与所选helper的17处绑定，保存8条源码事实。9单位5259字节的34场景完成，另保留一次跨VM原型断言失败的部分执行命令；所有transport、状态历史选择、follower与清理设施均为显式替身。补发成功只写原turn、goal暂停失败后仍可能已中断、后台清理和descendant异常分别保留。真实取消点击仍0，既有SIGTERM／重启仅证明绑定UI中同一turn为interrupted；34功能及36操作队列未改，模式／完整分母未知。',
     {'runtimeRunsAdded': 2, 'runtimeScope': 'Two local Node22 isolated VM command attempts: one partial harness failure and one completed 34-scenario suite; no real app or backend.',
      'isolatedObservationCommandAttempts': 2, 'completedObservationCommands': 1,
      'failedObservationCommands': 1, 'isolatedScenarioCount': 34,
      'savedSourceUnitsLoaded': 9, 'executedSavedSourceBytes': 5259,
      'originalClientRunsAdded': 0, 'newActualCancelClicks': 0,
      'modelSubmissionsAdded': 0, 'newFeatureDefinitions': 0}),
    ('coreFeatureScope', 'core-feature-scope-provenance.json',
     ['core-feature-scope-summary.md', 'core-feature-scope.json',
      'feature-scope-current.json', 'feature-scope-current.csv', 'feature-scope-current-scenarios.json'],
     'Three additional scoped user goals; 33 prior nonsettings candidates reviewed as user operations, mechanisms or pending consumers; full denominator unknown',
     '[核心功能粒度与当前有限清单](core-feature-scope-summary.md)新增FSC-0035已有本地提交、0036普通停止和0037MCP电脑应用审批，三个审批选择保留不同操作。原71候选现分40用户操作、5机制支撑、26队列；支撑不穷尽所有调用方且不称操作等价。累计有限清单37功能／160未执行验收规格，原34／140快照保留。六个冻结Program的84范围与223 metadata pointer／line复核通过，没有新AST／REA或运行；34个取消VM场景和SIGTERM重启均未升级为真实stop验收。37模式unknown、排除0、完整分母与967入口映射仍待闭合。',
     {'scopedFeatureDefinitions': 37, 'newScopedFeatureDefinitions': 3,
      'assignedUserOperations': 40, 'mechanismSupportOperations': 5, 'queuedOperations': 26,
      'currentUnexecutedScenarioSpecifications': 160, 'newUnexecutedScenarioSpecifications': 20,
      'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0, 'runtimeObservationsAdded': 0}),
    ('cuaSettingsConsumers', 'cua-settings-consumer-provenance.json',
     ['cua-settings-consumer-summary.md', 'cua-settings-consumer-contracts.json', 'cua-settings-consumer-scenarios.json'],
     '14 bounded settings consumer links; 30 source facts and two inferences; mode and actual execution remain unproven',
     '[电脑使用设置的控件与共用服务](cua-settings-consumer-summary.md)为14个包装接上限定消费者，保存30条源码事实、2条推断、77个完整单位、139处词法绑定和44处import/export使用。原9个operation实际含8写与1搜索，另5个query定义；Messages的local/macOS条件、Windows认证来源条件、锁屏策略及手机／安装后复用分开记录。20条控件规格未执行，37功能／26队列／160功能规格保持原快照；没有新REA、目标执行、模型提交或模式排除。',
     {'sourceFacts': 30, 'inferredFacts': 2, 'selectedSourceUnits': 77, 'operationConsumers': 14,
      'programLexicalJoins': 139, 'qualifiedImportExportUses': 44, 'newOriginalProgramParses': 16,
      'distinctParsedSourcePrograms': 7, 'unexecutedControlSpecifications': 20,
      'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0, 'actualSettingsMutationsAdded': 0,
      'newFeatureDefinitions': 0}),
    ('settingsModeBoundary', 'settings-mode-boundary-provenance.json',
     ['settings-mode-boundary-summary.md', 'settings-mode-boundary-contracts.json', 'settings-mode-boundary-scenarios.json'],
     '53 settings predicates joined to 40 access-family properties; no complete product-mode classification or exclusions',
     '[设置分类与访问资格](settings-mode-boundary-summary.md)将40个分类项接到访问状态选择器及53个可见性分支：chatGpt14、chatGptOrCodex4、codex7、codexOrWorkLocal9、codexLocal6，另13分支无分类。codexOrWorkLocal合并本地与Work本地访问，分类不等于home composer模式。保存23源码事实／2推断、80单位／140词法位置／5导入导出连接；修正首版反引号值漏读，并保留被弃用的图标候选。12规格未执行；37功能／26队列／160功能规格保持，模式排除仍0，完整分母未知。',
     {'sourceFacts': 23, 'inferredFacts': 2, 'selectedSourceUnits': 80,
      'programLexicalJoins': 140, 'qualifiedImportExportUses': 5,
      'settingsCases': 53, 'familyProperties': 40, 'unclassifiedFamilyCases': 13,
      'unexecutedScenarios': 12, 'newOriginalProgramParses': 8, 'canonicalProgramParses': 7,
      'distinctParsedSourcePrograms': 2, 'originalClientRunsAdded': 0,
      'modelSubmissionsAdded': 0, 'newFeatureDefinitions': 0, 'newModeAssignments': 0,
      'newConfirmedExclusions': 0}),
    ('settingsEntryCallers', 'settings-entry-callers-provenance.json',
     ['settings-entry-callers-summary.md', 'settings-entry-callers-contracts.json',
      'settings-entry-callers-scenarios.json', 'settings-entry-callers-observations.json'],
     'Two caller arguments and host resolver joined; five-file REA subset plus 17 synthetic VM cases; real provider and UI remain unknown',
     '[设置入口与主机解析](settings-entry-callers-summary.md)将两个实际hook调用的第二参数接到所选host的kind===local，并闭合命令菜单lazy导出与访问条件。22源码事实／2推断、67单位／270词法位置／6跨模块连接另存；未知主机回退local，Cloud executor也标local。REA五文件子集应用图完整、语义图unknown且8815未知；两调用site仅作坐标匹配，不能宣称REA闭合调用。一次17场景VM仅使用保存函数、合成FI与memo替身，真实Q6/provider、host配置、导航及UI未知；8规格未执行，37功能／26队列／160规格与模式排除保持。',
     {'sourceFacts': 22, 'inferredFacts': 2, 'selectedSourceUnits': 67,
      'programLexicalJoins': 270, 'qualifiedImportExportUses': 6,
      'newOriginalProgramParses': 9, 'distinctParsedSourcePrograms': 5,
      'newReaCommandAttempts': 3, 'successfulReaCommands': 1, 'failedReaCommands': 2,
      'reaSubsetFiles': 5, 'reaSemanticUnknowns': 8815, 'unexecutedScenarios': 8,
      'runtimeRunsAdded': 1, 'runtimeScope': 'One Node22 VM command: saved host functions with synthetic FI and memo-cache substitutes only.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 17,
      'savedSourceUnitsLoaded': 15, 'savedFunctionsLoaded': 10, 'executedSavedSourceBytes': 1941,
      'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
      'modelSubmissionsAdded': 0, 'actualSettingsMutationsAdded': 0,
      'newFeatureDefinitions': 0, 'newModeAssignments': 0, 'newConfirmedExclusions': 0}),
    ('hostStateProvider', 'host-state-provider-provenance.json',
     ['host-state-provider-summary.md', 'host-state-provider-contracts.json',
      'host-state-provider-scenarios.json', 'host-state-provider-observations.json'],
     'Host selection and shared snapshots traced; 26 synthetic VM cases; live provider, repository DI and durability remain unknown',
     '[主机选择与共享快照](host-state-provider-summary.md)接上Q6→p8a、路由／连接过滤、NI订阅桥、preload缓存及首次快照IPC channel。26源码事实／2推断、75单位／328词法位置／9跨模块连接另存；26项合成VM观察通过，状态先写后导航、发送前快照更新分别保留。MMe／hXe仓库同实例、真实provider、连接查询与持久化仍未知；没有新增REA、真实UI或模型提交，8条新UI规格未执行，37功能／26队列／160规格及模式排除保持。',
     {'sourceFacts': 26, 'inferredFacts': 2, 'selectedSourceUnits': 75,
      'programLexicalJoins': 328, 'qualifiedImportExportUses': 9,
      'newOriginalProgramParses': 14, 'distinctParsedSourcePrograms': 6,
      'analysisCommands': 6, 'newReaCommandAttempts': 0, 'unexecutedScenarios': 8,
      'runtimeRunsAdded': 1, 'runtimeScope': 'One Node22 VM command: saved host-selection, shared-state and repository units with synthetic providers only.',
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 26,
      'savedSourceUnitsLoaded': 9, 'savedFunctionsLoaded': 7, 'savedClassesLoaded': 1,
      'savedFactoryAssignmentsLoaded': 1, 'executedSavedSourceBytes': 2243,
      'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
      'modelSubmissionsAdded': 0, 'actualIpcMessagesAdded': 0, 'actualSettingsMutationsAdded': 0,
      'newFeatureDefinitions': 0, 'newModeAssignments': 0, 'newConfirmedExclusions': 0}),
    ('hostStateDi', 'host-state-di-provenance.json',
     ['host-state-di-summary.md', 'host-state-di-contracts.json', 'host-state-di-scenarios.json', 'host-state-di-observations.json'],
     'Static shared repository identity and snapshot registration closed; 26 synthetic scenarios; actual constructors and IPC unobserved',
     '[仓库注入与窗口快照](host-state-di-summary.md)用同一main Program接上hXe仓库→MMe第11实参、vXe→H.setWindowContext及$Xe真实参数；关闭这一静态同对象与context来源缺口。18源码事实／2推断、47单位含4继承／1403词法位置另存。修正版26项合成观察通过；首版bound函数故障注入断言失败及两次class形状派生失败保留。真实构造／窗口／IPC、React provider、远程查询和持久化仍未知；7规格未执行，原37功能／26队列／160规格及排除不改。',
     {'sourceFacts': 18, 'inferredFacts': 2, 'selectedSourceUnits': 47, 'newSourceUnits': 43,
      'inheritedSourceUnits': 4, 'programLexicalJoins': 1403, 'successfulProgramParses': 3,
      'distinctParsedSourcePrograms': 1, 'analysisCommandAttempts': 5, 'successfulAnalysisCommands': 3,
      'failedAnalysisCommands': 2, 'unexecutedScenarios': 7, 'newReaCommandAttempts': 0,
      'runtimeRunsAdded': 2, 'runtimeScope': 'Two Node22 synthetic VM commands, first 24/25 passed and revised 26/26 passed; actual constructors and IPC not executed.',
      'isolatedObservationCommandAttempts': 2, 'successfulObservationCommands': 1, 'failedObservationCommands': 1,
      'isolatedScenarioCount': 26, 'scenarioExecutions': 51, 'savedSourceUnitsLoaded': 24,
      'executedSavedSourceBytes': 3947, 'originalClientRunsAdded': 0, 'actualIpcMessagesAdded': 0,
      'modelSubmissionsAdded': 0, 'actualSettingsMutationsAdded': 0, 'newFeatureDefinitions': 0,
      'newModeAssignments': 0, 'newConfirmedExclusions': 0}),
    ('remoteConnectionState', 'remote-connection-state-provenance.json',
     ['remote-connection-state-summary.md', 'remote-connection-state-contracts.json',
      'remote-connection-state-scenarios.json', 'remote-connection-state-observations.json'],
     'Remote state producer contracts and 35 synthetic scenarios; renderer query, real instances and durability pending',
     '[远程目录与刷新状态](remote-connection-state-summary.md)接上hXe→fKe仓库注入、三类列表发布/订阅和registry状态查询；SSH、WSL、remote-control的过期结果、异常、重试与授权策略分别保留。21源码事实/2推断、45单位含1继承/616去重词法位置；一次完整main解析，无新REA。完整fKe/wee与helper的35项合成观察通过，10条集成场景未执行。renderer query、真实provider/连接和耐久保存继续调查；原37功能/26队列/160规格与模式排除保持。',
     {'sourceFacts': 21, 'inferredFacts': 2, 'selectedSourceUnits': 45, 'newSourceUnits': 44,
      'inheritedSourceUnits': 1, 'programLexicalJoins': 616, 'newOriginalProgramParses': 1,
      'distinctParsedSourcePrograms': 1, 'newReaCommandAttempts': 0, 'runtimeRunsAdded': 1,
      'isolatedObservationCommands': 1, 'isolatedScenarioCount': 35, 'savedSourceUnitsLoaded': 9,
      'executedSavedSourceBytes': 24785, 'unexecutedScenarios': 10, 'originalClientRunsAdded': 0,
      'modelSubmissionsAdded': 0, 'actualIpcMessagesAdded': 0, 'actualSettingsMutationsAdded': 0,
      'realNetworkRequestsAdded': 0, 'newFeatureDefinitions': 0, 'newModeAssignments': 0,
      'newConfirmedExclusions': 0}),
    ('remoteStatusConsumer', 'remote-status-consumer-provenance.json',
     ['remote-status-consumer-summary.md', 'remote-status-consumer-contracts.json',
      'remote-status-consumer-scenarios.json', 'remote-status-consumer-observations.json'],
     'Local status aggregation and guarded bootstrap request endpoints; real React and transport remain pending',
     '[连接状态选择器与启动请求](remote-status-consumer-summary.md)接上Vs→SF/state$、a8a聚合、s8a筛选及ERs→yo URI/host参数→$L/fKe端点的限定静态来源。Fn仅把CF设true；快照严格身份、manager替换、cleanup和progress清空分别保留。18源码事实/2推断、70单位含1继承/958词法位置/11跨模块使用；24项替身观察通过。真实React/bridge、后续写入者和normalizer依赖仍待调查，8集成规格未执行；原37功能/26队列/160规格与模式排除不改。',
     {'sourceFacts': 18, 'inferredFacts': 2, 'selectedSourceUnits': 70, 'newSourceUnits': 69,
      'inheritedSourceUnits': 1, 'programLexicalJoins': 958, 'qualifiedImportExportUses': 11,
      'newOriginalProgramParses': 5, 'distinctParsedSourcePrograms': 3, 'newReaCommandAttempts': 0,
      'runtimeRunsAdded': 1, 'isolatedObservationCommands': 1, 'isolatedScenarioCount': 24,
      'savedSourceUnitsLoaded': 21, 'executedSavedSourceBytes': 4671, 'unexecutedScenarios': 8,
      'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0, 'actualIpcMessagesAdded': 0,
      'realNetworkRequestsAdded': 0, 'actualSettingsMutationsAdded': 0, 'newFeatureDefinitions': 0,
      'newModeAssignments': 0, 'newConfirmedExclusions': 0}),
    ('cuaFeatureScope', 'cua-feature-scope-provenance.json',
     ['cua-feature-scope-summary.md', 'cua-feature-scope.json', 'cua-feature-scope-scenarios.json',
      'feature-scope-v2.json', 'feature-scope-v2.csv', 'feature-scope-v2-scenarios.json'],
     'Seven user goals from 14 proved CUA consumers; immutable v2 finite scope, mode and real execution pending',
     '[电脑使用设置功能归属及当前v2清单](cua-feature-scope-summary.md)将14个已接消费者的候选归为7个用户目标、8个写操作与6个查询/搜索支撑。当前有限视图为44功能、48用户操作/11机制/12队列、192条未执行规格；相同71候选守恒，原37功能/160规格和v1文件逐对象/逐字节保留。9冻结文件373范围与521次metadata pointer复核；模式unknown、排除0，真实UI/provider/receiver和持久化仍待验证，REA及模型调用均未增加。',
     {'scopedFeatureDefinitions': 44, 'newScopedFeatureDefinitions': 7,
      'reviewedOperationCandidates': 14, 'assignedUserOperations': 48,
      'mechanismSupportOperations': 11, 'queuedOperations': 12,
      'knownOperationCandidatesAccountedFor': 71, 'currentUnexecutedScenarioSpecifications': 192,
      'newUnexecutedScenarioSpecifications': 32, 'newInferenceRecords': 21,
      'sourceFilesByteChecked': 9, 'uniqueSourceSpansChecked': 373,
      'metadataPointerOccurrencesChecked': 521, 'uniqueMetadataPointersChecked': 71,
      'newReaRuns': 0, 'newOriginalProgramParses': 0, 'originalClientRunsAdded': 0,
      'modelSubmissionsAdded': 0, 'actualSettingsMutationsAdded': 0,
      'newModeAssignments': 0, 'newConfirmedExclusions': 0}),
]


def build_context(out, baseline_id):
    out = Path(out).resolve()
    patch, notes, artifacts = {}, [], []
    for profile in PROFILES:
        key, index_name, readers, scope, note = profile[:5]
        extras = profile[5] if len(profile) > 5 else {}
        index = out / index_name
        if not index.exists():
            continue
        raw = index.read_bytes()
        value = json.loads(raw)
        assert value['baselineId'] == baseline_id
        patch[key] = {'path': index_name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'scope': scope,
                      'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'fullAnalysisCompleted': False}
        if key == 'objcIndependentBuild':
            assert value['observedNativeModuleLoads'] == extras['nativeModuleLoadsObserved'] == 1
            assert value['nativeMethodsInvokedAfterModuleInit'] == extras['nativeMethodsInvokedAfterModuleInit'] == 0
            assert value['originalClientRunsAdded'] == extras['originalClientRunsAdded'] == 0
            assert value['deliveryRuntimeRunsAdded'] == extras['deliveryRuntimeRunsAdded'] == 0
        if key == 'modeBehaviorObservations':
            for field in ['isolatedObservationCommands', 'isolatedScenarioCount', 'savedFunctionsExecuted',
                          'originalClientRunsAdded', 'originalStorageRunsAdded', 'deliveryRuntimeRunsAdded']:
                assert value[field] == extras[field]
            assert value['additionalModelTasks'] == 0 and value['fullAnalysisCompleted'] is False
        if key == 'sourceContextBehaviorObservations':
            for field in ['isolatedObservationCommands', 'isolatedScenarioCount', 'savedFunctionsExecuted',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'originalStorageRunsAdded',
                          'deliveryRuntimeRunsAdded']:
                assert value[field] == extras[field]
            assert value['additionalModelTasks'] == 0 and value['fullAnalysisCompleted'] is False
        if key == 'modePublisherInstantiation':
            assert value['sourceRecords'] == 23 and value['unexecutedScenarios'] == 13
            assert value['confidenceCounts'] == {'confirmed': 21, 'inferred': 1, 'unresolved': 1}
            assert value['staticIdentityJoinsOnly'] and not value['fullAnalysisCompleted']
            assert value['deliveryTargetClientRunsAdded'] == value['deliveryModelTasksAdded'] == 0
        if key == 'behaviorInterventions':
            for field in ['modelSubmissionsObserved', 'remainingModelSubmissions', 'newModelSubmissionsOn20261023',
                          'cancelClicks', 'stopRestartScenarioSignals']:
                assert value[field] == extras[field]
            assert value['authorizedModelSubmissions'] == 2 and not value['fullAnalysisCompleted']
            assert value['deliveryModelTasksAdded'] == value['deliveryRuntimeRunsAdded'] == 0
        if key == 'behaviorStopRestartOutcome':
            for field in ['groupModelSubmissionsObserved', 'remainingModelSubmissions', 'newModelSubmissionsOn20261023',
                          'scenarioStopSignals', 'scenarioRestarts', 'actualTerminalStatus']:
                assert value[field] == extras[field]
            assert value['deliveryModelTasksAdded'] == value['deliveryRuntimeRunsAdded'] == 0
            assert not value['fullAnalysisCompleted']
        if key == 'modePersistenceReceiver':
            assert value['selectedUnits'] == 4 and value['selectedSourceBytes'] == 1235
            assert value['confidenceCounts'] == {'confirmed': 11, 'inferred': 1}
            assert value['targetCodeExecuted'] is False and value['globalRecordsAdded'] == 0
        if key == 'mainPersistencePolicy':
            assert value['selectedUnits'] == 8 and value['selectedSourceBytes'] == 2486
            assert value['confidenceCounts'] == {'confirmed': 20, 'inferred': 2}
            assert value['unexecutedScenarios'] == 13 and not value['targetCodeExecuted']
            assert value['globalRecordsAdded'] == value['modelSubmissionsAdded'] == 0
            assert not value['fullAnalysisCompleted']
        if key == 'globalStateStorageOrigin':
            assert value['sourceRecords'] == 37 and value['successfulAnalysisPrograms'] == 3
            for field in ['isolatedObservationCommands', 'isolatedScenarioCount', 'savedSourceUnitsLoaded',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'originalStorageInstanceRunsAdded',
                          'deliveryRuntimeRunsAdded']:
                assert value[field] == extras[field]
            assert value['modelSubmissionsAdded'] == value['globalRecordsAdded'] == 0
            assert not value['fullAnalysisCompleted']
        if key == 'shutdownPersistence':
            assert value['sourceRecords'] == 20 and value['successfulAnalysisPrograms'] == 1
            assert value['sourceSelections'] == 19 and value['syntheticTimersAndApp'] is True
            for field in ['isolatedObservationCommands', 'isolatedScenarioCount', 'savedSourceUnitsLoaded',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'originalStorageInstanceRunsAdded',
                          'deliveryRuntimeRunsAdded']:
                assert value[field] == extras[field]
            assert value['modelSubmissionsAdded'] == value['globalRecordsAdded'] == 0
            assert not value['fullAnalysisCompleted']
        if key == 'featureScopeLedger':
            for field in ['scopedFeatureDefinitions', 'assignedOperations', 'queuedOperations',
                          'unexecutedScenarioSpecifications', 'newModeAssignments',
                          'newConfirmedExclusions', 'originalClientRunsAdded']:
                assert value[field] == extras[field]
            assert value['runtimeObservationsAdded'] == value['modelSubmissionsAdded'] == value['globalRecordsAdded'] == 0
            assert not value['featureDenominatorEstablished'] and not value['fullAnalysisCompleted']
        if key == 'interruptControlFlowObservations':
            assert value['sourceFacts'] == 8 and value['programLexicalJoins'] == 17
            for field in ['isolatedObservationCommandAttempts', 'completedObservationCommands',
                          'failedObservationCommands', 'isolatedScenarioCount', 'savedSourceUnitsLoaded',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'newActualCancelClicks',
                          'modelSubmissionsAdded', 'newFeatureDefinitions']:
                assert value[field] == extras[field]
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'coreFeatureScope':
            for field in ['scopedFeatureDefinitions', 'newScopedFeatureDefinitions',
                          'assignedUserOperations', 'mechanismSupportOperations', 'queuedOperations',
                          'currentUnexecutedScenarioSpecifications', 'newUnexecutedScenarioSpecifications',
                          'originalClientRunsAdded', 'modelSubmissionsAdded', 'runtimeObservationsAdded']:
                assert value[field] == extras[field]
            assert value['reviewedNonsettingsOperationCandidates'] == 33
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'cuaSettingsConsumers':
            for field in ['sourceFacts', 'inferredFacts', 'selectedSourceUnits', 'operationConsumers',
                          'programLexicalJoins', 'qualifiedImportExportUses', 'newOriginalProgramParses',
                          'distinctParsedSourcePrograms', 'unexecutedControlSpecifications',
                          'originalClientRunsAdded', 'modelSubmissionsAdded', 'actualSettingsMutationsAdded',
                          'newFeatureDefinitions']:
                assert value[field] == extras[field]
            assert value['operationKinds'] == {'writes': 8, 'serializedSearches': 1, 'queryDefinitions': 5}
            assert not value['targetCodeExecuted'] and value['globalRecordsAdded'] == 0
            assert not value['featureDenominatorEstablished'] and not value['fullAnalysisCompleted']
        if key == 'settingsModeBoundary':
            for field in ['sourceFacts', 'inferredFacts', 'selectedSourceUnits', 'programLexicalJoins',
                          'qualifiedImportExportUses', 'settingsCases', 'familyProperties', 'unclassifiedFamilyCases',
                          'unexecutedScenarios', 'newOriginalProgramParses', 'canonicalProgramParses',
                          'distinctParsedSourcePrograms', 'originalClientRunsAdded', 'modelSubmissionsAdded',
                          'newFeatureDefinitions', 'newModeAssignments', 'newConfirmedExclusions']:
                assert value[field] == extras[field]
            assert value['rejectedDerivedMetadataParses'] == 1 and not value['targetCodeExecuted']
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'settingsEntryCallers':
            for field in ['sourceFacts', 'inferredFacts', 'selectedSourceUnits', 'programLexicalJoins',
                          'qualifiedImportExportUses', 'newOriginalProgramParses', 'distinctParsedSourcePrograms',
                          'newReaCommandAttempts', 'successfulReaCommands', 'failedReaCommands', 'reaSubsetFiles',
                          'reaSemanticUnknowns', 'unexecutedScenarios', 'runtimeRunsAdded',
                          'isolatedObservationCommands', 'isolatedScenarioCount', 'savedSourceUnitsLoaded',
                          'savedFunctionsLoaded', 'executedSavedSourceBytes', 'originalClientRunsAdded',
                          'originalStorageInstanceRunsAdded', 'modelSubmissionsAdded', 'actualSettingsMutationsAdded',
                          'newFeatureDefinitions', 'newModeAssignments', 'newConfirmedExclusions']:
                assert value[field] == extras[field]
            assert value['targetCodeExecuted'] and value['syntheticProvidersOnly']
            assert value['reaSemanticCoverage'] == 'unknown' and value['globalRecordsAdded'] == 0
            assert not value['featureDenominatorEstablished'] and not value['fullAnalysisCompleted']
        if key == 'hostStateProvider':
            for field in ['sourceFacts', 'inferredFacts', 'selectedSourceUnits', 'programLexicalJoins',
                          'qualifiedImportExportUses', 'newOriginalProgramParses', 'distinctParsedSourcePrograms',
                          'analysisCommands', 'newReaCommandAttempts', 'unexecutedScenarios', 'runtimeRunsAdded',
                          'isolatedObservationCommands', 'isolatedScenarioCount', 'savedSourceUnitsLoaded',
                          'savedFunctionsLoaded', 'savedClassesLoaded', 'savedFactoryAssignmentsLoaded',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'originalStorageInstanceRunsAdded',
                          'modelSubmissionsAdded', 'actualIpcMessagesAdded', 'actualSettingsMutationsAdded',
                          'newFeatureDefinitions', 'newModeAssignments', 'newConfirmedExclusions']:
                assert value[field] == extras[field]
            assert value['rejectedDerivedSelections'] == 2
            assert value['targetCodeExecuted'] and value['syntheticProvidersOnly']
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'hostStateDi':
            for field in ['sourceFacts', 'inferredFacts', 'selectedSourceUnits', 'newSourceUnits',
                          'inheritedSourceUnits', 'programLexicalJoins', 'successfulProgramParses',
                          'distinctParsedSourcePrograms', 'analysisCommandAttempts', 'successfulAnalysisCommands',
                          'failedAnalysisCommands', 'unexecutedScenarios', 'newReaCommandAttempts', 'runtimeRunsAdded',
                          'isolatedObservationCommandAttempts', 'successfulObservationCommands', 'failedObservationCommands',
                          'isolatedScenarioCount', 'scenarioExecutions', 'savedSourceUnitsLoaded',
                          'executedSavedSourceBytes', 'originalClientRunsAdded', 'actualIpcMessagesAdded',
                          'modelSubmissionsAdded', 'actualSettingsMutationsAdded', 'newFeatureDefinitions',
                          'newModeAssignments', 'newConfirmedExclusions']:
                assert value[field] == extras[field]
            assert value['targetCodeExecuted'] and value['syntheticProvidersOnly']
            assert not value['fullConstructorsExecuted'] and value['globalRecordsAdded'] == 0
            assert not value['featureDenominatorEstablished'] and not value['fullAnalysisCompleted']
        if key == 'remoteConnectionState':
            assert all(value[field] == expected for field, expected in extras.items())
            assert value['targetCodeExecuted'] and value['syntheticProvidersOnly']
            assert value['fullFKeAndWeeConstructorsExecuted'] and not value['hXeConstructorExecuted']
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'remoteStatusConsumer':
            assert all(value[field] == expected for field, expected in extras.items())
            assert value['targetCodeExecuted'] and value['syntheticProvidersOnly']
            assert not value['fullConstructorsExecuted'] and not value['actualReactHooksExecuted']
            assert not value['externalNormalizerImplementationExecuted']
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'cuaFeatureScope':
            assert all(value[field] == expected for field, expected in extras.items())
            assert not value['targetCodeExecuted'] and not value['thirdPartyImplementationsPublished']
            assert value['globalRecordsAdded'] == 0 and not value['featureDenominatorEstablished']
            assert not value['fullAnalysisCompleted']
        if key == 'modePreferenceStorageOrigin':
            reader = json.loads((out / 'mode-preference-storage-origin.json').read_bytes())
            assert reader['evidenceJournal']['recordCount'] == 46
            qualifications = reader['authorQualifications']
            assert any(item['path'] == 'raw/mode-preference-storage-origin/qualification/cleanup-errata.json'
                       and item['addsEvidenceRecords'] is False for item in qualifications)
        patch[key].update(extras)
        artifacts += [index_name] + readers
        notes.append(note)
        selected = value.get('exactCopies', value.get('copies', [])) + value.get('outputs', []) + value.get('derived', [])
        selected += [{'published': item['published'], 'bytes': item['original']['bytes'],
                      'sha256': item['original']['sha256']} for item in value.get('ownCompletedDeliveryCaptures', [])]
        for item in selected:
            target = item.get('outputPath', item.get('published', item.get('destination', item.get('relativePath', item.get('path')))))
            assert target is not None
            path = Path(target)
            if not path.is_absolute():
                path = out / path
            path = path.resolve()
            assert path.is_relative_to(out) and path.is_file()
            data = path.read_bytes()
            assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
            artifacts.append(path.relative_to(out).as_posix())
    for relative in ['raw/current-contracts/delivery-execution-provenance.json',
                     'raw/current-contracts/integration-execution-provenance.json',
                     'raw/settings-config-dispatch/delivery-execution-provenance.json',
                     'raw/terminal-feature-contracts/delivery-execution-provenance.json',
                     'raw/functional-catalog-reconciliation/delivery-execution-provenance.json',
                     'raw/current-contracts/publication-review-provenance.json',
                     'raw/file-change-view-contracts/delivery-code-peer-provenance.json',
                     'raw/reviewed-contracts/integration-execution-provenance.json',
                     'raw/source-contracts/delivery-execution-provenance.json',
                     'raw/source-contracts/integration-execution-provenance.json',
                     'raw/source-contracts/receiver-delivery-execution-provenance.json',
                     'raw/objc-independent-build/delivery-execution-provenance.json',
                     'raw/receiver-native-integration/execution-provenance.json',
                     'raw/storage-di-contracts/delivery-execution-provenance.json',
                     'raw/mode-behavior-observations/delivery-execution-provenance.json',
                     'raw/settings-source-context-origin/delivery-execution-provenance.json',
                     'raw/storage-context-integration/execution-provenance.json',
                     'raw/source-context-behavior-observations/delivery-execution-provenance.json',
                     'raw/mode-publisher-instantiation/delivery-execution-provenance.json',
                     'raw/behavior-interventions/publication-execution-provenance.json',
                     'raw/analysis-resume-20261023/execution-provenance.json',
                     'raw/completed-scenario-integration/execution-provenance.json',
                     'raw/main-persistence-policy/execution-provenance.json',
                     'raw/global-state-storage-origin/execution-provenance.json',
                     'raw/shutdown-persistence/execution-provenance.json',
                     'raw/feature-scope-ledger/execution-provenance.json',
                     'raw/interrupt-control-flow/execution-provenance.json',
                     'raw/core-feature-scope/execution-provenance.json',
                     'raw/cua-settings-consumer/execution-provenance.json',
                     'raw/settings-mode-boundary/execution-provenance.json',
                     'raw/settings-entry-callers/execution-provenance.json',
                     'raw/host-state-provider/execution-provenance.json',
                     'raw/host-state-di/execution-provenance.json',
                     'raw/remote-connection-state/execution-provenance.json',
                     'raw/remote-status-consumer/execution-provenance.json',
                     'raw/cua-feature-scope/execution-provenance.json']:
        path = out / relative
        if path.exists():
            artifacts.append(relative)
            value = json.loads(path.read_bytes())
            for item in value.get('copies', []):
                relative_copy = item.get('path', item.get('published'))
                if relative_copy:
                    candidate = (out / relative_copy).resolve()
                    assert candidate.is_relative_to(out) and candidate.is_file()
                    data = candidate.read_bytes()
                    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
                    artifacts.append(candidate.relative_to(out).as_posix())
    return patch, '\n\n'.join(notes), sorted(set(artifacts))
