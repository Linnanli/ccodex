# 当前完成标准覆盖审计

固定基线 `codex-26.1007.30912-c5b273322a83`，固定成功发布 `20261013T164818487650Z`（93 artifacts）。当前分析仍未完成。

原9项标准：4满足、5部分；原6阶段：阶段1满足，其余5部分。已复制63份选定来源并记录完整SHA-256/bytes；25份属于此run发布清单且匹配。其余为当前引用的分析来源和历史审计背景；本审计未重验全部93产物或原始大输入。

| 标准 | 状态 | 证明范围与未闭合条件 |
| --- | --- | --- |
| AC-01 输入版本和哈希已固定，分析结果未混用版本。 | satisfied | 指定publication exit 0、93 artifacts；63份选定分析来源已先复制，其中25份当前发布工件与run登记匹配。既有副本复核一致，7条声明矛盾保留。 本条没有新增完成缺口；声明完整性、外部CLI源码身份和实际runtime兼容不被本条一并证明。未重新核验全部93产物或原始大输入。 |
| AC-02 已登记所有发现的文件、入口和功能候选，并说明分析覆盖的范围。 | partial | 旧14输入入口台账登记868主类+100辅助；176支持与337deferred另列。后续候选确有各自来源产物，未发现本审计可证实的漏项。 全局“所有已发现”登记的当前跨产物对齐尚未证明；旧台账不会自动纳入后续发现。功能分母unknown单独不是漏登记证明，operation等价与功能映射也不是本条登记动作的替代判据。 |
| AC-03 已区分 Codex、ChatGPT 专属、共享和未知项，排除理由可追溯。 | partial | 36组20 codex/9 shared/2 chatgpt/5 unknown全部inferred；438模块明确分类unknown，9个续查候选也unknown，确认排除0。unknown是已分类状态，不等于不存在或可删。 实际模式判定和拟排除项的保留依赖闭包仍无完整证据。0排除或存在unknown本身不构成失败；当前名称/Work/gate/header不足以授权排除。 |
| AC-04 每个保留功能已追踪到足以说明其职责的模块和关键跨进程或外部边界。 | partial | 19进程/传输边界及preload→host context/provider→network选定静态链已有来源；新的条件/信任/policy/lifecycle合同应保留。 36/36 codeChain仍通用非穷尽文字；候选链、41同handler链接、结构链接均不证明功能等价。外层绑定、动态实例、RPC/base、状态和持久化的逐功能闭合仍缺。 |
| AC-05 第三方依赖有版本与来源依据；无法确认的条目列出调查动作。 | satisfied | 202/202记录有versionBasis/sourcePath/sourceHash/recommendedIntegration/unresolved；17/17内嵌候选有来源/建议及各5类调查动作，自报与实际发行版本分列。 本条登记义务满足。71根声明未锁实际安装版本、17发行身份未确认、修改/native与必要调用闭包仍影响阶段3/6，不能据此宣称依赖可直接采用。 |
| AC-06 原生、Wasm、辅助程序、定制运行时和私有服务均有独立记录。 | satisfied | native记录分49归档工件、112磁盘runtime/helper、8外部Wasm、5runtime metadata、16plist及756source inputs；Owl和私有边界有独立合同。 本条独立记录义务满足；不证明源码取得、完整native调用闭包、实际Node查询、Electron/ABI或替代方案成功。 |
| AC-07 Source map 覆盖、构建输入缺失、REA 解析限制和动态关系均有说明。 | satisfied | 17848限定输入的map范围说明、30缺失build-input occurrences、REA partial/truncated及226389 semantic unknown均保留。 本条要求解释范围和限制，已满足；不能升级为map全域不存在、动态关系已解析或构建缺口关闭。 |
| AC-08 主要行为与静态结论已对照，未验证项有明确触发条件。 | partial | 30观察、一个授权README样例、已完成任务重启重新打开、5命令与11纯代码样例分列。project条件补充给出一个静态gate/capability/identity/data条件。 36/36功能conditions仍generic，feature runtime-pending；主要失败/取消/审批/文件写入/PTY/执行中断恢复没有逐功能场景和条件闭合。一条局部条件不升级全部功能。 |
| AC-09 项目结构建议、恢复顺序和验收条件能够引用分析证据。 | partial | 已有11局部维护建议/138范围映射；实施草案新增context、network和project条件的保留理由，恢复阶段的启动门槛已说明。 全保留功能→具体任务依赖→精确场景/预期后效的来源关系尚未形成；局部建议和模板阶段不能当完整目录/包/功能验收表。 |

| 阶段 | 状态 | 下一项安全调查 |
| --- | --- | --- |
| 第一阶段 固定输入与文件清单 | satisfied | 在既有固定基线中维护明确的外部版本身份隔离。 |
| 第二阶段 功能范围盘点 | partial | 只读补一个发现域的登记reconciliation，再追一个unknown候选的实际consumer。 |
| 第三阶段 第三方依赖识别 | partial | 按已保留功能选一个wrapper，界定第一方与库实现边界和已有依赖方案条件。 |
| 第四阶段 REA 架构与调用链分析 | partial | 围绕一个feature candidate补发送方、接收方、状态和后效的矩阵。 |
| 第五阶段 行为与依赖验证 | partial | 仅编制三类待验证场景卡与静态依据，不执行目标或模型。 |
| 第六阶段 形成实施依据 | partial | 编制一个完整有来源的模块/任务/契约验收条目作为模板并保留所有未解决门槛。 |

36/36功能候选仍为inferred模式、generic条件/链路及runtime-pending；438/438发布模块明确unknown。968入口候选与30行为观察各自保持分母，旧台账0已确认feature mapping不等于客户端没有功能。新增网络、信任和项目条件来源是局部静态进展，第一方封装、条件、取消/销毁及共享边界继续保留。

候选登记与功能分母不同；没有据功能分母unknown指控实际漏登记。unknown已被分类，不能直接删除。旧审计只覆盖旧发布；本次依据当前快照重新评估，未将局部green升级整体完成。

每项必要证据、当前权威定位、证明范围、缺失关闭条件与下一项具体安全调查见 `current-requirement-matrix.json`；`evidence.jsonl`固定所有引用的快照位置。本次只执行自己的工件统计/产物一致性验证，不执行目标、UI、模型或网络，也不读global journal、凭据或账户历史。
