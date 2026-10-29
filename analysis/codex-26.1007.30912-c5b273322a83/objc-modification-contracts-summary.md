# objc-js 源码与原生依赖边界

固定基线 `codex-26.1007.30912-c5b273322a83`。实际比较纠正了“native 源码已修改”的前提：所选 9 个 package/source/wrapper 文件与官方 objc-js@1.5.0 归档一致，包括 nobjc.mm、nobjc_block.h。已保存的差异在 x64 原生二进制和缺少 arm64 prebuild；源码一致不解释二进制来源或 ABI，也不构成维护源码补丁的依据。

22 条合同保留 19 confirmed、2 inferred、1 unresolved。保存单位为 17 native lexical、7 包装 JS、5 第一方函数，后两组共 12 个 JS 单位经过有限解析；第一方函数合计 2679 B。窗口事件、通知权限／RunLoop、Apple Event 工厂是需要保留的应用适配边界，第三方实现仍应通过依赖包引入。

[来源读者](objc-modification-contracts.json)连接[冻结作者合同](raw/objc-modification-contracts/author/objc-modification-contracts.json)和[独立审查](raw/objc-modification-contracts/independent-review/review.md)。独立父审查 278 项与 [native 子审查](raw/objc-modification-contracts/independent-review/native-block-review.md)210 项分别通过，不相加为功能或整个库的覆盖；源比较由作者执行，peer 没有重读原 bundle 或二进制。

C018 只在正常 callback 路径将首参数原样传给 resolve；B 是 block 编码，并非 JavaScript Boolean 校验。cleanup/logger/accessor 抛错、重复 callback、等待 helper、shutdown、回值缓冲区与完整生命周期仍未验证。另有旧 native-runtime 元数据识别已发布文件为 Mach-O x86_64，属于静态架构信息；实际构建来源、加载兼容、Node／Owl ABI 是不同缺口。

15 个原回归场景均未执行。本批为静态合同与 saved-unit peer，之后独立编译／加载证据须另列，不追溯升级本批。作者原 snapshot 保留“peer／build 尚未执行”的历史状态，新读者单独关联后续审查。全局证据、功能分母、模式排除与本批 runtime 次数均未改变，第三方源码及 AST 不进入正式分析交付。
