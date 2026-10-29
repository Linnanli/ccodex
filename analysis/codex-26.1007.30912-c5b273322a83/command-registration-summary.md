# Renderer 命令注册的完整 Program 核对

固定基线 `codex-26.1007.30912-c5b273322a83`。旧6个renderer注册候选均已接到同一个原Program函数 `Pw`；此前函数片段保留的callee身份缺口在这6处关闭。实际组件挂载、store实例和命令执行仍未验证。

完整 `app-initial` 中，同一绑定共有49个直接调用，旧6个只是子集；另外43个调用现已登记。[完整清单](command-registration-contracts.json)保存所有范围、参数、局部参数绑定和最近函数。47处使用静态字符串首参，涉及44个不同命令ID；2处动态ID保留。调用数、ID数均不作为用户功能数。

`Pw` 是 effect 注册hook：处理enabled/isActive/priority以及键盘、context和普通handler；调用 `Pqt`登记到 `dJt`，再更新独立的 `Nqt` 菜单/可用性记录，cleanup分别移除。`Pqt`允许同一ID保留多个handler，并按注册对象身份注销。`Lqt`按normal再fallback、同级逆注册顺序尝试，只有严格false表示不消费，再查默认命令表。普通handler的返回值没有由Pw返回，dispatcher也不等待Promise；维护时需要保留这些顺序和返回值语义。

静态scope证明了注册关系；没有执行源码函数、触发原客户端命令或提交模型任务。本次不是行为验收，没有增加用户功能、模式归属或真实通过场景。

`Pw`的真实导出为 `IBn`。另发现24个具有该静态import拼写的文件，作为词法候选保存；尚未据此宣称跨文件绑定或全应用覆盖。下一批逐个完整Program核对这些import和局部作用域，枚举直接调用及传递边界。默认命令表、实际dispatch调用方、账户/平台/模式和挂载条件仍单列，不能把菜单元数据当handler。

本批解析2次同一完整原Program，均无解析错误；既有源码单位和新增核心范围经冻结字节核对。原6条入口ID及原台账保持不变。[来源索引](command-registration-provenance.json)保存解析器、工具源码、命令、stdout/stderr及终态；[旧入口分组](entry-family-summary.md)和[实施计划v6](implementation-plan-v6.md)继续有效。
