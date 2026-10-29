# 精确后台提交与 npm 签名构建证明

桌面声明的精确提交 [`740e5af3…`](https://github.com/openai/codex/commit/740e5af33c71225640e0c1c1555c514c2c93ab74) 可以公开读取。API记录的tree是`8d3f62d2b7cf4bbc92d226542c397fa007f74c49`，Cargo版本补丁对应`0.162.0-alpha.17.2`。当前取得的是提交元数据和补丁，尚未取得完整源树或源码构建结果；Git签名字段为unsigned。

[npm证明入口](https://registry.npmjs.org/-/npm/v1/attestations/@openai%2fcodex@0.162.0-darwin-x64)返回两份签名声明。其subject SHA512与保存的实际tar内容一致；SLSA声明绑定公开提交`c1382380de69521303b416720a52f42d51af6248`及`rust-release.yml@refs/tags/rust-v0.162.0`发布工作流。

离线校验使用固定哈希的已安装npm/Sigstore bootstrap信任材料。证书链、SCT、Rekor SET、Merkle inclusion、checkpoint和DSSE签名检查通过，CT/tlog阈值保持1；另用Node crypto直接复核两份DSSE签名。篡改payload和错误workflow身份均被拒绝。共13项Sigstore检查、15项独立检查通过。

这支持“实际公开包摘要由签名provenance关联到选定源码提交”。没有在线刷新TUF、验证跨checkpoint日志一致性或执行可重复源码构建，不能扩写为完整供应链/后台行为验收。

桌面alpha.17.2与公开0.162.0继续分列。已有桌面manifest/native摘要差异、11项协议差异、实际预测/通知/取消/恢复及独立Owl能力缺口均保留。下一批只读取得740e5af3…的Cargo版本/锁、协议v2及app-server处理文件，核对精确版本fork/prediction契约；不直接换成较易接入的公开版本。

本批只访问两个固定公开地址，成功HTTP响应2；sandbox DNS失败已另存，不作为远端缺席证据。没有目标执行、客户端启动、私有服务/模型调用、源码构建或客户端实现。功能、模式、来源和场景台账均不变，完整分析未完成。

[结构化结论](backend-source-provenance-v1.json) · [证据](backend-source-provenance-v1-evidence.jsonl)
