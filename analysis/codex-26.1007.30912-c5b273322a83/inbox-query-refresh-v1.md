# 收件项列表、未读统计与刷新条件

本批补齐既有 FSC-0434 / AUT-M03 的选定读侧链路，与[写侧存储合同](inbox-storage-authority-v1.md)合用；[结构化结果](inbox-query-refresh-v1.json)记录12项源码事实及12条未执行补充场景。

列表端点默认取200项，并可按threadId筛选；未读统计独立查询整个身份范围，不受这两个参数限制。列表包含IN_PROGRESS、PENDING_REVIEW、ACCEPTED、ARCHIVED，未读统计只含PENDING_REVIEW及ACCEPTED且read_at为空。ARCHIVED可出现在列表，却不进入未读数。

renderer注册60000毫秒的刷新间隔和staleTime，查询键含序列化参数。inbox-items-changed在选定普通窗口分支请求按类型前缀失效inbox-items和list-automations，没有等待失效完成。组件缓存的窗口路由条件涵盖头像叠加、Spotlight、听写和快捷窗口路径；这个条件不能当作Codex／ChatGPT模式判定。

选定主进程构造器和URI适配连接到SQL读接口。实际组件挂载、传输、窗口消息、原生查询、有效身份与重启耐久性仍需运行验证。本批未执行客户端、目标模块、模型、服务或数据库。源码范围和绑定核对通过，不计产品行为通过。

功能、场景、任务和来源处置清单版本保持。原始选择、3份机械声明缓存和一次已修正的局部资格检查失败保存在压缩归档；缓存仅用于定位，不能代替语义判断。本批到已命名的运行边界收口，不再以其尚未运行验证为由递归追踪provider。
