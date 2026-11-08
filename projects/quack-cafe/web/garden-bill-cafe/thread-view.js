import * as THREE from 'three';

// Two bead pose markers precede the cut end of the continuous cotton strand.
export async function loadThread() {
  const [fitResponse, motionResponse] = await Promise.all([fetch('thread-fit.json'), fetch('thread.bin')]);
  if (!fitResponse.ok || !motionResponse.ok) throw Error('The thread replay could not load.');
  const fit = await fitResponse.json();
  const record = new Float32Array(await motionResponse.arrayBuffer());
  if (record.length !== fit.frames * fit.points * 3) throw Error('Incomplete thread replay');
  const points = Array.from({length:fit.points}, () => new THREE.Vector3());
  const sides = 10, rings = points.length - 2;
  const positions = new THREE.Float32BufferAttribute(new Float32Array(rings * sides * 3), 3);
  const normals = positions.clone();
  const indices = [];
  for (let j=0; j<rings-1; j++) for (let k=0; k<sides; k++) {
    const a=j*sides+k, b=j*sides+(k+1)%sides;
    indices.push(a,b,a+sides,b,b+sides,a+sides);
  }
  const tube = new THREE.BufferGeometry();
  for(let k=1;k<sides-1;k++) indices.push(0,k+1,k);
  tube.setIndex(indices);
  tube.setAttribute('position', positions.setUsage(THREE.DynamicDrawUsage));
  tube.setAttribute('normal', normals.setUsage(THREE.DynamicDrawUsage));
  const line = new THREE.Mesh(tube,new THREE.MeshStandardMaterial({color:0xa87b5d,roughness:.9,side:THREE.DoubleSide}));
  const profile = [], r=fit.pearl_radius, bore=fit.radius+.00029;
  const edge=Math.asin(bore/r);
  for(let j=0;j<=32;j++) {
    const theta=Math.PI-edge+(2*edge-Math.PI)*j/32;
    profile.push(new THREE.Vector2(r*Math.sin(theta),r*Math.cos(theta)));
  }
  profile.push(new THREE.Vector2(bore,-Math.sqrt(r*r-bore*bore)));
  const pearl=new THREE.Mesh(new THREE.LatheGeometry(profile,48),new THREE.MeshPhysicalMaterial({
    color:0xffecd7,roughness:.25,metalness:.1,clearcoat:.75,iridescence:.4,iridescenceIOR:1.42
  }));
  line.name='Cotton pull thread';pearl.name='Pearl thread marker';
  line.castShadow=pearl.castShadow=true;
  const axis=new THREE.Vector3(), normal=new THREE.Vector3(), binormal=new THREE.Vector3();
  const radial=new THREE.Vector3(), v=new THREE.Vector3(), up=new THREE.Vector3(0,1,0);
  return {holdAngle:fit.hold_angle_rad,meshes:[line,pearl], update(frame) {
    const f=THREE.MathUtils.clamp(frame,0,fit.frames-1), lo=Math.floor(f), hi=Math.min(fit.frames-1,lo+1);
    points.forEach((p,j)=>p.fromArray(record,(lo*points.length+j)*3).lerp(v.fromArray(record,(hi*points.length+j)*3),f-lo));
    pearl.position.copy(points[0]);pearl.quaternion.setFromUnitVectors(up,v.subVectors(points[1],points[0]).normalize());
    normal.set(0,1,0);
    for (let j=2;j<points.length;j++) {
      axis.subVectors(points[Math.min(j+1,points.length-1)],points[Math.max(2,j-1)]).normalize();
      if (Math.abs(normal.dot(axis))>.99) normal.set(1,0,0);
      binormal.crossVectors(axis,normal).normalize();normal.crossVectors(binormal,axis).normalize();
      for(let k=0;k<sides;k++) {
        const a=2*Math.PI*k/sides, id=(j-2)*sides+k;
        radial.copy(normal).multiplyScalar(Math.cos(a)).addScaledVector(binormal,Math.sin(a));
        normals.setXYZ(id,radial.x,radial.y,radial.z);
        v.copy(points[j]).addScaledVector(radial,fit.radius);positions.setXYZ(id,v.x,v.y,v.z);
      }
    }
    positions.needsUpdate=normals.needsUpdate=true;tube.computeBoundingSphere();tube.computeBoundingBox();
  }};
}
