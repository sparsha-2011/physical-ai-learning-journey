import {PerspectiveCamera} from 'three';
import {OrbitControls} from '../vendor/OrbitControls.js';

const byId=id=>document.getElementById(id);
const canvas=byId('screen'), ctx=canvas.getContext('2d',{alpha:false});
const camera=new PerspectiveCamera(38,16/9,.01,80);
camera.up.set(0,0,1);
const controls=new OrbitControls(camera,canvas);
controls.minDistance=.16;
controls.maxDistance=14;
controls.maxPolarAngle=Math.PI*.94;
controls.screenSpacePanning=true;
const views={
  room:[[3.25,-3.88,4.85],[-.35,1.95,.89]],
  duck:[[-1.84,1.98,.85],[-2.13,1.53,.59]],
  gate:[[-1.33,2.76,2.12],[.35,1.20,1.35]],
  bend:[[.83,3.17,2.20],[.82,3.16,.48]],
  mug:[[-2.31,1.13,.59],[-1.91,1.30,.43]]
};
function frame(name){
  const [eye,target]=views[name];camera.position.fromArray(eye);controls.target.fromArray(target);controls.update();queueFrame();
}
let socket, pending=false, dirty=true, playing=false, duration=20, time=0, last=0, speed=.5, scheduled=false;
let generation=0, settle=0;
const status=byId('status'), retry=byId('retry'), play=byId('play'), timeline=byId('seek');
function clock(){
  if(playing){
    const now=performance.now();time=Math.min(duration,time+(now-last)*.001*speed);last=now;
    if(time>=duration)setPlaying(false);
  }
}
function setPlaying(value){playing=value;last=performance.now();play.textContent=value?'Pause':'Play'}
function updateTime(){
  timeline.value=time;byId('time').textContent=time.toFixed(2)+' / '+duration.toFixed(2)+' s';
}
function send(){
  scheduled=false;
  if(pending||document.hidden||socket?.readyState!==WebSocket.OPEN||(!dirty&&!playing&&settle===0))return;
  clock();updateTime();dirty=false;pending=true;
  if(settle>0)settle--;
  socket.send(JSON.stringify({time,eye:camera.position.toArray(),target:controls.target.toArray()}));
}
function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(send)}}
function queueFrame(){dirty=true;settle=2;schedule()}
controls.addEventListener('change',queueFrame);
frame('room');
function connect(){
  const gen=++generation;socket?.close();pending=false;setPlaying(false);
  status.hidden=false;status.textContent='Connecting to Brev…';retry.hidden=true;
  const endpoint = new URL('/cafe', location.href);
  endpoint.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(endpoint);
  socket.onmessage=async({data})=>{
    if(gen!==generation)return;
    if(typeof data==='string'){
      duration=JSON.parse(data).duration;timeline.max=duration;status.textContent='Preparing the RTX view…';queueFrame();return;
    }
    try{
      const image=await createImageBitmap(data);
      if(gen!==generation){image.close();return}
      ctx.drawImage(image,0,0,canvas.width,canvas.height);image.close();
      status.hidden=true;byId('rtx-controls').disabled=false;canvas.dataset.frames=String(Number(canvas.dataset.frames||0)+1);
      pending=false;schedule();
    }catch{socket.close(1000,'Invalid frame')}
  };
  socket.onclose=()=>{
    if(gen!==generation)return;
    pending=false;setPlaying(false);byId('rtx-controls').disabled=true;
    status.textContent='Brev connection closed. Reconnect when the RTX service is ready.';status.hidden=false;retry.hidden=false;
  };
}
retry.onclick=connect;
play.onclick=()=>{if(time>=duration)time=0;setPlaying(!playing);queueFrame()};
byId('restart').onclick=()=>{time=0;setPlaying(true);queueFrame()};
timeline.oninput=()=>{setPlaying(false);time=Number(timeline.value);updateTime();queueFrame()};
byId('speed').onchange=e=>{clock();speed=Number(e.target.value);queueFrame()};
byId('view').onchange=e=>frame(e.target.value);
byId('full').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else byId('live-shell').requestFullscreen()};
document.addEventListener('visibilitychange',()=>{if(document.hidden){clock();setPlaying(false)}else queueFrame()});
window.addEventListener('pagehide',()=>{generation++;socket?.close()});
window.addEventListener('pageshow',e=>{if(e.persisted)connect()});
// Old film bookmarks now open the live viewer.
if(location.hash==='#film')history.replaceState(null,'',location.pathname);
connect();
