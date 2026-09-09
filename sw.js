const CACHE='bahnengolf-v11.15-shell';
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(['./','./index.html','./manifest.webmanifest','./apple-touch-icon.png'])));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET') return;
  const url=new URL(req.url);
  if(url.origin!==location.origin) return;
  event.respondWith(fetch(req).then(res=>{if(res.ok && (req.mode==='navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('.webmanifest') || url.pathname.endsWith('.png'))) {const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy));} return res;}).catch(()=>caches.match(req).then(r=>r||caches.match('./index.html'))));
});
