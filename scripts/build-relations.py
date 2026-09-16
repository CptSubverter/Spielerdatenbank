# Relationen-Generator – automatischer Aufbau bei Änderungen der Quelldaten
# Build trigger: rebuild after validated DRL archive refresh.
import json, re, os, glob, hashlib, unicodedata
from collections import defaultdict
ROOT='data'; OUT=os.path.join(ROOT,'relations')
def norm(v):
 s=str(v or '').strip()
 for _ in range(2):
  if any(x in s for x in ('Ã','Â','â','ð')):
   try:s=s.encode('latin1').decode('utf-8')
   except Exception:pass
 s=unicodedata.normalize('NFKD',s); s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss'); return re.sub(r'[^a-z0-9]+',' ',s).strip()
def teamless(v):
 s=str(v or '').strip(); s=re.sub(r'\s+(?:I{1,3}|IV|V|[1-5])\s*$','',s,flags=re.I); s=re.sub(r'\s+e\.?\s*v\.?\s*$','',s,flags=re.I); return s.strip()
def first(d,keys):
 for k in keys:
  if k in d and d[k] not in (None,''): return d[k]
 return ''
def load_json(path):
 with open(path,encoding='utf-8') as f:return json.load(f)
def arr(x,keys=()):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in keys:
   if isinstance(x.get(k),list):return x[k]
 return []
os.makedirs(OUT,exist_ok=True)
for p in glob.glob(os.path.join(OUT,'*')):
 if os.path.isfile(p):os.remove(p)
players=[]
for path in sorted(glob.glob(os.path.join(ROOT,'players-*.json'))):players.extend(arr(load_json(path),('players','data')))
by_id={}; by_pass=defaultdict(set); by_name=defaultdict(set); by_name_club=defaultdict(set); player_out=[]
for i,p in enumerate(players):
 pid=str(first(p,('player_id','playerId','personId','person_id','id')) or f'P{i+1:06d}'); name=str(first(p,('name','fullName','playerName','player_name','spielerName','spieler_name'))); pas=str(first(p,('pass','passnummer','passNumber','card','cardNumber','dmvPass'))); club=teamless(first(p,('club','verein','vereine'))); lv=str(first(p,('lv','association','verband','landesverband')))
 rec={'id':pid,'name':name,'pass':pas,'club':club,'lv':lv,'result_ids':[],'drl_ids':[],'match_status':'canonical'}; by_id[pid]=rec; player_out.append(rec)
 if pas:by_pass[norm(pas)].add(pid)
 if name:by_name[norm(name)].add(pid)
 if name and club:by_name_club[(norm(name),norm(club))].add(pid)
results=[]; tournaments={}; clubs={}; associations={}
def tournament_id(year,name,place):return 'T'+hashlib.sha1(f'{year}|{norm(name)}|{norm(place)}'.encode()).hexdigest()[:12]
def club_id(name):return 'C'+hashlib.sha1(norm(teamless(name)).encode()).hexdigest()[:12]
def assoc_id(name):return 'A'+hashlib.sha1(norm(name).encode()).hexdigest()[:12]
def resolve_player(z):
 explicit=str(first(z,('player_id','playerId','spieler_id','spielerId','person_id','personId')))
 if explicit and explicit in by_id:return explicit,'player_id'
 pas=str(first(z,('pass','passnummer','passNumber','card','cardNumber')))
 if pas:
  c=by_pass.get(norm(pas),set())
  if len(c)==1:return next(iter(c)),'pass_verified'
 name=str(first(z,('playerName','player_name','spielerName','spieler_name','name','fullName','player','spieler','Name'))); club=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
 if name and club:
  c=by_name_club.get((norm(name),norm(club)),set())
  if len(c)==1:return next(iter(c)),'name_unique_club_verified'
 c=by_name.get(norm(name),set()) if name else set()
 if len(c)==1:return next(iter(c)),'name_unique'
 if len(c)>1:return None,'ambiguous'
 return None,'unresolved'
