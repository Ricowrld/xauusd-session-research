"""Measurement/timing checks using synthetic examples and already-viewed pilot only."""
import unittest
import numpy as np
import pandas as pd
from confirmation import measure
from design import ROOT

class ConfirmationTests(unittest.TestCase):
    def test_measurement_matches_frozen_already_viewed_pilot(self):
        p=ROOT.parent/'study-iii-b/data/processed/m5_comparison.parquet'
        d=pd.read_parquet(p);d=d[d.native_present].copy()
        f=measure(d,'2016-01-01','2023-12-31')
        old=pd.read_csv(ROOT/'data/calibration/PILOT_COMPONENT_FEATURES.csv',index_col=0,parse_dates=True)
        for ours,theirs in [('lag_london','lag_london'),('lag_daily','lag_daily'),('mean5','mean5'),('mean20','mean20'),('A','A'),('L','L')]:
            np.testing.assert_allclose(f[ours].to_numpy(),old[theirs].to_numpy(),rtol=1e-10,atol=1e-10,equal_nan=True)

    def test_later_quality_flags_cannot_cancel_asia_close_forecast(self):
        # Synthetic test prices, not historical market observations.
        ix=pd.date_range('2012-01-01','2012-02-11',freq='5min',inclusive='left',tz='UTC')
        mid=1000+np.sin(np.arange(len(ix))*.1)
        d=pd.DataFrame(index=ix)
        for s,offset in [('mid',0),('bid',-.1),('ask',.1)]:
            d['o_'+s]=mid+offset;d['c_'+s]=mid+offset+.01
            d['h_'+s]=mid+offset+.02;d['l_'+s]=mid+offset-.02
        baseline=measure(d,'2012-01-02','2012-02-10')
        day=pd.Timestamp('2012-02-10')
        later=d.index>=pd.Timestamp('2012-02-10 06:00',tz='UTC')
        d.loc[later,'h_mid']=0.
        changed=measure(d,'2012-01-02','2012-02-10')
        self.assertTrue(baseline.loc[day,'forecast_eligible'])
        self.assertTrue(changed.loc[day,'forecast_eligible'])
        self.assertFalse(changed.loc[day,'london_valid'])
        for col in ['lag_london','lag_daily','mean5','mean20','A']:
            self.assertEqual(baseline.loc[day,col],changed.loc[day,col])

if __name__=='__main__':unittest.main()
