# 通知与取消调用的选定模块绑定补充

固定 shared 模块 `607ad086…0245` 中，六个声明及十个显式 identifier 引用已核对，六条 call/new 的静态词法身份闭合：Dfn.onNotification → Vnn，Vnn → unn/Rnn，Dfn.interruptConversationSelf 的回调 → Ien，Dfn.constructor → new T7t，Sii → new Dfn。

Dfn 是 Program `var`，其声明在 `[3198945,3198948)`；Ofn 是包含 class 初始化赋值的函数，范围 `[3198949,3255813)`。class RHS 为 `[3199539,3255806)`，与旧 frozen class span 同 hash。T7t 同样是 Program `var`，E7t 是初始化函数。祖先函数名与 class 绑定名分别记录，没有改写旧冻结合同。

取消 caller 进一步限于 interruptConversationSelf 的 2065B method：局部 let i 的 arrow 初始化中调用 Ien，`return i()` 与 `await i()` 两处 callee 均回查该局部声明；try/catch 中另外两个 i 是不同绑定。实际 callback 执行与间接 alias/effect 仍未知。

constructor 直接写 `this.threadStore = new T7t(...)`；notificationContext 的 threadStore 属性读取该字段，notificationReductionContext 写 manager:this 与 notificationContext:this.notificationContext。onNotification 传入后一个字段。conversations getter 返回 `this.threadStore.conversations`。T7t 的 conversations 字段为 new Map，constructor 写 this.params=e。两段完整 class 仅对六个字段槽做直接语法清点：238 个访问节点、5 个有值 class 初始化或直接 Assignment/Update，另有 5 个 class field 定义（4 个无 initializer）。其他成员未进行完整语义审查；这些计数不是完整 mutation census，destructuring、for-in/of、delete、defineProperty 和外部写入仍未知。

这些是固定源码中的绑定与字段连接。初始化是否执行、实际 this/manager/store/host/transport/RPC/context、helper 与 alias 闭包、动态或间接写入、通知实际送达、UI/持久化和模式仍未知。两个 broad aliasCandidates 是 Dfn.dispose 的对象读取，不是已确认的构造器 alias。custom scope resolver 的通用局限与本次十个引用的人工校核范围保留在 main。

两次 Program AST 尝试中，第一次在 parse 后的 UTF16/byte 定位比较失败；第二次成功。两个旧 class span 又做一次有界 AST 字段选取，2065B method 做一次局部 callback 解析。各次 exact script、stdout、stderr、exit 与 receipt 均保存；失败记录不作为最终 evidence。旧 notification frozen 产物及 public analysis 未改。没有执行或 import 目标、调用目标 CLI/UI/网络/模型，未读取凭据或个人历史，也未把第三方实现复制到客户端源码。

- [局部合同](turn-notification-bindings.json)
- [证据](evidence.jsonl)
- [模块绑定元数据](module-bindings.json)
- [选定字段 AST 元数据](instance-fields.json)
- [取消 caller 元数据](cancellation-callback.json)
