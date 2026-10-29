# 固定版本 npm 上游逐文件比较

基线：`codex-26.1007.30912-c5b273322a83`。状态：`complete`。

仅比较冻结根包与官方 npm 精确版本归档。归档仅静态读取，不解包安装、不执行脚本；第三方实现保留在 ignored `raw/upstream`，发布结果只有定位、哈希、统计和包元数据差异。

| 包 | 冻结根文件 / 上游文件 | 共同相同 / 共同总数 | 源码相同 / 共同源码 | 上游独有 / 冻结独有 | 修改状态 |
| --- | --- | --- | --- | --- | --- |
| better-sqlite3@12.11.1 | 19 / 49 | 17 / 17 | 13 / 13 | 32 / 2 | source-match, cropped, native-unverified |
| node-pty@1.1.0 | 20 / 286 | 15 / 17 | 11 / 13 | 269 / 3 | source-modification-candidates, cropped, native-unverified |
| objc-js@1.5.0 | 36 / 37 | 35 / 36 | 31 / 31 | 1 / 0 | source-match, cropped, native-unverified |
| tslib@2.8.1 | 14 / 14 | 14 / 14 | 6 / 6 | 0 / 0 | source-match |
| node-addon-api@8.9.0 | 18 / 18 | 18 / 18 | 8 / 8 | 0 / 0 | source-match |

`source-match` 仅证明共同源码文件字节一致；`metadata-modified` 表示 package.json 语义有差异；`cropped` 表示上游文件未被交付；`native-unverified` 表示原生 ABI、来源及构建仍未验证。共同文件一致不证明整个包未修改、可完整重建或客户端行为兼容。

## better-sqlite3@12.11.1

[官方固定版本元数据](https://registry.npmjs.org/better-sqlite3/12.11.1)；[归档](https://registry.npmjs.org/better-sqlite3/-/better-sqlite3-12.11.1.tgz)。`dist.integrity` 已验证；归档 SHA-256：`ebf0ed75a7a59dbcb3b24bbd014ef49d9f15bc328e4adcbf516f2a8fadfa2835`。

package.json 语义差异：无。
源码或构建输入修改候选：无。
冻结原生文件：`build/Release/better_sqlite3.node`（shipped-only）。
额外 `.codex-native-module-build.json` 已单列为生成构建元数据；所列产物哈希存在缺失或不匹配。其自报运行时与构建签名未独立验证。
排除嵌套安装文件：1；逐文件来源和分母见 `upstream-comparison.json`。

## node-pty@1.1.0

[官方固定版本元数据](https://registry.npmjs.org/node-pty/1.1.0)；[归档](https://registry.npmjs.org/node-pty/-/node-pty-1.1.0.tgz)。`dist.integrity` 已验证；归档 SHA-256：`c7517f19083ddcb05f276904680eb2b11a6b5ecab778b8e4e5685a6d645b3f60`。

package.json 语义差异：无。
源码或构建输入修改候选：`lib/windowsPtyAgent.js`, `lib/windowsTerminal.js`。
冻结原生文件：`build/Release/pty.node`（shipped-only）, `build/Release/spawn-helper`（shipped-only）。
额外 `.codex-native-module-build.json` 已单列为生成构建元数据；所列产物哈希存在缺失或不匹配。其自报运行时与构建签名未独立验证。
排除嵌套安装文件：1；逐文件来源和分母见 `upstream-comparison.json`。

## objc-js@1.5.0

[官方固定版本元数据](https://registry.npmjs.org/objc-js/1.5.0)；[归档](https://registry.npmjs.org/objc-js/-/objc-js-1.5.0.tgz)。`dist.integrity` 已验证；归档 SHA-256：`314dd3561804c2c7d6568094ae2c3e3dc4532e50991def46985491748089effe`。

package.json 语义差异：无。
源码或构建输入修改候选：无。
冻结原生文件：`prebuilds/darwin-x64/node.napi.node`（different）。
排除嵌套安装文件：12；逐文件来源和分母见 `upstream-comparison.json`。

## tslib@2.8.1

[官方固定版本元数据](https://registry.npmjs.org/tslib/2.8.1)；[归档](https://registry.npmjs.org/tslib/-/tslib-2.8.1.tgz)。`dist.integrity` 已验证；归档 SHA-256：`66f635d5eeabae44807534976913a102cf615b9a045368359c9f79ae6ee2119e`。

package.json 语义差异：无。
源码或构建输入修改候选：无。
冻结原生文件：无。
排除嵌套安装文件：0；逐文件来源和分母见 `upstream-comparison.json`。

## node-addon-api@8.9.0

[官方固定版本元数据](https://registry.npmjs.org/node-addon-api/8.9.0)；[归档](https://registry.npmjs.org/node-addon-api/-/node-addon-api-8.9.0.tgz)。`dist.integrity` 已验证；归档 SHA-256：`19b87e2ce3a77fec0121ac97d7db088aae28aacfff481adab50d5f61b70e68f4`。

package.json 语义差异：无。
源码或构建输入修改候选：无。
冻结原生文件：无。
排除嵌套安装文件：0；逐文件来源和分母见 `upstream-comparison.json`。
