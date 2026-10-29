# objc-js 独立源码构建验证

在隔离目录从官方 objc-js@1.5.0 源码实际构建。原配方 configure 成功，native build 因缺少 ffi.h 失败；独立副本只调整 SDK ffi include 与系统动态 -lffi，configure/build 均成功。27 个 native 源文件（6 .mm、21 .h）保持一致，原 binding.gyp 未改。该结果给出了可审查的构建配方候选，尚未证明干净环境可复现。

实际产物为 x86_64；在 Node22.23.2/x64 上唯一一次模块加载成功，10 个预期导出都是函数，未调用加载后的导出原生方法。没有执行原客户端、随包prebuilt、通知／窗口eventhook、RunLoop或Apple Event。只有 module init 与导出类型检查，不能当完整功能验收。

[构建读者](objc-independent-build.json)连接[作者实际结果](raw/objc-independent-build/author/independent-build.json)及[独立审查](raw/objc-independent-build/independent-review/review.md)。独立65项metadata与子审查82项编译日志核对分列；没有重新编译、重载或独立验证smoke instrumentation。原失败、SDK成功与单次smoke的实际命令、stdio、时间和exit均留owned evidence。

原配方2条及SDK6条已发出的 .mm clang命令均未包含声明的 -fobjc-arc；这是一项本机构建观察，不能推断已发布binary的内存管理配置。brew最小环境探针因HOME缺失失败，空输出被转为当前路径的准备字段也有明确纠正，不能用它证明libffi存在。

Node header缓存来源未重新核官方归档，全部package TS/build/prebuild所需脚本不齐；Owl Node24、ARM、传统ABI、外部库兼容、回调生命周期和原发布binary来源仍待验证。原22条静态合同及15个未执行场景保持历史范围。本次仅正式交付metadata，第三方源码、构建配方和编译产物留local-only；维护方案继续以固定依赖和单独配方补丁为候选。
