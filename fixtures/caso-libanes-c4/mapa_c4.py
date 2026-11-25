import json
E={k:{o['id']:o for o in json.load(open(f'{k}.json'))['options']} for k in ['E1','E2','E3']}
# group code: (readable name, members, matches baseline?)
G={
'C01':("Inventario nacional de archivos de emisoras",['E2:O1'],True),
'C02':("Triaje y gestión de derechos de archivos",['E1:O1','E2:O11'],False),
'C03':("Rescate de cintas en emisoras privadas y regionales",['E1:O2'],True),
'C04':("Rescate de cintas y vídeos domésticos",['E1:O3','E2:O2','E3:O2','E2:O4'],False),
'C05':("Depósito de custodia sin publicación (escrow)",['E2:O6','E3:O1'],False),
'C06':("Copias de seguridad distribuidas, también en la diáspora",['E1:O19','E2:O7'],False),
'C07':("Archivo semilla mínimo",['E1:O18'],False),
'C08':("Licencia de custodia comunitaria",['E1:O8','E3:O3'],False),
'C09':("Archivos sonoros regionales de gobierno comunitario",['E2:O8'],False),
'C10':("Reemitir archivos por radio y televisión",['E1:O4','E2:O15'],False),
'C11':("Red de radios locales en dialecto",['E3:O6'],False),
'C12':("Línea telefónica para escuchar archivos",['E1:O5'],False),
'C13':("Puntos de escucha sin internet",['E2:O12','E3:O16'],False),
'C14':("Acceso en línea por niveles contra la recolección",['E1:O10','E2:O13','E3:O9'],True),
'C15':("Colección abierta con derechos liberados",['E2:O14'],True),
'C16':("Catalogación colaborativa por escucha",['E1:O7','E2:O9'],False),
'C17':("Indexación de archivos con reconocimiento de voz",['E1:O9','E2:O10','E3:O12'],True),
'C18':("Búsqueda e interfaz por voz para quien no lee",['E1:O23','E2:O23','E3:O4'],False),
'C19':("Medir dónde se pierde antes de actuar",['E1:O11','E2:O3','E3:O7'],False),
'C20':("Atlas sonoro de variantes regionales",['E1:O12','E3:O17'],True),
'C21':("Grabar oficios, trabajo y vida cotidiana en contexto",['E2:O5','E3:O10'],False),
'C22':("Escolares entrevistan a sus mayores",['E1:O6','E3:O15'],True),
'C23':("Actividades escolares ligadas al uso en casa",['E1:O24'],False),
'C24':("Nidos lingüísticos para la infancia",['E2:O19'],False),
'C25':("Aprendizajes pagados con portadores de la tradición",['E1:O20','E2:O22','E3:O8'],False),
'C26':("Pagar la práctica viva: zajal, relatos, teatro",['E1:O13','E2:O16'],False),
'C27':("Proteger los espacios de encuentro",['E1:O21','E2:O17'],False),
'C28':("Transmisión familiar con la diáspora",['E1:O14','E3:O5'],True),
'C29':("Círculos familiares intergeneracionales sin grabar",['E2:O18'],False),
'C30':("Grabaciones familiares guardadas en casa",['E1:O15'],False),
'C31':("Barajas de refranes y recetas para la mesa familiar",['E3:O13'],False),
'C32':("La diáspora como reservorio propio",['E2:O20'],False),
'C33':("Incluir otras herencias habladas del Líbano",['E1:O22'],False),
'C34':("Reforma legal: preservación y obras huérfanas",['E1:O16'],False),
'C35':("Protocolo único de consentimiento oral",['E1:O17'],False),
'C36':("Datos de voz alojados en el Líbano, acceso federado",['E3:O11'],False),
'C37':("Intervención mínima con observación periódica",['E2:O21'],False),
'C38':("Depósitos para generaciones futuras",['E2:O24'],False),
'C39':("Preservar lo digital contemporáneo",['E2:O25'],False),
'C40':("Restauración acústica de cintas dañadas",['E3:O18'],False),
'C41':("Regalías colectivas por uso de archivos y voces",['E3:O14'],False),
}
assigned=[m for g in G.values() for m in g[1]]
allids=[f'{k}:{i}' for k in E for i in E[k]]
assert sorted(assigned)==sorted(allids), (set(allids)-set(assigned), [a for a in assigned if assigned.count(a)>1])
n=len(G); nov=sum(not g[2] for g in G.values())
print('opciones',len(allids),{k:len(E[k]) for k in E},'-> grupos',n,'| nuevos vs línea base',nov,f'({nov/n:.0%})')
cov={k:{g for g,v in G.items() if any(m.startswith(k) for m in v[1])} for k in E}
for a,b in [('E1','E2'),('E1','E3'),('E2','E3')]:
    print(a,b,'Jaccard',round(len(cov[a]&cov[b])/len(cov[a]|cov[b]),2))
print('aportes únicos:',{k:len([g for g in cov[k] if all(g not in cov[o] for o in E if o!=k)]) for k in E})
print('en los tres:',len(cov['E1']&cov['E2']&cov['E3']))
ai={g for g,v in G.items() if any(E[m.split(':')[0]][m.split(':')[1]]['depends_on_ai'] for m in v[1])}
print('grupos que dependen de IA (alguna variante):',len(ai))
json.dump({g:{'name':v[0],'members':v[1],'baseline':v[2]} for g,v in G.items()},open('grupos_c4.json','w'),ensure_ascii=False,indent=1)
