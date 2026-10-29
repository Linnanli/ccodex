# Owl 独立取得与构建来源定向分析

状态：有界元数据调查完成，GAP-08 保持 open。没有选定、取得、构建或验收任何替代运行时；完整 Codex 功能目标保持。

冻结包确认 runtimeName=owl，runtimeArchiveSha=d47046415e1f69a9c2dd6b272cdf131225bc508582c43b7487065251b1bf9cd8。独立 Owl 下载/源码/类型头文件/许可证/版本映射没有在本次检查范围建立。该声明摘要不等于 ASAR 摘要或已交付 Codex Framework 二进制摘要；框架 plist 的 155.0.8059.40 和 root electron devDependency 的 42.3.0 都不能替代实际兼容/ABI 测量。

根脚本给出了 owl-shell ensure/run/prepare-native-modules 和 Owl types/prepare 接口名。既有冻结清单中的 30 个 build-input occurrences 全为 missing-from-release，包括对应脚本与 lock/workspace/config。release 根文件只有 package.json，没有 root README/LICENSE；manifest 没有 repository/homepage/license/Owl 分发声明。这是有界 release 元数据缺失，不能推导外部源码不存在。

root metadata 的 [官方 x64 client feed](https://persistent.oaistatic.com/codex-app-prod/appcast-x64.xml) 是整客户端更新线索。初次 web 读取失败与随后 HTTP 部分 XML/超时均已保留；另一次只读公开元数据请求完整取得 24046 字节 XML，10 个 item 中包括 26.1007.30912/build 20156，声明最低 macOS 13.0、[整客户端 archive URL](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-darwin-x64-26.1007.30912.zip)、长度 703637622 和 EdDSA 签名。archive 未下载、验算或验签，app 版本/build 匹配不能证明该 archive 与冻结 ASAR 的字节对应，也没有提供独立 Owl 分发/源码/许可。[官方开源组件表](https://learn.chatgpt.com/docs/open-source)列出了 CLI/SDK/App Server 等，但该表没有提供 Owl 取得入口。限定搜索无结果，仍不能证明不存在。

| 已核对组件 | 可独立取得渠道的证据 | 版本与完整性 | 本次仍未证明 |
| --- | --- | --- | --- |
| Owl | 冻结 package/runtime/plist metadata；没有独立渠道成立 | runtimeArchiveSha 仅声明；交付 x86_64 framework SHA-256 已核验 | 独立下载、源码、许可、types、build scripts、ABI、平台矩阵、升级通道 |
| 普通 Electron | [v42.3.0 release](https://github.com/electron/electron/releases/tag/v42.3.0)、tagged README/LICENSE、公开 source tag 和 [asset metadata](https://github.com/electron/electron/releases/expanded_assets/v42.3.0) | darwin-x64.zip 发布摘要 92bc6bc82cbfe4c855e9b8c55cf48c32f0448553bb74defe8cc436da9588a73e；源码 MIT | 未下载/验算 archive；未与 Owl 比较；42.3.0 只是原 root devDependency |
| Sparkle | [2.9.1 release](https://github.com/sparkle-project/Sparkle/releases/tag/2.9.1)、tagged source/Package.swift/LICENSE | [SPM manifest](https://raw.githubusercontent.com/sparkle-project/Sparkle/2.9.1/Package.swift) checksum 9fec2b888e6e2940b1bfbd5d3d010b9f67076b52170923549095cbb74132403b；macOS 10.13 声明；MIT + external notices | 未下载/验算 archive 或比对 shipped 修改；不能替代 Owl native update binding |

公开 dependency 的版本、URL、平台及 published digest 都与固定 desktop baseline 的实际发行身份分开。web capture 源哈希固定 provider 返回文本；另行冻结的 XML 源哈希固定真实收到的 HTTP body；两者均不是发行 archive 的哈希。没有第三方实现副本；未执行目标代码或 UI，未发起目标网络请求或模型任务；公开来源工具访问和只读匿名 XML 请求仅用于元数据调查。没有读取真实凭据/环境值/账户历史。

改变独立构建决策需要：对应 d470… 的官方/授权独立 archive 或源码及真实取得摘要；Owl custom runtime 许可；匹配的 types/headers 和 prepare/ensure/native rebuild/package 完整 inputs；确切 runtime/ABI/平台证据；四个私有边界及完整保留 Codex 功能契约的验收；第二版本在同一契约下的升级比对。main.json 中 U01–U06 给出了逐项证据要求。公开 Electron/Sparkle 的可取性只提供后续依赖候选，本轮没有 adoption 或 upgrade acceptance。

复现：运行 producer.py（只读输入/自身目录写入），再运行 verifier.py。finalProducts 由 freeze-manifest.json 精确固定；独立核验范围是 pins/ranges/schema/identity separation，不能证明 runtime 行为。
