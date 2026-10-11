"""Access boundary test: a failed gate cannot open a price file."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import confirmation

class GuardTests(unittest.TestCase):
    def test_failed_capacity_stops_before_any_quarantine_numeric_load(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            (p/'DESIGN_DECISION.json').write_text(json.dumps({'capacity_sufficient':False,'minimum_scored_n':None}))
            with patch.object(confirmation,'RESULTS',p),patch.object(confirmation,'load_cached_pre2016') as loader:
                with self.assertRaisesRegex(RuntimeError,'must remain closed'):confirmation.run()
                loader.assert_not_called()
                self.assertFalse((p/'FRESH_OPEN_EVENT.json').exists())

if __name__=='__main__':unittest.main()
