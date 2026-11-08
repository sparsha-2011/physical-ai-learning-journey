import {loadThread} from './thread-view.js';
import * as THREE from 'three';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {RoomEnvironment} from '../vendor/RoomEnvironment.js';

const inLab=!!document.querySelector('#lab');
let inspector, clipEnd=null;
const host=document.querySelector('#viewport'),loading=document.querySelector('#loading');
const scene=new THREE.Scene();scene.background=new THREE.Color('#d9c6b9');
const camera=new THREE.PerspectiveCamera(28,1,.01,80);camera.up.set(0,0,1);
let renderer,controls,motion,groups={},rig,ropeMeshes={},time=0,playing=true,speed=.5;
const presets={sling:{eye:[.28,1.54,1.12],target:[-.125,1.20,.987]},knot:{eye:[-.035,1.325,1.145],target:[-.125,1.20,1.111]},kick:{eye:[-1.36,1.16,1.23],target:[-1.60,.55,1.08]},upper:{eye:[-.48,1.52,1.43],target:[.85,1.35,1.035]},lower:{eye:[-.45,2.56,1.25],target:[.84,2.20,.96]},carpentry:{eye:[-.99,1.95,1.54],target:[.87,1.77,1.]},inventor:{eye:[-.10,2.8,2.05],target:[-1.68,.91,.86]},machine:{eye:[5.,-5.1,4.5],target:[-.25,1.4,.85]},study:{eye:[4.6,-4.2,2.6],target:[2.60,-1.85,.65]},lounge:{eye:[1.,-3.6,2.2],target:[2.9,-1.4,.5]},sofa:{eye:[3.7,2.0,2.1],target:[2.8,4.7,1.]},service:{eye:[1.5,3.4,2.6],target:[-1.8,5.1,1.2]},nook:{eye:[-.6,-3.5,2.25],target:[-3.25,-1.4,1.]},pastries:{eye:[-1.1,3.8,1.9],target:[-3.,5.1,1.18]},coffee:{eye:[-1.7812649054302652,1.010915509532968,0.6852697779516655],target:[-1.9712649054302651,1.250915509532968,0.4102697779516655]},cafe:{eye:[7.,-6.7,6.7],target:[0,0,.3]},mechanism:{eye:[2.2,3.1,2.4],target:[.55,1.2,1.05]},duck:{eye:[-.35,1.45,1.8],target:[-1.63,.58,1.10]},cart:{eye:[2.6,1.5,2.1],target:[1.1,2.1,1.15]},supports:{eye:[2.65,3.90,1.20],target:[1.32,2.95,.62]},donut:{eye:[.05,2.53,1.43],target:[-1.75,1.00,.72]},tipper:{eye:[-2.75,.75,1.10],target:[-1.87,1.30,.48]},return:{eye:[3.0,4.9,4.6],target:[-.2,2.5,.55]}};
let pullRecord,pullMeshes=[],lowerJaw,followServing=true;let events={};
let followingBowl=null;function frame(name){const p=presets[name];followingBowl=(name==='sling'||name==='knot')?(groups['/World/Pan']?.position.z||.88):null;camera.position.fromArray(p.eye);controls.target.fromArray(p.target);if(followingBowl!==null){camera.position.z+=followingBowl-.88;controls.target.z+=followingBowl-.88}controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('selected',b.dataset.view===name))}
const array=(buffer,spec)=>spec.type==='uint32'?new Uint32Array(buffer,spec.offset,spec.count):new Float32Array(buffer,spec.offset,spec.count);
async function fetchJSON(url){const response=await fetch(url);if(!response.ok)throw new Error(`${url}: HTTP ${response.status}`);return response.json()}
async function loadGeometry(meta){
 const total=Math.max(...meta.geometries.flatMap(g=>Object.values(g).filter(v=>v&&Number.isFinite(v.offset)&&Number.isFinite(v.count)).map(v=>v.offset+v.count*4)));
 loading.textContent='Downloading the room… 0%';
 const response=await fetch('scene.bin');if(!response.ok)throw new Error(`Room download: HTTP ${response.status}`);
 if(!response.body)return response.arrayBuffer();
 // Fetch exposes decompressed bytes, so compare with geometry offsets rather
 // than the HTTP Content-Length (which describes the smaller gzip transfer).
 const data=new Uint8Array(total),reader=response.body.getReader();let received=0;
 while(true){const {done,value}=await reader.read();if(done)break;
  if(received+value.length>total){await reader.cancel();throw new Error('Room files changed during loading. Please reload.')}
  data.set(value,received);received+=value.length;
  loading.textContent=`Downloading the room… ${Math.floor(received/total*100)}% — first load may take a few minutes`;
 }
 if(received!==total)throw new Error('The room download was interrupted. Please reload.');
 return data.buffer;
}
async function init(){
 loading.textContent='Starting the 3D viewer…';
 renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.84;
 host.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','Interactive café scene. Drag to orbit, right-drag to pan, scroll to zoom.');
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.minDistance=.12;controls.maxDistance=12;controls.maxPolarAngle=Math.PI*.94;controls.zoomToCursor=true;controls.screenSpacePanning=true;
 controls.addEventListener('start',()=>{followServing=false});controls.addEventListener('start',()=>document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('selected')));
 const pmrem=new THREE.PMREMGenerator(renderer);const room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;scene.environmentIntensity=.42;room.dispose();pmrem.dispose();
 const ambient=new THREE.HemisphereLight(0xfff1df,0x594337,.35);ambient.position.set(0,0,5);scene.add(ambient);
 const key=new THREE.DirectionalLight(0xffeddc,2.25);key.position.set(-2,-3,6);key.castShadow=true;key.shadow.mapSize.set(4096,4096);Object.assign(key.shadow.camera,{left:-6,right:6,top:6,bottom:-6,near:.1,far:15});key.shadow.bias=-.00015;key.shadow.normalBias=.003;key.shadow.radius=3;scene.add(key);
 const fill=new THREE.DirectionalLight(0xe3ebff,.38);fill.position.set(3,-.5,3);scene.add(fill);
 loading.textContent='Loading the room description…';
 const metaPromise=fetchJSON('scene.json');
 const [meta,buffer,record,configuration,pull,simulation]=await Promise.all([metaPromise,metaPromise.then(loadGeometry),fetchJSON('motion.json'),fetchJSON('rig.json'),loadThread(),fetchJSON('simulation.json')]);events=simulation.events;pullRecord=pull;motion=record;rig=configuration;presets.coffee={eye:[rig.coffee_center[0]+.19,rig.coffee_center[1]-.24,rig.finale.cup_bottom+.38],target:[...rig.coffee_center,rig.finale.cup_bottom+.105]};
 loading.textContent='Preparing the furniture and lighting…';
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 const loader=new THREE.TextureLoader(),textures=new Map();
 function tex(url,color){if(!textures.has(url)){const t=loader.load(url);t.colorSpace=color?THREE.SRGBColorSpace:THREE.NoColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=renderer.capabilities.getMaxAnisotropy();textures.set(url,t)}return textures.get(url)}
 const mats=meta.materials.map(m=>{const p={color:new THREE.Color(...m.color),roughness:m.roughness,metalness:m.metalness,side:THREE.DoubleSide};if(m.opacity!==undefined&&m.opacity<1){p.opacity=m.opacity;p.transparent=true;p.depthWrite=false}for(const k of ['map','roughnessMap','metalnessMap','normalMap'])if(m[k]){p[k]=tex(m[k],k==='map');const uv=m[k+'Transform'];if(uv){p[k]=p[k].clone();p[k].repeat.fromArray(uv.repeat);p[k].offset.fromArray(uv.offset);p[k].wrapS=THREE.ClampToEdgeWrapping;p[k].wrapT=THREE.ClampToEdgeWrapping;p[k].needsUpdate=true}}return new THREE.MeshStandardMaterial(p)});
 const geos=meta.geometries.map(g=>{const b=new THREE.BufferGeometry();if(g.inlinePositions){b.setAttribute('position',new THREE.Float32BufferAttribute(g.inlinePositions,3));b.setAttribute('normal',new THREE.Float32BufferAttribute(g.inlineNormals,3));return b}for(const k of ['position','normal','uv'])if(g[k])b.setAttribute(k,new THREE.BufferAttribute(array(buffer,g[k]),k==='uv'?2:3));if(g.index)b.setIndex(new THREE.BufferAttribute(array(buffer,g.index),1));if(!g.normal)b.computeVertexNormals();b.computeBoundingSphere();return b});
 meta.labels.forEach(l=>{const g=new THREE.Group();g.name=l;groups[l]=g;scene.add(g)});
 for(const m of meta.meshes){if(m.retired)continue;let material=mats[m.material];if(m.name.endsWith('/lens_stl_0')){material=material.clone();material.color.setRGB(.048,.087,.100);material.roughness=.14;material.metalness=.18}const mesh=new THREE.Mesh(geos[m.geometry],material);mesh.name=m.name;if(m.name.startsWith("/World/RopeDraw/"))ropeMeshes[m.name.split("/").pop()]=mesh;mesh.matrix.fromArray(m.matrix);mesh.matrixAutoUpdate=false;mesh.castShadow=!m.name.includes('/Tiles/');mesh.receiveShadow=true;(m.group?groups[m.group]:scene).add(mesh)}
 Object.assign(presets,{audience:{eye:[-1.57,1.73,.755],target:[-2.145,1.46,.548]},inventor:{eye:[-.39,3.80,2.16],target:[-1.45,.99,.98]},kick:{eye:[-2.02,-.62,1.43],target:[-1.48,.55,1.22]},duck:{eye:[-1.54,1.56,1.15],target:[-2.12,1.36,.47]},pastries:{eye:[1.1,-.34,1.58],target:[1.45,.27,.98]},coffee:{eye:[-1.52,1.78,1.06],target:[-2.09,1.36,.48]},shelves:{eye:[-1.49,2.84,.62],target:[-.68,1.27,.25]},handoff:{eye:[-.83,-.49,1.67],target:[-.40,.47,1.04]}});lowerJaw=new THREE.Group();lowerJaw.position.set(-.009,.02175,.01696035);const headGroup=groups['/World/DuckFace'];headGroup.add(lowerJaw);
 for(const part of [...headGroup.children])if(/\/(jaw_stl_11|jaw_soft_stl_3)(?:$|\/)/.test(part.name)){part.matrix.premultiply(new THREE.Matrix4().makeTranslation(.009,-.02175,-.01696035));lowerJaw.add(part)}
 pullMeshes=pullRecord.meshes;scene.add(...pullMeshes);frame('inventor');new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.fov=camera.aspect<1.2?50:38;camera.updateProjectionMatrix()}).observe(host);
 loading.hidden=true;document.querySelector('#scene-status').textContent='Explore the café';
 window.cafe={camera,controls,scene,renderer,groups,meta,get time(){return time},set time(t){time=t;applyPose()},frame};
 if(inLab){
   const {installInspector}=await import('./inspector.js');
   const transport=(t,run=false,end=null)=>{time=t;playing=run;clipEnd=end;followServing=false;followingBowl=null;play.textContent=run?'Pause':'Play';applyPose();scene.updateMatrixWorld(true);};
   inspector=await installInspector({scene,camera,controls,renderer,groups,meta,rig,motion,pullMeshes,simulation,transport,read:fetchJSON,getTime:()=>time});
 }else await locateCatalogueItem();
 let previous=performance.now();
 function tick(now){requestAnimationFrame(tick);const elapsed=Math.max(0,Math.min((now-previous)/1000,.1));previous=now;if(inLab && (document.hidden || document.querySelector("#lab").hidden)){return;}if(playing)time=(time+elapsed*speed)%(motion.dt*(motion.poses.length-1)+1.2);if(clipEnd!==null&&time>=clipEnd){time=clipEnd;clipEnd=null;playing=false;play.textContent='Play'}applyPose();controls.update();if(followServing&&playing){
   const key=events.celebration!=null&&time>=events.celebration-.10?'audience':events.launcher_contact!=null&&time>=events.launcher_contact-.45?'coffee':events.bowl_contact!=null&&time>=events.bowl_contact-.35?(events.cart_contact!=null&&time>=events.cart_contact+.6?'return':'mechanism'):events.seesaw_contact!=null&&time>=events.seesaw_contact-.40?'handoff':'inventor';
   const view=presets[key],alpha=1-Math.exp(-4*elapsed);camera.position.lerp(new THREE.Vector3(...view.eye),alpha);controls.target.lerp(new THREE.Vector3(...view.target),alpha);controls.update();
  }if(inspector)inspector.tick(now);renderer.render(scene,camera);updateUI()}
 requestAnimationFrame(tick);
}
function applyPose(){if(!motion)return;const f=Math.max(0,Math.min(time/motion.dt,motion.poses.length-1)),lo=Math.floor(f),hi=Math.min(lo+1,motion.poses.length-1),a=f-lo;motion.labels.forEach((l,i)=>{const p=motion.poses[lo][i],q=motion.poses[hi][i],g=groups[l];g.position.set(p[0],p[1],p[2]).lerp(new THREE.Vector3(...q.slice(0,3)),a);g.quaternion.set(...p.slice(3)).slerp(new THREE.Quaternion(...q.slice(3)),a)});updateRope()}
const play=document.querySelector('#scene-play'),scrub=document.querySelector('#scene-seek');
function updateUI(){if(!motion)return;const duration=motion.dt*(motion.poses.length-1);scrub.value=Math.min(time,duration)/duration*1000;document.querySelector('#scene-time').textContent=Math.min(time,duration).toFixed(2)+' / '+duration.toFixed(2)+' s';if(inLab)return;let step=0;for(const [i,key] of ['seesaw_contact','bowl_contact','pulley_motion','gate_release','cart_contact','hinge_release','return_start'].entries())if(events[key]!=null&&time>=events[key])step=i+1;document.querySelectorAll('.beat').forEach((el,i)=>el.classList.toggle('active',i===step));document.querySelector('#scene-event').textContent=['Microduck takes the string, leans back and lets the ladle swing.','The seesaw sends the first marble on its way.','The marble circles the rose bowl. Microduck checks its handiwork.','The loaded bowl spins the pulleys and raises the gate.','Small car, big job. The red Beetle rolls downhill.','The Beetle opens the door. Microduck gives an approving glance.','A second marble crosses the supported slide steps.',(events.celebration!=null&&time>=events.celebration?'One sugar. Two very pleased nods.':events.sugar_received!=null&&time>=events.sugar_received?'Sugar delivered beside Microduck.':(events.launcher_contact!=null&&time>=events.launcher_contact?'The spatula gives the sugar one small nudge.':'Microduck watches the marble take the long way home.'))][step]}
play.onclick=()=>{playing=!playing;play.textContent=playing?'Pause':'Play'};
scrub.oninput=()=>{if(!motion)return;clipEnd=null;time=Number(scrub.value)/1000*motion.dt*(motion.poses.length-1);playing=false;play.textContent='Play';applyPose()};
document.querySelector('#scene-replay').onclick=()=>{followServing=true;frame('inventor');time=0;playing=true;play.textContent='Pause'};
if(!inLab)document.querySelector('#finale-replay').onclick=()=>{followServing=false;frame('coffee');time=Math.max(0,(events.launcher_contact??8)-.5);playing=true;play.textContent='Pause';applyPose()};
document.querySelector('#scene-speed').onchange=e=>speed=Number(e.target.value);
document.querySelector('#scene-full').onclick=()=>host.parentElement.requestFullscreen();
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{followServing=false;frame(b.dataset.view)});
window.addEventListener('keydown',e=>{if((inLab && document.querySelector('#lab').hidden)||e.target.matches('input,select,button,a,summary'))return;if(e.key.toLowerCase()==='r')frame('cafe');if(e.code==='Space'){e.preventDefault();play.click()}});
init().catch(error=>{console.error(error);loading.hidden=false;loading.textContent='The room could not load. '+error.message+' Reload this page to retry; if the error mentions WebGL, enable browser graphics acceleration.';document.querySelector('#scene-status').textContent='Viewer unavailable'});

