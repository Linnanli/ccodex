# 浏览器、Computer history 与语音：模块和运行时边界

本批交付26项有限操作目标、6项支撑机制与78条待执行产品规格，接入[恢复覆盖表v6](restoration-coverage-v6.json)的T26至T28。[功能台账v15](feature-scope-v15.json)现有237项定义、241项用户操作、52项支撑及808条未执行规格。原实施计划v7保留，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Browser use | 10 | Keep browser preference/history/download presentation in renderer, assign privileged settings pages, partition/mount lifecycle and actual browser operations to a runtime adapter; reuse plugin manager only through its existing contract. |
| Chronicle | 6 | Separate Computer history enablement/permissions/recorder lifecycle from recorded-activity browsing/deletion and derived-memory service effects; browser and audio history remain independent modules. |
| Voice | 10 | Separate local device/preferences, account voice services, OS command/shortcut registration, local media records and account/local dictionary stores; preserve capability/identity gates. |

Browser use把网页/本地URL打开偏好、地址栏/批注规则、数据清理与历史/下载分开；内嵌Chrome设置依赖特权页面、partition和配对mountId，应接运行时适配，不能按普通Web页面替代。插件管理与Try in chat作为既有扩展/会话流程的委托入口保留。

浏览历史行身份含URL、时间和agent标记，删除身份按URL与本地日去重；下载合并只补入匹配搜索的进行中条目，并保留历史fileExists。清下载历史不能直接声称删除文件。

Chronicle区分配置启用、权限/记忆前置条件、activationState和recorderState；应用/网站范围、活动浏览和区间/时间范围删除分别接服务。删除文案包含派生记忆，实际服务效果需单独验收。

Voice区分系统默认/具体麦克风、账户语言与实时声音、命令快捷键与听写快捷键、本机录音和词典。账户词典按accountId:userId重挂载，本地词典只trim并过滤空项，不推断去重；媒体权限和track清理使用合成替身验证。

22项精确源码helper/回调隔离用例通过；仅用合成记录、设备、权限回调、query与写入替身核对历史身份/下载合并、原生设置导航、清理请求guard、麦克风track释放和词典/账户语言保存；未读取真实历史、调用麦克风、录制屏幕、播放音频、访问服务或提交模型任务。307个已选择源码单元的冻结文件与字节范围核验通过。

保留两个codexOrWorkLocal入口与一个codex入口的静态访问证据，实际模式闭包仍待核对，确认排除为0。第三方实现通过既有依赖清单和服务/运行时适配引入；第一方保留门控、生命周期、请求与展示策略。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中25个已有局部合同，20个待展开。浏览器原生页面/partition、Chronicle录制与权限、媒体/音频/快捷键、词典及账户服务均已归属到对应适配任务；委托内部实现、实际运行、模式与持久化留作局部验收。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