for fi,path in enumerate(sorted(glob.glob(os.path.join(ROOT,'results-*.json'))),1):
 for j,z in enumerate(arr(load_json(path),('results','ergebnisse','participations','teilnahmen','data'))):
  rid=f'R{fi:02d}-{j+1:06d}'; name=str(first(z,('tournamentName','tournament_name','turnierName','turnier_name','tournament','turnier','eventName','event_name','code'))); year=str(first(z,('year','jahr')) or str(first(z,('date','datum')))[:4]); place=str(first(z,('place','ort','location','loc'))); tid=tournament_id(year,name,place)
  tournaments.setdefault(tid,{'id':tid,'year':year,'name':name,'date':str(first(z,('date','datum'))),'place':place,'result_ids':[],'player_ids':[]}); tournaments[tid]['result_ids'].append(rid)
  pid,status=resolve_player(z)
  if pid:tournaments[tid]['player_ids'].append(pid); by_id[pid]['result_ids'].append(rid)
  club=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
  if club:
   cid=club_id(club); clubs.setdefault(cid,{'id':cid,'name':club,'player_ids':[],'result_ids':[],'tournament_ids':[]}); clubs[cid]['result_ids'].append(rid); clubs[cid]['tournament_ids'].append(tid); pid and clubs[cid]['player_ids'].append(pid)
  lv=str(first(z,('lv','association','verband','landesverband','LV')))
  if lv:
   aid=assoc_id(lv); associations.setdefault(aid,{'id':aid,'name':lv,'player_ids':[],'result_ids':[],'tournament_ids':[],'club_ids':[]}); associations[aid]['result_ids'].append(rid); associations[aid]['tournament_ids'].append(tid); pid and associations[aid]['player_ids'].append(pid)
  results.append({'id':rid,'player_id':pid,'match_status':status,'tournament_id':tid,'year':year,'source_file':os.path.basename(path)})
drl_ids=[]
for path in sorted(glob.glob(os.path.join(ROOT,'drl','drl-*.json'))):
 for j,z in enumerate(load_json(path)):
  did=str(z.get('_record_id') or f'D{os.path.basename(path)[4:7]}-{j+1:06d}'); name=str(first(z,('Name','name','player','Player','spieler','Spieler'))); pas=str(first(z,('Pass','pass','passnummer','Card','card'))); club=teamless(first(z,('Verein','verein','club','Club'))); pid=None; status='unresolved'
  if pas:
   c=by_pass.get(norm(pas),set())
   if len(c)==1:pid=next(iter(c)); status='pass_verified'
  if not pid and name and club:
   c=by_name_club.get((norm(name),norm(club)),set())
   if len(c)==1:pid=next(iter(c)); status='name_unique_club_verified'
  if not pid and name:
   c=by_name.get(norm(name),set())
   if len(c)==1:pid=next(iter(c)); status='name_unique'
   elif len(c)>1:status='ambiguous'
  if pid:by_id[pid]['drl_ids'].append(did)
  drl_ids.append({'id':did,'player_id':pid,'match_status':status,'date':str(first(z,('_source_date','date','Datum','Stichtag'))),'name':name,'pass':pas,'club':club,'lv':str(first(z,('LV','lv','Landesverband'))),'source_file':str(z.get('_source_file',''))})
for coll in (tournaments.values(),clubs.values(),associations.values()):
 for x in coll:
  for k in ('player_ids','result_ids','tournament_ids','club_ids'):
   if k in x:x[k]=sorted(set(x[k]))
for x in player_out:x['result_ids']=sorted(set(x['result_ids'])); x['drl_ids']=sorted(set(x['drl_ids']))
def write_chunks(items,prefix,size=5000):
 files=[]
 for i in range(0,len(items),size):
  fn=f'{prefix}-{i//size+1:03d}.json'; path=os.path.join(OUT,fn)
  with open(path,'w',encoding='utf-8') as f:json.dump(items[i:i+size],f,ensure_ascii=False,separators=(',',':'))
  files.append(fn)
 return files
rf=write_chunks(results,'results'); df=write_chunks(drl_ids,'drl')
for fn,obj in [('players.json',player_out),('clubs.json',list(clubs.values())),('associations.json',list(associations.values())),('tournaments.json',list(tournaments.values()))]:
 with open(os.path.join(OUT,fn),'w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,separators=(',',':'))
status=defaultdict(int)
for r in results:status['results_'+r['match_status']]+=1
for r in drl_ids:status['drl_'+r['match_status']]+=1
manifest={'version':'relations-v1','generated_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'players':len(player_out),'results':len(results),'tournaments':len(tournaments),'clubs':len(clubs),'associations':len(associations),'drl_records':len(drl_ids),'result_chunks':len(rf),'drl_chunks':len(df),'match_status_counts':dict(status),'files':{'players':'players.json','clubs':'clubs.json','associations':'associations.json','tournaments':'tournaments.json','result_chunks':rf,'drl_chunks':df}}
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
print(json.dumps(manifest,ensure_ascii=False))
