import numpy as np
import pandas as pd
from scipy.stats import norm

def causal_lag(s):
    out=pd.Series(np.nan,index=s.index);last=None
    for date,value in s.items():
        if last is not None and (date-last[0]).days<=4:out.loc[date]=last[1]
        if np.isfinite(value) and value>0:last=(date,value)
    return out

def block_indices(rng,rows,length,pool,block):
    starts=rng.integers(0,pool,size=(rows,int(np.ceil(length/block))))
    return ((starts[:,:,None]+np.arange(block))%pool).reshape(rows,-1)[:,:length]

def forecasts(xs,ys,train):
    rows,total,_=xs.shape;pred=[];coeff=[];smears=[]
    for dim in [4,5]:
        xp=np.concatenate([np.ones((rows,total,1)),xs[:,:,:dim]],axis=2)
        out=np.empty((rows,total-train));cs=[];ss=[]
        for r in range(rows):
            coef=np.linalg.lstsq(xp[r,:train],ys[r,:train],rcond=None)[0]
            smear=np.exp(ys[r,:train]-xp[r,:train]@coef).mean()
            out[r]=np.maximum(1e-12,np.exp(xp[r,train:]@coef)*smear)
            cs.append(coef);ss.append(smear)
        pred.append(out);coeff.append(np.asarray(cs));smears.append(np.asarray(ss))
    actual=np.exp(ys[:,train:]);ratio=[actual/v for v in pred]
    loss=[r-np.log(r)-1 for r in ratio]
    if not all(np.isfinite(v).all() for v in [actual,*pred,*loss]):raise ValueError('Nonfinite synthetic forecast')
    return {'actual':actual,'baseline':pred[0],'enhanced':pred[1],'loss_b':loss[0],'loss_e':loss[1],
            'diff':loss[0]-loss[1],'asia_coef':coeff[1][:,-1],'coef_b':coeff[0],'coef_e':coeff[1],
            'smear_b':smears[0],'smear_e':smears[1]}

def bootstrap_weights(n,block,draws=1999):
    """Count-matrix equivalent of iid uniform circular block starts."""
    rng=np.random.default_rng(8191+n*31+block*101+draws)
    k,r=divmod(n,block);starts=rng.integers(0,n,size=(draws,k))
    counts=np.bincount((starts+n*np.arange(draws)[:,None]).ravel(),minlength=draws*n).reshape(draws,n).astype(np.float32)
    remainder=rng.integers(0,n,size=draws) if r else None
    return counts,remainder

def block_sums(d,block):
    # d: observations x independent paths. Circular endpoint wrapping.
    extended=np.concatenate([d,d[:block-1]],axis=0) if block>1 else d
    cum=np.concatenate([np.zeros((1,d.shape[1])),np.cumsum(extended,axis=0)],axis=0)
    return cum[block:]-cum[:-block]

def bootstrap_lower(d,block,weights):
    counts,rem=weights;n=len(d)
    means=counts@block_sums(d,block).astype(np.float32)
    r=n%block
    if r:means+=block_sums(d,r)[rem].astype(np.float32)
    return np.quantile(means/n,.025,axis=0)

def wilson(mask):
    n=len(mask);p=float(np.mean(mask));z=norm.ppf(.975);den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return p,float(center-half),float(center+half)
