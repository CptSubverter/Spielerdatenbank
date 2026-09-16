# Relation builder v2: associations come from player master; result/player matching requires pass+name consistency.
import json,re,os,glob,hashlib,unicodedata
from collections import defaultdict
ROOT='data';OUT=os.path.join(ROOT,'relations')
def norm(v):
 s=str(v or '').strip()
 for _ in range(2):
  if any(x in s for x in ('Ã','Â','â','ð')):
   try:s=s.encode('latin1').decode('utf-8')
   except:pass
 s=unicodedata.normalize('NFKD',s);s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss');return re.sub(r'[^a-z0-9]+',' ',s).strip()
def teamless(v):
 s=str(v or '').strip();s=re.sub(r'\s+(?:I{1,3}|IV|V|[1-5])\s*$','',s,flags=re.I);s=re.sub(r'\s+e\.?\s*v\.?\s*$','',s,flags=re.I);return s.strip()
def first(d,keys):
 for k in keys:
  if k in d and d[k] not in (None,''):return d[k]
 return ''
def load(path):
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
for path in sorted(glob.glob(os.path.join(ROOT,'players-*.json'))):players+=arr(load(path),('players','data'))
by_id={};by_pass=defaultdict(set);by_name=defaultdict(set);by_nc=defaultdict(set);PO=[]
for i,p in enumerate(players):
 pid=str(first(p,('player_id','playerId','personId','person_id','id')) or f'P{i+1:06d}');name=str(first(p,('name','fullName','playerName','player_name','spielerName','spieler_name')));pas=str(first(p,('pass','passnummer','passNumber','card','cardNumber','dmvPass')));club=teamless(first(p,('club','verein','vereine')));lv=str(first(p,('lv','association','verband','landesverband')));r={'id':pid,'name':name,'pass':pas,'club':club,'lv':lv,'result_ids':[],'drl_ids':[],'match_status':'canonical'};by_id[pid]=r;PO.append(r)
 if pas:by_pass[norm(pas)].add(pid)
 if name:by_name[norm(name)].add(pid)
 if name and club:by_nc[(norm(name),norm(club))].add(pid)
T={};C={};A={};results=[]
def tid(y,n,p):return 'T'+hashlib.sha1(f'{y}|{norm(n)}|{norm(p)}'.encode()).hexdigest()[:12]
def cid(n):return 'C'+hashlib.sha1(norm(teamless(n)).encode()).hexdigest()[:12]
def aid(n):return 'A'+hashlib.sha1(norm(n).encode()).hexdigest()[:12]
def adda(a,n,p=None,r=None,t=None,c=None):
 x=A.setdefault(a,{'id':a,'name':n,'player_ids':[],'result_ids':[],'tournament_ids':[],'club_ids':[]})
 if p:x['player_ids'].append(p)
 if r:x['result_ids'].append(r)
 if t:x['tournament_ids'].append(t)
 if c:x['club_ids'].append(c)
for p in PO:
 if p['lv']:adda(aid(p['lv']),p['lv'],p=p['id'])
def resolve(z):
 explicit=str(first(z,('player_id','playerId','spieler_id','spielerId','person_id','personId')))
 if explicit in by_id:return explicit,'player_id'
 pas=str(first(z,('pass','passnummer','passNumber','card','cardNumber')));name=str(first(z,('playerName','player_name','spielerName','spieler_name','name','fullName','player','spieler','Name')));club=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
 if pas:
  s=by_pass.get(norm(pas),set())
  if len(s)==1:
   p=next(iter(s))
   if not name or norm(name)==norm(by_id[p]['name']):return p,'pass_verified'
   return None,'pass_name_conflict'
 if name and club:
  s=by_nc.get((norm(name),norm(club)),set())
  if len(s)==1:return next(iter(s)),'name_unique_club_verified'
 s=by_name.get(norm(name),set()) if name else set()
 if len(s)==1:return next(iter(s)),'name_unique'
 return (None,'ambiguous' if len(s)>1 else 'unresolved')
