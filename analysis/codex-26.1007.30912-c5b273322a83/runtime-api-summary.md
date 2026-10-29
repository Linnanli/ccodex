# Scoped desktop runtime API contracts

Baseline: codex-26.1007.30912-c5b273322a83; archive SHA-256 c5b273322a833ce5165429d468021cc6289a11cc68d075b80ae773bd7fb6731f. Target code was parsed as data; no target/UI/model execution or personal histories/credentials were accessed.

The package names runtime `owl`. A complete bootstrap guard rejects an Electron-version-bearing process lacking `app.showTaskManager`. Actual Electron/Node versions and native ABI remain unknown. The root Electron development dependency cannot supply those values.

| Core frozen file | Bytes | Call/constructor expressions | Electron-derived call sites | Unknown name candidates | Resolver budget hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| early-bootstrap.js | 3304 | 77 | 21 | 0 | 0 |
| bootstrap-CooIJpZm.js | 461537 | 8007 | 195 | 103 | 0 |
| main-CqEoQDOU.js | 3824411 | 63888 | 958 | 4068 | 34 |
| preload.js | 6909 | 101 | 30 | 3 | 0 |
| sandbox-preload.js | 2102 | 31 | 1 | 0 | 0 |
| browser-page-preload.js | 527604 | 9970 | 18 | 1 | 0 |
| browser-background-switches-Zzmx0u5p.js | 144216 | 167 | 3 | 0 | 0 |
| desktop-open-path-queue-BbHRJtaX.js | 3749 | 89 | 4 | 2 | 0 |
| application-network-startup-CfAQmSYg.js | 290566 | 5197 | 0 | 101 | 0 |
| startup-requirements-C6B1x9gL.js | 115575 | 2719 | 12 | 15 | 0 |

The fixed ten-file denominator is 90246 call/constructor expressions and 5379973 bytes. There are 1242 Electron-derived call sites, including 6 JavaScript bind expressions, 241 member references and 229 distinct callee paths. 4293 unknown name candidates may include third-party/ordinary methods; they are not confirmed runtime APIs or complete unknown coverage. The bounded resolver recorded 34 budget hits, conservatively leaving those paths unresolved. One extra frozen Rolldown helper was reviewed for property forwarding, and one packaged Owl JSON resource for identity; neither inflates the core-file denominator.

Each source-confirmed usage includes the whole call and argument nodes, actual literal object properties/spreads, callback signatures/full spans, lexical binding/assignment chain, complete enclosing function/class spans and selected enclosing platform/lifecycle predicates. Constant identifier arguments are resolved within lexical scopes when unmutated; dynamic values and injected objects remain unknown. The supplemental anchors retain the stock-runtime guard, native update binding, network relaunch/check/scope functions, Linux startup ordering, packaged Owl user-agent defaults, adoption shape/routine and full preload bridge object.

Partial public primitives are documented: [IPC](https://www.electronjs.org/docs/latest/api/ipc-renderer), [contextBridge](https://www.electronjs.org/docs/latest/api/context-bridge), [CommandLine](https://www.electronjs.org/docs/latest/api/command-line), [Session](https://www.electronjs.org/docs/latest/api/session) and [window APIs](https://www.electronjs.org/docs/latest/api/browser-window). This supports adapter candidates only; it does not establish packaged Owl equivalence. `executeInMainWorld` is experimental in the current public reference; IPC structured cloning/port ownership, synchronous initialization and bridge type rules need explicit contract tests.

The scoped current public reference searches did not find `app.showTaskManager`, `app.setRuntimeFeatures`, `app.beginNativeMenuTracking`, `Session.setPermissionPromptHandler`, `BrowserWindow.setHistorySwipeNavigationState`, `AdoptionLease` or `setFaviconImageSizes`. Private update binding and Owl permission/switch semantics likewise have no established public replacement. This is limited document inspection, not proof of absence in every version. Many other members remain documentation-unknown.

The injected adoption receiver requires `_createWebViewAdoptionLease(owner)` and a nonempty lease string, and tracks destruction/cleanup. Its full cross-caller provenance is unresolved. Favicon candidates are kept as unknown receivers with complete function/call spans. Portability therefore requires explicit runtime adapters and evidence-driven regression fixtures; deleting the Owl guard or changing the Electron version does not implement missing contracts. No independent client build or UI fidelity is claimed.

Implementation boundary: keep app/lifecycle, window, WebContents, session, IPC/preload and optional Owl capabilities behind owned runtime interfaces. A stock-Electron adapter is a candidate for the reviewed public subset only. Private task manager/menu tracking, adoption/favicons, permission prompt, runtime feature controls, native policies and custom switches require an explicit replacement decision or capability fallback; do not silently report them as supported. Before implementation, pin an actually measured target runtime/ABI, resolve dynamic options/callback contracts for the chosen feature slice, and define fixtures for sync IPC initialization, structured clone/chunk ack, MessagePort ownership, destroy/cleanup ordering and platform guards. Upgrade comparison should use source-hashed callee/option/event contracts and capability tests rather than minified names.

Reproduce with Node and Babel parser (target code is never executed):

`node .analysis-local/runtime-api-work/scan-runtime-api.cjs /path/to/@babel/parser/lib/index.js`

`node .analysis-local/runtime-api-work/review-runtime-api.cjs /path/to/@babel/parser/lib/index.js`

The final evidence spans were reread and SHA-256 checked against frozen source and source inventory before publication. The final result has 11512 evidence records and 0 parser failures.
