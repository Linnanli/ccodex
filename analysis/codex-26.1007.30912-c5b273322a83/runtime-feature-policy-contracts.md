# 运行时特性策略的第一方边界

本批关闭上一轮限定的源码问题：`At`、`e$`和`n$`已有完整Program绑定与调用者证据；允许键、重置入口、异常处理和原生职责已明确。两个允许键是`OwlOpenAIGoLinks`、`OwlRemoteSearchSuggestions`，分别接到灰度开关`3646210497`、`3217069062`。

第一方setter只合并允许键中的boolean，包括false；多实例共享缓存。setter在原生调用成功后提交缓存，reset先清空缓存再调用原生方法，因此两种路径失败后的缓存状态不同。缺失方法的TypeError不会自动进入`Unsupported Owl feature:`异常回退。

Windows legacy策略启用要求非空且匹配的认证账号，异步认证返回时generation仍有效，并且运行时方法存在且为function。成功后保存账号/用户owner；清理先删除owner再按平台/能力禁用。账号或用户切换、退出相应认证类型会重置。renderer另检查评估上下文、账号时间及身份连续性；legacy开关`3384989494`需要Recognized结果，LocalOverride不足以启用。

维护决定是保留三个第一方职责单元：策略状态、运行时provider接口、renderer灰度分发。RPC与灰度SDK按第三方依赖引入，不生成其实现。源码中的`chatgpt`是认证条件，不能据此将这组能力整体作为ChatGPT产品模式删除。本批不改变任何功能模式分类。

底层三个效果仍未知：两键如何改变Owl/Chromium、运行时特性注册/查询、Windows旧策略回退。它们属于明确的运行时provider前置条件；公开Electron的同名接口缺失结论沿用[上一轮对照](runtime-surface-disposition.md)。本批没有实现替代provider，也未证明完整运行时路线。

四个冻结Program的定向解析、精确范围与跨文件import/export连接见[结构化合同](runtime-feature-policy-contracts.json)。12条选定源码离线回放通过，使用合成RPC基类、状态、原生方法及SDK helper；它们不计入真实客户端或产品场景通过。新增REA运行、模型提交、原客户端运行、功能定义和客户端实现均为0。

上一轮的有限源码问题已收口，整个分析仍未完成。下一步只基于现有产物汇总原九项标准与六组架构问题，区分已交付、仍缺证据和外部前置条件；不在这次汇总中扩充功能清单、重新扫描源码或要求实施测试全部通过。
