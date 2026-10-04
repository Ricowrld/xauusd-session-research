"""Synthetic implementation checks; fixtures never enter empirical results."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from common import bounded, verify_plan
from coverage import grid_counts
from power import lrv, required_n


class DesignTests(unittest.TestCase):
    def test_two_missing_minutes_in_same_block_only_remove_one_m5(self):
        p=np.ones(1440,dtype=bool);p[[0,4]]=False
        got,complete,boundary=grid_counts(p)
        self.assertEqual(got[0],58);self.assertEqual(complete[0],11)
        self.assertEqual(complete.sum(),287);self.assertEqual(boundary[0],1)

    def test_hour_end_is_a_boundary_even_with_high_minute_coverage(self):
        p=np.ones(1440,dtype=bool);p[59]=False
        got,complete,boundary=grid_counts(p)
        self.assertEqual(got[0],59);self.assertEqual(boundary[0],1)

    def test_variance_formula_for_iid_and_positive_dependence(self):
        self.assertAlmostEqual(lrv([1,-1,1,-1],0),1.)
        rng=np.random.default_rng(7);x=np.zeros(10000);noise=rng.normal(size=len(x))
        for i in range(1,len(x)):x[i]=.7*x[i-1]+noise[i]
        self.assertGreater(lrv(x,20),3*lrv(x,0))

    def test_power_and_effect_requirements(self):
        self.assertGreater(required_n(2,.05,.9),required_n(2,.05,.8))
        self.assertLessEqual(abs(required_n(2,.1,.9)*4-required_n(2,.05,.9)),3)

    def test_holdout_queries_are_refused(self):
        with self.assertRaises(ValueError):bounded('2024-01-01','2024-01-02')
        bounded('2023-12-31','2024-01-01')

    def test_unchanged_trading_candidate_and_registered_planning_source(self):
        old=json.loads((ROOT.parent/'gold-session-study-ii/configs/study.json').read_text())
        new=json.loads((ROOT/'configs/confirmation.json').read_text())
        self.assertEqual(new['trading_candidate'],old['one_conditional_trading_candidate'])
        verify_plan()


if __name__=='__main__':unittest.main()
