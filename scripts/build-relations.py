import json,re,os,glob,hashlib,unicodedata
from collections import defaultdict,Counter
from datetime import datetime,timezone
ROOT='data';OUT=ROOT+'/relations';OFF={'BBS','BMV','BVBB','BVSA','BVS','HBSV','HBV','MRP','MVBN','NBV','SaarMV','SHMV','WBV'}
ALIASES={'BBS':('bbs','badischer','baden'),'BMV':('bmv','bayer'),'BVBB':('bvbb','berlin','brandenburg'),'BVSA':('bvsa','sachsen anhalt'),'BVS':('bvs','sachsen'),'HBSV':('hbsv','hessen'),'HBV':('hbv','hamburg'),'MRP':('mrp','rheinland pfalz'),'MVBN':('mvbn','bremen','niedersachsen'),'NBV':('nbv','nordrhein','nrw'),'SaarMV':('saarmv','saarland','saar'),'SHMV':('shmv','schleswig holstein'),'WBV':('wbv','württemberg','wuerttemberg')}
def norm(v):
 s=str(v or '').strip();s=unicodedata.normalize('NFKD',s);s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss');return re.sub(r'[^a-z0-9]+',' ',s).strip()
def equiv(a,b):return norm(a)==norm(b) or sorted(norm(a).split())==sorted(norm(b).split())
def lv(v):
 s=norm(v)
 for c,a in ALIASES.items():
  if s==norm(c) or any(norm(x) in s for x in a):return c
 return ''
def teamless(v):
 s=str(v or '').strip();s=re.sub(r'\s+(?:I{1,3}|IV|V|[1-5])\s*$','',s,flags=re.I);s=re.sub(r'\s+e\.?\s*v\.?\s*$','',s,flags=re.I);return s.strip()
def first(d,ks):
 for k in ks:
  if k in d and d[k] not in (None,''):return d[k]
 return ''
def load(p):
 with open(p,encoding='utf-8') as f:return json.load(f)
def arr(x):return x if isinstance(x,list) else next((v for v in x.values() if isinstance(v,list)),[]) if isinstance(x,dict) else []
os.makedirs(OUT,exist_ok=True)
for f in glob.glob(OUT+'/*'):
 if os.path.isfile(f):os.remove(f)
players=[]
for f in sorted(glob.glob(ROOT+'/players-*.json')):players+=arr(load(f))
P=[];byid={};bypass=defaultdict(set);byname=defaultdict(set);bync=defaultdict(set)
for i,x in enumerate(players):
 pid=str(first(x,('player_id','playerId','personId','person_id','id')) or f'P{i+1:06d}');name=str(first(x,('name','fullName','playerName','player_name','spielerName','spieler_name')));pas=str(first(x,('pass','passnummer','passNumber','card','cardNumber','dmvPass','player_key')));club=teamless(first(x,('club','verein','vereine')));a=lv(first(x,('lv','association','verband','landesverband'))) or lv(club);p={'id':pid,'name':name,'pass':pas,'club':club,'lv':a,'result_ids':[],'drl_ids':[],'match_status':'canonical'};P.append(p);byid[pid]=p
 if pas:bypass[norm(pas)].add(pid)
 if name:byname[norm(name)].add(pid)
 if name and club:bync[(norm(name),norm(club))].add(pid)
T={};C={};A={c:{'id':'A'+hashlib.sha1(norm(c).encode()).hexdigest()[:12],'name':c,'player_ids':[],'result_ids':[],'tournament_ids':[],'club_ids':[]} for c in OFF};R=[]
def tid(y,d,n,p):return 'T'+hashlib.sha1(f'{y}|{d}|{norm(n)}|{norm(p)}'.encode()).hexdigest()[:12]
def cid(n):return 'C'+hashlib.sha1(norm(teamless(n)).encode()).hexdigest()[:12]
def addrel(a,p=None,r=None,t=None,c=None):
 if not a:return
 x=A[''+a] if a in A else A.setdefault(a,{'id':'A'+hashlib.sha1(norm(a).encode()).hexdigest()[:12],'name':a,'player_ids':[],'result_ids':[],'tournament_ids':[],'club_ids':[]})
 if p:x['player_ids'].append(p)
 if r:x['result_ids'].append(r)
 if t:x['tournament_ids'].append(t)
 if c:x['club_ids'].append(c)
for p in P:
 if p['lv']:addrel(p['lv'],p=p['id'])
def resolve(z):
 ex=str(first(z,('player_id','playerId','spieler_id','spielerId','person_id','personId','player_key','playerKey')));name=str(first(z,('playerName','player_name','spielerName','spieler_name','name','fullName','player','spieler','Name')));club=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
 if ex in byid:return (ex,'player_key_verified') if not name or equiv(name,byid[ex]['name']) else (None,'player_key_name_conflict')
 pas=str(first(z,('pass','passnummer','passNumber','card','cardNumber')));s=bypass.get(norm(pas),set()) if pas else set()
 if len(s)==1:
  p=next(iter(s));return (p,'pass_verified') if not name or equiv(name,byid[p]['name']) else (None,'pass_name_conflict')
 if name and club:
  s=bync.get((norm(name),norm(club)),set())
  if len(s)==1:return next(iter(s)),'name_unique_club_verified'
 s=byname.get(norm(name),set()) if name else set()
 if len(s)==1:return next(iter(s)),'name_unique'
 return None,('ambiguous' if len(s)>1 else 'unresolved')
