# 普通线程头部的面板控制补充

已核对 Fa 的剩余 ai/oi 控件：ai 精确导入 K，提供底部按钮显示偏好和底部面板开关；oi 导入 q，提供侧面板开关。它们不提供 review 轮次或标签选项。Fa 在 archived preview 或统一 header 分支不渲染这两个控件。

复用 FSC-0009、FSC-0401、FSC-0409 三个既有目标与操作。General 设置页和头部 checkbox 经同一 QWn/_Gn 导出读取 wzt、调用 ezt；偏好键为 app-shell-bottom-panel-launcher-visible，默认 true。checkbox 隐藏 launcher，不调用面板显隐接收方。底部按钮复用已分析 Hc，保留可见、tab、route/capability 与 guarded focus 分支。

侧面板按钮 disabled=!showReviewTab，回调本身直接 apa(scope)，没有再检查该参数。apa 有自己的 Qp/EC/tab 守卫，并可进入布局恢复、deferred browser fallback 与 RAF 焦点恢复。它不同于 native 命令路径，不能未经观察就宣称跨入口等价。

本批作为现有功能、任务与 MPA-M02 职责的有效证据补充，不重写全套清单。500功能、566不同操作、1761条原有未执行规格、51任务、104职责与48粗facade均未增加。11条头部入口子场景关联9条原规格，全部未执行；不会重复计入新规格或产品通过。

THV-GAP-HEADER 中 ka/ya/ai/oi 的选定静态回调合同已交付。local chrome、effective provider、模式、真实布局/浏览器/终端/存储后效与独立构建仍未验；全页面与完整分析未完成。本批没有新模型任务、目标运行、服务调用、剪贴板或Git修改。

[合同及去向](thread-panel-header-refinement-v1.json) · [当前功能基表](feature-scope-v47.json) · [当前任务基表](restoration-coverage-v38.json) · [当前职责基表](feature-module-ownership-v13.json)
