# 模式偏好、状态与持久化边界

固定基线 `codex-26.1007.30912-c5b273322a83`。所选Fu导出实际接到FJ，fd接到Uk，Ch接到_I。模式调用只有两个参数，未启用可选coerceStoredValue或delay；不能以这条链中的名称宣称模式值域已被校验。

不同值的同步正常路径先更新TI Map，再调用ARt第二参数注入到$Rt的publisher，再通知DRt，随后执行局部atom setter；相等值跳过publisher但仍有局部写入。同步抛错可能留下部分更新，未await的返回Promise需单独判断。具体publisher caller、provider/store实例与耐久后端仍未知，附近generic localStorage代码未接到这条模式链。

[来源读者](mode-preference-storage-origin.json)连接[冻结46条合同](raw/mode-preference-storage-origin/author/mode-preference-storage-origin-contracts.json)与[独立审查](raw/mode-preference-storage-origin/independent-review/independent-review.md)。51保存单位为50新单位及1复用导入，137319字节包含较大导出声明；5条来源链与18个场景不等于完整功能分母。作者11569项、独立保存单位解析758项／metadata845项分别登记，不相加为功能覆盖率。

读者必须同时应用[清理语义勘误](raw/mode-preference-storage-origin/qualification/cleanup-errata.json)：IJ取消注册依次调用c()、l()，只有c正常返回后才调用l；i.watch建立订阅同步抛错不保证清理之前CI注册。callback finally仅重置局部重入标记。旧E29／S14原文和journal未改；勘误不增加46条之外的证据行或功能。作者勘误79项与独立delta53项另列。

本批为静态来源分析，未执行实际模式UI、provider、存储或恢复；旧MODE26与全局登记、模式排除0不改。隔离内存替身函数观察另批登记，不升级本快照的18个真实行为场景。
