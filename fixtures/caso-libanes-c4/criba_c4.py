import json, statistics as st
G=json.load(open('grupos_c4.json'))
E={k:{o['id']:o for o in json.load(open(f'{k}.json'))['options']} for k in ['E1','E2','E3']}
S={k:{a['id']:a for a in json.load(open(f'{k}.json'))['assessments']} for k in ['S1','S2','S3']}
crit=['impact','feasibility','evidence','safety','inclusion']
print('completas:',[len(S[k])==41 for k in S],'| votos fatales:',sum(a['fatal'] for k in S for a in S[k].values()))
rows=[]
for g,v in G.items():
    med={c:st.median(S[s][g]['scores'][c] for s in S) for c in crit}
    rng=[c for c in crit if max(S[s][g]['scores'][c] for s in S)-min(S[s][g]['scores'][c] for s in S)>=2]
    m=v['members'][0].split(':'); stage=E[m[0]][m[1]]['chain_stage']
    ai=any(E[x.split(':')[0]][x.split(':')[1]]['depends_on_ai'] for x in v['members'])
    rows.append(dict(id=g,name=v['name'],tot=sum(med.values()),med=med,dis=rng,stage=stage,new=not v['baseline'],ai=ai))
rows.sort(key=lambda r:(-r['tot'],-r['med']['impact'],-r['med']['inclusion']))
for i,r in enumerate(rows,1):
    print(f"{i:2} {r['id']} {r['tot']:4.1f} "+' '.join(f"{r['med'][c]:.0f}" for c in crit),r['stage'][:8].ljust(8),'N' if r['new'] else '-','IA' if r['ai'] else '  ',','.join(r['dis']),'|',r['name'])
# regla de cartera: top 10 + mejor de cada etapa no cubierta
top=rows[:10]; sel=list(top)
for s in ['find','record_or_rescue','preserve','describe','access','keep_alive','transmit']:
    if not any(r['stage']==s for r in sel):
        best=next(r for r in rows if r['stage']==s); sel.append(best); print('añadido por etapa',s,best['id'])
print('cartera:',[r['id'] for r in sel],'| nuevas',sum(r['new'] for r in sel),'de',len(sel))
json.dump(rows,open('ranking_c4.json','w'),ensure_ascii=False,indent=1)
