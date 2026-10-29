#!/usr/bin/env python3
"""Publish selected frozen-source storage contracts; never runs the target client."""
import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/storage-feature-ownership-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
PREFIX = 'storage-feature-ownership-v1'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    return json.loads(p.read_text())


def dump(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def pin(name, pointer=None):
    p = OUT / name
    b = p.read_bytes()
    value = {'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': sha(b)}
    if pointer is not None:
        value['jsonPointer'] = pointer
    return value


def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    raw_dir = destination / 'raw' / PREFIX
    raw_dir.mkdir(parents=True, exist_ok=True)
    source_dir = raw_dir / 'source-units'
    source_dir.mkdir(exist_ok=True)
    lookup, units, unit_keys, passes, exports = {}, [], {}, [], []
    for number in range(1, 8):
        receipt = read(WORK / f'source-selection-{number}.json')
        for program in receipt['results']:
            passes.append({k: v for k, v in program.items() if k not in ['units', 'relations']})
            for relation in program['relations']:
                relation = {**relation, 'sourcePath': 'app.asar/.vite/build/' + program['file']}
                if relation not in exports:
                    exports.append(relation)
            for selection in program['units']:
                key = (selection['sourcePath'], selection['byteRange']['start'], selection['byteRange']['endExclusive'])
                raw = (FROZEN / selection['sourcePath'].removeprefix('app.asar/')).read_bytes()
                b = raw[key[1]:key[2]]
                assert sha(raw) == selection['sourceHash'] and sha(b) == selection['spanHash']
                assert (ROOT / selection['savedPath']).read_bytes() == b
                if key not in unit_keys:
                    uid = f'SFO-SOURCE-{len(units) + 1:03d}'
                    name = uid + '.txt'
                    (source_dir / name).write_bytes(b)
                    unit = {k: v for k, v in selection.items() if k not in ['id', 'savedPath']}
                    unit.update(id=uid, savedPath=f'raw/{PREFIX}/source-units/{name}', completeAstNode=True)
                    unit_keys[key] = uid
                    units.append(unit)
                lookup[(program['file'].split('-')[0], selection['label'])] = unit_keys[key]
                # src is ambiguous only in discovery, whose units are not selected here.
    for program in read(WORK / 'discovery.json')['programs']:
        passes.append({'file': program['file'], 'sourceHash': program['sourceHash'], 'bytes': program['bytes'],
                       'parserErrors': program['parserErrors'], 'purpose': 'initial storage owner discovery; no target execution'})
    by_id = {u['id']: u for u in units}

    def source(file, label):
        return lookup[(file, label if label.startswith(('new-', 'property-', 'contains-', 'export-')) else 'binding-' + label)]

    def sources(*names):
        return list(dict.fromkeys(source(*name.split(':', 1)) for name in names))

    facts = []

    def fact(number, claim, selected, lifecycle, remaining):
        ids = sources(*selected)
        facts.append({'id': f'SFO-FACT-{number:02d}', 'claim': claim, 'sourceUnitIds': ids,
                      'lifecycle': lifecycle, 'remainingBoundary': remaining,
                      'method': 'static-code', 'confidence': 'confirmed', 'verificationStatus': 'static-confirmed; runtime-unobserved'})

    fact(1, 'x4 是注入 globalState 的本地项目适配器；create/update/appearance 写 LOCAL_PROJECTS/PROJECT_APPEARANCES。NHe 在所选装配处收到 scopedState 与 new x4(scopedState)。这不是远程项目数据库的证明。',
         ['main:x4', 'main:Yr', 'main:ni', 'main:new-NHe-9'],
         '项目对象与外观通过 globalState.set 写入；删除分支委托 ni。写入完成沿用 SDMD-02 的队列/flush 合同。',
         '所有项目用户入口到本适配器的完整连接、远程项目 provider、实际有效 home 与磁盘完成仍分别待验。')
    fact(2, 'noe 把旧工作区根整理成本地项目与 selected project；Eoe 只迁移满足旧 self-mapping 条件的远程项目，按 host/path 去重并重写顺序、选择和旧映射；goe 的自动化 cwd 迁移可创建项目并 await flushOrThrow。',
         ['main:noe', 'main:coe', 'main:Eoe', 'main:goe'],
         '多个 globalState.set 是分步改写；goe 对新建项目显式排空。不得推断全部旧键均删除或跨自动化/项目事务。',
         '迁移触发时序与崩溃恢复、实际旧数据形状；不读取个人项目记录。')
    fact(3, 'SSH 保存和 autoConnect 偏好通过 fKe.appState 写入；保存列表会保留未参与当前目录的旧项并清理被移除项的偏好。两个命名请求 handler 分别委托 saveCodexManagedRemoteSshConnections 和 setRemoteConnectionAutoConnect。',
         ['main:fKe', 'main:property-save-codex-managed-remote-ssh-connections-1', 'main:property-set-remote-connection-auto-connect-2'],
         '偏好先写再 await 刷新/连接或断开；网络失败不等于偏好回滚。loadSavedRemoteConnections 兼容旧 alias 字段，继承 RCS-E018。',
         '继承已选 hXe→fKe 注入合同；实际文件排空/连接后效不由 UI mutation 成功或内存替身证明。')
    fact(4, 'uqe.add 可从 ~/.ssh/config 解析指定 alias 元数据，再登记 managed connection 与 autoConnect；remove 先过滤 globalState 列表和偏好再刷新。它与 sharedObjectRepository 的连接列表、registry 实时状态属于不同职责。',
         ['main:uqe', 'main:fKe'],
         'SSH 配置路径是所选元数据读取输入；这两个登记方法没有把 appState 写入等同于修改 ~/.ssh/config。共享列表与错误/进度是内存发布。',
         'SSH 解析 helper 的 Include/路径语义沿原边界保留；没有实际读取 .ssh/config。')
    fact(5, 'MMe 构造 kje 时传入下载目录与提示偏好 getter，目录回退 app.getPath(downloads)；kje 使用同一 options 构造 Xwe。AppHost createAppHost 从浏览器 manager 的 downloadStore 字段创建 downloads: new Kb(...)，Kb 逐项转发。',
         ['main:new-kje-6', 'main:new-Xwe-5', 'main:contains-18c3cf7b42d6', 'main:Kb', 'main:Xwe'],
         '偏好读取来源是 settingsStore.getEffective；设置写入继续继承 SDMD-03，下载目录选择对话框只返回路径。',
         '运行时 session 的实际 partition、有效目录/权限、renderer bridge 实例运行值仍未观察。')
    fact(6, 'Xwe 的持久下载历史交给 browserSession.getDownloadHistory/searchDownloadHistory/removeDownloadFromHistory/clearData；clearHistory 捕获非 progressing GUID，清理 downloads 类型，再读回并对残留抛错。',
         ['main:Xwe', 'main:Kb'],
         '记录删除拒绝 live/progressing 条目；clearHistory 的 JS 后验只检查非 progressing 历史。所选 Xwe 没有 rm/unlink 下载文件的调用。',
         '运行时 API 如何写磁盘、clearData 的完整原生副作用和重启恢复留在 SDMD-08 provider 边界。')
    fact(7, 'Xwe 将 liveDownloads、activeSavePaths、unacknowledgedDownloadIds 和生命周期序号放在主进程对象内；暂停、取消和恢复委托 DownloadItem。完成或失败加入未确认集合，取消不走同一提醒分支。',
         ['main:Xwe'],
         'finish 移除 live 对象和活动路径；存在下载时产生 download.active 重启阻塞项。没有选定证据证明这些 Set/Map 跨重启保存。',
         'DownloadItem 写入/取消后的文件后效、进程崩溃时内存与原生历史的协调仍须运行观察。')
    fact(8, 'Xwe.reserveSavePath 使用所选下载目录和 basename，规避已存在/活动路径并分配后缀；用户下载可走保存对话框或 session 目录，非用户下载调用 setSavePath。update 可采纳实际 getSavePath。',
         ['main:Xwe'],
         '文件 payload 路径由系统/偏好/用户对话框产生，不固定在 Codex profile；existsSync 仅作存在检查。',
         '实际文件写入由运行时承担；JS 的候选路径保留不构成跨进程原子占位。')
    fact(9, '本地自动化目录由 mF=join(o.ot(),automations) 与 gF/_F 得到 <home>/automations/<id>/automation.toml；MF 校验 ID 并读 TOML，FF 在已有行无 accountId 时写文件。',
         ['src:mF', 'src:gF', 'src:_F', 'src:JP', 'src:YP', 'src:MF', 'src:hF', 'src:FF', 'src:PF', 'src:NF'],
         'PF 在同目录写唯一临时文件后 rename；rename 失败时先 rm 目标再 rename，不能承诺任意平台的原子替换或 fsync。',
         'o.ot 的 home 选择继承已有 SDMD-01/02 源码合同；实际有效根、路径隔离、写失败残留与耐久性未观察。')
    fact(10, '自动化行/运行记录使用共享 SQLite provider q；$i 选择 <home>/sqlite/<databaseFileName|Qi()>，Qi 依据 BUILD_FLAVOR/NODE_ENV 选择 codex.db 或 codex-dev.db。na 通过 require(better-sqlite3) 加载外部实现。',
         ['src:q', 'src:$i', 'src:Qi', 'src:na', 'src:ea', 'src:Bi', 'src:Zi'],
         'ea 创建目录并打开数据库，尝试 WAL：返回 wal 则 synchronous=NORMAL，否则 FULL，再调用迁移 callback；失败关闭。q 只在 Electron 下返回缓存连接。',
         '这是共享数据库内所选表的 owner，不是所有 SQLite 表的完整恢复；退出 close/崩溃/迁移兼容性和 native ABI 分别待验。')
    fact(11, '本地 rI/iI 在默认 persist 分支先 FF 写自动化文件，再 dF INSERT OR REPLACE 数据库；dF 捕获 SQL 异常并返回 false，而这两个调用点没有把该返回值作为成功前提。QF 的读取规范化也可能更新调度行。',
         ['src:rI', 'src:iI', 'src:dF', 'src:QF', 'src:FF'],
         '文件和 SQL 是顺序副作用；读取列表不保证无写入。persist:false 用于先准备对象、后走服务保存和本地缓存。',
         '文件成功/SQL 失败的恢复策略没有由所选调用建立事务保证；不执行真实自动化。')
    fact(12, '本地 aI 删除先 DELETE automations 行，再递归 rm 自动化目录，分别返回 store_unavailable/invalid_id/not_found/state_cleanup_failed/remove_failed/deleted。z_e 仅在 deleted/not_found 后另尝试 Br/ha 删除 automation_runs，异常被捕获。',
         ['src:aI', 'src:ha', 'src:export-Br', 'main:z_e'],
         'SQL 行、文件目录与 runs 清理不在一个事务内；已有行也计入存在判断。外层 success 包含 not_found，不能推出所有残留文件已成功删除。',
         '删除后的恢复/运行中自动化协调与实际权限错误留待独立数据行为验证。')
    fact(13, 'SF/TF/xF 根据 accountId/userId/installationId 和 migration 状态区分旧本地文件与当前账户 SQL 缓存。IF 仅首次尝试在没有自动化文件、没有 owner 时从旧无账户行重建文件。',
         ['src:SF', 'src:TF', 'src:xF', 'src:IF', 'src:AF', 'src:oF', 'src:sF', 'src:fF', 'src:pF'],
         '迁移期间可合并旧文件与当前 owner 缓存，完成后仅当前 owner；owner 切换和列表可见性不等价于物理删除另一账户数据。',
         '账户切换、旧文件读取失败和重启时的实际条件未验证；不读取账户数据。')
    fact(14, 'zF 接纳已验证的服务副本时校验旧文件 hash；可先复制 memory.md，然后 BEGIN，写 owner 行/移动 runs/删除旧行并再次核对 hash，COMMIT 后再 unlink 旧 TOML。BF/goe 的旧 cwd→project 迁移另分步改写项目与自动化。',
         ['src:zF', 'src:BF', 'src:HF', 'src:WF', 'main:goe'],
         'SQL 部分有 BEGIN/COMMIT/ROLLBACK；memory 复制与 TOML 删除在事务之外。文件删除失败可在数据库已提交后返回 null。',
         '跨文件、数据库与服务的中断恢复没有全局事务证明；各失败阶段需后续合成行为测试。')
    fact(15, 'ppe.saveAndVerify 先 POST /automations/save，再 GET /automation/<id> 独立核对安装 ID、legacy ID 与内容；hosted create/update 之后经 Tn/LF 缓存 SQL，delete 先请求服务 remove 再本地删除。',
         ['main:ppe', 'main:z_e', 'main:i', 'src:LF', 'src:DF', 'src:EF'],
         '每次请求前后检查当前 principal/install；15s timeout。服务保存成功后本地缓存仍可能失败，不能报告为跨端原子事务。',
         '服务的实际持久化、幂等、认证和离线协调属于外部 API；没有调用任何服务。')
    fact(16, 'ppe 的 enrollment 与迁移状态分别来自服务接口和 globalState。persistStatus 写 account:user[:installation] 键后 flushOrThrow；失败恢复先前内存值。安装 ID 新建也显式排空。',
         ['main:ppe', 'main:gpe', 'src:SF'],
         'syncOwner 先处理 DELETED heartbeat 再分页拉取（limit=100，限制重复/过多 cursor），缓存返回项并修剪当前 owner 行；内存 owner/queue/enrollment 不作为磁盘仓库。',
         '恢复内存不证明此前磁盘或远端副作用已撤销；退出排空与实际重新登录同步仍待验证。')
    fact(17, '自动化 jitter salt 保存于 <home>/automations/.run-jitter-salt；ZF 先读非空值，否则生成 UUID，尝试写入，失败仍返回并缓存生成值。',
         ['src:ZF', 'src:QP', 'src:mF', 'src:KF'],
         '磁盘写入失败时本进程仍使用内存 salt；不能假定跨重启调度 jitter 必然稳定。',
         '并发进程、失败权限与重启后的调度行为未观察。')
    fact(18, 'Windows wn 的状态根是 realpath(userData/windows-msix-updater/<currentPackageFamily>)；staged-msix.json 保存 buildVersion/packagePath/length/sha256。有效包路径必须等于 native cache/windows-updates/prepared.msix，且文件可访问。',
         ['bootstrap:wn', 'bootstrap:A', 'bootstrap:Kn'],
         'readStageState 对无效/缺失状态移除状态文件；reconcile 对不新于当前 build 的版本 discard。读取路径检查不是重新 hash 或完整 native stage 验证。',
         'native 返回的有效缓存根、Windows 权限/包身份和激活提交行为未在当前 macOS 上观察。')
    fact(19, 'Windows _n 仅接受 HTTPS URL/最终响应，在 native cache/windows-updates/prepared.download 流式写入并计算 SHA-256；按可用 manifest 长度/hash核对，rename 到 prepared.msix 后调用 native.readPackageMetadata 核对应用身份、publisher 和 arch。',
         ['bootstrap:_n', 'bootstrap:wn'],
         'finally 清理 .download；包 metadata 核对在 rename 后。wn 再 stagePackage，之后 temp-write/rename staged-msix.json；策略变化会 discard，激活交给 native。',
         '校验信息可选性、文件与元数据提交、native stage/activate、断电恢复均不由静态成功路径替代验收。')
    fact(20, 'wn 初始化会删除状态根内 .msix/.download 普通文件和 installing 目录，再 reconcile；discard 分别移除 staged-msix.json 与 native cache 的 prepared.msix。Windows Store 路线由 Mn/Nn 与 native provider 管理。',
         ['bootstrap:wn', 'bootstrap:Mn', 'bootstrap:Nn'],
         '桌面状态根与包缓存根是不同输入；清理动作不能推广到 profile 的所有文件。Store 检查/安装队列状态主要为实例字段与 native 回调。',
         'MSIX/Store provider 的内部数据库、系统账户命名空间和实际清理结果留在平台边界。')
    fact(21, 'Kn 的 macOS 路线加载 resources/native/sparkle.node 并登记回调，下载/安装由 addon 承担；Linux Ze 读取 executable 同目录 resources/linux-package-metadata.json，仅比较已安装版本并在需要时 relaunch。',
         ['bootstrap:Kn', 'bootstrap:Ze', 'bootstrap:Je', 'bootstrap:$e', 'bootstrap:Qe', 'bootstrap:et'],
         'macOS 的 ready/progress/下载时间与重启提示是 JS 实例状态；没有选定 JS 缓存路径。Linux 路线没有在此实现远程包下载或安装。',
         'Sparkle/native/system package manager 的实际数据目录、命名空间、签名及恢复仍需对应 provider 证据；不能猜写 profile/cache。')

    domains = []
    old_map = read(OUT / 'storage-domain-map-v1.json')
    for index, domain in enumerate(old_map['domains']):
        domains.append({'id': domain['id'], 'name': domain['name'], 'status': 'reused-with-original-qualification',
                        'contractRef': pin('storage-domain-map-v1.json', f'/domains/{index}'),
                        'effectiveRootObserved': False, 'fullIsolationProven': False})
    extra_domains = [
        ('SDMD-12', '本地自动化文件、memory 与 jitter salt', ['SFO-FACT-09', 'SFO-FACT-12', 'SFO-FACT-14', 'SFO-FACT-17'], 'home/automations/<id>/automation.toml; memory.md; home/automations/.run-jitter-salt', '文件适配器拥有所选读写/删除；实际根与恢复未验收。'),
        ('SDMD-13', '共享桌面 SQLite 中的自动化与运行记录', ['SFO-FACT-10', 'SFO-FACT-11', 'SFO-FACT-12', 'SFO-FACT-13', 'SFO-FACT-14'], 'home/sqlite/<databaseFileName or codex.db|codex-dev.db>; exact Qi selection retained', 'SQLite provider + 第一方 repository/迁移；不是 history-snapshot 文件族，也不是所有表的完整分母。'),
        ('SDMD-14', '自动化账户副本与 enrollment 服务', ['SFO-FACT-15', 'SFO-FACT-16'], 'desktop authenticated HTTP /automations/*, /automations, /automation/<id>; server effective storage unknown', '服务是独立 authority；本地 SQL 是按 owner 缓存，不能与旧 TOML 一概称为缓存。'),
        ('SDMD-15', '浏览器下载的实际文件', ['SFO-FACT-05', 'SFO-FACT-08'], 'settings downloadDirectory -> OS downloads fallback -> user-selected save path', '运行时 DownloadItem 写文件；与 SDMD-08 下载历史及 Xwe 内存分开。'),
        ('SDMD-16', '平台更新的元数据与包缓存边界', ['SFO-FACT-18', 'SFO-FACT-19', 'SFO-FACT-20', 'SFO-FACT-21'], 'Windows userData state + native cache; macOS addon unknown; Linux installed package metadata', '各平台 provider 拥有不同存储/激活职责，不存在已证明的跨平台统一更新缓存根。'),
    ]
    for did, name, ids, rule, boundary in extra_domains:
        domains.append({'id': did, 'name': name, 'status': 'new-selected-source-boundary', 'sourceFactIds': ids,
                        'pathRule': rule, 'authorityQualification': boundary, 'effectiveRootObserved': False, 'fullIsolationProven': False})

    owners = []

    def owner(number, responsibility, path, fact_ids, imports, exports_, state, effects, dependencies, domains_):
        selected = list(dict.fromkeys(uid for f in facts if f['id'] in fact_ids for uid in f['sourceUnitIds']))
        owners.append({'id': f'SFO-OWNER-{number:02d}', 'responsibility': responsibility,
                       'environment': 'main; platform/host guards retained', 'mode': 'unknown',
                       'retentionDecision': 'retained pending selected mode evidence; no new Chat-only exclusion',
                       'sourceRanges': [by_id[uid] for uid in selected], 'imports': imports, 'exports': exports_,
                       'sharedState': state, 'sideEffects': effects, 'thirdPartyDependencies': dependencies,
                       'proposedPath': path, 'storageDomainIds': domains_, 'sourceFactIds': fact_ids,
                       'qualification': 'maintenance boundary proposal inferred from selected source; not an original module or a complete feature partition'})

    owner(1, '本地项目目录、外观及旧工作区迁移', 'apps/desktop/src/main/projects/local-project-state.ts',
          ['SFO-FACT-01', 'SFO-FACT-02'], ['globalState', 'project normalizers', 'automation target migration callback'],
          ['x4 project backend operations', 'noe/Eoe/goe migration steps'], ['scoped/global project keys'], ['set/update and selected flushOrThrow'], ['Node path/crypto', 'existing globalState backend'], ['SDMD-02', 'SDMD-04'])
    owner(2, '连接配置与 autoConnect 偏好、共享连接镜像的协调', 'apps/desktop/src/main/connections/connection-state.ts',
          ['SFO-FACT-03', 'SFO-FACT-04'], ['appState', 'sharedObjectRepository', 'connection registry', 'SSH metadata lookup'],
          ['managed SSH save/import/remove', 'autoConnect mutation and refresh'], ['saved host preferences', 'transient shared lists/state'], ['state writes followed by network refresh/connect'], ['Node path/os', 'SSH parser/provider', 'runtime transport'], ['SDMD-02', 'SDMD-10', 'SDMD-06'])
    owner(3, '下载控制、历史 gateway、活动对象与实际保存路径', 'apps/desktop/src/main/browser/downloads.ts',
          ['SFO-FACT-05', 'SFO-FACT-06', 'SFO-FACT-07', 'SFO-FACT-08'], ['settingsStore', 'runtime session/DownloadItem', 'AppHost receiver'],
          ['Kb forwarding API', 'Xwe snapshot/search/control'], ['liveDownloads', 'activeSavePaths', 'unacknowledged IDs'], ['runtime history clear/remove', 'download control', 'filesystem existence checks'], ['runtime download-history APIs', 'Electron/Node shell/path/fs'], ['SDMD-03', 'SDMD-08', 'SDMD-15'])
    owner(4, '自动化 TOML、目录及本地 salt 文件', 'apps/desktop/src/main/automations/local-files.ts',
          ['SFO-FACT-09', 'SFO-FACT-12', 'SFO-FACT-17'], ['home policy', 'ID validation', 'TOML schema/serializer'],
          ['file read/write/delete', 'jitter salt'], ['cached jitter salt'], ['filesystem mkdir/write/rename/rm/read'], ['Node fs/path/crypto', 'TOML parser/schema packages as dependencies'], ['SDMD-12'])
    owner(5, '共享 SQL 自动化 repository、owner 过滤与迁移协调', 'apps/desktop/src/main/automations/repository.ts',
          ['SFO-FACT-10', 'SFO-FACT-11', 'SFO-FACT-12', 'SFO-FACT-13', 'SFO-FACT-14'], ['shared database provider', 'local file adapter', 'schedule calculations'],
          ['list/get/create/update/delete and hosted cache adoption'], ['cached database handle', 'active owner and local visibility'], ['SQL CRUD and transactions', 'migration file copy/unlink outside SQL transaction'], ['better-sqlite3 12.11.1 metadata; native ABI/source qualification inherited', 'rrule/TOML dependencies'], ['SDMD-12', 'SDMD-13'])
    owner(6, '自动化账户保存、独立验证、enrollment 与本地协调', 'apps/desktop/src/main/automations/account-sync.ts',
          ['SFO-FACT-15', 'SFO-FACT-16'], ['authenticated HTTP gateway', 'principal provider', 'globalState', 'automation repository'],
          ['ppe create/update/delete/sync/migrate', 'z_e local facade'], ['owner', 'operationTail', 'migration/sync promises', 'enrollment cache'], ['HTTP', 'SQL adoption/pruning', 'migration status flush'], ['Electron net', 'remote automation service; source/storage external'], ['SDMD-02', 'SDMD-13', 'SDMD-14'])
    owner(7, 'Windows MSIX 状态、下载文件及 native stage/activate 协调', 'apps/desktop/src/main/updates/windows-msix.ts',
          ['SFO-FACT-18', 'SFO-FACT-19', 'SFO-FACT-20'], ['update offers/policy', 'native package/cache API'],
          ['check/stage/discard/install coordination'], ['check/install promises', 'progress/ready flags'], ['filesystem state/cache cleanup and writes', 'HTTPS fetch', 'native stage/activate'], ['Node fs/path/crypto', 'windows-updater.node dependency'], ['SDMD-01', 'SDMD-16'])
    owner(8, '平台更新 gateway 与原生/包管理器边界', 'apps/desktop/src/main/updates/platform-updater.ts',
          ['SFO-FACT-18', 'SFO-FACT-20', 'SFO-FACT-21'], ['managed update policy', 'platform package identity', 'Sparkle/Store/Linux provider'],
          ['Kn platform selection', 'Mn/Nn/Ze lifecycle/check interfaces'], ['ready/progress/check state', 'mac executable identity and timers'], ['native callbacks/check/install', 'Linux metadata reads and relaunch'], ['sparkle.node', 'Windows Store/native updater', 'Linux system package manager'], ['SDMD-01', 'SDMD-16'])

    fmo = read(OUT / 'feature-module-ownership-v1.json')
    features = {f['featureId']: (index, f) for index, f in enumerate(fmo['features'])}
    links = []

    def link(fid, owners_, domain_ids, ids, interpretation, remaining, reused=None):
        index, f = features[fid]
        links.append({'featureId': fid, 'name': f['name'], 'mode': f['mode'], 'featureOwnershipRef': pin('feature-module-ownership-v1.json', f'/features/{index}'),
                      'operationContractRefs': [o['contractRef'] for o in f['operationContracts']],
                      'ownerIds': owners_, 'storageDomainIds': domain_ids, 'sourceFactIds': ids,
                      'reusedContractRefs': reused or [], 'interpretation': interpretation, 'remainingBoundary': remaining,
                      'status': 'qualified-static-boundary-link; full-operation-closure-unproven', 'confidence': 'inferred',
                      'completeStateAuthorityProven': False, 'runtimeAcceptanceChanged': False})

    remote_rules = {
        'FSC-0146': '连接页面消费共享列表与状态；保存配置和实时连接实例分别所有。',
        'FSC-0147': '刷新/发现连接的只读来源与共享发布可定位；刷新也可能触发旧保存形状迁移。',
        'FSC-0148': '编辑器保存整份 managed SSH list 对应命名 save handler → fKe.appState；不推断编辑 ~/.ssh/config。',
        'FSC-0149': '导入别名保存 managed list，随后连接；uqe 的独立 alias 登记也写同类状态，不能将二者入口混为一个。',
        'FSC-0150': 'UI 过滤后保存列表；receiver 对旧目录不可见项有保留规则，过滤发送不等于所有同 host 数据均已删除。',
        'FSC-0151': 'autoConnect 请求先写偏好，再刷新并连接/断开；registry state 不作为持久配置。',
        'FSC-0154': '深链的 alias 登记阶段关联 uqе；remote project create/reuse 是额外职责，不能由 SSH 登记推定其全部存储。',
    }
    for fid, interpretation in remote_rules.items():
        link(fid, ['SFO-OWNER-02'], ['SDMD-02', 'SDMD-10', 'SDMD-06'], ['SFO-FACT-03', 'SFO-FACT-04'], interpretation,
             'renderer contract→receiver 的完整实例运行链、有效根、flush 与远程 backend 后效仍按各操作保留。',
             [pin('remote-connection-state-contracts.json', '/facts/17'), pin('remote-connection-state-contracts.json', '/facts/19')])
    link('FSC-0216', ['SFO-OWNER-03'], ['SDMD-03', 'SDMD-15'], ['SFO-FACT-05', 'SFO-FACT-08'],
         '下载偏好进入 getter；文件路径还可被保存对话框或 DownloadItem 的实际路径覆盖。', '配置后台有效层与原生写入未观察。')
    link('FSC-0219', ['SFO-OWNER-03'], ['SDMD-08', 'SDMD-15'], ['SFO-FACT-05', 'SFO-FACT-06', 'SFO-FACT-07', 'SFO-FACT-08'],
         'AppHost downloads→Kb→同一 browser manager.downloadStore；历史 API、内存控制和实际文件分别记录。', '原生 history API 的文件、取消和重启语义未验收。')
    link('FSC-0220', ['SFO-OWNER-03'], ['SDMD-08'], ['SFO-FACT-05', 'SFO-FACT-06'],
         'clearHistory 到 Xwe 的清理/读回检查已定位；不是用户下载文件的删除接口合同。', 'clearData 的完整原生后效与真实清空仍需运行验证。')
    link('FSC-0376', ['SFO-OWNER-07', 'SFO-OWNER-08'], ['SDMD-01', 'SDMD-16'], ['SFO-FACT-18', 'SFO-FACT-19', 'SFO-FACT-20', 'SFO-FACT-21'],
         '继承已交付菜单→Kn 的 provider 链；检查更新可能在 Windows 生成暂存包/状态。菜单功能不因而扩展为已盘点的全部安装 UI。',
         '平台 updater、组织策略、发行来源、实际安装/重启均未验收。', [pin('managed-update-policy-v1.json', '/facts/4'), pin('managed-update-policy-v1.json', '/facts/6')])
    for fid, indices in [('FSC-0124', [3, 4, 5, 6]), ('FSC-0125', [0, 1, 2]), ('FSC-0126', [3, 9]), ('FSC-0135', [3, 6]), ('FSC-0136', [3, 9])]:
        link(fid, [], ['SDMD-03', 'SDMD-06'], [], '复用插件合同中的条件性 HTTP/RPC/配置/物化路径；各账户与执行端分流仍分开。',
             '交互安装/卸载到全部 provider 的实例连接与实际生效/路径按原合同保留，不提升为完整 storage closure。',
             [pin('plugin-storage-authority-v1.json', f'/facts/{i}') for i in indices])
    link('FSC-0390', [], ['SDMD-07'], [], '退出命名菜单入口复用 account/logout 与令牌 cache 失效合同。',
         '内存清空不证明 auth.json/keyring 删除；实际凭据 provider/namespace 未知。', [pin('auth-storage-authority-v1.json', '/facts/5'), pin('auth-storage-authority-v1.json', '/facts/6')])

    decisions = [
        {'id': 'SFO-D01', 'decision': '以项目/连接 repository 适配已有 globalState，不新增无证据数据库；内存共享镜像另设接口。', 'factIds': ['SFO-FACT-01', 'SFO-FACT-02', 'SFO-FACT-03', 'SFO-FACT-04']},
        {'id': 'SFO-D02', 'decision': '下载的历史 provider、控制对象、偏好与实际 payload 分离；清历史与删文件采用不同验收。', 'factIds': ['SFO-FACT-05', 'SFO-FACT-06', 'SFO-FACT-07', 'SFO-FACT-08']},
        {'id': 'SFO-D03', 'decision': '自动化旧 TOML、共享 SQL、账户服务与 enrollment/owner 协调分层；不得统一替换为单一 query cache。', 'factIds': ['SFO-FACT-09', 'SFO-FACT-10', 'SFO-FACT-13', 'SFO-FACT-15', 'SFO-FACT-16']},
        {'id': 'SFO-D04', 'decision': '保留文件/SQL/服务不同失败完成点，针对写后 SQL 失败、迁移提交后 unlink 失败和云成功本地失败设计恢复场景。', 'factIds': ['SFO-FACT-11', 'SFO-FACT-12', 'SFO-FACT-14', 'SFO-FACT-15']},
        {'id': 'SFO-D05', 'decision': '更新器选择平台 gateway；Windows 状态根和 native cache 单独注入，Sparkle/Store/包管理器作为明确依赖。', 'factIds': ['SFO-FACT-18', 'SFO-FACT-19', 'SFO-FACT-20', 'SFO-FACT-21']},
        {'id': 'SFO-D06', 'decision': 'better-sqlite3 等第三方实现声明依赖；所选第一方 schema/repository 可恢复，分析选段不进入客户端 vendor 源码。', 'factIds': ['SFO-FACT-10']},
    ]
    scenarios = [
        ('SFO-C01', 'SSH 偏好已写，refresh/connect 随后失败', '偏好值、共享列表与 registry 错误分别可观察，明确重启后值；不以 UI 报错推断回滚。', ['SFO-FACT-03']),
        ('SFO-C02', '历史清理期间有 live/progressing 下载', '非 progressing 历史残留检测、活动下载状态和实际文件是否保留分别核对。', ['SFO-FACT-06', 'SFO-FACT-07']),
        ('SFO-C03', '保存对话框改路径并发生同名并发下载', '候选路径、实际路径、冲突和取消后文件逐一观察。', ['SFO-FACT-08']),
        ('SFO-C04', '自动化 TOML 写成功而 SQL 写失败', '核对调用返回、列表再次读取、重启恢复和残留文件，不能只看 create 返回对象。', ['SFO-FACT-11']),
        ('SFO-C05', 'SQL 删除成功而目录 rm 或 runs 清理失败', '核对状态码、目录、automations/automation_runs 行及外层 success 的区别。', ['SFO-FACT-12']),
        ('SFO-C06', '迁移 copy/BEGIN/COMMIT/unlink 各阶段中断', '核对 memory、旧/新 TOML、owner 行与 runs；确认可重复迁移和恢复规则。', ['SFO-FACT-14']),
        ('SFO-C07', '服务保存成功、本地缓存失败或账户切换', '核对服务副本、owner 校验、重复保存与本地恢复，不发送真实用户任务。', ['SFO-FACT-15', 'SFO-FACT-16']),
        ('SFO-C08', 'jitter salt 写失败后重启', '核对进程内稳定性与重启后 nextRunAt 差异；不得宣称磁盘 salt 已持久化。', ['SFO-FACT-17']),
        ('SFO-C09', 'Windows 下载、stage、状态 rename、activate 分别失败/中断', '核对两个根下的 prepared.download/prepared.msix/staged-msix.json、清理与再检查。', ['SFO-FACT-18', 'SFO-FACT-19', 'SFO-FACT-20']),
        ('SFO-C10', 'macOS Sparkle 或 Linux 包更新后的重启', '核对 provider 有效路径、包身份、ready 来源及新进程版本；当前未运行平台安装。', ['SFO-FACT-21']),
    ]
    scenario_records = [{'id': sid, 'trigger': trigger, 'acceptance': acceptance, 'sourceFactIds': ids,
                         'status': 'unexecuted; no new authorization or submission implied', 'personalDataAllowed': False}
                        for sid, trigger, acceptance, ids in scenarios]
    inputs = [pin(name) for name in ['feature-module-ownership-v1.json', 'storage-domain-map-v1.json', 'remote-connection-state-contracts.json',
              'plugin-storage-authority-v1.json', 'auth-storage-authority-v1.json', 'managed-update-policy-v1.json',
              'settings-operation-batch-05.json', 'settings-operation-batch-08.json']]
    sqlite_meta = FROZEN / 'node_modules/better-sqlite3/package.json'
    sqlite = read(sqlite_meta)
    dependency = {'name': sqlite['name'], 'version': sqlite['version'], 'license': sqlite['license'],
                  'sourcePath': 'app.asar/node_modules/better-sqlite3/package.json', 'sourceHash': sha(sqlite_meta.read_bytes()),
                  'locator': {'jsonPointer': '/version'}, 'qualification': 'frozen package metadata version; source/build/ABI adoption retains prior dependency audit',
                  'generateImplementationCopy': False}
    document = {
        'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'scope': 'SQ-04 selected multi-family storage ownership integration; frozen-source only; full Codex analysis scope unchanged',
        'sourceFacts': facts, 'sourceUnits': units, 'analysisPasses': passes, 'namedExportJoins': exports,
        'domains': domains, 'ownerProposals': owners, 'featureStorageLinks': links,
        'reusedAuthorities': [pin('plugin-storage-authority-v1.json'), pin('auth-storage-authority-v1.json')],
        'automationEntryCandidate': {'name': '本地与账户同步的自动化创建/更新/删除和迁移',
            'sourceUnitIds': sources('main:property-automation-create-2', 'main:property-automation-update-3', 'main:property-automation-delete-4', 'main:z_e', 'main:gpe', 'main:ppe'),
            'ownerIds': ['SFO-OWNER-04', 'SFO-OWNER-05', 'SFO-OWNER-06'], 'storageDomainIds': ['SDMD-02', 'SDMD-12', 'SDMD-13', 'SDMD-14'],
            'status': 'source-visible candidate retained for SQ-02 feature census; not a new finite feature definition',
            'qualification': 'source includes cron and heartbeat; request/agent-instruction strings are source data, not instructions to this analysis'},
        'restorationDecisions': decisions, 'additionalUnexecutedStorageScenarios': scenario_records,
        'dependencyPolicy': {'generateThirdPartyImplementation': False, 'selectedDependency': dependency,
                             'runtimeAndNativeProviders': 'explicit dependencies; frozen binaries/copies do not establish independent rebuildability'},
        'counts': {'sourceFacts': len(facts), 'savedSourceUnits': len(units), 'fullProgramParsePasses': len(passes),
                   'distinctFrozenPrograms': len({p['sourceHash'] for p in passes}), 'parseErrors': sum(p['parserErrors'] for p in passes),
                   'reusedStorageDomains': 11, 'newSelectedStorageBoundaries': 5, 'cataloguedStorageBoundaries': len(domains),
                   'ownerProposals': len(owners), 'qualifiedFeatureLinks': len(links), 'newSourceFeatureLinks': sum(bool(l['sourceFactIds']) for l in links),
                   'reusedAuthorityFeatureLinks': sum(not l['sourceFactIds'] for l in links), 'otherFiniteFeatureAssignmentsUnchanged': len(features) - len(links),
                   'restorationDecisions': len(decisions), 'additionalUnexecutedStorageScenarios': len(scenario_records),
                   'newFeatureDefinitions': 0, 'newReaRuns': 0, 'newClientLaunches': 0, 'newModelSubmissions': 0, 'newServiceCalls': 0,
                   'newProductScenarioPasses': 0, 'newClientImplementation': 0},
        'batchClosure': {'batchId': 'SQ-04-storage-feature-ownership-01', 'selectedNamedFamilyStopConditionSatisfied': True,
                         'closed': ['selected workspace/project state', 'selected remote state/preferences', 'browser downloads/history', 'automation files/SQL/account coordination', 'platform updater storage boundaries'],
                         'doesNotClose': ['all retained features storage mapping', 'full feature denominator', 'runtime/native/backend storage internals', 'effective roots/isolation/durability', 'original nine completion criteria'],
                         'repeatRule': 'Reopen only for contradictory/new source or a new retained consumer, not because existing runtime prerequisites remain unexecuted.'},
        'remaining': ['SQ-02 feature/menu/command/route census includes source-visible automation entry candidate.',
                      'SQ-04 full per-feature authority coverage remains partial; other current feature assignments stay as precise inherited gaps.',
                      'Native/backend effective roots and implementations, shared database other tables, real restart/failure/cancel behavior retain external prerequisites.',
                      '17 qualified links and8 maintenance proposals are not complete operation chains or recovered runnable packages.'],
        'inputPins': inputs, 'completeStorageDenominatorEstablished': False, 'fullStorageIsolationProven': False,
        'fullAnalysisCompleted': False, 'implementationReady': False,
    }
    dump(destination / (PREFIX + '.json'), document)
    evidence = []
    for f in facts:
        u = by_id[f['sourceUnitIds'][0]]
        evidence.append({'id': f['id'], 'baselineId': BASE, 'claim': f['claim'], 'sourcePath': u['sourcePath'], 'sourceHash': u['sourceHash'],
                         'locator': {'byteRange': u['byteRange'], 'spanHash': u['spanHash'], 'supportingSourceUnitIds': f['sourceUnitIds']},
                         'method': f['method'], 'confidence': f['confidence'], 'verificationStatus': f['verificationStatus']})
    for o in owners:
        u = o['sourceRanges'][0]
        evidence.append({'id': o['id'], 'baselineId': BASE, 'claim': o['responsibility'] + '；拟议维护边界 ' + o['proposedPath'],
                         'sourcePath': u['sourcePath'], 'sourceHash': u['sourceHash'], 'locator': {'byteRange': u['byteRange'], 'sourceFactIds': o['sourceFactIds']},
                         'method': 'inference-from-static-source', 'confidence': 'inferred', 'verificationStatus': 'maintenance-proposal; runtime-unobserved'})
    (destination / (PREFIX + '-evidence.jsonl')).write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in evidence))
    with (destination / (PREFIX + '.csv')).open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['featureId', 'name', 'ownerIds', 'domainIds', 'status', 'remainingBoundary'])
        for link_ in links:
            writer.writerow([link_['featureId'], link_['name'], '|'.join(link_['ownerIds']), '|'.join(link_['storageDomainIds']), link_['status'], link_['remainingBoundary']])
    md = ['# 存储与功能职责整合 v1', '',
          '本批将项目/远程状态、下载、自动化及平台更新的源码所有者接入既有11域，并新增5类限定存储边界。21条静态事实、8个维护职责提议与17项功能的条件关联已记录。它不代表全客户端存储分母、完整调用链或实际持久化验收。', '',
          '## 会影响恢复工程的结论', '',
          '| 家族 | 数据与所有者 | 恢复时必须区分 |', '| --- | --- | --- |',
          '| 项目/远程 | 项目对象、外观和 managed SSH/autoConnect 复用 globalState；共享列表/registry 是内存视图 | set/刷新/连接/flush 各自完成；迁移不是跨文件事务 |',
          '| 下载 | Xwe 控制活动对象；Kb/AppHost 转发；session 管历史；DownloadItem 写用户文件 | 清历史、停止下载、删除实际文件、清提醒四种后果分开 |',
          '| 自动化 | 旧 TOML + memory/salt、共享 SQLite、当前账户/安装实例服务副本、enrollment/globalState | 本地文件不是一律可丢的缓存；SQL事务不覆盖文件或服务 |',
          '| Windows 更新 | userData 下的状态文件 + native cache 下的更新包 | 两个根与 native stage/activate 单独配置/验收 |',
          '| macOS/Linux 更新 | Sparkle addon / 已安装包元数据与系统包管理器 | 未知 native 缓存根显式留空；Linux 检查不等同于下载安装 |', '',
          '## 写入、删除与恢复的具体边界', '']
    for f in facts:
        md += [f"- **{f['id']}** {f['claim']} {f['lifecycle']}", f"  待验证：{f['remainingBoundary']}"]
    md += ['', '## 拟议工程职责', '', '| 维护单元 | 拟议路径 |', '| --- | --- |']
    md += [f"| {o['responsibility']} | `{o['proposedPath']}` |" for o in owners]
    md += ['', '这些是第一方职责提议。better-sqlite3 的冻结包元数据为12.11.1；声明依赖并沿用既有原生 ABI/来源审计，不生成其实现副本。Sparkle、Windows updater 与浏览器私有历史接口的独立来源/构建资格仍保留。', '',
           '## 功能关联及覆盖限制', '',
           '17项关联中11项补充本批源码边界，6项复用插件/认证已有合同。CSV用于浏览，JSON保留各功能原操作合同及未闭合边界。其余409项当前有限功能的存储/provider缺口不变；没有将相似名字或共同源码范围当作状态归属。', '',
           '自动化 create/update/delete handler 已登记为 SQ-02 的待盘点入口候选，包含 cron/heartbeat；本批不新增功能定义或改写426项分母。项目目录的源码 owner 登记也不等于每个项目入口已连接。', '',
           '新增10条未执行存储恢复场景单列在本 JSON，不混入既有1407条产品规格或报告为通过。没有新增客户端启动、模型提交、服务调用或客户端实现。', '',
           '## 本批关闭条件与下一步', '',
           '本批命名家族中可见的存储职责已登记；native/backend内部、有效根、隔离和耐久性保持精确外部边界。整个SQ-04仍为部分完成，不将该固定批次关闭扩大为全域映射完成。下一步转SQ-02剩余菜单/命令/路由来源，优先对照已发现自动化 handler；只有新增消费者或矛盾证据才重开本批源码调查。', '',
           f"来源：[结构化合同]({PREFIX}.json)、[功能关联表]({PREFIX}.csv)、[证据]({PREFIX}-evidence.jsonl)。全部源范围对应冻结基线，源码验证只证明所述静态结构，不能证明实际产品/native/build通过。", '']
    (destination / (PREFIX + '.md')).write_text('\n'.join(md))
    shutil.copyfile(WORK / 'extract.cjs', raw_dir / 'extract.cjs')
    for number in range(1, 8):
        shutil.copyfile(WORK / f'select-{number}.json', raw_dir / f'select-{number}.json')
    return document['counts']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=WORK / 'publication')
    args = parser.parse_args()
    print(json.dumps(build(args.destination), ensure_ascii=False))
