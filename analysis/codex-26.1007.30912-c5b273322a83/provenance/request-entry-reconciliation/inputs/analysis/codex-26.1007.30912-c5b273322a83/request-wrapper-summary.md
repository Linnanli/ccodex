# Scoped request wrapper identity review

Baseline: `codex-26.1007.30912-c5b273322a83`. Static frozen-source analysis only; no target implementation, UI, IPC, personal history or project creation was executed by this review.

The existing 337 published `sendRequest` literal candidates (108 distinct methods, 15 files) all map to one complete AST call each. The existing selected 37-file AST index contains 375 calls: 353 single literals and 22 dynamic/conditional first arguments. These are selected-file counts, not full-client coverage.

| Observed receiver category | AST calls | Published candidates |
| --- | ---: | ---: |
| Unresolved concrete receiver | 264 | 242 |
| Host manager RPC selector (`KI`, shared `y$t`) | 70 | 66 |
| Manager request facade (`Dfn` and reviewed injected helpers) | 27 | 23 |
| App-server extension connection callback (`fue`) | 5 | 5 |
| Desktop HTTP/fetch adapter (`AW`, shared `TFt`) | 6 | 0 |
| Injected resolver facade (`X2t`) | 2 | 1 |
| Coordination socket client (`c1`) | 1 | 0 |

`KI` selects `forHost`, connected `client.rpc`, a cached proxy or a deferred proxy. Its category does not establish that each call uses AppHost MessagePort or direct public app-server transport. `Dfn` forwards to its injected transport. The reviewed local fallback construction injects `Spn`, whose general enqueue path dispatches `mcp-request`; it also has a `config/read` special branch. The live appServices manager capability disables this local fallback. `thread/stop` and `thread/rollback` are confirmed through manager parameter/caller bindings; public protocol support and runtime success remain unverified.

The project dialog's `He().createLocal` resolves through initial `Mln → mI → Pd.projects`, where `Pd` imports shared `fN → e6`. `qli` gets those services through `Uli(Vli)` and its AppHost MessagePort connection. Main `hXe` constructs `qHe` as `projectsManager` and publishes it in `createAppHost`. A nonempty explicit `sources` array takes normalization rather than the default root creation branch; confirmation and thread reassignment still follow.

Reassignment is not a subtree-only cwd filter. Stored workspace-root hints can select a thread whose actual cwd differs, and matching uses identity set membership. A newly created own random temporary source path avoids these matches only if no eligible stored cwd or hint, including canonical/host identity, already matches it. This review did not inspect history or establish that runtime precondition.

`request-wrapper-contracts.json` contains eight contracts, all call classifications, unresolved bindings and published-candidate links. `request-wrapper-evidence.jsonl` contains 1,787 records with original source hash, UTF-8 byte range, span hash, claim, method, confidence and explicit static scope. All retained hashes were checked against the frozen inventory. Complete selected class ASTs verify lexical `this` ownership; helper parameter scopes are compared with the complete function range before classification.

Reproduce consolidation with `node scripts/analysis/request_wrapper_contracts.cjs <@babel/parser entry>`. It reuses the existing index and local supplemental artifacts; selected complete prefix evidence is recreated with `request_wrapper_targets.cjs`. Input hashes and supporting local reproduction scripts are listed in the JSON. It does not rerun the complete bundle analysis.

Evidence SHA-256: `770d8d34a97e784b9213021a6f800494c2bfb0a4f933ce5ba200bc377d0ad433`.
