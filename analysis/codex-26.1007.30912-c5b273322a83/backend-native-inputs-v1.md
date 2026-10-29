# 后台 V8 与语音构建输入

固定提交`740e5af33c71225640e0c1c1555c514c2c93ab74`的两条构建输入边界已取得具体来源。V8的版本/profile和校验信任起点已明确；voice公开manifest已给出固定上游归档与源码构建目标。尚未校验发布二进制、取得完整toolchain或运行构建。

V8 crate为`150.4.0`，与workspace和Cargo锁一致。解析脚本在当前锁含唯一v8版本时直接采用该值。action选择`rusty-v8-v150.4.0`中的`ptrcomp_sandbox_release`静态库及匹配Rust bindings，并设置`RUSTY_V8_ARCHIVE`和`RUSTY_V8_SRC_BINDING_PATH`。

校验链为：固定提交中的manifest索引 → 目标checksum manifest的摘要 → 静态库与bindings各自摘要。已取得索引中的8项目标pin；基线x86_64-Darwin的二级manifest声明摘要为`d85c7ae0cf437a4415376c4b5b7daba50b0dcbe30f52612d21df8ce52eb8ada0`。这不是静态库摘要。本批没有下载二级manifest或二进制，不记为产物校验通过。

voice的`native_runtime`目标使用以下manifest来源。摘要和URL全部保存在结构化结论中；以下版本是仓库声明，未逐个下载上游归档核验。

| 来源 | 版本 | manifest角色 |
| --- | --- | --- |
| meson | 1.12.0 | build-tool |
| ninja | 1.13.2 | build-tool |
| libffi | 3.8.0 | native-library |
| pcre2 | 10.47 | native-library |
| zlib | 1.3.2 | native-library |
| opus | 1.6.1 | native-library |
| glib | 2.88.3 | native-library |
| proxy-libintl | 0.5 | native-library |
| gstreamer | 1.28.6 | native-library |
| gst-plugins-base | 1.28.6 | native-library |
| gst-plugins-good | 1.28.6 | native-library |

另有GLib归档内的gvdb，固定revision为`2b42fc75f09dbe1cd1057580b5782b08f2dcb400`，无需独立fetch。Bazel配置按执行平台与目标CPU选择native prefix/runtime；宏、转换脚本、LLVM/pkg-config/SDK输入仍作为具名边界保留。license清单与是否应用上游补丁尚未在本批核实。

采用决定：V8保留固定版本/profile的库与bindings配对构建依赖；voice使用固定上游归档的独立源码构建组件，第一方适配器单列。第三方实现不进入恢复客户端的业务源码。不能用默认V8产物或任意本机GStreamer代替这些输入，也不能据此宣布桌面Owl runtime已可替代。

共取得5份源码/manifest、4份同提交目录，9个完整HTTP200收据；仅解析和检查文本，没有import或运行下载的Python/action/Bazel代码，没有下载native发行物或上游源码归档。10条结论、9个来源单元已保存。核心台账、功能/模式/场景数量及授权不变，完整独立构建和实际行为仍未验收。

本批收口，不继续沿已命名provider递归。下一批回到冻结客户端中仍未归属的Br `app/installed`、`app/read`两条调用，核对真实消费者和既有功能/机制归属。

[结构化决定](backend-native-inputs-v1.json) · [逐项证据](backend-native-inputs-v1-evidence.jsonl) · [V8 action](https://github.com/openai/codex/blob/740e5af33c71225640e0c1c1555c514c2c93ab74/.github/actions/setup-rusty-v8/action.yml) · [voice来源](https://github.com/openai/codex/blob/740e5af33c71225640e0c1c1555c514c2c93ab74/third_party/voice/sources.json)
