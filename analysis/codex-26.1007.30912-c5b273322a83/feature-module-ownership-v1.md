# 有限功能到维护职责的统一映射 v1

基线：`codex-26.1007.30912-c5b273322a83`。范围：当前 426 项有限定义、443 项用户操作；完整产品功能分母仍未知。客户端实现尚未开始。

本批把原来的功能台账、37 个职责和菜单增补接成同一份可追溯设计。每项功能现在都有操作合同、源码范围证据、拟议维护去向，以及尚未确定的状态／服务 owner。达到 SQ-03 原定的“当前有限集合都有可回溯去向或精确缺口”停止条件；不代表完整客户端源码已分区，也不提升原九项完成标准。

## 阅读入口

- [逐功能映射 JSON](feature-module-ownership-v1.json)：`features` 保留每项操作的状态、效果、失败／取消合同引用和具体剩余问题。
- [426 行 CSV](feature-module-ownership-v1.csv)：按功能查看任务、拟议路径、菜单适配器、条件 provider 和证据标识。
- [492 条证据记录](feature-module-ownership-v1-evidence.jsonl)：426 项功能、54 个已有职责记录及 12 条设计决定；结论类型均为有范围限定的维护设计推断。
- [核对程序](../../scripts/analysis/verify_feature_module_ownership_v1.py)：核对实际输入、引用、范围和关联集合，不将路径或几何包含当作业务所有权。

## 哪些归属得到整合

| 层次 | 本批结果 | 限定 |
| --- | --- | --- |
| 已有职责 | 37 个既有职责、16 个菜单适配器提议、1 个菜单装配职责，共 54 条 | 通过引用保留原十字段合同及重叠规则；不是 54 个已恢复、可构建的模块 |
| 工作流承接 | 48 个粗粒度 renderer 工作流 facade 提议，对应 T01–T48；T49 使用菜单装配与选定回调适配器 | 采用已有操作合同和维护路径，职责限于界面／动作编排；不把任务数量当作原始模块数量 |
| 已有 provider 连接 | 5 项功能具有原分析中明确列出的条件连接 | 只复用那些消费者，不推广到全部功能 |
| 菜单连接 | 55 项不同功能具有已发布目标与适配器关系 | 包含已有功能的菜单别名，不新增功能定义 |
| 局部状态 | About 窗口生命周期、缩放提示条、快捷键对话框控制器 3 处明确承接 | 实际 native 效果、注入 zoom provider 和 dialog 内容仍分开 |
| 持久／远端状态 | 每项均保留精确操作合同和 owner 连接缺口 | 本批没有确认新的完整持久／远端状态归属；这不是声称此前没有存储合同 |

`sourceUnits` 共 1,510 处范围，来自 100 个冻结文件；其中既有调用点，也有被调用 helper 的证据。它们是实现职责的见证范围，不是可直接复制的排他源码分配。54 条记录之间的 16 组相同范围明确按共享见证处理，不能在每个功能目录复制整段 `CZe` 或公共 dispatcher。

48 个 facade 仍保留 32 条已分析页面的细分规则。例如：Plugins 复用 skills/MCP；归档展示分别委托本地主机、云任务和账户会话；密码元数据与 1Password 注册分开；Micro 的界面、硬件桥接、布局与保存时机分开。细分规则在 JSON 的 `featureAdapterProposals[].refinementRules`，没有被目录层级抹平。

## 由职责决定的项目结构建议

下面是维护设计，尚未创建客户端目录或配置。每个叶子对应 JSON 中的已有职责合同或工作流 facade 提议；没有声称恢复原作者目录。

