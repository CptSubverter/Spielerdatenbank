import json,glob,os,unicodedata,re
from collections import defaultdict
ROOT='data';REL=ROOT+'/relations';OFF={'BBS','BMV','BVBB','BVSA','BVS','HBSV','HBV','MRP','MVBN','NBV','SaarMV','SHMV','WBV'}
def norm(v):
 s=unicodedata.normalize('NFKD',str(v or '').strip());s=''.join(c for c in s if not unicodedata.combining(c)).lower().replace('ß','ss');return re.sub(r'[^a-z0-9]+',' ',s).strip()
def load(p):
 with open(p,encoding='utf-8') as f:return json.load(f)
P=load(REL+'/players.json');T=load(REL+'/tournaments.json');R=[]
for f in glob.glob(REL+'/results-*.json'):R+=load(f)
ids={p['id'] for p in P};byrid={r['id']:r for r in R};byp=defaultdict(list)
for r in R:
 if r.get('player_id'):byp[r['player_id']].append(r['id'])
checks={'duplicate_player_ids':len(P)-len(ids),'results_unknown_player_ids':sum(1 for r in R if r.get('player_id') and r['player_id'] not in ids),'player_result_backlinks_wrong':sum(set(p.get('result_ids',[]))!=set(byp.get(p['id'],[])) for p in P),'tournament_player_ids_not_result_backed':0,'tournament_result_player_mismatch':0,'official_association_entities':sum(1 for a in load(REL+'/associations.json') if a.get('name') in OFF),'players_without_lv':sum(not p.get('lv') for p in P),'invalid_nonempty_player_lvs':sum(bool(p.get('lv')) and p['lv'] not in OFF for p in P)}
for t in T:
 d={byrid[r]['player_id'] for r in t.get('result_ids',[]) if r in byrid and byrid[r].get('player_id')}
 if set(t.get('player_ids',[]))!=d:checks['tournament_player_ids_not_result_backed']+=1
 for p in t.get('player_ids',[]):checks['tournament_result_player_mismatch']+=not any(byrid.get(r,{}).get('player_id')==p for r in t.get('result_ids',[]))
jsrc=load(ROOT+'/jlp-2025.json');exp={x['pass'] for x in jsrc};jt=[t for t in T if 'jugendlanderpokal' in norm(t.get('name'))];jr=[byrid[r] for t in jt for r in t.get('result_ids',[]) if r in byrid];actual={next((p['pass'] for p in P if p['id']==r.get('player_id')),None) for r in jr};actual.discard(None)
checks.update({'jlp_tournaments':len(jt),'jlp_result_count':len(jr),'jlp_expected_players':len(exp),'jlp_actual_players':len(actual),'jlp_missing_expected_players':len(exp-actual),'jlp_unexpected_players':len(actual-exp),'jlp_unresolved_results':sum(not r.get('player_id') for r in jr),'jlp_hoever_results':sum(next((p['pass'] for p in P if p['id']==r.get('player_id')),None) in {'68364','68365'} for r in jr)})
ho=[]
for p in P:
 if 'hoever' in norm(p.get('name')):
  ids=set(p.get('result_ids',[]));ts=[]
  for t in T:
   hits=[r for r in t.get('result_ids',[]) if r in ids]
   if hits:ts.append({'id':t['id'],'year':t.get('year'),'date':t.get('date'),'name':t.get('name'),'place':t.get('place'),'result_ids':hits})
  ho.append({'id':p['id'],'name':p['name'],'pass':p.get('pass'),'result_count':len(ids),'tournaments':ts,'jlp_matches':[t for t in ts if 'jugendlanderpokal' in norm(t['name'])]})
out={'checks':checks,'hoever':ho,'jlp_players':sorted(actual)};json.dump(out,open(REL+'/audit.json','w',encoding='utf-8'),ensure_ascii=False,indent=2);print(json.dumps(out,ensure_ascii=False,indent=2))
fail=[k for k in ('duplicate_player_ids','results_unknown_player_ids','player_result_backlinks_wrong','tournament_player_ids_not_result_backed','tournament_result_player_mismatch','invalid_nonempty_player_lvs','jlp_missing_expected_players','jlp_unexpected_players','jlp_unresolved_results','jlp_hoever_results') if checks[k]]
if fail:raise SystemExit('Relation audit failed: '+', '.join(fail))
