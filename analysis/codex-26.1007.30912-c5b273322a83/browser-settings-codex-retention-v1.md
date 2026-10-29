# 浏览器设置的 Codex 保留决定

**保留 FSC-0221 的四类原生设置页及 RAM-15，不能随 ChatGPT 专属功能删除。** 已把显式路由、访问策略、页面能力和 native 调用方连接起来；本批静态问题已收口，实际运行和独立 provider 资格仍开放。

`CodexLocal` 选择器检查 `pq.status === allowed`。浏览器设置使用 `codexOrWorkLocal`：`JAn=LAn(pq,hq)`，合并函数先返回已获准的 `pq`。所以同一个 CodexLocal 访问结果足以通过该 family，不要求 Work-local 结果也获准。这是可供实施的条件路径；family、认证方式和主机种类均不能代替当前产品模式判断。

进入条件按以下顺序保留：

1. 设置页把所选 host 的 `kind === local` 传入可见性 hook。`browser-use` 不在精简主机列表，其他 kind 会在逐页判断前被过滤；这里的 local 不证明物理本机。
2. family 获准后，还需浏览器可用、native 浏览器可用，或 primary 已结束加载且原因是 `statsig-disabled`、`config-requirement-disabled`、`wsl-disabled` 之一。最后一种情况允许展示设置，不代表浏览器能操作。
3. 最终不可见且不 pending 时外层跳转；pending 时不创建 outlet。可见优先于 pending，所以页面内部仍需独立校验能力。
4. 六条子路由均以 `slug=browser-use` 进入 M6。所选 usage 别名表没有这个 slug；工厂动态导入 `BrowserUseSettings→da`，保留 M6 的错误边界和 route key。
5. `da` 按所选 host 读取 `in_app_browser` 能力；扩展页另需开关 `2982604767`。新子页在加载中显示占位，已选同类页在重新加载时保留，确定不可用时 replace 回设置根页。

| 子页 | 内部 kind | 实现边界 |
| --- | --- | --- |
| 联系信息 | contactInfo | ki → Ai 原生 WebView |
| 扩展 | extensions | ki → Ai；另有扩展开关 |
| 密码 | passwordManager | ki → Ai 原生 WebView |
| 站点设置 | siteSettings | ki → Ai 原生 WebView |
| 下载 | downloads | 独立 ci 页面 |
| 历史 | history | Gr 页面；缺 browsingHistory provider 时返回根页 |

保留三项工程职责：renderer 管理准入、选择和生命周期；contracts 声明四类 native 边界；runtime adapter 提供特权页面和底层浏览器服务。Ai 即使没有 mount 通知接口也会尝试创建 WebView，不能将这一尝试记作成功或等价 HTML 回退。第三方实现继续通过独立依赖引入。

已有固定 Electron 42.3 guest 探针拒绝八个特权 URL 的结果继续适用，范围仅限该探针。四类页面的数据操作、独立 provider、来源、ABI 和构建方式仍需落实；本批不重复追踪已记录的 native 内部未知项。

本批复用 33 个原始源码节点，新解析一个 1,973 字节小模块（703 AST 节点），核对六条路由、六类子页、12 条源码结论和 12 条未执行子规格。509 功能、582 不同操作、1,844 条规范场景及模式标签不变；没有新增运行通过、客户端实现或构建资格。

详见 [结构化合同](browser-settings-codex-retention-v1.json)、[六条路由映射](browser-settings-codex-retention-v1.csv) 和 [来源证据](browser-settings-codex-retention-v1-evidence.jsonl)。
