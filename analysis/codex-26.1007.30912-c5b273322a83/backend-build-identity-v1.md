# 后台构建标识与公开源码对应

公开 npm 候选的来源已经有进一步证据：其 native CLI、同包 voice 清单与已保存公开源码提交均对应 `c1382380de69521303b416720a52f42d51af6248`。当前资格是**声明/嵌入提交对应**，尚未验证构建证明或源码重建；完整后台采用仍未通过。

| 对象 | 桌面冻结包 | 公开 npm 候选 |
| --- | --- | --- |
| 版本记录 | 0.162.0-alpha.17.2 | 0.162.0 |
| 声明及嵌入提交 | `740e5af33c71225640e0c1c1555c514c2c93ab74` | `c1382380de69521303b416720a52f42d51af6248` |
| native SHA256 | `13c90fa898602a5f165da3b61265142d3a2bfb77786def29a313d3a3756b88d0` | `fd4bb93679bfcc546765a3363a0df9a855f364b61ea6681009b28ba4c2e5b60d` |
| voice manifest 的 bin/codex 摘要 | 与 launcher/native 均不匹配，原因未定 | 与 tar member 及已提取 native 匹配 |

旧 protocol-generation 中的 `cliPath` 指向328字节 shell launcher；其SHA标识 launcher。实际native位于同资源目录的 `CodexCLI.app/Contents/MacOS/codex`，已与原冻结清单核对。不要把 launcher 摘要当 native 构建身份。

公开包按保存metadata复核SHA512/SHA1和tar SHA256；native member、已提取文件和同包manifest摘要一致。无gitHead不是全部来源证据：包内还有commit记录，metadata还提供SLSA attestation入口；本批没有取得或验证证明正文/签名。

桌面与公开包的voice sources.json字节相同，只支持该依赖来源清单一致，不扩大为CLI或全后台相同。桌面原生二进制中的提交值与voice metadata对应，也不证明当前运行实例或源码可构建。

已有三条运行路线、15组能力可行性决定继续复用。下一项来源取证限定为：取得精确 `740e5af33c71225640e0c1c1555c514c2c93ab74` 提交的源码身份，以及metadata列出的公开包构建证明。随后按既有11项协议差异与成功/失败/取消/恢复合同决定后台采用；不以换成较易接入的候选缩小完整目标。

8项事实和12项独立静态检查通过。本批无目标执行、启动、联网、服务/模型调用、源码构建或客户端实现。525功能、603操作、1912未执行规格、模式、来源台账及实施依赖图均不变。

[结构化结论](backend-build-identity-v1.json) · [证据](backend-build-identity-v1-evidence.jsonl)
