# 诊断、Pets 与 Import：操作归属及共享模块复用

本批交付14项有限操作目标、6项支撑机制与42条待执行产品规格，接入[恢复覆盖表v8](restoration-coverage-v8.json)的T31至T33。[功能台账v17](feature-scope-v17.json)现有274项定义、278项用户操作、64项支撑及919条未执行规格。原实施计划v7保留，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Debug | 2 | Keep diagnostic control definitions in renderer, route stored preference and effective CSS/GPU policy through explicit adapters, and reuse browser runtime capability constraints. |
| Pets | 7 | Separate pet preferences/catalog, floating overlay, renderer preview and creation/upgrade preparation; reuse keybindings and plugin/skill managers, with generation as separately authorized task execution. |
| Import | 5 | Separate detection/import controller, automatic sync, result history and post-import setup; reuse existing OAuth/plugin/MCP/skill/hook owners rather than creating duplicate implementations. |

Debug的Chrome诊断行受allowDebugMenu控制，GPU组仍被构造；实际GPU效果另受debug gate控制。偏好写入、URL信任策略和底层能力分别验收。

Pets区分petVisibility、petVisible和overlay-open；None只隐藏宠物外观。创建/升级先安装启用必要技能或插件，再准备提示；不能计为自动模型提交或资源生成。

Import区分检测与选择入口、实际导入控制器、自动同步偏好、历史结果和导入后连接。暂停同步保留类别，修改类别仅影响后续同步。

Mini快捷键复用FSC-0068，导入后的MCP认证复用FSC-0119，插件安装复用FSC-0124；各入口仍保留自己的失败、重试、账户/宿主和防重条件。

22项精确源码helper/回调隔离用例通过；仅执行冻结控制回调、合成插件/应用分类、技能准备、导入偏好守卫与 OAuth 请求替身；未安装插件/技能、打开浏览器、读取个人资源、执行导入或提交模型任务。169个已选择源码单元的冻结文件与字节范围核验通过。

三页继续保留待模式核对；快捷键、MCP认证和插件安装登记为已有功能的新消费者，未重复增加相应功能定义。第三方包通过既有依赖清单外置，第一方策略与协调保留。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中30个已有局部合同，15个待展开。实际渲染/浮层/资源、导入执行与同步、账户连接和共享管理器均有明确接收边界；局部隔离通过不代表运行时、导入或产品验收。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
