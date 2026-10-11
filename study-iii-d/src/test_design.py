import unittest
import numpy as np
from frozen_core import generate,forecasts,block_sums
from design import se_circular,reference_risk

class MethodTests(unittest.TestCase):
    def test_circular_remainder_variance_by_exhaustive_resampling(self):
        d=np.array([[1.,4.],[2.,2.],[4.,1.],[8.,3.],[3.,7.]])
        s=block_sums(d,2)
        samples=np.array([(s[a]+s[b]+d[c])/5 for a in range(5) for b in range(5) for c in range(5)])
        np.testing.assert_allclose(se_circular(d,2),samples.std(axis=0),rtol=1e-12)

    def test_future_outcomes_do_not_change_fitted_models_or_smearing(self):
        rng=np.random.default_rng(74);x=rng.normal(size=(3,80,5));y=x[:,:,0]+rng.normal(size=(3,80))
        a=forecasts(x,y,40);y[:,40:]+=3;b=forecasts(x,y,40)
        for name in ['coef_b','coef_e','smear_b','smear_e','baseline','enhanced']:
            np.testing.assert_array_equal(a[name],b[name])

    def test_conditional_oracle_matches_direct_qlike(self):
        rng=np.random.default_rng(59);x=rng.normal(size=(4,70,5));y=rng.normal(size=(4,70))
        fit=forecasts(x,y,40);refx=rng.normal(size=(8,60,5));refy=rng.normal(size=(8,60))
        truth=reference_risk(refx,refy,fit);direct=[]
        for i in range(8):
            preds=[]
            for k,dim in [('b',4),('e',5)]:
                pred=np.exp(np.c_[np.ones(60),refx[i,:,:dim]]@fit['coef_'+k].T)*fit['smear_'+k]
                ratio=np.exp(refy[i])[:,None]/pred
                preds.append(ratio-np.log(ratio)-1)
            direct.append((preds[0]-preds[1]).mean(axis=0))
        np.testing.assert_allclose(truth['risk'],np.mean(direct,axis=0),atol=1e-12)

    def test_coherent_components_and_causal_har_features(self):
        meta={'initial_log_london':-10.,'initial_log_daily':-8.,'asia_loading':.3,
            'parameters':{'asia':[-2,.3,.2,.1,.2],'london':[-2,.3,.2,.1,.2],'remainder':[-1,.3,.2,.1,.2]}}
        resid=np.random.default_rng(5).normal(size=(100,3))*.5
        x,y=generate(meta,resid,1.,20,4,40,60,54,burn=40)
        np.testing.assert_allclose(x[:,1:,0],y[:,:-1])
        self.assertTrue((np.exp(x[:,1:,1])>=np.exp(x[:,:-1,4])+np.exp(y[:,:-1])).all())

if __name__=='__main__':unittest.main()
