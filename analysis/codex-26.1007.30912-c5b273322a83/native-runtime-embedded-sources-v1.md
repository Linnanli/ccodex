# 原生框架内嵌源码与 preload 构建边界 v1

从冻结的 Codex Framework 新提取7份可完整解析的 JavaScript，共427893字节。它们补充了原REA应用归档分析未覆盖的运行时脚本输入。**可恢复的接口装配边界增加了；完整 Owl 运行时仍未取得或验收。**

| 内嵌脚本 | 字节 | 模块工厂出现数 |
| --- | ---: | ---: |
| browser_init.js | 150281 | 70 |
| isolated_bundle.js | 15270 | 4 |
| node_init.js | 19816 | 1 |
| renderer_init.js | 43733 | 31 |
| sandbox_bundle.js | 163132 | 76 |
| utility_init.js | 20778 | 12 |
| worker_init.js | 14883 | 19 |

共213个模块工厂出现位置、150个不同路径标签；同名标签在不同bundle中的工厂分别保留。167个位置属于 `./lib/` 路径，46个带 `node_modules` 路径。路径标签可指导边界恢复，不能直接当作150个原始源码文件或业务模块。原框架SHA-256与基线文件清单一致，所有位置保留二进制字节范围。

## 对工程方案的具体改变

1. **区分业务源码与运行时。** browser API表有39个惰性loader；选定app/window/session等wrapper继续委托原生绑定。恢复这层JS不会产生底层C++实现或SDK。上述运行时脚本作为依赖分析证据，不生成到第一方业务源码目录。
2. **按进程决定依赖打包方式。** sandbox preload的require只查指定缓存和loader表。维护源码可继续用包导入，构建时把所需JS依赖打入preload bundle；不应统一把所有第三方包external。第三方实现由包管理器提供，不手工生成副本。需要受限表外能力时，落实相应main/桥接契约。
3. **保留sandbox启动装配。** pre-init向process shim注入`binding.get`及process元数据，再运行preload。普通npm包的存在不代表已经恢复这个过程。contextBridge还有contextIsolation检查和原生world接口。
4. **独立登记preload资源及错误。** 主侧只保留绝对路径，按frame/service-worker选脚本，逐条返回读取内容或错误。sandbox侧逐条执行或报告preload-error；读取成功的空内容会跳过。新工程须使用自己的打包资源路径。

## 已核对的跨进程合同

`BROWSER_SANDBOX_LOAD`由runtime内部RPC返回preloadScripts、webPreferences和process元数据。主侧handleSync返回`[null, await result]`或`[error]`；renderer invokeSync解包并传播truthy错误。这里只登记源码中的字段，没有读取实际环境变量。preload入口有5个已加载名称（electron、electron/common、electron/renderer、events、node:events）和4个惰性名称（timers、node:timers、url、node:url）；未知名称抛错。外部输入仍可能提供其他process字段，不能把测试switch分支误读为最终对象的全局否定证明。

frame IPC invoke在选定wrapper内按frame.ipc、WebContents.ipc、全局ipcMain优先级选第一个handler；internal和service-worker另行分流。这个规则不证明底层网络或越界IPC限制已恢复。

## 第三方边界

46个模块位置提供23个包名线索、31个包安装位置标签，全部位于sandbox运行时bundle。嵌套的get-intrinsic、has-proto、function-bind等位置分别登记，未猜测是否同版本。仅base64-js、buffer、ieee754与原202行依赖表有同名行；同名不证明相同实例。另20个名称尚未出现在那张表，不能简单将202加23作为新的依赖总数。实际版本、许可和修改状态均未由路径标签证实。

## 限制与收口

7份源码的102处`._linkedBinding`成员调用涉及49个字面名称；其中59处直接global process调用涉及44个名称，别名调用另行保留。不能把全部语法匹配当成已证明的同一provider。17个已选非标准方法名中，16个在cstring中有精确字符串；这不是方法注册或原生行为证明。未匹配到Windows legacy policy方法名，也不证明其实现不存在。

本批按计划4.6使用完整Babel AST补充REA结果，没有重新运行REA，没有执行目标脚本、客户端、模型或原生调用。未取得原生实现、独立provider来源、headers、ABI与完整构建配方；clone、权限、特权设置及实际产品行为继续待验收。提取规则只覆盖选定cstring模式，不宣称已发现全部内嵌代码。

509项功能、504 unknown/5 shared、582个不同操作、1844条未执行场景及原完整验收标准保持。已关闭这7份内嵌脚本的边界提取批次，后续复用这些位置；不因底层实现未知而重复提取。

[逐项合同](native-runtime-embedded-sources-v1.json) · [213个模块位置](native-runtime-embedded-sources-v1-modules.csv) · [23个依赖线索](native-runtime-embedded-sources-v1-dependencies.csv) · [证据](native-runtime-embedded-sources-v1-evidence.jsonl)
