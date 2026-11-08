import * as T from 'three';

const $ = id => document.getElementById(id);
const vec = (x=0,y=0,z=0) => new T.Vector3(x,y,z);
const up = vec(0,0,1), down = vec(0,0,-1);
const degrees = T.MathUtils.radToDeg;
const cameras = {
  gate:{eye:[1.89,-.25,2.02], at:[.43,1.20,1.37], t:6.1, end:8.45},
  starter:{eye:[-3.15,-1.25,2.02], at:[-1.63,.85,1.04], t:.24, end:3.54},
  lever:{eye:[.57,-.61,1.82], at:[-.37,.67,1.06], t:3.11, end:6.39},
  curve:{eye:[1.09,3.71,1.65], at:[1.09,3.71001,.48], t:9.27, end:9.925},
  coffee:{eye:[-2.78,2.03,1.34], at:[-1.98,1.35,.53], t:12.55, end:16.97},
  room:{eye:[3.25,-3.88,4.85], at:[-.35,1.95,.89], t:0, end:17.1}
};
function zone(key){
  if (/Domino|Ladle|Microduck|DuckFace|KickLeg|DuckHead|PullCord/.test(key)) return 'starter';
  if (/Lever|^Marble$|Bridge|BowlFeeder|Fulcrum/.test(key)) return 'lever';
  if (/Marble2|TurnRails|Turnaround|ReturnRun|ReturnRails|SecondRun/.test(key)) return 'curve';
  if (/Sugar|Tipper|CoffeeMug/.test(key)) return 'coffee';
  return 'gate';
}
const titles={Cart:'Beetle',Gate:'Sliding gate',GateBracket:'Fixed gate guide',CarStop:'Wooden bumper',Pan:'Pulley bowl',Marble2:'Return marble',TurnRails:'Curved pipe guides','Turnaround/Board':'Bend board',Marble:'First marble',Lever:'Chopping-board seesaw',BowlFeeder:'Bowl feeder',WheelLeft:'Bowl-side pulley',WheelRight:'Gate-side pulley',SugarTipper:'Hanging spatula',Sugar:'Sugar cube',PullCord:'Beak pull cord',RopeDraw:'Pulley cord',CoffeeMug:'Coffee mug',CartTrack0:'Upper Beetle ramp',CartTrack1:'Lower Beetle ramp',KickLeg:'Microduck’s ankle assembly',DuckFace:'Microduck’s face',DuckHead:'Microduck’s neck'};
function title(key,record){
  if(titles[key])return titles[key];
  if(/^Domino/.test(key))return 'Carton '+(1+Number(key.slice(-2)));
  if(record)return record.title;
  return key.split('/').pop().replace(/([a-z])([A-Z])/g,'$1 $2');
}
const useful = ['Cart','Gate','GateBracket','Pan','WheelLeft','CartTrack0','CartTrack1','CarStop','PullCord','Ladle','Domino00','Domino13','Lever','Marble','Bridge','Flap','Marble2','TurnRails','Turnaround/Board','SugarTipper','Sugar'];

