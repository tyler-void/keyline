import subprocess, unicodedata
from fontTools.ttLib import TTFont
from keyline.fit import load_table
fams=[('Arial','Liberation Sans'),('Times New Roman','Liberation Serif'),('Courier New','Liberation Mono'),('Georgia','Gelasio'),('Calibri','Carlito'),('Cambria','Caladea')]
for fam,twin in fams:
  for w,st in (('regular','Regular'),('bold','Bold')):
    path=subprocess.run(['fc-match','-f','%{file}',f'{fam}:style={st}'],capture_output=True,text=True).stdout
    f=TTFont(path); upm=f['head'].unitsPerEm; cmap=f.getBestCmap(); gs=f.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    T=load_table(fam,w)
    ymax=[];ymin=[]
    for cp,g in cmap.items():
      ch=chr(cp)
      cat=unicodedata.category(ch)
      if cat.startswith('C') or cat.startswith('Z'): continue
      bp=BoundsPen(gs); gs[g].draw(bp)
      if bp.bounds is None: continue
      x0,y0,x1,y1=bp.bounds
      ymax.append((y1/upm,ch,hex(cp))); ymin.append((y0/upm,ch,hex(cp)))
    ymax.sort(reverse=True); ymin.sort()
    viet=[x for x in ymax if x[1] in 'ỖẪẨẤẦẬỒỔỐỘỂỄẾỀỆẴẲẮẰẶ']
    print(fam,w,path.split('/')[-1],'descent_em',round(float(T.descent_em),3))
    print('  top ymax', [(round(a,3),b,c) for a,b,c in ymax[:6]])
    print('  viet caps ymax', [(round(a,3),b) for a,b,c in viet[:5]])
    deeper=[(round(-a,3),b,c) for a,b,c in ymin if -a> float(T.descent_em)+0.001]
    print('  deeper than descent_em:',len(deeper), deeper[:12])