function updateRope(){
 if(lowerJaw){
  const ease=(a,b)=>{const u=Math.max(0,Math.min(1,(time-a)/(b-a)));return u*u*(3-2*u)};
  const returnToRest=1-ease(1.85,2.06);
  const angle=(pullRecord.holdAngle+.165*(1-ease(.16,.42))+.21*ease(1.62,1.71))*returnToRest;
  const joy=time-(events.celebration??Infinity);
  const chirp=(joy>0 && joy<1.7) ? .31*Math.sin(Math.PI*joy/.85)**2 : 0;
  lowerJaw.rotation.y=angle+chirp;
 }
 if(pullRecord)pullRecord.update(time/motion.dt);
if(followingBowl!==null&&groups['/World/Pan']){const z=groups['/World/Pan'].position.z;camera.position.z+=z-followingBowl;controls.target.z+=z-followingBowl;followingBowl=z;}if(!rig||!groups['/World/Pan'])return;const zs=[groups['/World/Pan'].position.z+.24,groups['/World/Gate'].position.z+.10],xs=[rig.pan_xy[0],rig.gate_initial[0]];['Left','Right'].forEach((name,i)=>{const mesh=ropeMeshes[name];if(!mesh)return;const a=new THREE.Vector3(xs[i],rig.wheel_y,zs[i]),b=new THREE.Vector3(xs[i],rig.wheel_y,rig.wheel_z),v=b.clone().sub(a);mesh.matrix.compose(a.clone().add(b).multiplyScalar(.5),new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),v.clone().normalize()),new THREE.Vector3(1,1,v.length()));mesh.matrixWorldNeedsUpdate=true});
 if(rig.return_cord){
  const ends=rig.return_cord.attachments.map(v=>new THREE.Vector3(...v.local).applyQuaternion(groups[v.body].quaternion).add(groups[v.body].position));
  const curve=sag=>Array.from({length:17},(_,i)=>{const u=i/16;const p=ends[0].clone().lerp(ends[1],u);p.z-=4*sag*u*(1-u);return p});
  let lo=0,hi=.5;for(let k=0;k<28;k++){const mid=(lo+hi)/2,pts=curve(mid);const length=pts.slice(1).reduce((sum,p,i)=>sum+p.distanceTo(pts[i]),0);if(length>rig.return_cord.length_m)hi=mid;else lo=mid}
  const pts=curve((lo+hi)/2);for(let i=0;i<16;i++){const mesh=ropeMeshes['Return'+i];if(!mesh)continue;const a=pts[i],b=pts[i+1],v=b.clone().sub(a);mesh.matrix.compose(a.clone().add(b).multiplyScalar(.5),new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),v.clone().normalize()),new THREE.Vector3(1,1,v.length()));mesh.matrixWorldNeedsUpdate=true}
 }
}

