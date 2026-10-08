import subprocess
from fontTools.ttLib import TTFont
fams=[('Arial','Liberation Sans'),('Times New Roman','Liberation Serif'),('Courier New','Liberation Mono'),('Georgia','Gelasio'),('Calibri','Carlito'),('Cambria','Caladea')]
def pairs(font):
    out={}
    if 'GPOS' not in font: 
        if 'kern' in font:
            for t in font['kern'].kernTables:
                out.update(t.kernTable)
        return out
    gpos=font['GPOS'].table
    for li,lookup in enumerate(gpos.LookupList.Lookup):
        for st in lookup.SubTable:
            if st.LookupType==9: st=st.ExtSubTable
            if getattr(st,'LookupType',None)!=2: continue
            cov=st.Coverage.glyphs
            if st.Format==1:
                for i,g1 in enumerate(cov):
                    for pvr in st.PairSet[i].PairValueRecord:
                        v=getattr(pvr.Value1,'XAdvance',0) if pvr.Value1 else 0
                        if v: out.setdefault((g1,pvr.SecondGlyph),v)
            elif st.Format==2:
                c1=st.ClassDef1.classDefs; c2=st.ClassDef2.classDefs
                g2s={}
                for g,c in c2.items(): g2s.setdefault(c,[]).append(g)
                for g1 in cov:
                    k1=c1.get(g1,0)
                    rec=st.Class1Record[k1]
                    for k2,r2 in enumerate(rec.Class2Record):
                        v=getattr(r2.Value1,'XAdvance',0) if r2.Value1 else 0
                        if v>0:
                            for g2 in g2s.get(k2,[]):
                                out.setdefault((g1,g2),v)
    return out
for fam,twin in fams:
  for st in ('Regular','Bold'):
    path=subprocess.run(['fc-match','-f','%{file}',f'{fam}:style={st}'],capture_output=True,text=True).stdout
    f=TTFont(path); upm=f['head'].unitsPerEm; rc={g:cp for cp,g in f.getBestCmap().items()}; hm=f['hmtx']
    ps=pairs(f)
    pos=[(v/upm, v/(hm[a][0]+hm[b][0]) if hm[a][0]+hm[b][0] else 0, chr(rc[a]), chr(rc[b])) for (a,b),v in ps.items() if v>0 and a in rc and b in rc]
    pos.sort(key=lambda x:-x[1])
    print(fam,st,'pairs',len(ps),'positive',len(pos), [(round(e,3),round(r,3),a+b) for e,r,a,b in pos[:8]])

print("---- common pairs")
from keyline.fit import VIETNAMESE
common=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?'\"()-%$&/’‘“”–—")|set(VIETNAMESE)
for fam,st in (('Calibri','Regular'),('Calibri','Bold'),('Cambria','Regular'),('Cambria','Bold'),('Arial','Bold'),('Times New Roman','Bold')):
    path=subprocess.run(['fc-match','-f','%{file}',f'{fam}:style={st}'],capture_output=True,text=True).stdout
    f=TTFont(path); upm=f['head'].unitsPerEm; rc={g:cp for cp,g in f.getBestCmap().items()}; hm=f['hmtx']
    ps=pairs(f)
    pos=[(v/upm, v/(hm[a][0]+hm[b][0]), chr(rc[a])+chr(rc[b])) for (a,b),v in ps.items() if v>0 and a in rc and b in rc and chr(rc[a]) in common and chr(rc[b]) in common]
    pos.sort(key=lambda x:-x[1])
    print(fam,st,len(pos),[(round(e,3),round(r,3),p) for e,r,p in pos[:25]])
