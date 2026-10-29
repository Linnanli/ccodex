# 同版本后台的构建输入与锁文件策略

固定提交 `740e5af33c71225640e0c1c1555c514c2c93ab74` 的候选构建配方已能具体指明。workspace alpha版本与锁中0.0.0的差异有发布工作流的直接解释；本批未编译、安装依赖、签名或运行包测试，完整客户端重建仍未验证。

| 项目 | 同提交证据与决定 |
| --- | --- |
| 工具链 | Rust 1.95.0；clippy、rustfmt、rust-src |
| 基线目标 | x86_64-apple-darwin；发布矩阵也包含aarch64-apple-darwin |
| primary bundle | codex、codex-code-mode-host、codex-responses-api-proxy |
| app-server bundle | codex-app-server、codex-code-mode-host；尚未接受替代冻结codex入口 |
| feature | 所选发布命令没有额外feature参数；CLI无自定义features表，传递依赖仍需各自解析 |
| 构建身份 | 从codex-rs运行，导出STABLE_GIT_COMMIT为checkout HEAD；保留根及子目录Cargo配置 |
| profile | thin LTO、line-tables-only、codegen-units 4；macOS通过环境将split debug覆盖为packed，后续另做符号归档/strip |

发布源码明确说明：release tag只提升Cargo.toml，不重写workspace锁。已保存的提交补丁也只修改该版本；macOS voice job先执行`cargo update --workspace`再让Bazel读Cargo图。现有锁中的0.0.0并非混用版本的充分证据，原锁也不是已经通过的`--locked`构建输入。

后续源码构建阶段应保留原锁，在隔离checkout中用固定工具链刷新workspace记录，保存并审查完整diff，再固定审查后的派生锁。刷新是否改变外部依赖尚未实际验证。本批没有修改锁或执行这些命令。

所选primary发布命令展开为以下候选配方（未执行）：

```sh
cargo build --target x86_64-apple-darwin --release --timings --bin codex --bin codex-code-mode-host --bin codex-responses-api-proxy
```

此命令还依赖工作流之前的rusty_v8产物配置/摘要检查。语音另用Bazel构建voice-host/native_runtime并检查文件，完整资源包还有签名与打包步骤。SDK、传递build.rs和全部artifact身份尚未闭合，不能把这条Cargo命令当成完整客户端构建成功。

桌面provisioned工作流的资源包布局含`CodexCLI.app`，与冻结launcher包装线索相符；它受repository变量控制，并要求独立profile/签名校验和sandboxed code mode包测试。这里取得的是公开流程源码，没有拿到签名凭据、触发工作流或证实冻结native来自该次发布。

独立客户端应把固定提交后台作为独立组件/构建依赖，继续保留已取得的预测fork契约。不能依据依赖中的chatgpt名称裁掉共享代码；本批也没有找到CLI级disable-chatgpt构建开关。客户端模式剥离仍由既有调用和模式证据决定。

取得6份新构建源码及6份同提交目录，共12个有完整收据的HTTP200响应；3个DNS失败收据和最初helper输入断言失败亦保留，最初并发调用缺少完整收据的尝试不混入成功计数。12条结论和13个来源单元已记录，核心台账、产品场景和授权保持原值。

本批已收口。下一批仅核对setup-rusty-v8及third_party/voice实际引用的构建产物身份，最多5份目录确认的源码/manifest；不重做通用运行时可行性审计。

[结构化决定](backend-build-inputs-v1.json) · [逐项证据](backend-build-inputs-v1-evidence.jsonl) · [发布构建](https://github.com/openai/codex/blob/740e5af33c71225640e0c1c1555c514c2c93ab74/.github/workflows/rust-release.yml) · [provisioned资源包](https://github.com/openai/codex/blob/740e5af33c71225640e0c1c1555c514c2c93ab74/.github/workflows/rust-release-provisioned-macos.yml)