async function locateCatalogueItem() {
  const id = new URLSearchParams(location.search).get('find');
  if (!id) return;
  const entries = await fetchJSON('catalogue.json'), entry = entries.find(row=>row.id===id);
  if (!entry) { document.querySelector('#scene-status').textContent='This catalogue entry could not be found'; return; }
  let index=0, outline;
  const next=document.querySelector('#next-instance'), title=document.querySelector('#focus-name');
  function locate() {
    playing=false; followServing=false; followingBowl=null; time=0; applyPose(); controls.update(); scene.updateMatrixWorld(true);
    play.textContent='Play';
    if (outline) {scene.remove(outline);outline.geometry.dispose();outline.material.dispose();}
    const box = new THREE.Box3();
    for (const i of entry.instances[index]) {
      const mesh=scene.getObjectByName(typeof i==='string'?i:window.cafe.meta.meshes[i].name);
      if(mesh)box.expandByObject(mesh,true);
    }
    if(box.isEmpty())return;
    const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
    const fov=THREE.MathUtils.degToRad(Math.min(camera.fov,2*THREE.MathUtils.radToDeg(Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.aspect))));
    const dist=Math.max(.17,size.length()*.66/Math.tan(fov/2));
    const direction=new THREE.Vector3(1,-1.7,1).normalize();
    camera.position.copy(center).addScaledVector(direction,dist);controls.target.copy(center);controls.update();
    outline=new THREE.Box3Helper(box.clone().expandByScalar(.002),0xfa7192);
    outline.material.depthTest=false;outline.material.transparent=true;outline.material.opacity=.9;outline.renderOrder=50;scene.add(outline);
    title.textContent=entry.title;
    document.querySelector('#scene-status').textContent=entry.section+' · Placement '+(index+1)+' of '+entry.instances.length;
  }
  next.hidden=entry.instances.length<2;next.onclick=()=>{index=(index+1)%entry.instances.length;locate()};
  // Keep the locator attached only while inspecting the selected placement.
  const dismiss=()=>{if(outline)outline.visible=false;};
  for(const el of document.querySelectorAll('[data-view],#scene-replay,#scene-play,#finale-replay,#scene-seek'))el.addEventListener(el.id==='scene-seek'?'input':'click',dismiss);
  requestAnimationFrame(locate);
}
