// Only round trips to this process's synthetic loopback and Unix socket servers.
const fs=require('node:fs');
const net=require('node:net');
const path=require('node:path');
const output=process.argv[2],ipcPath=process.argv[3];
if(!path.isAbsolute(output)||!ipcPath.startsWith('/private/tmp/ccx-ep-'))throw Error('Owned fixture paths required');
const result={kind:'public-electron-run-as-node-permission-probe',node:process.version,pid:process.pid,
  permissionEnabled:typeof process.permission==='object',
  scopes:{net:process.permission?.has('net'),ipc:process.permission?.has('ipc',ipcPath)},
  allowIpcInNodeEnvironmentFlags:process.allowedNodeEnvironmentFlags.has('--allow-ipc'),
  originalClientRunsAdded:0,modelSubmissionsAdded:0,observations:[]};
async function roundTrip(endpoint){
  return new Promise((resolve,reject)=>{
    let client,done=false;const server=net.createServer(socket=>socket.once('data',data=>socket.end(data)));
    const timer=setTimeout(()=>finish(Error('owned roundtrip timeout')),5000);
    function finish(error){
      if(done)return;done=true;clearTimeout(timer);client?.destroy();
      const complete=()=>error?reject(error):resolve(true);
      if(server.listening)server.close(complete);else complete();
    }
    server.on('error',finish);
    server.listen(endpoint,()=>{
      const address=typeof endpoint==='string'?{path:endpoint}:{host:'127.0.0.1',port:server.address().port};
      client=net.connect(address,()=>client.write('CCODEX_OWNED_NET_FIXTURE'));
      client.on('error',finish);
      client.once('data',data=>finish(data.toString()==='CCODEX_OWNED_NET_FIXTURE'?null:Error('fixture mismatch')));
    });
  });
}
(async()=>{
  for(const [id,endpoint]of [['owned-tcp-loopback',{host:'127.0.0.1',port:0}],['owned-unix-ipc',ipcPath]]){
    try{await roundTrip(endpoint);result.observations.push({id,status:'roundtrip-completed'});}
    catch(error){result.observations.push({id,status:'denied-or-error',code:error.code??null,message:error.message});}
  }
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(error=>{console.error(error);process.exitCode=1;});
