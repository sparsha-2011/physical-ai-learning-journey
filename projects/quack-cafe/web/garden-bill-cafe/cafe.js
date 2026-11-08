const $ = id => document.getElementById(id);
const read = async file => {
  const response = await fetch(file);
  if (!response.ok) throw new Error(file + ' could not be loaded');
  return response.json();
};
const roomNames = ['Machine', 'Coffee station', 'Kitchen', 'Living room'];
let catalogue, viewer, selectedRoom = 'All';
function button(label, act) {
  const el = document.createElement('button');
  el.type = 'button'; el.textContent = label; el.onclick = act;
  return el;
}
function pressed(el, value) { el.setAttribute('aria-pressed', String(value)); }
async function openView() {
  const id = location.hash.slice(1);
  if (!['lab','catalogue'].includes(id)) {
    location.replace('live.html');
    return;
  }
  for (const name of ['lab','catalogue']) $(name).hidden = name !== id;
  for (const link of document.querySelectorAll('nav a')) {
    if (link.hash === '#'+id) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  }

  try {
    if (id === 'catalogue') {
      catalogue ||= await read('catalogue.json');
      drawCatalogue();
    }
    if (id === 'lab') {
      viewer ||= import('./explore.js?v=scene-lab');
      await viewer;
    }
  } catch (err) {
    const panel = $(id);
    if (!panel.querySelector('[role=alert]')) {
      const msg = document.createElement('p'); msg.setAttribute('role','alert');
      msg.textContent = 'This view could not load. Reload the page to retry. '+err.message; panel.append(msg);
    }
  }
}
function drawCatalogue() {
  const query = $('search').value.toLowerCase().trim(), inventory = $('inventory');
  inventory.replaceChildren(); $('filters').replaceChildren();
  for (const group of ['All',...roomNames]) {
    const el = button(group, () => {selectedRoom = group; drawCatalogue(); $('filters').children[['All',...roomNames].indexOf(group)].focus();});
    pressed(el, group === selectedRoom); $('filters').append(el);
  }
  for (const room of roomNames) {
    if (selectedRoom !== 'All' && room !== selectedRoom) continue;
    const matches = catalogue.filter(r => r.section === room && (r.title+' '+r.author+' '+room).toLowerCase().includes(query));
    if (!matches.length) continue;
    const section = document.createElement('section'), title = document.createElement('h2'), cards = document.createElement('div');
    section.className = 'group'; title.textContent = room; cards.className = 'cards'; section.append(title,cards); inventory.append(section);
    for (const r of matches) {
      const card = document.createElement('article'); card.className = 'card';
      const thumb = new Image(); thumb.loading = 'lazy'; thumb.width = 480; thumb.height = 320; thumb.alt = r.title; thumb.src = 'thumbs/'+r.id+'.webp';
      const body = document.createElement('div'); body.className = 'card-body';
      const source = document.createElement('a'); source.className = 'credit'; source.href = r.url; source.textContent = r.author+' ↗'; source.target = '_blank'; source.rel = 'noopener'; source.title = r.license;
      const name = document.createElement('h3'); name.textContent = r.title;
      const foot = document.createElement('div'); foot.className = 'cardfoot';
      const qty = document.createElement('span'); qty.className = 'qty'; qty.textContent = 'Qty '+r.instances.length;
      const find = document.createElement('a'); find.textContent = 'Find in scene ↗'; find.className = 'find'; find.href = 'explore.html?find='+r.id;
      foot.append(qty,find); body.append(source,name,foot); card.append(thumb,body); cards.append(card);
    }
  }
  if (!inventory.children.length) inventory.textContent = 'No matching objects.';
}
$('search').oninput=()=>{if(catalogue)drawCatalogue()};
addEventListener('hashchange',openView);openView();
