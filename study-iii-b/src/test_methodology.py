import unittest
import numpy as np
import pandas as pd
from common import bounds
from equivalence import rv,quality
from power import generate,forecasts,block_sums,bootstrap_lower

class MethodologyTests(unittest.TestCase):
    def test_period_guard(self):
        bounds('2016-01-01','2024-01-01')
        for a,b in [('2015-12-31','2016-01-01'),('2023-12-31','2024-01-02'),('2024-01-01','2024-01-02')]:
            with self.assertRaises(ValueError):bounds(a,b)

    def test_rv_does_not_bridge_gaps(self):
        frame=pd.DataFrame({'o':[100.,101.,200.],'c':[101.,102.,201.]},index=pd.to_datetime(['2020-01-02T00:00Z','2020-01-02T00:05Z','2020-01-02T00:15Z']))
        self.assertAlmostEqual(rv(frame,'o','c'),np.log(101/100)**2+np.log(102/101)**2)

    def test_london_dst_bounds(self):
        for date,hour in [('2023-01-03',8),('2023-07-03',7)]:
            self.assertEqual(pd.Timestamp(date+' 08:00',tz='Europe/London').tz_convert('UTC').hour,hour)

    def test_recursive_lags_and_freeze(self):
        meta={'initial_log_london':-10.,'mean_log_daily_london_ratio':1.,'asia_generator':[-2.,.5,0.,.2,.1],
              'reduced_har_generator':[-2.,.4,.1,.1,.2],'partial_asia_coefficient':.3}
        rng=np.random.default_rng(123);res=np.c_[rng.normal(size=100),rng.normal(size=100)*.2,np.ones(100)]
        x,y=generate(meta,res,1,5,3,40,50,42,burn=20)
        np.testing.assert_allclose(x[:,1:,0],y[:,:-1])
        np.testing.assert_allclose(x[:,1:,1],y[:,:-1]+1)
        np.testing.assert_allclose(x[:,20:,3],np.array([[np.log(np.exp(row[t-20:t]).mean()) for t in range(20,90)] for row in y]))
        f=forecasts(x,y,40);changed=y.copy();changed[:,40:]+=5;g=forecasts(x,changed,40)
        np.testing.assert_array_equal(f['baseline'],g['baseline'])
        np.testing.assert_array_equal(f['enhanced'],g['enhanced'])
        np.testing.assert_array_equal(f['coef_e'],g['coef_e'])

    def test_circular_block_bootstrap_against_explicit_draws(self):
        rng=np.random.default_rng(17);d=rng.normal(size=(13,7));b=5;draws=100
        starts=rng.integers(0,13,size=(draws,2));last=rng.integers(0,13,size=draws)
        counts=np.bincount((starts+13*np.arange(draws)[:,None]).ravel(),minlength=draws*13).reshape(draws,13).astype(np.float32)
        direct=[]
        for i in range(draws):
            idx=np.r_[((starts[i,:,None]+np.arange(b))%13).ravel(),(last[i]+np.arange(3))%13]
            direct.append(d[idx].mean(axis=0))
        np.testing.assert_allclose(bootstrap_lower(d,b,(counts,last)),np.quantile(direct,.025,axis=0),atol=2e-7)

if __name__=='__main__':unittest.main()