export async function installInspector({scene,camera,controls,renderer,groups,meta,rig,motion,pullMeshes,simulation,transport,read,getTime}){
  const [loads,support,plan,catalogue] = await Promise.all(['lab-motion.json','board-support-check.json','plan.json','catalogue.json'].map(read));
  const ev=simulation.events;
  Object.assign(cameras.gate,{t:Math.max(0,ev.bowl_contact-.20),end:ev.cart_contact+.22});
  Object.assign(cameras.curve,{t:plan.frames[0].t,end:plan.frames.at(-1).t});
  Object.assign(cameras.starter,{end:ev.seesaw_contact+.15});
  Object.assign(cameras.lever,{t:ev.seesaw_contact-.32,end:ev.bowl_contact+.12});
  Object.assign(cameras.coffee,{t:ev.launcher_contact-.68,end:ev.celebration+3.0});
  cameras.room.end=ev.celebration+3.1;
  const canvas=renderer.domElement, viewport=$('viewport'), card=$('probe'), parts=new Map(), records=new Map(), sources=new Map();
  const boardMap=new Map(support.boards.map(b=>[b.board.slice(7),b]));
  catalogue.forEach(entry=>entry.instances.forEach((indices,n)=>indices.forEach(i=>sources.set(i,{entry,n}))));
  const objects=[];
  function add(mesh,key,record){
    if(!parts.has(key))parts.set(key,[]);
    parts.get(key).push(mesh);mesh.userData.probeKey=key;objects.push(mesh);if(record)records.set(key,record);
    if(!mesh.geometry.boundingBox)mesh.geometry.computeBoundingBox();
  }
  meta.meshes.forEach((m,i)=>{
    if(m.retired)return;
    const mesh=scene.getObjectByName(m.name), root=m.name.split('/')[2], source=sources.get(i);
    let key=m.group?.slice(7)||root;
    if(/^Tire\d$/.test(key))key='Cart';
    if(root==='GateBracket'||root==='CarStop')key=root;
    if(root==='RopeDraw'&&m.name.includes('/Return'))key='Return cord';
    if(!m.group && ['Decor','Room','Set','ShelfLife','DominoShelf','Breakfast','BreakfastBakes'].includes(root))key=source.entry.id+'-'+source.n;
    add(mesh,key,source?.entry);
  });
  pullMeshes.forEach(m=>add(m,'PullCord'));
  const anatomy=new Map(), originalMaterial=new WeakMap(), highlightedMaterial=new WeakMap();
  function highlight(key,on) {
    for(const mesh of parts.get(key)||[]){
      if(!on){if(originalMaterial.has(mesh))mesh.material=originalMaterial.get(mesh);continue}
      const orig=mesh.material;originalMaterial.set(mesh,orig);
      if(!highlightedMaterial.has(orig)){
        const mat=orig.clone();mat.emissive?.setHex(0xb65d55);mat.emissiveIntensity=.32;highlightedMaterial.set(orig,mat);
      }
      mesh.material=highlightedMaterial.get(orig);
    }
  }
  const ray=new T.Raycaster(),box=new T.Box3(),v=vec();
  function intersect(clientX,clientY){
    const rect=canvas.getBoundingClientRect();
    ray.setFromCamera(new T.Vector2(2*(clientX-rect.left)/rect.width-1,1-2*(clientY-rect.top)/rect.height),camera);
    const possible=[];
    for(const mesh of objects){
      box.copy(mesh.geometry.boundingBox).applyMatrix4(mesh.matrixWorld);
      const origin=ray.ray.origin;
      if(box.containsPoint(origin))possible.push([0,mesh]);
      else if(ray.ray.intersectBox(box,v))possible.push([origin.distanceTo(v),mesh]);
    }
    possible.sort((a,b)=>a[0]-b[0]);
    let nearest;
    for(const [near,mesh] of possible){
      if(nearest && near>nearest.distance)break;
      const hits=ray.intersectObject(mesh,false);if(hits.length&&(!nearest||hits[0].distance<nearest.distance))nearest=hits[0];
    }
    if(!nearest)return null;
    const mesh=nearest.object;
    return {key:mesh.userData.probeKey,mesh,local:mesh.worldToLocal(nearest.point.clone()),normal:nearest.face.normal.clone()};
  }
  function representative(key){
    const mesh=(parts.get(key)||[])[0];if(!mesh)return null;
    return {key,mesh,local:mesh.geometry.boundingBox.getCenter(vec()),normal:null};
  }
  function boardNormal(key){
    if(!anatomy.has(key)){
      const meshes=parts.get(key);
      const mesh=meshes.find(m=>/cuttingBoard/i.test(m.name))||meshes[0];
      const b=box.copy(mesh.geometry.boundingBox).applyMatrix4(mesh.matrixWorld),center=b.getCenter(vec());
      const test=new T.Raycaster(vec(center.x,center.y,b.max.z+.1),down);
      const top=test.intersectObject(mesh,false)[0];
      anatomy.set(key,top?{mesh,normal:top.face.normal.clone()}:null);
    }
    const face=anatomy.get(key);
    return face?face.normal.clone().applyNormalMatrix(new T.Matrix3().getNormalMatrix(face.mesh.matrixWorld)):null;
  }
  const arrow=new T.ArrowHelper(down,vec(),.1,0xb53e58);
  for(const child of arrow.children){child.material.depthTest=false;child.renderOrder=100}
  scene.add(arrow);arrow.visible=false;
  const marker=new T.Mesh(new T.SphereGeometry(1,12,8),new T.MeshBasicMaterial({color:0xffead0,depthTest:false}));
  scene.add(marker);marker.renderOrder=101;marker.visible=false;
  // A level reference and a line along the measured grade meet at the picked point.
  const angleGeometry=new T.BufferGeometry(),anglePoints=new Float32Array(4*3);
  angleGeometry.setAttribute('position',new T.BufferAttribute(anglePoints,3));
  const angleLines=new T.LineSegments(angleGeometry,new T.LineBasicMaterial({color:0xf8bd68,depthTest:false}));
  angleLines.renderOrder=98;angleLines.frustumCulled=false;angleLines.visible=false;scene.add(angleLines);
  function showGrade(origin,grade,length){
    angleLines.visible=!!grade && Math.abs(grade.z)>.001;
    if(!angleLines.visible)return;
    const level=vec(grade.x,grade.y,0).normalize();
    [origin.clone().addScaledVector(level,length),origin,origin,origin.clone().addScaledVector(grade,length)].forEach((v,i)=>v.toArray(anglePoints,3*i));
    angleGeometry.attributes.position.needsUpdate=true;
  }
  let lastMachineKey=null,hit=null,pinned=false,activeZone='gate',pointer=null,drag=null,orbiting=false,lastRead=-Infinity,lastRay=-Infinity,dirty=true;
  const note=$('probe-note'),list=$('part-list'),select=$('lab-view'),viewNote=$('scene-status');
  function setHit(next,lock=false){
    const previous=hit?.key;
    if(previous!==next?.key){highlight(previous,false);if(next)highlight(next.key,true)}
    hit=next;pinned=!!next&&lock;card.hidden=!hit;arrow.visible=false;marker.visible=false;angleLines.visible=false;
    $('unpin').hidden=!pinned;list.value=pinned&&useful.includes(hit.key)?hit.key:'';
    canvas.style.cursor=next?'pointer':'grab';
    if(next){if(!next.key.startsWith('asset-'))lastMachineKey=next.key;$('probe-state').textContent=pinned?'Pinned part':'Under pointer';$('probe-name').textContent=title(next.key,records.get(next.key));lastRead=-Infinity}
    updateCross();
  }
  const responsive=matchMedia('(max-width:650px)');
  function moveCard(){
    if(responsive.matches)viewport.after(card);else viewport.append(card);
  }
  moveCard();responsive.addEventListener('change',moveCard);
  function setCamera(name){
    activeZone=name;select.value=name;const shot=cameras[name];transport(shot.t);
    camera.position.fromArray(shot.eye);controls.target.fromArray(shot.at);controls.update();
    pointer=null;dirty=true;lastMachineKey=null;setHit(null);
    viewNote.textContent=name==='curve'?'Marble bend · overhead':'Hover or tap a part';
  }
  select.onchange=()=>setCamera(select.value);
  useful.filter(k=>parts.has(k)).forEach(k=>list.add(new Option(title(k,records.get(k)),k)));
  list.onchange=()=>{
    const key=list.value;if(!key){setHit(null);return}
    const where=zone(key);if(where!==activeZone)setCamera(where);setHit(representative(key),true);
  };
  function release(){pointer=null;setHit(null);canvas.focus({preventScroll:true})}
  $('unpin').onclick=release;
  canvas.tabIndex=0;canvas.addEventListener('keydown',e=>{if(e.key==='Escape')release()});
  canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,id:e.pointerId,moved:false}});
  canvas.addEventListener('pointermove',e=>{
    if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>5)drag.moved=true;
    if(e.pointerType==='mouse'&&!e.buttons){pointer={x:e.clientX,y:e.clientY};dirty=true;}
  });
  canvas.addEventListener('pointerup',e=>{
    if(!drag||e.pointerId!==drag.id)return;
    if(!drag.moved&&e.button===0){
      scene.updateMatrixWorld(true);const next=intersect(e.clientX,e.clientY);
      if(pinned&&next?.key===hit?.key)release();else setHit(next,!!next);
    }
    drag=null;
  });
  canvas.addEventListener('pointercancel',()=>{drag=null;pointer=null});
  canvas.addEventListener('pointerleave',()=>{pointer=null;if(!pinned)setHit(null)});
  controls.addEventListener('start',()=>{orbiting=true;if(!pinned)setHit(null)});
  controls.addEventListener('end',()=>{orbiting=false;dirty=true});
  controls.addEventListener('change',()=>dirty=true);
  const slice=new Image();slice.src='sections.webp';
  const first=plan.frames[0].t,last=plan.frames.at(-1).t;
  function nearestFrame(t){return plan.frames.reduce((a,b)=>Math.abs(b.t-t)<Math.abs(a.t-t)?b:a)}
  function updateCross(){
    $('cross').hidden=!(activeZone==='curve'||hit?.key==='TurnRails'||hit?.key==='Marble2'||hit?.key==='Turnaround/Board');
  }
  let sliceIndex=-1;
  function drawSlice(t){
    if($('cross').hidden||!$('cross').open||!slice.complete)return;
    const within=t>=first&&t<=last, f=within?nearestFrame(t):null,idx=f?plan.frames.indexOf(f):-2;
    if(idx===sliceIndex)return;sliceIndex=idx;const ctx=$('live-section').getContext('2d');
    $('live-section').hidden=!within;
    if(f){ctx.drawImage(slice,idx%5*680,Math.floor(idx/5)*252,680,252,0,0,680,252);$('slice-caption').textContent=f.t.toFixed(3)+' s · Pipe gap '+f.gap.toFixed(2)+' mm';}
    else $('slice-caption').textContent='The marble is outside the sampled bend.';
  }
  $('nearest').onclick=()=>{setCamera('curve');transport(plan.frames[plan.critical].t);setHit(representative('Marble2'),true);$('cross').open=true};
  function replayZone(key){
    if(boardMap.has(key)){
      if(/^ReturnRun/.test(key))return [ev.return_start-.16,ev.launcher_contact+.12];
      if(/^SecondRun/.test(key))return [ev.hinge_release-.12,first+.16];
      if(key==='BowlFeeder')return [ev.seesaw_contact+.87,ev.bowl_contact+.22];
    }
    if(key==='Flap'||key==='CarStop'||key==='CartTrack1')return [ev.cart_contact-.80,ev.cart_contact+.36];
    if(key==='Pan')return [ev.bowl_contact-.65,ev.gate_release+.23];
    const s=cameras[key?zone(key):activeZone];return [s.t,s.end];
  }
  $('scene-replay').onclick=()=>{const [start,end]=replayZone(hit?.key||lastMachineKey);if(hit)setHit(hit,true);transport(start,true,end)};
  function describe(t){
    const key=hit.key,rows=[],idx=Math.min(loads.gate.length-1,Math.max(0,Math.floor(t*loads.hz)));
    const add=(label,value,source)=>rows.push([label,value,source]);
    const angle=(label,n,src='Simulated')=>add(label,n.toFixed(1)+'°',src);
    const force=(label,n,src='Simulated')=>add(label,n.toFixed(2)+' N',src);
    const board=boardMap.get(key),col=key.match(/^Pantry\/Column(\d+)/);
    const mass=key==='Cart'?loads.mass.Cart+[1,2,3,4].reduce((s,i)=>s+loads.mass['Tire'+i],0):(board?.board_mass_kg??loads.mass[key]);
    let direction=null,grade=null,detail='',hasAngle=false;
    if(key==='Cart'){
      const axle=i=>groups['/World/Tire'+i].position;
      const axis=axle(1).clone().add(axle(3)).sub(axle(2)).sub(axle(4)).normalize();
      grade=axis;angle('Chassis pitch',degrees(Math.asin(axis.z)));hasAngle=true;
    }
    if(key==='Gate'||key==='GateBracket'||key==='Pan'){angle('Guide from horizontal',90);hasAngle=true}
    if(board||key==='Lever'||key==='TurnRails'){
      const n=boardNormal(key==='TurnRails'?'Turnaround/Board':key);
      if(n){grade=down.clone().addScaledVector(n,n.z).normalize();angle('Board slope',degrees(Math.acos(Math.min(1,Math.abs(n.z)))),'Measured');hasAngle=true}
    }
    if(/^Domino/.test(key)||['Ladle','SugarTipper','Flap'].includes(key)){
      const axis=up.clone().applyQuaternion(groups['/World/'+key].quaternion);
      angle(/^Domino/.test(key)?'Carton lean':'Swing from vertical',degrees(axis.angleTo(up)));hasAngle=true;
    }
    if(['WheelLeft','WheelRight','Microduck','DuckHead','DuckFace','KickLeg'].includes(key)){
      const i=motion.labels.indexOf('/World/'+key),initial=new T.Quaternion(...motion.poses[0][i].slice(3));
      angle('Rotation since start',degrees(initial.angleTo(groups['/World/'+key].quaternion)));hasAngle=true;
    }
    if(key==='Marble'){
      const contact=simulation.contacts.find(c=>c.pair.includes('Marble')&&c.pair.some(p=>['Lever','Bridge','BowlFeeder'].includes(p))&&t>=c.first_s-.017&&t<=c.last_s+.017);
      const on=contact?.pair.find(p=>p!=='Marble');
      if(on){
        const n=boardNormal(on);
        if(n){const slope=Math.acos(Math.min(1,Math.abs(n.z)));
          angle(on==='Lever'?'Seesaw slope':'Board slope',degrees(slope),'Measured');
          force('Down-slope weight',mass*9.81*Math.sin(slope),'Estimated');hasAngle=true}
      }
      const id=motion.labels.indexOf('/World/Marble'),i=Math.min(motion.poses.length-2,Math.max(0,Math.floor(t/motion.dt)));
      const a=vec().fromArray(motion.poses[i][id]),b=vec().fromArray(motion.poses[i+1][id]);
      add('Travel speed',(1000*a.distanceTo(b)/motion.dt).toFixed(1)+' mm/s','Simulated');
    }
    if(key==='Marble2' && t>=first&&t<=last){angle('Board slope',plan.slope,'Measured');hasAngle=true}
    if(!hasAngle&&hit.normal){const n=hit.normal.clone().applyNormalMatrix(new T.Matrix3().getNormalMatrix(hit.mesh.matrixWorld));angle('Surface under pointer',degrees(Math.acos(Math.min(1,Math.abs(n.z)))),'Measured')}
    if(mass!=null){add('Model mass',mass>=1?mass.toFixed(2)+' kg':(mass*1000).toFixed(1)+' g','Estimated');force('Weight ↓',mass*9.81,'Estimated');direction=down}
    if(['Gate','GateBracket','Cart','CarStop'].includes(key)){
      const values=key==='CarStop'?loads.bumper[idx]:loads.gate[idx], contact=vec(...values);
      if(key==='Cart')contact.negate();
      force(key==='CarStop'?'Car on bumper':key==='Cart'?'Gate on car':'Car on gate',contact.length());
      if(contact.length()>.005){direction=contact.normalize();detail='Arrow shows the contact force direction.'}
      if(key==='GateBracket'){detail='The bolted guides take the sliding gate’s side load. The displayed force acts on the gate.';direction=null}
      if(key==='Gate')detail+=' The wood-backed gate carries the car. The carton counterbalances the bowl.';
    }else if(board){
      const total=board.seats.reduce((s,v)=>s+loads.boardNormal[idx][v.column],0);
      force('Support normal load',total);detail='Sum of recorded normal loads at the board’s seats.';
    }else if(col){
      force('Stack base normal load',loads.baseNormal[idx][Number(col[1])]);detail='Reaction at the base of this support column.';
    }else if(key==='Marble2'||key==='TurnRails'){
      if(t>=first&&t<=last){
        const f=nearestFrame(t),radial=loads.radialN[plan.frames.indexOf(f)];
        add('Marble–pipe gap',f.gap.toFixed(2)+' mm','Simulated');
        force(radial>=0?'Net force inward':'Net force outward',Math.abs(radial),'Estimated');
        detail='Net radial force on the marble, estimated from its motion over 25 ms.';
        if(key==='Marble2'&&Math.abs(radial)>.005){direction=vec(-f.radial[0],-f.radial[1],0).multiplyScalar(Math.sign(radial));detail+=' Arrow shows its direction.'}
      }
      else detail='Replay the bend to inspect clearance.';
      if(key==='TurnRails')detail+=' A negative gap is slight contact overlap.';
    }else if(key==='Marble'){
      detail=simulation.marble_rest_run?'Starts in the resting spot found by the no-pull run. The final carton tilts the seesaw.':'The last carton tilts the seesaw and sends the marble toward the bowl.';
    }else if(key==='Pan'){
      add('Incoming marble',Math.round(loads.mass.Marble*1000)+' g','Estimated');detail='The added weight lifts the gate through the pulley line.';
    }else if(key==='PullCord'||key==='Microduck'){
      force('Peak beak pull',simulation.starter.peak_tension_N);detail=key==='PullCord'?'Peak tension comes from the recorded ladle drive. The flexible spans and pearl follow that replay.':'Peak over the opening pull.';
    }else if(key==='RopeDraw'||key==='Return cord'){
      detail='Tension-only link. This recording contains no force trace for this cord.';
    }else if(mass==null){detail='This surface has no recorded force reading.'}
    if(direction===down)detail+=(detail?' ':'')+'Arrow shows weight.';
    return {rows,direction,detail,grade};
  }
  let lastHTML='',lastTime=-1;
  function tick(now){
    const t=getTime();scene.updateMatrixWorld(true);
    if(pointer&&!pinned&&!orbiting&&!drag&&now-lastRay>90&&(dirty||t!==lastTime)){
      const pick=intersect(pointer.x,pointer.y);setHit(pick);dirty=false;lastRay=now;
    }
    lastTime=t;
    if(hit){
      const origin=hit.mesh.localToWorld(hit.local.clone()),screen=origin.clone().project(camera);
      marker.position.copy(origin);const length=Math.max(.008,camera.position.distanceTo(origin)*.065);
      marker.scale.setScalar(length*.04);marker.visible=true;
      if(!responsive.matches){
        const x=(screen.x+1)*viewport.clientWidth/2,y=(1-screen.y)*viewport.clientHeight/2;
        const width=card.offsetWidth,height=card.offsetHeight;
        card.style.left=Math.max(8,Math.min(viewport.clientWidth-width-8,x+width+20<viewport.clientWidth?x+16:x-width-16))+'px';
        card.style.top=Math.max(8,Math.min(viewport.clientHeight-height-8,y-height/2))+'px';
      }
      if(now-lastRead>65){
        const {rows,detail,direction,grade}=describe(t),html=rows.map(([k,val,src])=>'<div class="probe-row"><span>'+k+'</span><span>'+val+'<small>'+src+'</small></span></div>').join('');
        if(html!==lastHTML){$('probe-values').innerHTML=html;lastHTML=html}
        note.textContent=detail;showGrade(origin,grade,length*1.45);arrow.visible=!!direction;
        if(direction){arrow.position.copy(origin);arrow.setDirection(direction);arrow.setLength(length,length*.24,length*.13)}
        lastRead=now;
      }
      if(arrow.visible)arrow.position.copy(origin);
    }
    drawSlice(t);
  }
  const requested=new URLSearchParams(location.search).get('part');
  if(useful.includes(requested)&&parts.has(requested)){
    setCamera(zone(requested));setHit(representative(requested),true);
  }else setCamera('gate');
  return {tick};
}