```text
apps/desktop/src/
  main/
    bootstrap/                     # 启动记录环境输入
    menus/application-menu.ts       # 菜单装配；不承接所有领域状态
    app-host/                      # service assembly、连接入口
    window-services/               # context/sender/frame 与生命周期
    http/                          # 请求、取消、Response bridge
    network/                       # application-network 与 runtime startup
    windows/about-window.ts        # About 单例与销毁
    diagnostics/                   # debug 菜单、启动记录适配器
    context/                       # source-context 转发与生命周期
    projects/                      # 项目 service 合同
    runtime/                       # feature policy/provider
    native/                        # 已识别原生封装
  preload/app-host-bridge.ts        # 消息/port 转移合同
  browser-preload/annotation/       # annotation root/lifecycle
  worker/native/apple-events.ts    # 已识别 Apple Event 封装
  renderer/
    app-host/                      # provider 生命周期与 RPC 分支
    settings/                      # 注册表、factory、可见性和路由
    mode/                          # 状态、resolver、transition
    runtime/                       # capability/gate 接口
    projects/                      # 项目 client 合同
    features/                      # 工作流粗边界与 renderer 菜单适配器
      tasks/                       # 实际提交/停止；草稿适配器单列
      projects/                    # 项目命令与对话框，领域状态另委托
      archives/                    # 带类型的归档展示/动作编排
      workspace/                   # 侧栏、面板、布局命令复用
      browser/                     # 页面命令与 runtime port
      navigation/                  # 应用路由历史
      window/                      # zoom 提示/订阅，实际 zoom 注入
      commands/                    # 快捷键 dialog 控制器
      ...                          # 其余路径逐项见 CSV，不视为额外源码包
packages/
  app-server-client/               # request manager、host connection
  app-host-client/                 # resolver 与 host-rpc selector
  desktop-http-client/             # HTTP adapter
  desktop-transport/               # framing/ack/assembly
  projects/                       # 已有领域合同；不等同于所有项目 UI
```

跨进程调用保留显式 bridge／RPC／注入接口。renderer 的调用动作不授予它 native 或后端状态所有权；main 的菜单入口也不授予它 renderer 工作流状态。存储的路径输入、实际写入和耐久性归属继续复用既有 11 域及后续 SQ-04 连接，不在每个设置页面发明一个持久层。

## 会影响维护和升级的决定

JSON 的 `designDecisions` 为 D01–D12 保存逐条来源。关键约束如下：

1. 设置注册表、page factory、可见性和 route 与实际页面操作分开。原 37 职责不能替代所有设置业务。
2. 菜单装配与 16 个动作适配器通过合同连接；公共注册／dispatch helper 不随每个消费者复制。
3. 准备任务草稿、真正提交、停止执行分别保留；条件 provider 连接不能成为通用提交路径。
4. 归档聚合展示保留本地主机、云任务和账户会话的不同效果接口；菜单归档复用已有本地工作流。
5. 浏览器页面历史、应用路由历史、相邻线程列表导航分别维护。
6. 侧栏别名与 Full view 复用工作区适配器。缩放数字键仍仅尝试页面；普通缩放保留页面未处理后的窗口回退。
7. 缩放提示条和快捷键 dialog 的局部 UI 状态不承担实际 zoom 服务或 lazy dialog 全部实现。
8. 项目命令／对话框与项目领域状态连接，不按名字直接认定为同一 owner。
9. 第三方实现保持包、独立运行时或明确 adapter 边界；通用依赖提示不选择准确版本，也不证明普通上游可替换定制实现。
10. 模式未知的功能继续保留；复用既有三组 Chat 专属分支决定，不按 `chat`／归档／账户名称删除整项功能。

升级时以稳定功能／操作标识比较新基线的合同、依赖和行为差异，并重新绑定 source hash／range；维护路径不是原 bundle 文件名的镜像。依赖版本和 runtime 来源仍受既有清单约束，不由此设计自动补全。

## 核对与下一行动

生成结果已核对全部功能和操作 ID、54 条职责来源、48 个粗边界提议、菜单与 provider 的精确既有连接、源码文件与范围哈希，以及九字段证据格式。发布后按同一程序回读；这些检查只证明输入身份、映射和引用一致，不是完整语义分区、实际产品行为或独立构建通过。

下一项 SQ-04：将本映射中的具体操作与既有 11 个存储域连接，优先处理 workspace／remote 状态、更新／下载缓存、自动化等未归域的源码 owner。native／后台内部事实保留为外部断点，不继续伪装成无限 JS 深挖。

SQ-02 的其余菜单／命令／路由来源（包括 `CZe` record33）仍保留。426 项有限功能、443 操作、117 支撑、49 任务及 1,407 条未执行产品规格不变；不新增客户端启动、模型提交、服务调用、第三方实现副本或客户端实现。完整分析目标继续执行。