for fi,path in enumerate(sorted(glob.glob(os.path.join(ROOT,'results-*.json'))),1):
 for j,z in enumerate(arr(load(path),('results','ergebnisse','participations','teilnahmen','data'))):
  rid=f'R{fi:02d}-{j+1:06d}';n=str(first(z,('tournamentName','tournament_name','turnierName','turnier_name','tournament','turnier','eventName','event_name','code')));y=str(first(z,('year','jahr')) or str(first(z,('date','datum')))[:4]);pl=str(first(z,('place','ort','location','loc')));tt=tid(y,n,pl);T.setdefault(tt,{'id':tt,'year':y,'name':n,'date':str(first(z,('date','datum'))),'place':pl,'result_ids':[],'player_ids':[]});T[tt]['result_ids'].append(rid);pid,status=resolve(z)
  if pid:T[tt]['player_ids'].append(pid);by_id[pid]['result_ids'].append(rid)
  cl=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
  if cl:
   cc=cid(cl);C.setdefault(cc,{'id':cc,'name':cl,'player_ids':[],'result_ids':[],'tournament_ids':[]});C[cc]['result_ids'].append(rid);C[cc]['tournament_ids'].append(tt)
   if pid:C[cc]['player_ids'].append(pid)
  lv=str(first(z,('lv','association','verband','landesverband','LV')))
  if lv:adda(aid(lv),lv,p=pid,r=rid,t=tt,c=cid(cl) if cl else None)
  results.append({'id':rid,'player_id':pid,'match_status':status,'tournament_id':tt,'year':y,'source_file':os.path.basename(path)})
drl=[]
for path in sorted(glob.glob(os.path.join(ROOT,'drl','drl-*.json'))):
 for j,z in enumerate(load(path)):
  did=str(z.get('_record_id') or f'D{os.path.basename(path)[4:7]}-{j+1:06d}');n=str(first(z,('Name','name','player','Player','spieler','Spieler')));pas=str(first(z,('Pass','pass','passnummer','Card','card')));cl=teamless(first(z,('Verein','verein','club','Club')));pid=None;st='unresolved';s=by_pass.get(norm(pas),set()) if pas else set()
  if len(s)==1:
   p=next(iter(s));
   if not n or norm(n)==norm(by_id[p]['name']):pid=p;st='pass_verified'
   else:st='pass_name_conflict'
  if not pid and n and cl:
   s=by_nc.get((norm(n),norm(cl)),set())
   if len(s)==1:pid=next(iter(s));st='name_unique_club_verified'
  if not pid and n:
   s=by_name.get(norm(n),set())
   if len(s)==1:pid=next(iter(s));st='name_unique'
   elif len(s)>1:st='ambiguous'
  if pid:by_id[pid]['drl_ids'].append(did)
  drl.append({'id':did,'player_id':pid,'match_status':st,'date':str(first(z,('_source_date','date','Datum','Stichtag'))),'name':n,'pass':pas,'club':cl,'lv':str(first(z,('LV','lv','Landesverband'))),'source_file':str(z.get('_source_file',''))})
for coll in (T.values(),C.values(),A.values()):
 for x in coll:
  for k in ('player_ids','result_ids','tournament_ids','club_ids'):
   if k in x:x[k]=sorted(set(x[k]))
for p in PO:p['result_ids']=sorted(set(p['result_ids']));p['drl_ids']=sorted(set(p['drl_ids']))
def chunks(items,prefix,size=5000):
 out=[]
 for i in range(0,len(items),size):
  fn=f'{prefix}-{i//size+1:03d}.json';json.dump(items[i:i+size],open(os.path.join(OUT,fn),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'));out.append(fn)
 return out
rf=chunks(results,'results');df=chunks(drl,'drl')
for fn,obj in [('players.json',PO),('clubs.json',list(C.values())),('associations.json',list(A.values())),('tournaments.json',list(T.values()))]:json.dump(obj,open(os.path.join(OUT,fn),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
sc=defaultdict(int)
for r in results:sc['results_'+r['match_status']]+=1
for r in drl:sc['drl_'+r['match_status']]+=1
json.dump({'version':'relations-v2','generated_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'players':len(PO),'results':len(results),'tournaments':len(T),'clubs':len(C),'associations':len(A),'drl_records':len(drl),'result_chunks':len(rf),'drl_chunks':len(df),'match_status_counts':dict(sc),'files':{'players':'players.json','clubs':'clubs.json','associations':'associations.json','tournaments':'tournaments.json','result_chunks':rf,'drl_chunks':df}},open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
