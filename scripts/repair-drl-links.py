import json,glob,re,unicodedata,os
from collections import defaultdict

def norm(v):
 s=str(v or '').strip()
 for _ in range(2):
  if any(x in s for x in ('Ã','Â','â','ð')):
   try:s=s.encode('latin1').decode('utf8')
   except:pass
 s=unicodedata.normalize('NFKD',s); s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss')
 return re.sub(r'[^a-z0-9]+',' ',s).strip()
def teamless(v):
 s=str(v or '').strip(); s=re.sub(r'\s+(?:I{1,3}|IV|V|[1-5])\s*$','',s,flags=re.I); s=re.sub(r'\s+e\.?\s*v\.?\s*$','',s,flags=re.I); return s.strip()
def fuzzy(d,terms):
 for k,v in d.items():
  nk=norm(k)
  if any(t in nk for t in terms) and v not in ('',None): return v
 return ''
rel='data/relations'; os.makedirs(rel+'/drl',exist_ok=True); players=json.load(open(rel+'/players.json',encoding='utf8')); pbyid={p['id']:p for p in players}
by_pass=defaultdict(set); by_name=defaultdict(set); by_name_club=defaultdict(set)
for p in players:
 if p.get('pass'):by_pass[norm(p['pass'])].add(p['id'])
 if p.get('name'):by_name[norm(p['name'])].add(p['id'])
 if p.get('name') and p.get('club'):by_name_club[(norm(p['name']),norm(p['club']))].add(p['id'])
for p in players:p['drl_ids']=[]
status=defaultdict(int); total=0
for path in sorted(glob.glob('data/drl/drl-*.json')):
 rows=json.load(open(path,encoding='utf8')); out=[]
 for j,z in enumerate(rows):
  did=str(z.get('_record_id') or f'D{os.path.basename(path)[4:7]}-{j+1:06d}'); name=str(fuzzy(z,['name','spieler','player'])); pas=str(fuzzy(z,['pass','card'])); club=teamless(fuzzy(z,['verein','club'])); lv=str(fuzzy(z,['landesverband','verband',' lv'])); pid=None; st='unresolved'
  c=by_pass.get(norm(pas),set()) if pas else set()
  if len(c)==1:pid=next(iter(c));st='pass_verified'
  if not pid and name and club:
   c=by_name_club.get((norm(name),norm(club)),set())
   if len(c)==1:pid=next(iter(c));st='name_unique_club_verified'
  if not pid and name:
   c=by_name.get(norm(name),set())
   if len(c)==1:pid=next(iter(c));st='name_unique'
   elif len(c)>1:st='ambiguous'
  if pid:pbyid[pid]['drl_ids'].append(did)
  out.append({'id':did,'player_id':pid,'match_status':st,'date':str(z.get('_source_date') or fuzzy(z,['stichtag','date'])),'name':name,'pass':pas,'club':club,'lv':lv,'source_file':str(z.get('_source_file',''))}); status[st]+=1; total+=1
 with open(rel+'/drl/'+os.path.basename(path),'w',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,separators=(',',':'))
for p in players:p['drl_ids']=sorted(set(p['drl_ids']))
with open(rel+'/players.json','w',encoding='utf8') as f:json.dump(players,f,ensure_ascii=False,separators=(',',':'))
m=json.load(open(rel+'/manifest.json',encoding='utf8')); m['drl_link_repair']=dict(status); m['drl_records']=total
with open(rel+'/manifest.json','w',encoding='utf8') as f:json.dump(m,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status),ensure_ascii=False))
