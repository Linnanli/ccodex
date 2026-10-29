# 设置分支的页面与重定向处置

剩余50个分支已逐项关联到工厂、具体模块导出和入口类型。结合前批三个页面，53个设置分支均有处置记录；这没有建立完整功能分母，也没有新增可排除的ChatGPT专属功能。

| 本批入口类型 | 数量 | 处理方式 |
| --- | ---: | --- |
| 设置页面容器 | 42 | 保留具体组件、调用边界及控件分析任务 |
| usage 的 tab 别名 | 3 | 转到同页不同 tab，保留各自功能边界 |
| renderer 重定向 | 1 | work-settings → agent?mode=work |
| 组件重定向 | 1 | time-management → safety，转换 view |
| 独立 appRoute 链接 | 1 | profile → /profile；实际独立路由组件仍待连接 |
| 目录外工厂键 | 2 | family 共用 General；environments 是展示占位，其他调用待核对 |

46个初始目标模块及6个转发模块均完成原始Program解析，命名导出均落到具体函数。已记录age、cloud-computer、local-environments、cloud-environments、cloud-settings、teams、browser-use、plugins-settings和usage的条件导航；页面存在不代表条件始终满足。

冻结源码的MNs/PNs与FNs字面量在隔离VM中执行60个用例，全部通过：53个slug归类及7个查询转换。验证包含tab替换、重复参数保留、URL编码和未知section回退。该结果只证明这些纯函数，不计入212条客户端场景的通过数。

| slug | 入口类型 | 模块导出 |
| --- | --- | --- |
| family | noncatalog-shared-factory-key | GeneralSettings |
| appshots | catalog-page-container | AppshotsSettings |
| file-type-handlers | catalog-page-container | FileTypeHandlersSettings |
| plugins-settings | catalog-page-container | PluginsSettings |
| skills-settings | catalog-page-container | SkillsSettings |
| connections | catalog-page-container | RemoteConnectionsSettings |
| work-settings | renderer-redirect | WorkSettingsPanel |
| usage | catalog-page-container | UsageSettingsPage |
| billing | catalog-page-container | ConsumerBillingSettings |
| analytics | usage-tab-alias | UsageSettingsPage |
| usage-code-review | usage-tab-alias | UsageSettingsPage |
| consumer-view | usage-tab-alias | UsageSettingsPage |
| teams | catalog-page-container | TeamSettingsPage |
| age | catalog-page-container | ChatGptAgeSettings |
| profile | standalone-app-route-link | ProfileSettings |
| passwords | catalog-page-container | PasswordsSettings |
| cloud-computer | catalog-page-container | ChatGptCloudBrowserSettings |
| browser-use | catalog-page-container | BrowserUseSettings |
| appearance | catalog-page-container | AppearanceSettings |
| chronicle | catalog-page-container | ComputerHistorySettingsPage |
| voice | catalog-page-container | VoiceSettings |
| debug | catalog-page-container | DebugSettings |
| pets | catalog-page-container | PetsSettingsRoute |
| git-settings | catalog-page-container | GitSettings |
| worktrees | catalog-page-container | WorktreesSettingsPage |
| local-environments | catalog-page-container | LocalEnvironmentsSettings |
| environments | noncatalog-placeholder-factory | SettingsExternalSection |
| import | catalog-page-container | ImportSettings |
| ads-controls | catalog-page-container | AdsControlsSettings |
| archived-chats | catalog-page-container | DataControlsSettings |
| data-controls | catalog-page-container | ChatGptDataControlsSettings |
| agreements | catalog-page-container | AgreementsSettings |
| account | catalog-page-container | ChatGptAccountSettings |
| extension | catalog-page-container | BrowserExtensionSettings |
| storage | catalog-page-container | DeviceStorageSettings |
| security | catalog-page-container | ChatGptSecuritySettings |
| parental-controls | catalog-page-container | ChatGptParentalControlsSettings |
| trusted-contact | catalog-page-container | ChatGptTrustedContactSettings |
| safety | catalog-page-container | ChatGptSafetySettings |
| time-management | component-redirect | ChatGptTimeManagementSettings |
| code-review | catalog-page-container | CodeReviewPluginSettings |
| cloud-settings | catalog-page-container | CloudPreferencesSettings |
| codex-cloud | catalog-page-container | CodexCloudSettings |
| cloud-environments | catalog-page-container | CloudEnvironmentsSettingsPage |
| personalization | catalog-page-container | ChatGptPersonalizationSettings |
| notifications | catalog-page-container | NotificationsSettingsPage |
| hooks-settings | catalog-page-container | HooksSettings |
| mcp-settings | catalog-page-container | McpSettings |
| keyboard-shortcuts | catalog-page-container | KeyboardShortcutsSettings |
| codex-micro | catalog-page-container | CodexMicroSettings |

结构化逐项记录及源码引用见[分支处置数据](settings-section-dispositions.json)。现有48个功能、212条未执行产品场景和模式分类均保持原状。下一步从保留页面的控件和处理函数建立实际操作合同；Git设置优先接到已有偏好与持久化边界。