def add(rid,z,src):
 n=str(first(z,('tournamentName','tournament_name','turnierName','turnier_name','tournament','turnier','eventName','event_name','code')));d=str(first(z,('date','datum')));y=str(first(z,('year','jahr')) or d[:4]);pl=str(first(z,('location','ort','loc','venue','anlage')));tt=tid(y,d,n,pl);T.setdefault(tt,{'id':tt,'year':y,'name':n,'date':d,'place':pl,'result_ids':[],'player_ids':[]});T[tt]['result_ids'].append(rid);pid,st=resolve(z)
 if pid:T[tt]['player_ids'].append(pid);byid[pid]['result_ids'].append(rid)
 cl=teamless(first(z,('club','verein','result_club','resultClub','Verein')))
 if cl:
  cc=cid(cl);C.setdefault(cc,{'id':cc,'name':cl,'player_ids':[],'result_ids':[],'tournament_ids':[]});C[cc]['result_ids'].append(rid);C[cc]['tournament_ids'].append(tt)
  if pid:C[cc]['player_ids'].append(pid)
 a=lv(first(z,('lv','association','verband','landesverband','LV')))
 if a:addrel(a,p=pid,r=rid,t=tt,c=cid(cl) if cl else None)
 q={'id':rid,'player_id':pid,'match_status':st,'tournament_id':tt,'year':y,'date':d,'source_file':src}
 for k in ('category','place','club','rating_value','rounds','total','average','diff','event_url','source_tournament_history','round_source','round_match_method','identity_match'):
  if k in z:q[k]=z[k]
 R.append(q)
for fi,f in enumerate(sorted(glob.glob(ROOT+'/results-*.json')),1):
 for j,z in enumerate(arr(load(f))):
  tn=str(first(z,('tournamentName','tournament_name','turnierName','turnier_name','tournament','turnier','eventName','event_name','code')))
  if 'jugendlanderpokal' in norm(tn):continue
  add(str(z.get('result_id') or f'R{fi:02d}-{j+1:06d}'),z,os.path.basename(f))
for i,z in enumerate(load(ROOT+'/jlp-2025.json'),1):
 add(f'JLP25-{i:03d}',{'player_key':z['pass'],'pass':z['pass'],'name':z['name'],'year':2025,'date':'2025-04-24','tournament':'Jugendländerpokal - U23 Vergleich','location':'Mainz','category':z['category'],'total':z['total'],'average':(z['base_average']+z['eternit_average'])/2,'diff':z['diff'],'event_url':'https://www.minigolfsport.de/pdf/Sportbetrieb/Meisterschaften/2025/Ergebnisliste_JLP_2025%20250505.pdf','source_tournament_history':False,'round_source':'DMV offizielle Ergebnisliste JLP 2025','identity_match':'pass_verified'},'jlp-2025.json')
D=[]
for f in sorted(glob.glob(ROOT+'/drl/drl-*.json')):
 for j,z in enumerate(load(f)):
  n=str(first(z,('Name','name','player','Player','spieler','Spieler')));pas=str(first(z,('Pass','pass','passnummer','Card','card')));cl=teamless(first(z,('Verein','verein','club','Club')));pid=None;st='unresolved';s=bypass.get(norm(pas),set()) if pas else set()
  if len(s)==1:
   p=next(iter(s));pid=p if not n or equiv(n,byid[p]['name']) else None;st='pass_verified' if pid else 'pass_name_conflict'
  if not pid and n and cl:
   s=bync.get((norm(n),norm(cl)),set());pid=next(iter(s)) if len(s)==1 else None;st='name_unique_club_verified' if pid else st
  if not pid and n:
   s=byname.get(norm(n),set());pid=next(iter(s)) if len(s)==1 else None;st='name_unique' if pid else ('ambiguous' if len(s)>1 else st)
  if pid:byid[pid]['drl_ids'].append(str(z.get('_record_id') or f'D{j+1:06d}'))
  D.append({'id':str(z.get('_record_id') or f'D{j+1:06d}'),'player_id':pid,'match_status':st,'date':str(first(z,('_source_date','date','Datum','Stichtag'))),'name':n,'pass':pas,'club':cl,'lv':lv(first(z,('LV','lv','Landesverband'))),'source_file':str(z.get('_source_file',''))})
for x in list(T.values())+list(C.values())+list(A.values()):
 for k in ('player_ids','result_ids','tournament_ids','club_ids'):
  if k in x:x[k]=sorted(set(x[k]))
for p in P:p['result_ids']=sorted(set(p['result_ids']));p['drl_ids']=sorted(set(p['drl_ids']))
def chunks(xs,prefix):
 out=[]
 for i in range(0,len(xs),5000):
  fn=f'{prefix}-{i//5000+1:03d}.json';json.dump(xs[i:i+5000],open(OUT+'/'+fn,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'));out.append(fn)
 return out
rf=chunks(R,'results');df=chunks(D,'drl')
for fn,obj in [('players.json',P),('clubs.json',list(C.values())),('associations.json',list(A.values())),('tournaments.json',list(T.values()))]:json.dump(obj,open(OUT+'/'+fn,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
sc=Counter('results_'+r['match_status'] for r in R);sc.update(Counter('drl_'+r['match_status'] for r in D));json.dump({'version':'relations-v3','generated_at':datetime.now(timezone.utc).isoformat(),'players':len(P),'results':len(R),'tournaments':len(T),'clubs':len(C),'associations':len(A),'drl_records':len(D),'result_chunks':len(rf),'drl_chunks':len(df),'match_status_counts':dict(sc),'files':{'players':'players.json','clubs':'clubs.json','associations':'associations.json','tournaments':'tournaments.json','result_chunks':rf,'drl_chunks':df}},open(OUT+'/manifest.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
