"""Run one bounded, owned public runtime probe; keep receipts on failure."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'.analysis-local/runtime-surface-disposition-work'
RUNTIME=ROOT/'.analysis-local/public-runtime-comparison-work/electron-42.3.0-01'
PROBE=WORK/'probe-01'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


if __name__=='__main__':
    PROBE.mkdir(exist_ok=False)
    receipt={'startedAtUtc':datetime.now(timezone.utc).isoformat(),
             'originalClientRunsAdded':0,'modelSubmissionsAdded':0}
    binary=RUNTIME/'unpacked/Electron.app/Contents/MacOS/Electron'
    framework=RUNTIME/'unpacked/Electron.app/Contents/Frameworks/Electron Framework.framework/Versions/A/Electron Framework'
    archive=RUNTIME/'electron-v42.3.0-darwin-x64.zip'
    assert digest(archive)=='92bc6bc82cbfe4c855e9b8c55cf48c32f0448553bb74defe8cc436da9588a73e'
    with zipfile.ZipFile(archive) as z:
        pins=[]
        for p in [binary,framework]:
            member=str(p.relative_to(RUNTIME/'unpacked'))
            with z.open(member) as source:
                expected=hashlib.file_digest(source,'sha256').hexdigest()
            actual=digest(p);assert actual==expected
            pins.append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual,'archiveMember':member})
    receipt['runtimePins']=pins
    script=PROBE/'probe_runtime_surface.cjs'
    shutil.copyfile(ROOT/'scripts/analysis/probe_runtime_surface.cjs',script)
    receipt['probeSha256']=digest(script)
    command=[str(binary),f'--user-data-dir={PROBE}/profile',str(script),f'--ccodex-owned-surface={WORK}']
    receipt['command']=command
    environment={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LANG':'en_US.UTF-8','TMPDIR':str(PROBE/'tmp')}
    Path(environment['TMPDIR']).mkdir()
    with (PROBE/'stdout.txt').open('wb') as stdout,(PROBE/'stderr.txt').open('wb') as stderr:
        process=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr,start_new_session=True)
        receipt['pid']=process.pid
        try:
            receipt['exitCode']=process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            receipt['timedOut']=True
            assert os.getpgid(process.pid)==process.pid
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
            receipt['exitCode']=process.returncode
    listing=subprocess.run(['/bin/ps','-axo','pid=,ppid=,command='],capture_output=True,text=True,check=False)
    marker=str(PROBE)
    receipt['ownedProcessCheck']={'exitCode':listing.returncode,'matchingProcesses':[x.strip() for x in listing.stdout.splitlines() if marker in x and '/Electron' in x]}
    receipt['completedAtUtc']=datetime.now(timezone.utc).isoformat()
    (PROBE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['pid','exitCode','ownedProcessCheck']}))
