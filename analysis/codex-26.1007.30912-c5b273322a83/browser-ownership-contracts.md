# 浏览器所有权接收契约

原客户端的所有权交接包含成对的 lease/ID、路由与存储校验、renderer/host generation、防重复接收和失败销毁；并非传入 WebContents ID 后直接显示。[九条来源事实](browser-ownership-contracts.json)定位到两份完整原 Program 的选定函数、方法和属性赋值。

公共 Electron 42.3.0 的一次独立探针得到了两个结果：

- 把同一个 WebContentsView 从一个隐藏自有窗口移到另一个，WebContents ID、编辑后的表单值和 JS 堆值均保留。
- 移除旧 view 后，用其 WebContents 构造新 view，仍因“already attached to a window”被拒绝。

因此可以评估“主进程持有并移动同一视图”的第一方管理器；不能把重建 view、历史恢复、live clone 和 renderer 的 Owl adoption lease 当成同一能力。公开 [WebContentsView 构造接口](https://github.com/electron/electron/blob/v42.3.0/docs/api/web-contents-view.md)支持传入 WebContents，但本次负例表明仍需处理已有附着关系。

恢复模块须保留接收校验、生命周期、安全偏好和导航所有者。跨窗口 renderer receiver 还会调用 adoptWebContents，这一私有元素方法及 clone、消息送达、完整浏览器行为尚未验证。原生事件的真实时序没有由静态函数检查证明。

探针退出码为 0，无残留自有进程；没有运行原客户端或模型任务。两次初始 AST 抽取因输出父目录缺失而失败，修正后的结果另存，没有将失败计作成功。当前源码范围检查不等于客户端功能验收。[来源与执行记录](stage-consolidation-provenance.json)保留上述边界。
