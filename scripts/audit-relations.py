import json,glob,os,unicodedata,re
from collections import Counter,defaultdict
ROOT='data'; REL=os.path.join(ROOT,'relations')
def norm(v):
 s=str(v or '').strip()
 for _ in range(2):
  if any(x in s for x in ('Ã','Â','â','ð')):
   try:s=s.encode('latin1').decode('utf-8')
   except: pass
 s=unicodedata.normalize('NFKD',s);s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss')
 return re.sub(r'[^a-z0-9]+',' ',s).strip()
def load(p):
 with open(p,encoding='utf-8') as f:return json.load(f)
def arr(x,keys=()):
 if isinstance(x,list): return x
 if isinstance(x,dict):
  for k in keys:
   if isinstance(x.get(k),list): return x[k]
 return []
P=load(os.path.join(REL,'players.json')); T=load(os.path.join(REL,'tournaments.json'))
R=[]
for p in sorted(glob.glob(os.path.join(REL,'results-*.json'))): R+=load(p)
byrid={r['id']:r for r in R}; bypid=defaultdict(list)
for r in R:
 if r.get('player_id'): bypid[r['player_id']].append(r['id'])
checks={}
checks['duplicate_player_ids']=len(P)-len({p['id'] for p in P})
checks['results_unknown_player_ids']=sum(1 for r in R if r.get('player_id') and r['player_id'] not in {p['id'] for p in P})
checks['player_result_backlinks_wrong']=sum(1 for p in P if set(p.get('result_ids',[])) != set(bypid.get(p['id'],[])))
checks['tournament_player_ids_not_result_backed']=0
checks['tournament_result_player_mismatch']=0
for t in T:
 derived={byrid[rid]['player_id'] for rid in t.get('result_ids',[]) if rid in byrid and byrid[rid].get('player_id')}
 if set(t.get('player_ids',[]))!=derived: checks['tournament_player_ids_not_result_backed']+=1
 for pid in t.get('player_ids',[]):
  if not any(byrid.get(rid,{}).get('player_id')==pid for rid in t.get('result_ids',[])): checks['tournament_result_player_mismatch']+=1
raw_lvs=Counter(p.get('lv','') for p in P if p.get('lv'))
checks['raw_lv_values']=len(raw_lvs)
LV=[('BBS',('bbs','badischer','baden')),('BMV',('bmv','bayer','bayern')),('BVBB',('bvbb','berlin','brandenburg')),('BVSA',('bvsa','sachsen anhalt')),('BVS',('bvs','sachsen')),('HBSV',('hbsv','hessen')),('HBV',('hbv','hamburg')),('MRP',('mrp','rheinland pfalz')),('MVBN',('mvbn','bremen','niedersachsen')),('NBV',('nbv','nordrhein','nrw')),('SaarMV',('saarmv','saarland','saar')),('SHMV',('shmv','schleswig holstein')),('WBV',('wbv','württemberg','wuerttemberg'))]
def canon(raw):
 s=norm(raw)
 for code,aliases in LV:
  if s==norm(code) or any(norm(a) in s for a in aliases): return code
 return None
lv_groups=defaultdict(list); unknown=[]
for raw,n in sorted(raw_lvs.items()):
 c=canon(raw)
 if c: lv_groups[c].append({'raw':raw,'players':n})
 else: unknown.append({'raw':raw,'players':n})
checks['canonical_lvs']=len(lv_groups); checks['unmapped_lvs']=len(unknown)
hoever=[]
for p in P:
 if 'hoever' in norm(p.get('name')) or 'höver' in norm(p.get('name')):
  ids=set(p.get('result_ids',[])); turns=[]
  for t in T:
   hits=[rid for rid in t.get('result_ids',[]) if rid in ids]
   if hits: turns.append({'id':t['id'],'year':t.get('year'),'date':t.get('date'),'name':t.get('name'),'place':t.get('place'),'result_ids':hits})
  jlp=[x for x in turns if 'jugend' in norm(x['name']) and 'landerpokal' in norm(x['name'])]
  houver={'id':p['id'],'name':p['name'],'pass':p.get('pass'),'club':p.get('club'),'lv':p.get('lv'),'result_count':len(ids),'tournament_count':len(turns),'jlp_matches':jlp,'tournaments':turns}
  hoever.append(houver)
out={'checks':checks,'canonical_lv_groups':dict(lv_groups),'unmapped_lvs':unknown,'hoever':hoever}
json.dump(out,open(os.path.join(REL,'audit.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'checks':checks,'hoever':hoever},ensure_ascii=False,indent=2))
if checks['duplicate_player_ids'] or checks['results_unknown_player_ids'] or checks['player_result_backlinks_wrong'] or checks['tournament_player_ids_not_result_backed'] or checks['tournament_result_player_mismatch'] or checks['unmapped_lvs']:
 raise SystemExit('Relation audit failed')
