from PIL import Image; import numpy as np, json, cv2
from scipy import ndimage
from skimage.morphology import skeletonize
a=np.array(Image.open('images/3.png').convert('RGB')).astype(int)
H,W,_=a.shape; g=a.mean(2); sat=a.max(2)-a.min(2)
def near(c,t): return np.sqrt(((a-np.array(c))**2).sum(2))<t
CLS={'low':((154,152,144),22),'shop':((42,120,214),60),'ind':((235,104,52),55),
     'civic':((27,175,122),55),'strip':((231,117,160),45)}
PANELS={'tampa':((17,398,49,704),69/10),'orlando':((419,720,38,261),52/10),'se':((737,925,123,631),40/10)}
# regions to ignore (text, north arrows, scale bars)
IGN=[(320,375,180,200),(83,145,510,530),(588,640,93,110),(360,390,82,158),(690,710,50,80),(905,925,150,208),
     (35,115,640,680),(430,495,225,258),(740,795,575,612)]
ign=np.zeros((H,W),bool)
for x0,x1,y0,y1 in IGN: ign[y0:y1,x0:x1]=True
masks={k:near(c,t)&~ign for k,(c,t) in CLS.items()}
masks['ind']&=~masks['strip']
out={}
for pn,((x0,x1,y0,y1),ppk) in PANELS.items():
    sl=(slice(y0,y1+1),slice(x0,x1+1))
    to_km=lambda x,y:(float((x-x0)/ppk),float((y1-y)/ppk))
    anym=np.zeros((y1-y0+1,x1-x0+1),bool)
    pts=[]
    for k in CLS:
        m=masks[k][sl]; anym|=m
        m=ndimage.binary_opening(m,iterations=1) if k in('shop','civic','low') else m
        lab,n=ndimage.label(m,structure=np.ones((3,3)))
        areas=ndimage.sum(m,lab,range(1,n+1))
        pts_k=[]
        single={'low':30,'shop':40,'civic':45,'ind':16,'strip':16}[k]
        for i,ar in enumerate(areas,1):
            if ar<single*0.35: continue
            yy,xx=np.nonzero(lab==i)
            kk=max(1,int(round(ar/single)))
            if kk==1: cs=[(xx.mean(),yy.mean())]
            else:
                Z=np.float32(np.c_[xx,yy]); _,_,cen=cv2.kmeans(Z,kk,None,(3,50,.1),5,cv2.KMEANS_PP_CENTERS); cs=[tuple(c) for c in cen]
            for cx,cy in cs: pts_k.append(to_km(cx+x0,cy+y0))
        pts+= [[k,round(p[0],3),round(p[1],3)] for p in pts_k]
        print(pn,k,len(pts_k))
    # land / water / county lines
    sub=a[sl]; water=np.sqrt(((sub-np.array((227,235,242)))**2).sum(2))<10
    mk=ndimage.binary_dilation(anym|ign[sl],iterations=3)
    white=(sub.min(2)>=250)&~mk
    # corridor
    corr=(np.abs(sub.mean(2)-178)<14)&(sub.max(2)-sub.min(2)<16)&~ign[sl]&~water
    water=ndimage.binary_opening(ndimage.binary_closing(water|(mk&ndimage.binary_dilation(water,iterations=4)&~(white)),iterations=2),iterations=1)
    water&=~ndimage.binary_dilation(anym,iterations=1)|water
    land=~water&~white
    land=ndimage.binary_opening(land,iterations=1)
    lab,n=ndimage.label(land)
    polys=[]
    for i in range(1,n+1):
        m=(lab==i)
        if m.sum()<60: continue
        m=ndimage.binary_dilation(m,iterations=1)  # close half of white gap
        cnts,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        for c in cnts:
            c=cv2.approxPolyDP(c,0.8,True)[:,0,:]
            if len(c)<3: continue
            polys.append([list(map(lambda v:round(v,3),to_km(x+x0,y+y0))) for x,y in c])
    # corridor segments from skeleton of corridor+markers
    sk=skeletonize(ndimage.binary_closing(corr|anym,iterations=2))
    segs=[]
    ys,xs=np.nonzero(sk)
    S=set(zip(ys,xs))
    for y,x in S:
        for dy,dx in((0,1),(1,0),(1,1),(1,-1)):
            if (y+dy,x+dx) in S: segs.append([to_km(x+x0,y+y0),to_km(x+dx+x0,y+dy+y0)])
    wl=(sub.min(2)>=249)&~ign[sl]&~ndimage.binary_dilation(anym,iterations=4)
    wl[:3,:]=wl[-3:,:]=False; wl[:,:3]=wl[:,-3:]=False
    lab2,n2=ndimage.label(ndimage.binary_closing(wl,iterations=1),structure=np.ones((3,3)))
    sz=ndimage.sum(wl,lab2,range(1,n2+1))
    keep=np.isin(lab2,[i+1 for i,v in enumerate(sz) if v>=25])
    sk2=skeletonize(keep); S2=set(zip(*np.nonzero(sk2))); cseg=[]
    for y,x in S2:
        for dy,dx in((0,1),(1,0),(1,1),(1,-1)):
            if (y+dy,x+dx) in S2: cseg.append([to_km(x+x0,y+y0),to_km(x+dx+x0,y+dy+y0)])
    out[pn]={'county':[[[round(p,3) for p in q] for q in s_] for s_ in cseg],'w_km':(x1-x0)/ppk,'h_km':(y1-y0)/ppk,'land':polys,'markers':pts,
             'corridor':[[[round(p,3) for p in q] for q in s] for s in segs]}
    print(pn,'polys',len(polys),'segs',len(segs))
json.dump(out,open('/home/user/Mohsen/figures/study_area_map_data.json','w'))
