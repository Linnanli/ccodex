# 本批恢复任务与依赖决定

这是分析阶段的可执行实施依据，覆盖本批30项目标；不是已经实现或可构建的客户端。全工程仍按原分析计划验收，其他功能组不得被本表替代。

| 恢复任务 | 第一方职责与拟维护模块 | 外部依赖/接口 | 验收出口 |
| --- | --- | --- | --- |
| R03-01 外观状态控制 | renderer/features/appearance：变体快照、串行写入、paired-write补偿、partial标记、edit/accent revisions；页面与provider分开 | settings repository、theme parser/normalizer、query lifecycle | 第二次写入/补偿分别失败、连续编辑、旧预设晚到；与真实持久化核对 |
| R03-02 外观控件 | renderer/features/appearance：19项目标、Advanced/双模式本地状态、数字/hex草稿、导入取消与重置范围 | React、query、schema、菜单/slider/color picker/animation；clipboard与system fonts宿主接口 | 按FSC-0074至0092的57条规格验收；字体、系统外观和Dock图标另测消费者 |
| R03-03 Appshot编排 | renderer/features/appshots：热键状态、偏好、平台/开关、错误反馈；host/capabilities/appshot：独立接口合同 | getState/setHotkey、原生捕获、Mini/会话路由、声音与资产 | FSC-0093至0096；必须观察真实热键注册/捕获/路由，不以保存成功代替 |
| R03-04 桌面通知 | renderer/features/notifications/desktop：四种提醒、声音导入/预览、系统权限反馈；host/capabilities/notifications | systemPermissions、notifications、audio decode/playback、实际事件发送者 | FSC-0097至0102；取消不保存、独立播放/保存失败、重启后自定义音频仍可用 |
| R03-05 账户通知候选剥离 | renderer/features/notifications/account单独隔离；按账户/渠道保存与取消，保持共享控件独立 | /notifications/settings、账户/个人账号许可与contacts、任务管理导航 | FSC-0103；先核对选中模式与全部消费者，再决定只删除账户专属分支；整块chunk删除不允许据此推断 |

模块路径是职责划分提案，不是要还原的原作者目录，也没有在源码树生成这些文件。第三方实现不复制进拟恢复源码；确切包来源、版本、修改状态以[依赖引入决定](dependency-import-decisions.md)和[内嵌依赖调查](embedded-dependency-summary.md)为准。本批只确定引用边界，尚未确认身份的 primitive/color-picker 等不能凭 dist/chunk 名猜包。

实施顺序：先定义设置仓库与宿主capability接口，再恢复外观队列/草稿和桌面通知/Appshot编排，最后接真实宿主、存储和渲染消费者。账户通知剥离核对独立进行，不阻断其余模块的恢复设计；Owl与公开app-server的全局替换决定仍需专项证据。

干净构建的新增输入：主题解析/预设资源与字体加载来源；Dock图标预览/应用接口；Appshot演示与捕获/声音资源；自定义提醒声音的本地导入资产与迁移规则。原归档资源可用于分析定位，正式工程每项都必须有独立资源来源/生成方式和打包路径，不能引用原安装目录。没有来源的资产继续列缺口，不通过删除对应功能缩小范围。

升级时为这30项目标保留稳定FSC标识，以入口条件、偏好schema/default、状态机、宿主方法与90条产品规格比较新版本；bundle文件名和minified符号仅用于证据定位。旧v9的支撑关联修正已应用到v10；旧快照保留。跨入口等价、整体模式分类与其余35个设置容器尚未完成，不能据本表宣称全面可升级。
