"""Boundary checks for the real-data joins, plus an end-to-end replay of the frozen extracts."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.build_empirical_arc import analyze, binary, build, load_inputs, number, render, sha, unique

DATA=Path(__file__).resolve().parents[1]/'data'/'empirical'

class EmpiricalArcTests(unittest.TestCase):
    def test_missing_nonfinite_and_nonbinary_are_not_negative_labels(self):
        for value in (None,'',float('nan'),float('inf')):
            with self.assertRaises(ValueError):number(value)
        for value in (-1,2,.5):
            with self.assertRaises(ValueError):binary(value)

    def test_duplicate_join_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate key'):
            unique([{'id':7},{'id':7}],lambda row:row['id'])

    def test_mismatched_campaign_universes_fail_before_interpretation(self):
        data={'campaign_trope_profiles.csv':[{'campaign_id':'1'}],
              'campaign_narrative_measure.csv':[{'campaign_id':'2'}],
              'cluster_assignments.csv':[{'campaign_id':'1'}]}
        with self.assertRaisesRegex(ValueError,'universe mismatch'):analyze(data)

    def test_manifest_detects_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'x.json';p.write_text('[]')
            (root/'manifest.json').write_text(json.dumps({'files':{'x.json':sha(p.read_bytes())}}))
            self.assertEqual(load_inputs(root)[1],{'x.json':[]})
            p.write_text('[1]')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):load_inputs(root)

    def test_manifest_cannot_read_outside_input_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);root=parent/'inputs';root.mkdir();p=parent/'other.json';p.write_text('[]')
            (root/'manifest.json').write_text(json.dumps({'files':{'../other.json':sha(p.read_bytes())}}))
            with self.assertRaisesRegex(ValueError,'path escape'):load_inputs(root)

    def test_missing_originals_remain_explicit_in_review(self):
        result={'summary':{'campaigns':2,'segments':4,'positive_narrative_segments':3,'zero_valid_rows':0,
                'unweighted_mean_narrative_share':.75,'clusters':[],'matrix_campaign_counts':{}},
                'decisions':[{'item_id':166,'campaign_id':1,'segment_id':1,'original_readings':[],
                'adjudicated_codes':{'shaky_foundations':1}}],'cooccurrence':[],'cases':[],'overlay':[]}
        text=render(result)
        self.assertIn('Missing originals',text)
        self.assertIn('separate diagnostic',text)
        self.assertIn('not three rhetorical strategies',text)

    def test_frozen_extracts_replay_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            first,second=Path(tmp)/'one',Path(tmp)/'two'
            build(DATA,first);build(DATA,second)
            names=sorted(p.name for p in first.iterdir())
            self.assertEqual(len(names),8)
            self.assertEqual(names,sorted(p.name for p in second.iterdir()))
            for name in names:self.assertEqual((first/name).read_bytes(),(second/name).read_bytes(),name)
            summary=json.loads((first/'summary.json').read_text())
            self.assertEqual(summary['campaigns'],830)

    def test_output_inside_inputs_is_refused(self):
        with self.assertRaisesRegex(ValueError,'outside the input directory'):build(DATA,DATA/'replay')

if __name__=='__main__':unittest.main()
