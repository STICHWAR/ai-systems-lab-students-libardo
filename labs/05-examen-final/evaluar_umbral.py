"""FAR/FRR con >=10 pares genuinos y >=20 impostores (no inventar resultados)."""
import argparse, csv, json
from pathlib import Path

def analyze(path,thresholds):
    with open(path,encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    g=[float(r['similaridad']) for r in rows if r['tipo']=='genuino']
    i=[float(r['similaridad']) for r in rows if r['tipo']=='impostor']
    if len(g)<10 or len(i)<20:raise ValueError('Se necesitan al menos 10 genuinos y 20 impostores medidos')
    result=[{'umbral':t,'FAR':sum(x>=t for x in i)/len(i),'FRR':sum(x<t for x in g)/len(g),'genuinos':len(g),'impostores':len(i)} for t in thresholds]
    for row in result:print(f"{row['umbral']:.3f} | FAR={row['FAR']:.3%} | FRR={row['FRR']:.3%} | {row['genuinos']} genuinos | {row['impostores']} impostores")
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--umbrales',nargs='+',type=float,default=[.30,.363,.45]);a=p.parse_args();analyze(a.csv,a.umbrales)
