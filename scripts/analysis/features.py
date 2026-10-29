#!/usr/bin/env python3
"""Produce source-located functional candidates; never execute release JavaScript.

This is supplemental lexical analysis. It deliberately retains unknown mode,
computed route and transport boundaries instead of presenting heuristics as AST
or runtime proof. Frozen release files remain in the ignored evidence directory.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


LITERAL = rb"(?P<quote>[`'\"])(?P<value>(?:\\.|[^`'\"\\]){1,240})(?P=quote)"
IMPORT = re.compile(rb"(?:\bfrom\s*|\bimport\s*\(|\brequire\s*\()" + LITERAL)
ROUTE = re.compile(rb"\bpath\s*:\s*" + LITERAL)
METHOD = re.compile(rb"\b(?:sendAppServerRequest|sendRequest|request)\s*\(\s*" + LITERAL)
CHANNEL = re.compile(rb"[`'\"](codex_desktop:[^`'\"\r\n]{1,150})[`'\"]")
SETTING = re.compile(rb"(?:[`'\"](?P<quoted>[a-z][a-z0-9_-]+)[`'\"]|(?P<bare>[a-z][a-zA-Z0-9_-]+)):\{component:")
TYPE = re.compile(rb"\b(?:type\s*:\s*|case\s*)" + LITERAL)
FEATURE_PREFIX = re.compile(r"^(?:app-(?:initial|shared|primary|main|prefetch)|index-44a|rpc-|detachedWindow|local-conversation|pending-local|remote-conversation|sidebar|thread|conversation|chatgpt-conversation|chatgpt-project|projects?-|settings|use-visible-settings|use-codex-worktrees|worktrees?|terminal|background-terminal|automations?|cloud-|remote-connections|hooks-settings|plugins?|skills-settings|mcp-|computer-use|browser-use|browser-route|browser-extension-settings|appshots-settings|general-settings|appearance-settings|notifications-settings|keyboard-shortcuts-settings|code-review-settings|git-settings|login-route|account-settings|data-controls-settings|chronicle-settings|codex-|open-(?:local-conversation|thread|automation|pull-request)|create-project|import-settings|share-thread|use-start-new-conversation|page-codex|new-thread|hotkey-window|thread-handoff|use-resume-conversation|conversation-navigation|worktree-environment)")

# These labels are investigative candidates, not a claim of exhaustive UI coverage.
# Presence is confirmed by the source references. Mode assignment is separately
# inferred unless a condition/consumer is recorded in the boundary evidence.
FEATURES = [
    ('thread-lifecycle', '本地会话创建、恢复、分叉与归档', 'codex', ['local-conversation-page-', 'use-resume-conversation-if-needed-', 'threads-fork-'], ['thread/start', 'thread/resume', 'thread/fork', 'thread/archive'], '会话和状态在重启后恢复；分叉有独立身份'),
    ('thread-turn-stream', '消息、流式事件与任务取消', 'codex', ['local-conversation-thread-', 'local-conversation-turn-', 'pending-local-conversation-thread-'], ['turn/start', 'turn/interrupt', 'turn/steer'], '流式事件排序、终态和取消后状态与基线一致'),
    ('approval', '命令、文件与工具审批', 'codex', ['computer-use-app-approval-request-card-', 'local-conversation-thread-turn-entries-'], ['item/commandExecution/requestApproval', 'item/fileChange/requestApproval', 'item/tool/requestUserInput'], '接收请求、显示参数、反馈选择及取消符合契约'),
    ('subagents', '子代理状态与侧栏', 'codex', ['local-conversation-subagents-panel-tab-', 'open-local-conversation-subagents-panel-'], [], '可显示子代理进度、打开目标会话和完整消息'),
    ('task-goals', '持续目标与计划展示', 'codex', ['thread-goal-side-panel-content-', 'local-conversation-plan-model-'], [], '目标状态、预算及计划项变化符合事件状态'),
    ('projects', '项目、目录与来源管理', 'shared', ['create-project-dialog-', 'projects-index-page-', 'project-folder-consent-dialog-', 'project-import-prompt-host-'], [], '目录选择、同意、创建、重命名和会话归属验证'),
    ('worktrees', '工作树创建、归档、恢复和清理', 'codex', ['worktrees-settings-page-', 'worktree-creation-row-', 'use-codex-worktrees-', 'worktree-environment-dropdown-'], [], '实际隔离仓库完成生命周期和冲突处理'),
    ('handoff', '本地、工作树与主机交接', 'codex', ['thread-handoff-modal-', 'thread-executor-target-'], [], '跨环境交接保留文件、Git 状态和会话历史'),
    ('remote-hosts', 'SSH 与远程主机连接', 'codex', ['remote-connections-settings-', 'remote-conversation-page-', 'project-device-picker-'], ['remoteControl/enable', 'remoteControl/disable'], '连接、失败、断线恢复和目标主机执行验证'),
    ('cloud-execution', '云端任务与环境', 'unknown', ['cloud-environments-settings-page-', 'cloud-entry-route-', 'cloud-preferences-settings-'], [], '确认 Codex 模式入口、账户条件和服务能力'),
    ('terminal', '终端与后台命令面板', 'codex', ['terminal-panel-', 'terminal-tab-', 'local-conversation-background-terminal-tab-'], [], 'PTY 输入输出、resize、退出、取消、tab 恢复验证'),
    ('diff-review', '文件差异、代码评审与行内批注', 'codex', ['code-review-settings-', 'use-conversation-diff-comments-', 'local-conversation-git-actions-'], ['review/start'], '修改、暂存和评审视图及批注定位验证'),
    ('pull-requests', 'PR 列表、代码面板与修复任务', 'codex', ['pull-request-route-', 'open-thread-pull-request-code-tab-', 'pull-request-fix-automation-'], [], '仓库身份、PR 差异、动作及错误状态验证'),
    ('git-settings', 'Git 与本地环境设置', 'codex', ['git-settings-', 'local-environments-settings-content-', 'local-environments-settings-page-'], [], '设置读写与新任务/工作树应用一致'),
    ('automations', '定时任务、心跳与通知策略', 'codex', ['automations-page-', 'local-conversation-heartbeat-automation-', 'automation-frequency-section-', 'automation-notification-policy-dropdown-'], [], '计划持久化、触发、暂停、通知和失败状态验证'),
    ('plugins', '插件安装、市场、启停与配置', 'shared', ['plugins-settings-', 'plugin-detail-settings-enabled-', 'plugin-marketplace-context-'], ['marketplace/list', 'marketplace/add', 'marketplace/remove'], '来源、启停和配置作用域及失败处理验证'),
    ('skills-mcp', '技能与 MCP 配置及工具', 'codex', ['skills-settings-', 'mcp-settings-', 'mcp-tool-activity-label-'], ['skills/list', 'mcpServerStatus/list', 'mcpServer/oauth/login'], '技能发现、工具调用、状态和 OAuth 条件验证'),
    ('app-tools', '桌面工具与 Node REPL 集成', 'codex', ['register-app-actions-', 'open-in-codex-'], [], 'Codex app MCP、独立工具进程和授权链路验证'),
    ('browser', '内置浏览器、标签页与上下文操作', 'shared', ['browser-route-', 'browser-use-settings-', 'browser-extension-settings-'], [], '导航、标签、恢复、注释、外部浏览器与桥接验证'),
    ('computer-use', '电脑操作权限、应用审批与截图', 'codex', ['computer-use-settings-', 'computer-use-app-approvals-query-', 'appshots-settings-'], [], '平台权限和审批的正常、拒绝、撤销状态验证'),
    ('artifact-panels', '文件、文档与可视化面板', 'shared', ['thread-side-panel-tab-content-', 'thread-summary-panel-components-', 'local-conversation-summary-panel-artifacts-section-'], [], '文件打开、预览、编辑契约与资源定位验证'),
    ('sidebar', '侧栏排序、置顶、分区与搜索', 'shared', ['sidebar-actions-', 'sidebar-rename-dialog-', 'thread-pin-shortcut-bridge-', 'use-conversation-search-highlights-'], [], '排序、搜索、读取状态、归档和重启恢复验证'),
    ('shortcuts', '快捷键、菜单与快速窗口', 'shared', ['keyboard-shortcuts-settings-', 'hotkey-window-new-thread-page-', 'page-codex-quick-chat-window-'], [], '快捷键冲突、窗口切换、命令启用条件验证'),
    ('window-lifecycle', '窗口、托盘、主题与系统集成', 'shared', ['thread-app-shell-chrome-', 'thread-side-panel-tabs-'], [], '多窗口、关闭恢复、托盘、焦点、缩放和主题验证'),
    ('appearance-notification', '外观、语言与通知', 'shared', ['appearance-settings-', 'notifications-settings-', 'general-settings-'], [], '设置保存、系统主题和通知行为验证'),
    ('hooks', 'Hooks 设置', 'codex', ['hooks-settings-', 'hooks-settings-model-', 'hooks-settings-navigation-'], [], '作用域、脚本、执行条件和来源显示验证'),
    ('safety-policy', '权限、沙箱与执行策略', 'codex', ['safety-settings-', 'computer-use-settings-', 'local-conversation-thread-'], [], '策略变更应用于真实任务和审批路径'),
    ('authentication', '身份、账户切换与授权', 'shared', ['login-route-', 'account-settings-', 'app-connect-oauth-callback-page-'], ['account/read', 'account/login/start', 'account/logout'], '保留 Codex 身份；登录、登出、切换和失效验证'),
    ('usage-model', '模型、推理强度与使用量', 'codex', ['thread-usage-breakdown-', 'composer-controls-'], ['model/list', 'account/rateLimits/read'], '模型能力、用量与设定向任务的传递验证'),
    ('sharing', '会话分享与快照', 'unknown', ['share-thread-', 'shared-codex-snapshot-'], [], '确认 Codex 入口、远端服务与分享契约'),
    ('mobile', '移动端连接与设置', 'codex', ['codex-mobile-setup-dialog-', 'codex-mobile-setup-flow-', 'codex-mobile-page-'], [], '账户、平台和远程控制条件验证'),
    ('chronicle', 'Chronicle 记录与设置', 'unknown', ['chronicle-settings-page-'], [], '需确认 Codex/Work/ChatGPT 模式归属和权限条件'),
    ('codex-micro', 'Codex Micro 功能与设置', 'unknown', ['codex-micro-settings-', 'codex-micro-bridge-', 'codex-micro-onboarding-host-'], [], '需核实功能开关、模式归属和原生界面'),
    ('chatgpt-conversation', 'ChatGPT 对话、重生成与分享', 'chatgpt', ['chatgpt-conversation-page-', 'chatgpt-conversation-turn-content-', 'chatgpt-conversation-runtime-', 'chatgpt-conversation-share-dialog-'], [], '候选排除；拆分前核对共享渲染器及 Codex 调用方'),
    ('chatgpt-project', 'ChatGPT 项目设置与来源', 'chatgpt', ['chatgpt-project-settings-dialog-', 'chatgpt-project-sources-', 'chatgpt-project-fetch-'], [], '候选排除；Codex/Work 项目桥接 provisioning 需要单独保留'),
    ('work-pages-sites', 'Work Pages、Sites 与云端文档', 'unknown', ['space-route-', 'appgen-settings-page-', 'appgen-site-detail-route-'], [], 'Work 不自动等同 ChatGPT 专属；需追踪 Codex 可达性'),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='.analysis-local/current-baseline.json')
    parser.add_argument('--output', default='.analysis-local/feature-work')
    args = parser.parse_args()
    baseline = json.loads(Path(args.baseline).read_text())
    root = Path(baseline['extractedDirectory'])
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    files = json.loads((Path('analysis') / baseline['baselineId'] / 'files.json').read_text())['archiveFiles']
    hashes = {x['archivePath']: x.get('sha256') for x in files}
    all_js = [p for p in root.rglob('*.js') if 'node_modules' not in p.parts]
    names = sorted(p.relative_to(root).as_posix() for p in all_js)
    selected = [p for p in all_js if p.relative_to(root).as_posix().startswith('.vite/build/') or FEATURE_PREFIX.search(p.name)]
    # Explicit roots and route/setting entrypoints not captured by feature prefixes.
    for name in ['webview/index.html', 'webview/detached-window.html', 'webview/assets/routes-2879a4fdfb21.js']:
        p = root / name
        if p.exists() and p not in selected:
            selected.append(p)
    source = {p.relative_to(root).as_posix(): p.read_bytes() for p in selected}
    evidence, evidence_keys, verified_hashes = [], {}, {}

    def ev(name, start, end, claim, confidence='confirmed'):
        key = (name, start, end, claim)
        if key in evidence_keys:
            return evidence_keys[key]
        data = source[name]
        h = verified_hashes.get(name)
        if h is None:
            actual = hashlib.sha256(data).hexdigest()
            h = hashes.get(name) or actual
            if actual != h:
                raise RuntimeError('Frozen member changed: ' + name)
            verified_hashes[name] = h
        eid = f'FEATURE-E{len(evidence)+1:05d}'
        evidence_keys[key] = eid
        evidence.append({'id': eid, 'baselineId': baseline['baselineId'], 'claim': claim, 'sourcePath': 'app.asar/' + name, 'sourceHash': h, 'locator': {'kind': 'byte-range', 'start': start, 'endExclusive': end}, 'method': 'supplemental-static-lexical', 'confidence': confidence, 'verificationStatus': 'static-confirmed' if confidence == 'confirmed' else 'needs-verification'})
        return eid

    def anchor(name, pattern, claim, confidence='confirmed'):
        if name not in source:
            return None
        m = re.search(pattern.encode(), source[name])
        return ev(name, m.start(), m.end(), claim, confidence) if m else None

    imports, modules, channels, routes, methods, settings = [], [], [], [], [], []
    for name, data in sorted(source.items()):
        environment = 'main-or-shared' if name.startswith('.vite/build') else 'renderer'
        if 'preload' in name:
            environment = 'preload'
        elif name == '.vite/build/worker.js' or '.worker-' in name:
            environment = 'worker'
        members = []
        for m in IMPORT.finditer(data):
            spec = m.group('value').decode(errors='replace')
            if '${' in spec:
                continue
            target = (Path(name).parent / spec).as_posix() if spec.startswith('.') else None
            item = {'from': name, 'specifier': spec, 'target': target, 'kind': 'literal-import-or-require', 'evidenceId': ev(name, m.start(), m.end(), '字面导入 ' + spec)}
            imports.append(item)
            members.append(item)
        modules.append({'id': 'published:' + name, 'sourcePath': 'app.asar/' + name, 'sourceHash': hashes.get(name), 'bytes': len(data), 'environment': environment, 'mode': 'unknown', 'sourceOwnership': 'first-party-functional-candidate-or-mixed-bundle', 'boundary': 'published-file; not recovered-source-module', 'dependencies': members, 'sideEffects': 'not-exhaustively-analyzed', 'sharedState': 'not-exhaustively-analyzed', 'proposedPath': None})
        seen = set()
        for m in CHANNEL.finditer(data):
            value = m.group(1).decode(errors='replace')
            if value in seen:
                continue
            seen.add(value)
            channels.append({'channel': value, 'sourcePath': 'app.asar/' + name, 'computed': '${' in value, 'evidenceId': ev(name, m.start(), m.end(), '显式 IPC 通道或通道模板 ' + value), 'requestResponseContract': 'requires-consumer-resolution', 'runtimeVerified': False})
        if name.endswith('app-initial-6350d04672d0.js') or name.endswith('app-primary-6f60e9ac4103.js'):
            for m in ROUTE.finditer(data):
                value = m.group('value').decode(errors='replace')
                if not value.startswith('/') and '/' not in value and value not in ['new-thread', 'thread/:conversationId']:
                    continue
                context = data[max(0, m.start()-100):m.end()+140]
                is_registered = re.search(rb'\.jsx[s]?\)\(vh,\{[^{}]{0,90}$', data[max(0,m.start()-120):m.start()]) is not None
                kind = 'navigation-target' if b'navigate-to-route' in context else 'route-registration' if is_registered else 'path-property-needs-route-confirmation'
                routes.append({'path': value, 'dynamicTemplate': '${' in value, 'kind': kind, 'mode': 'unknown', 'gate': 'requires-enclosing-guard-resolution', 'evidenceId': ev(name, m.start(), m.end(), '路由属性/导航目标候选 ' + value)})
            for m in re.finditer(rb'\.jsx[s]?\)\(vh,\{path:(?P<identifier>[A-Za-z_$][\w$]*)(?=[,}])', data):
                identifier = m.group('identifier').decode()
                routes.append({'path': None, 'pathIdentifier': identifier, 'dynamicTemplate': True, 'kind': 'computed-route-registration', 'mode': 'unknown', 'gate': 'requires-path-symbol-and-enclosing-guard-resolution', 'evidenceId': ev(name,m.start(),m.end(),'计算得到的路由注册标识 '+identifier)})
        for m in METHOD.finditer(data):
            value = m.group('value').decode(errors='replace')
            if '/' not in value or '${' in value:
                continue
            methods.append({'method': value, 'callForm': m.group().decode(errors='replace').split('(')[0], 'sourcePath': 'app.asar/' + name, 'evidenceId': ev(name, m.start(), m.end(), '请求方法字面调用 ' + value), 'protocolClass': 'app-server' if b'sendAppServerRequest' in m.group() else 'unknown-request-wrapper', 'schema': 'not-resolved'})
        if name.endswith('use-visible-settings-sections-2fe9342ddfa1.js'):
            for m in SETTING.finditer(data):
                value = (m.group('quoted') or m.group('bare')).decode()
                settings.append({'section': value, 'mode': 'unknown', 'visibility': 'runtime-capability-and-feature-gates', 'evidenceId': ev(name, m.start(), m.end(), '设置注册组件 ' + value)})

    main_name = '.vite/build/main-CqEoQDOU.js'
    data = source[main_name]
    central = data.find(b'async handleMessage(e,t){if(gR(t))')
    stop = data.find(b'}setPrimaryWindowMode(', central)
    if stop < 0:
        stop = data.find(b'}getBrowserCommentOverlayOwner(', central)
    central_types = []
    if central >= 0 and stop > central:
        for m in re.finditer(rb'case\s*' + LITERAL, data[central:stop]):
            value = m.group('value').decode(errors='replace')
            if '${' in value:
                continue
            central_types.append({'type': value, 'direction': 'view-to-main-central-dispatcher', 'evidenceId': ev(main_name, central+m.start(), central+m.end(), '主消息分发器处理消息类型 ' + value), 'caseMayBeNoOp': True, 'runtimeVerified': False})

    curated = []
    for fid, label, mode, prefixes, method_names, observation in FEATURES:
        prefix_hits = [n for n in names if any(Path(n).name.startswith(p) for p in prefixes)]
        # Include those files as evidence, even if outside initial lexical scope.
        entry_evidence = []
        for name in prefix_hits:
            if name not in source:
                source[name] = (root/name).read_bytes()
            d = source[name]
            # A filename is only inferred responsibility, not functionality proof.
            entry_evidence.append(ev(name, 0, min(len(d), 512), '发布模块候选 ' + name, 'inferred'))
        method_hits = [x for x in methods if x['method'] in method_names]
        literal_evidence = []
        for wanted in method_names:
            raw = wanted.encode()
            for name, d in source.items():
                pos = d.find(b'`' + raw + b'`')
                if pos >= 0:
                    literal_evidence.append(ev(name, pos, pos+len(raw)+2, '功能相关方法字面量 ' + wanted))
                    if len(literal_evidence) >= 12:
                        break
        curated.append({'id': fid, 'name': label, 'trigger': 'see candidate published entrypoints; UI trigger requires observation', 'behavior': label, 'mode': mode, 'modeConfidence': 'inferred', 'classificationStatus': 'candidate; no-exclusion-authorized-by-name-alone', 'conditions': 'platform/account/feature/service conditions need per-consumer trace', 'publishedEntrypoints': prefix_hits, 'backendMethods': sorted(set(x['method'] for x in method_hits)), 'codeChain': 'entrypoints → app-host/electronBridge or typed app-server RPC; per-feature path not yet exhaustive', 'evidenceIds': list(dict.fromkeys(entry_evidence + [x['evidenceId'] for x in method_hits] + literal_evidence)), 'verificationStatus': 'static-candidate; runtime-pending', 'recoveryVerification': observation})

    boundaries = []
    boundary_specs = [
        ('main-bootstrap', '.vite/build/early-bootstrap.js', r'initializeNodeNetworkPermissions', 'early-bootstrap 在网络初始化满足后加载 bootstrap', 'shared'),
        ('main-startup', '.vite/build/bootstrap-CooIJpZm.js', r'runMainAppStartup:e', 'bootstrap 动态导入 main 后调用 runMainAppStartup', 'shared'),
        ('renderer-entry', 'webview/index.html', r'assets/index-44a69cb8b3cd.js', '主 HTML 的 renderer module 入口', 'shared'),
        ('renderer-lazy', 'webview/assets/index-44a69cb8b3cd.js', r'import\(`\./app-main-c3673115a651.js`\)', 'renderer 入口按序初始化 RPC 和 app-main', 'shared'),
        ('react-root', 'webview/assets/app-main-c3673115a651.js', r'__codexRoot=\(0,s.createRoot\)\(c\)', 'app-main 创建 React root 并渲染 app-initial 返回组件', 'shared'),
        ('preload-api', '.vite/build/preload.js', r'exposeInMainWorld\(`electronBridge`,z\)', 'preload 暴露 electronBridge', 'shared'),
        ('typed-host-transport', 'webview/assets/app-shared-8bd9d0399038.js', r'n.sendMessageFromView\(r\)', 'renderer postMessage 通过 electronBridge.sendMessageFromView 转发', 'shared'),
        ('request-forward', main_name, r'handleClientRequest\(new XJ\(e,this.chunkedMessageSender\),n', 'mcp-request 交给对应 host app-server connection，并支持 coalesce/priority/timeout/expiry', 'codex'),
        ('prewarm-forward', main_name, r'handlePrewarmThreadStart\(new XJ\(e,this.chunkedMessageSender\),n', 'thread-prewarm-start 独立预热请求路径', 'codex'),
        ('request-abandon', main_name, r'abandonClientRequest\(new XJ\(e,this.chunkedMessageSender\),t.requestId\)', 'mcp-request-abandon 通过 host connection 丢弃客户端请求', 'codex'),
        ('profile-isolation', '.vite/build/bootstrap-CooIJpZm.js', r'CODEX_ELECTRON_USER_DATA_PATH\?\.trim\(\)', '显式环境变量控制 userData', 'shared'),
        ('single-instance', '.vite/build/bootstrap-CooIJpZm.js', r'function iD\([^)]*\)\{return t\?!e\|\|n:!1\}', 'macOS packaged 显式 userData 启用 single-instance lock', 'shared'),
        ('codex-home', '.vite/build/application-network-startup-CfAQmSYg.js', r'return process.env.CODEX_HOME\?\?s.join\(p.homedir\(\),`\.codex`\)', 'CODEX_HOME 控制 Codex 数据根目录', 'shared'),
        ('persisted-mode', 'webview/assets/app-initial-6350d04672d0.js', r'uPt=`home-composer-mode-v1`', 'chat/work composer mode 有持久化状态', 'shared'),
        ('mode-switch', 'webview/assets/app-initial-6350d04672d0.js', r'function sPt\([^)]*\)\{[^}]+\}', 'Codex 与 chat/work 路由模式切换不等于字符串删除', 'shared'),
        ('work-chat-access', 'webview/assets/app-initial-6350d04672d0.js', r'function lPt\([^)]*\)\{[^}]+\}', 'chat/work effective mode 由账户能力、workOnly 与加载状态共同决定', 'shared'),
        ('atom-persistence', main_name, r'sendPersistedAtomState\(e,t\)\{', 'main 维护 electron-persisted-atom-state 并向各窗口同步', 'shared'),
        ('remote-version', '.vite/build/application-network-startup-CfAQmSYg.js', r'var x=`0.141.0`', '客户端 app-server 最低版本常量为 0.141.0', 'codex'),
        ('app-host-port', 'webview/assets/app-shared-8bd9d0399038.js', r'window.postMessage\(\{type:`connect-app-host`,port:n\}', '另有 MessageChannel app-host RPC，统一消息 IPC 不是全部接口', 'shared'),
    ]
    for ident, name, pattern, claim, mode in boundary_specs:
        eid = anchor(name, pattern, claim)
        boundaries.append({'id': ident, 'claim': claim, 'mode': mode, 'evidenceId': eid, 'status': 'static-confirmed' if eid else 'anchor-not-found'})

    transport_specs = [
        ('view-message', 'codex_desktop:message-from-view', 'renderer → main', 'invoke delivery; domain results arrive separately', 'message object; type discriminator; shared-object-set updates preload cache', 'delivery errors propagate/reject; handler makes domain error response', 'app-server request timeoutMs/expiresAtMs/retainResponse/coalesce/priority are optional fields', 'mcp-request-abandon; turn/interrupt is a separate domain operation', r'await e.ipcRenderer.invoke\(E,t\)'),
        ('host-message', 'codex_desktop:message-for-view', 'main → renderer', 'ipcRenderer.on → window message event', 'typed host notification or codex-host-chunked-message-v1 frame', 'non-chunk shared-object-updated refreshes local cache; type-specific errors remain payload', 'chunk sequencing/acknowledgement; complete tokenizer contract remains to trace', 'subscription lifecycle, not task cancellation', r'e.ipcRenderer.on\(D,\(e,t\)=>'),
        ('worker-request', 'codex_desktop:worker:${workerId}:from-view', 'renderer → main/worker manager', 'invoke on computed channel', 'workerId selected by function argument; worker message data', 'delivery rejection; worker response/error requires worker schema resolution', 'not resolved', 'worker-request-cancel candidate in main dispatcher; semantics need worker trace', r'await e.ipcRenderer.invoke\(b\(t\),n\)'),
        ('worker-response', 'codex_desktop:worker:${workerId}:for-view', 'worker manager → renderer', 'one listener per worker id + subscriber Set', 'worker message passed to all subscribers', 'not resolved', 'not resolved', 'last unsubscribe removes ipcRenderer listener', r'e.ipcRenderer.on\(x\(t\),i\)'),
        ('app-host-connect', 'codex_desktop:connect-app-host', 'renderer ↔ main service host', 'transferred MessagePort; independent RPC transport', 'window connect-app-host message with port', 'service RPC errors separate from typed host-message errors', 'requires RPC schema and service-registry analysis', 'MessagePort lifecycle; service cancellation not resolved', r'e.ipcRenderer.postMessage\(_,void 0,\[n\]\)'),
        ('theme-read', 'codex_desktop:get-system-theme-variant', 'preload → main', 'sendSync at preload startup', 'no request payload; theme variant return', 'not resolved', 'synchronous', 'none', r'e.ipcRenderer.sendSync\(f\)'),
        ('theme-change', 'codex_desktop:system-theme-variant-updated', 'main → preload/renderer', 'ipcRenderer.on + subscriber Set', 'theme variant', 'not resolved', 'event notification', 'unsubscribe removes subscriber', r'e.ipcRenderer.on\(h,\(e,t\)=>'),
        ('sidebar-bootstrap', 'codex_desktop:get-initial-sidebar-bootstrap', 'preload → main', 'sendSync lazily cached', 'first call cached as F; actual bootstrap schema needs receiver trace', 'not resolved', 'synchronous', 'none', r'F=e.ipcRenderer.sendSync\(p\)'),
        ('sandbox-host', 'codex_desktop:mcp-app-sandbox-host-message', 'main → renderer sandbox', 'ipcRenderer.on → window.postMessage using origin and transferred ports', 'host message plus event ports', 'does not forward when origin is null', 'not resolved', 'port lifecycle', r'window.postMessage\(t,n,e.ports\)'),
        ('context-menu', 'codex_desktop:show-context-menu', 'renderer → main', 'invoke', 'context menu payload and options', 'promise rejection; receiver checks caller permission', 'waits for user choice', 'menu dismissal returns id:null in receiver', r'e.ipcRenderer.invoke\(l,t,n\)'),
        ('file-drag', 'codex_desktop:start-file-drag', 'renderer → main', 'sendSync', 'file drag arguments; boolean success', 'false return', 'synchronous', 'OS drag lifecycle', r'e.ipcRenderer.sendSync\(v,t\)===!0'),
        ('link-drag', 'codex_desktop:start-link-drag', 'renderer → main', 'send', 'link drag payload', 'not resolved', 'fire-and-forget', 'OS drag lifecycle', r'e.ipcRenderer.send\(y,t\)'),
    ]
    transports=[]
    for ident, channel, direction, form, payload, errors, timeout, cancellation, pattern in transport_specs:
        claim='preload IPC transport '+channel
        eid=anchor('.vite/build/preload.js',pattern,claim)
        transports.append({'id':ident,'channel':channel,'direction':direction,'callForm':form,'payloadContract':payload,'errorContract':errors,'timeoutContract':timeout,'cancellationContract':cancellation,'evidenceId':eid,'verificationStatus':'static-confirmed; runtime-pending' if eid else 'unresolved'})

    totals = {
        'baselineId': baseline['baselineId'],
        'allArchiveMembers': len(files),
        'nonNodeModulesJsDiscovered': len(all_js),
        'lexicallyScannedFiles': len(selected),
        'publishedModuleCandidates': len(modules),
        'literalImportEdges': len(imports),
        'explicitChannelSourcePairs': len(channels),
        'distinctExplicitChannels': len(set(x['channel'] for x in channels)),
        'centralDispatcherMessageTypes': len(set(x['type'] for x in central_types)),
        'routePropertyCandidates': len(routes),
        'routeRegistrationsLiteral': sum(x['kind']=='route-registration' for x in routes),
        'routeRegistrationsComputed': sum(x['kind']=='computed-route-registration' for x in routes),
        'routeNavigationTargets': sum(x['kind']=='navigation-target' for x in routes),
        'settingRegistrationCandidates': len(settings),
        'appServerDirectCallSites': sum(x['protocolClass']=='app-server' for x in methods),
        'distinctAppServerDirectMethods': len(set(x['method'] for x in methods if x['protocolClass']=='app-server')),
        'curatedFeatureCandidates': len(curated),
        'featuresWithSourceEvidence': sum(bool(x['evidenceIds']) for x in curated),
        'featureModeCounts': {m: sum(x['mode']==m for x in curated) for m in ['codex','chatgpt','shared','unknown']},
        'featuresRuntimeVerified': 0,
        'confirmedExclusions': 0,
        'centralDispatcherRange': [central, stop] if stop>central>=0 else None,
        'limitations': [
            '本工具为补充字面静态扫描，REA 结果由主流程保存；未把正则当作 AST、调用链或行为证明。',
            '代码包含 codex、chat/work、local/cloud/chatgpt thread kind 等多个维度；暂不将 work 视为 ChatGPT 专属。',
            '功能候选来自入口和方法线索；功能分母尚在调查，36 个分组不代表完整功能数。',
            'selected files 是第一方功能候选和混合 bundle；第三方范围由依赖归属分析单独确定。',
            '显式 IPC 通道不等于全部接口；MessagePort RPC、计算通道和 native/owl 接口需要进一步解析。',
            'route-property 同时包含导航目标及 route declaration；动态路径和上层守卫保留未解析。',
            'central dispatcher 的 case 可能仅 no-op 或转发，登记存在不证明实现或 UI 可达。',
            '设置注册不证明可见；账户、平台、feature flag 与 host capability 要逐项核实。',
            '所有行为均未由本子任务运行验证，不能把静态证据计入行为覆盖。',
        ],
    }
    def dump(name, value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    dump('coverage.json', totals)
    dump('features.json', curated)
    dump('modules.json', modules)
    dump('imports.json', imports)
    dump('ipc-channels.json', channels)
    dump('ipc-transport-contracts.json',transports)
    dump('host-message-types.json', central_types)
    dump('routes.json', routes)
    dump('settings.json', settings)
    dump('app-server-methods.json', methods)
    dump('boundaries.json', boundaries)
    (output/'evidence.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in evidence))
    with (output/'features.csv').open('w', newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['id','name','mode','modeConfidence','verificationStatus','publishedEntrypoints','backendMethods','evidenceIds','recoveryVerification'])
        writer.writeheader()
        for item in curated:
            writer.writerow({k:json.dumps(item[k],ensure_ascii=False) if isinstance(item[k],list) else item[k] for k in writer.fieldnames})
    print(json.dumps(totals,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
