"""Synthetic fixtures test engineering only; never included in research evidence."""
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from study import bounds,replay_day,apply_sizing,block_means

class StudyTests(unittest.TestCase):
    def test_local_session_dst(self):
        winter,_=bounds('2016-01-04','Europe/London','08:00','12:00')
        summer,_=bounds('2016-07-04','Europe/London','08:00','12:00')
        self.assertEqual(winter.hour,8);self.assertEqual(summer.hour,7)
        tokyo,_=bounds('2016-07-04','Asia/Tokyo','09:00','15:00');self.assertEqual(tokyo.hour,0)

    def test_us_uk_transition_mismatch(self):
        uk,_=bounds('2016-03-21','Europe/London','08:00','12:00')
        us,_=bounds('2016-03-21','America/New_York','08:00','12:00')
        self.assertEqual((us-uk).total_seconds()/3600,4)

    def bars(self,values):
        ix=pd.date_range('2016-01-04 04:00',periods=len(values),freq='min',tz='UTC')
        rows=[]
        for o,h,l,c in values:
            rows.append({f'{k}_bid':v for k,v in zip(['open','high','low','close'],[o,h,l,c])}|{f'{k}_ask':v+.2 for k,v in zip(['open','high','low','close'],[o,h,l,c])})
        return pd.DataFrame(rows,index=ix)

    def test_both_edges_skip(self):
        g=self.bars([(100,102,98,101),(101,102,100,101)])
        t,status=replay_day(g,101,99,g.index[0],g.index[-1],g.index[-1]);self.assertIsNone(t);self.assertEqual(status,'ambiguous_entry')

    def test_long_ask_entry_bid_exit_cost(self):
        g=self.bars([(100,101.5,100,101),(102,103,102,102)])
        t,status=replay_day(g,101,99,g.index[0],g.index[-1],g.index[-1],slip=0)
        self.assertEqual(status,'trade');self.assertAlmostEqual(t['entry'],101.2);self.assertEqual(t['exit'],102)
        self.assertAlmostEqual(t['R'],(.8-.07)/2.2)

    def test_adverse_stop_gap(self):
        g=self.bars([(100,101.5,100,101),(98,98.5,97,98),(100,100,100,100)])
        t,_=replay_day(g,101,99,g.index[0],g.index[-1],g.index[-1],slip=.05)
        self.assertEqual(t['exit_reason'],'stop');self.assertAlmostEqual(t['exit'],97.95);self.assertLess(t['R'],-1)

    def test_brake_uses_prior_closed_trades(self):
        t=pd.DataFrame({'R':[-1]*21,'risk_usd_per_oz':[1]*21})
        s=apply_sizing(t);self.assertEqual(s.risk_fraction.iloc[19],.01);self.assertEqual(s.risk_fraction.iloc[20],.005)

    def test_bootstrap_deterministic(self):
        a=block_means([1,2,3],100,2,np.random.default_rng(7));b=block_means([1,2,3],100,2,np.random.default_rng(7))
        np.testing.assert_array_equal(a,b)

    def test_midnight_crossing(self):
        s,e=bounds('2016-01-03','America/New_York','23:00','03:00')
        self.assertEqual((e-s).total_seconds()/3600,4);self.assertEqual(str(s.date()),'2016-01-04')

if __name__=='__main__':unittest.main()
