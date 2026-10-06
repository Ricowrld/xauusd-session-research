import unittest
import numpy as np
import pandas as pd
from power import generate,se_circular
from helpers import forecasts,block_sums
from availability import bounds,coverage

class Tests(unittest.TestCase):
    def test_availability_bounds_exclude_all_later_outcomes(self):
        bounds('2015-12-18','2016-01-01')
        for start,end in [('1998-12-31','1999-01-01'),('2015-12-31','2016-01-02'),('2024-01-01','2024-01-02'),('1999-01-01','1999-02-01')]:
            with self.assertRaises(ValueError):bounds(start,end)

    def test_coverage_checks_no_price_inputs(self):
        a=pd.Timestamp('2010-01-04',tz='UTC');b=a+pd.Timedelta(hours=6)
        times=pd.date_range(a,b,freq='5min',inclusive='left')
        self.assertTrue(coverage(times,a,b)['structural_pass'])
        self.assertTrue(coverage(times.delete(20),a,b)['structural_pass'])
        self.assertFalse(coverage(times[1:],a,b)['structural_pass'])
        self.assertFalse(coverage(times.delete([20,21]),a,b)['structural_pass'])

    def test_common_component_containment_and_causality(self):
        meta={'initial_log_london':-10.,'initial_log_daily':-8.,'asia_loading':.3,
              'parameters':{'asia':[-2,.3,.2,.1,.2],'london':[-2,.3,.2,.1,.2],'remainder':[-1,.3,.2,.1,.2]}}
        rng=np.random.default_rng(11);res=rng.normal(size=(100,3))*.5
        x,y=generate(meta,res,1,10,8,40,100,19,burn=30)
        np.testing.assert_allclose(x[:,1:,0],y[:,:-1])
        self.assertTrue((np.exp(x[:,1:,1])>=np.exp(x[:,:-1,4])+np.exp(y[:,:-1])).all())
        f=forecasts(x,y,40);changed=y.copy();changed[:,40:]+=2;g=forecasts(x,changed,40)
        np.testing.assert_array_equal(f['baseline'],g['baseline']);np.testing.assert_array_equal(f['enhanced'],g['enhanced'])

    def test_circular_standard_error_including_remainder(self):
        d=np.array([[1.,4.],[2.,2.],[4.,1.],[8.,3.],[3.,7.]])
        # N5, block2: enumerate all 5^3 independent starts for 2+2+1 observations.
        s=block_sums(d,2);means=np.array([(s[a]+s[b]+d[c])/5 for a in range(5) for b in range(5) for c in range(5)])
        np.testing.assert_allclose(se_circular(d,2),means.std(axis=0,ddof=0),rtol=1e-12)

if __name__=='__main__':unittest.main()
