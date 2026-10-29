# 原生应用角色、菜单结构与浏览器历史 v1

固定批次 SQ-02-menu-native-history-06 已为 records87..96 的10条来源确定去向：3个用户目标、6项操作，另有4条集成或容器机制。

| 目标或机制 | 已确认的源码边界 |
| --- | --- |
| FSC-0419 请求退出应用 | At委托quit角色；Mac放入appMenu，其他平台在File子菜单存在时追加Ctrl+Q。复用已有退出确认/清理合同，原生事件投递和真正退出仍未验证。 |
| FSC-0420 应用可见性 | hide、hideOthers、unhide为同一目标的3项操作，经Mac条件进入appMenu；实际OS效果属于运行时依赖。 |
| FSC-0421 浏览器页面历史 | 两方向经隐藏快捷键生成器进入Browser子菜单；Ve将go-back/go-forward委托给聚焦页面管理器，无应用路由回退。 |
| Services | 原生服务菜单集成描述；没有枚举具体服务动作。 |
| File、Application menu、View | 装配容器；File后续插入动作，View后续赋值It，appMenu按Mac条件加入。没有独立用户操作。 |

浏览器历史与FSC-0418应用路由历史、FSC-0411相邻线程列表导航分别保留。Ve无聚焦webContents时直接false；有有效聚焦窗口时只尝试该窗口，否则遍历未销毁窗口。只有manager返回严格true才停止尝试。两个历史回调丢弃返回值，没有调用ensurePrimaryWindowVisible或renderer路由。生成器受browserPane和快捷键过滤控制，输出数量为0..N。

退出逻辑复用shutdown-persistence.json中的first-party合同：before-quit守卫/确认、will-quit重入锁及分支清理。初始allSettled组没有总体超时，之后context清理才使用5秒等待。历史源码/测试替身记录不升级为真实退出或持久化通过。

本批复用已保存CZe和退出合同，新增整Program解析、REA运行、客户端启动、模型提交、服务调用、第三方实现副本、产品验收均为0。现有MENU维护边界承接模板/委托；37职责及14个菜单增补提议仍待SQ-03统一，无新增维护模块。

当前[功能台账v34](feature-scope-v34.json)为421项有限定义、435项用户操作、117项支撑；[规格v31](feature-scope-v31-scenarios.json)为1387条未执行规格。[覆盖v25](restoration-coverage-v25.json)仍49任务，[排序v8](restoration-current-ordering-v8.json)仍两套58节点图。完整产品分母和模式归属仍有缺口。

[来源v12](legacy-entry-dispositions-v12.json)累计68条菜单目标部分关联（64schema、4生成选项），另4条机制去向；仍有894条来源无功能关联，其中包含无需独立功能的这4条机制。角色待审0、完整功能解决0，二者不能混同。九项标准/39项要求状态没有因新增计数而提升。

停点：固定10条已分配目标或机制并标明运行时断点。后续继续剩余固定来源，随后统一模块、状态、依赖与存储职责；本批不深入原生角色或浏览器历史管理器实现。
