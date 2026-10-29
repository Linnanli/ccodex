# 通知绑定格式补充独立复核

状态：passed-metadata-delta-only；metadata checks：197；errors：0。

31 条证据仅增加 baselineId 与 method；去掉两键后恢复旧 31 journal 原序列化字节。9 required fields 和三种 confidence 枚举符合固定 analysis-plan。
Main 仅变化 inputs、attempts、currentProducerReceiptPath、priorDraftProductsPreserved、evidenceFormatContract。其余 source/scope/labels/edges/claims/unknowns 保持原样。
已有 577 checks 的语义 peer 和首次 checker 失败历史保留；本次不重复语义检查，不读原或旧 frozen 源文本，不运行 parser/目标。

| 产品 | bytes | SHA256 |
| --- | ---: | --- |
| turn-notification-bindings.json | 29223 | a50d659b63b44a1980d8e8c5dabdbbc11888b24c0e71ca9b64077a9e282fa21a |
| evidence.jsonl | 46516 | 950358cf20aef0120a4ba671fc652b120b818d92572b7ed14de57e3b0ff84dc8 |
| summary.md | 2947 | d05060e8f9abd841dbaad8edbebab6523929b9853b9c4cf2430c9a0bb4d1d592 |
| module-bindings.json | 90367 | 3c8d6bb037131496bc10dd817e95250f1ff2d1ccb6695dc056977ad38bc8fc8b |
| instance-fields.json | 313054 | 0bf70d4aaffd3347535ba9ea09edd27cecd08c4d771e9b490331c0e16810cfc8 |
| cancellation-callback.json | 19154 | 76fb7d0c79b8d9cf5dfc6debcb678434bf90ea083060e5e3b9218beb5e0f8062 |
| validation.json | 3229 | b4df60694c77c7015b31e7f3970e0bfb66cdf6db96620060e034db8a934f944e |
