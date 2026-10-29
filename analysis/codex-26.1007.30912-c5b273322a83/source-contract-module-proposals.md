# 已审查来源到维护路径的补充建议

固定基线 `codex-26.1007.30912-c5b273322a83`。以下6条为新维护设计，confidence=inferred，不是原作者目录，也不增加已确认功能或模式归属。9个来源单位引用保留发布文件哈希和已固定合同中的精确JSON位置。

| 拟议路径 | 职责 | 来源单位引用 |
| --- | --- | ---: |
| `apps/desktop/src/renderer/mode/transition.ts` | Mode transition guard and ordered state writes; retain supplied store and atoms. | 1 |
| `apps/desktop/src/renderer/mode/resolver.ts` | Access-sensitive mode resolution, including persisted value passthrough. | 1 |
| `apps/desktop/src/renderer/mode/state.ts` | Selected state declarations/initialization; actual store/provider ownership remains unresolved. | 2 |
| `apps/desktop/src/main/native/window-events.ts` | First-party window scroll monitor registration and normal-path removal. | 1 |
| `apps/desktop/src/main/native/notifications.ts` | First-party notification permission callback, center cache and RunLoop reference management. | 3 |
| `apps/desktop/src/worker/native/apple-events.ts` | First-party Apple Event wrapper factories; no event execution proven. | 1 |

[机器映射](source-contract-module-proposals.json)可回到完整source locator；[模式合同](mode-transition-origin-summary.md)和[原生适配边界](objc-modification-contracts-summary.md)给出已审查范围。MODE state的实际provider／存储所有权继续待调查，不能从键名推定localStorage。objc-js库实现由依赖包引入，仅恢复应用自己的wrapper、条件和生命周期。

原11条模块建议与8条app-host建议保持各自范围，不把不同合同的重复表示相加为完整模块分母。消费者闭包、模式归属、实际运行和最终工程结构尚未完成；这些路径仍需随着证据修订。
