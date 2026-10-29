# 功能入口台账（不是功能数）

冻结版本：`codex-26.1007.30912-c5b273322a83`。仅汇总既有 JSON/JSONL；未重跑目标 AST、UI 或模型任务。

主类 868 条、辅助类 100 条，共 968 条入口/合同记录；另有 176 个支持节点和 337 条未知 wrapper 候选。这个总数只用于台账完整性核对。

| 分母 | 类型 | 数量 | 定义与限制 |
| --- | --- | ---: | --- |
| route-constructions | primary-entry | 170 | Actual Route element-construction expressions with resolved Route import/export identity in the two requested chunks. app-initial:170; app-primary:0;170 have saved conversion-contract membership; actual runtime reachability unknown. |
| route-conversion-consumers | auxiliary-entry | 3 | Saved bound createRoutesFromElements conversion calls. Three saved calls; static consumers, not UI features. |
| navigate-component-targets | auxiliary-entry | 47 | Actual Navigate component constructions with resolved Navigate import/export identity. 47 saved constructions; navigation URLs are not matched to Route paths for operation/feature links. |
| menu-contract-records | primary-entry | 411 | All411 frozen contractRecordIndex rows, retaining their distinct entryKind and stable contractId. Complete-main API registrations/selected factory scopes; metadata from bound src registry; renderer7 selected function fragments. |
| host-top-level-message-cases | primary-entry | 143 | Top-level SwitchCase clauses of main MMe async handleMessage(e,t), switch(t.type). 143 clauses/143 literal labels in the saved complete switch;112 effective handler groups. |
| settings-lexical-candidates | primary-entry | 53 | Saved lexical section candidates in settings.json, each associated with one lexical evidence match. 53 discovered candidates; registry/factory binding and whole-settings denominator are unresolved. |
| direct-app-server-call-candidates | primary-entry | 91 | Only saved callForm=sendAppServerRequest and protocolClass=app-server lexical rows. 91 callsite candidates/52 distinct method literals in the selected-source discovery. |
| unknown-request-wrapper-candidates | deferred-discovery | 337 | Saved generic sendRequest lexical rows with unknown wrapper/protocol. 337 rows retained separately with provenance; not added to91 direct calls. |
| ipc-source-channel-candidates | auxiliary-entry | 50 | Saved explicit IPC source-file/channel pairs (one representative lexical evidence match per pair). 50 source/channel pairs;25 distinct channel literals; not all invocation/registration callsites. |
| host-effective-handler-groups | support-node | 112 | Already saved effective switch-case handler/fallthrough groups. 112 support nodes overlap143 case entries and are not extra source entries. |
| route-static-map-instances | support-node | 52 | Saved finite-map expansions of two Route construction templates. 52 instances overlap2 of170 source constructions; not extra registrations. |
| ipc-transport-analysis-notes | support-node | 12 | Saved curated static IPC transport summaries, not a registration census. 12 support notes; no name/channel-based entry association. |

菜单411条混合合同细分：

| entryKind | 数量 |
| --- | ---: |
| application-menu-factory | 1 |
| application-menu-consumer | 1 |
| command-metadata-instance | 182 |
| native-menu-api | 31 |
| native-menu-schema | 130 |
| native-menu-generator-options | 26 |
| os-global-native-registration | 1 |
| os-global-wrapper-consumer | 10 |
| before-input-event-registration | 6 |
| renderer-hook-scope | 7 |
| renderer-command-registration-candidate | 6 |
| renderer-message-subscription-candidate | 10 |

各入口分母的合同关联覆盖：

| 分母 | 记录 | 已有关联 | 未有关联 | 同handler来源关联 |
| --- | ---: | ---: | ---: | ---: |
| route-constructions | 170 | 170 | 0 | 0 |
| route-conversion-consumers | 3 | 3 | 0 | 0 |
| navigate-component-targets | 47 | 0 | 47 | 0 |
| menu-contract-records | 411 | 150 | 261 | 4 |
| host-top-level-message-cases | 143 | 143 | 0 | 37 |
| settings-lexical-candidates | 53 | 0 | 53 | 0 |
| direct-app-server-call-candidates | 91 | 0 | 91 | 0 |
| ipc-source-channel-candidates | 50 | 0 | 50 | 0 |

关联状态必须分别理解：

- 有已审查合同关联：466/968；未关联：502/968。主类已关联 463/868、未关联 405/868。
- 有同完整 handler 的来源关联：41/968。该数仍不证明操作、payload 或功能等价。
- 经审查确认同一 domain operation 的跨入口关联：0。映射到已确认 feature_id：0；功能总分母仍 unknown。
- 当前跨产物 handler identity 为0：只对保存的119 host definition range、114 route terminal definition 与411 menu index进行坐标比较，不能据此断言完整图不存在关联。路径、commandId、channel 与 method 的同名未用于关联。

| 合同关系 | 数量 |
| --- | ---: |
| static-instance-of-source-template | 52 |
| route-parent-registration | 169 |
| route-registration-conversion-consumer | 493 |
| schema-registration-dataflow | 229 |
| dispatch-case-effective-handler | 143 |
| shares-callback-definition | 2 |

493条 route→conversion 关联仅表示冻结合同中保存的 source 构造/API适用关系，不能称作逐条实际路由运行可达或同一业务功能。所有链接的 runtimeReachability 都为 unknown。229条菜单注册关联是保存的双向 source-dataflow 引用核对；独立审查只抽验其中1条，未重新分析目标代码。

来源定位：每个 entry 保留冻结 sourceArtifact 的路径、SHA256、JSON pointer、evidenceIds、原始 source hash/UTF-8 byte range；evidenceReferences 保留 journal SHA256 与一基 JSONL 行号。菜单 entryId 直接继承原411稳定 contractId。其余 ID 限于当前 baseline，并不是未来升级时的 feature_id。

AST evidence 原有 spanHash 保留；词法候选原本没有 spanHash，显式记为 absent-in-lexical-discovery。台账只验证原始 hash 与 baseline manifest 一致、范围不越界，未再次读取目标源码重算 byte-span hash。

Route 170 source 构造、143 fixed path、144含字面 helper 的 resolved path、2 map template 与52 static instance 各有自己的分母；52实例只作支持节点。旧171 lexical host case 中28 nested labels不加入143顶层 case。Settings53与Route50 settings实例没有按名称合并。RPC只计91 sendAppServerRequest候选，337 sendRequest单列未解析。

下一轮通往 feature census 的审查：

- `resolve-candidate-bindings`：Resolve actual registry/callee/receiver definitions and payload/result/error/cancel/state contracts before linking them.
- `resolve-renderer-registration-scope`：Resolve original Program/import bindings and live normal/fallback registrations; same commandId does not prove same handler.
- `operation-equivalence-review`：Review arguments, branch conditions, account/platform/mode, side effects and results for each entry variant. Shared code may implement multiple operations.
- `feature-census`：Define user-visible workflow/operation specs, assign stable feature IDs, map entries N:M with evidence, and document merge/split decisions plus unresolved entries. Do not total route/menu/handler counts as features.
- `mode-reachability`：Establish actual Codex/Work/ChatGPT guards, prerequisites and runtime behavior before excluding any feature. Names do not justify exclusion.
- `bundled-package-ownership`：Resolve first-party versus bundled dependency ownership. A bound namespace/source symbol does not prove first-party ownership or justify generating dependency source.

校验：14 个输入 artifact hash、968 个唯一 entryId、所有 JSON pointer/link endpoint/evidence reference 均可解析；引用 8712 个既有 evidence。此次静态台账没有新增运行验证，所有模式归属仍 unknown。
