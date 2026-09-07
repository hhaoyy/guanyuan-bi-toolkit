import copy
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('synthetic',ROOT/'scripts/generate_synthetic_har.py')
synthetic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synthetic)
PARSER = ROOT/'skills/guanyuan-metric-lineage/scripts/parse_guanyuan_har.py'
ANALYZER = PARSER.with_name('analyze_guanyuan_logs.py')


class LineageTests(unittest.TestCase):
    def parse(self, har):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/'fixture.har';src.write_text(json.dumps(har))
            run=subprocess.run([sys.executable,str(PARSER),str(src),'--docs-dir',str(root/'docs'),'--out-dir',str(root/'data')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            with (root/'data/field_lineage.csv').open() as f:
                rows=list(csv.DictReader(f))
            with (root/'data/filter_inventory.csv').open() as f:
                filters=list(csv.DictReader(f))
            return json.loads(run.stdout),rows,filters

    def test_synthetic_contract_and_filters(self):
        summary,rows,filters=self.parse(synthetic.make_har())
        self.assertEqual((summary['card_count'],summary['dataset_count'],len(rows)),(2,1,4))
        self.assertTrue(all(row['evidence_level']=='confirmed_guanyuan' for row in rows))
        self.assertEqual({r['upstream_tables'] for r in rows},{'demo.cafe_daily'})
        self.assertEqual(filters[0]['target_count'],'1')
        self.assertIn('月球站',filters[0]['options_sample'])
        formula=next(r for r in rows if r['source_field']=='average_order_value')
        self.assertEqual(formula['calculation_layer'],'guanyuan_card')
        sales=next(r for r in rows if r['source_field']=='sales')
        self.assertEqual(sales['requires_warehouse_trace'],'true')

    def test_source_gaps_and_missing_dataset(self):
        har=synthetic.make_har()
        page=json.loads(har['log']['entries'][0]['response']['content']['text'])
        page['dsInfos'][0]['config']={}
        har['log']['entries'][0]['response']['content']['text']=json.dumps(page)
        _,rows,_=self.parse(har)
        self.assertEqual({r['evidence_level'] for r in rows},{'partial'})
        page['cards'][0]['content'].pop('dsId')
        har['log']['entries'][0]['response']['content']['text']=json.dumps(page)
        _,rows,_=self.parse(har)
        self.assertEqual({r['evidence_level'] for r in rows},{'missing'})

    def test_long_formulas_and_sql_are_preserved(self):
        har=synthetic.make_har()
        page=json.loads(har['log']['entries'][0]['response']['content']['text'])
        formula=' + '.join(['sales']*1100)
        sql='SELECT sales FROM demo.cafe_daily /*'+'synthetic '*6000+'*/'
        page['cards'][0]['content']['meta']['chartMain']['zoneData']['metric'][-1]['formula']=formula
        page['dsInfos'][0]['config']['tableQuery']['query']=sql
        page['dsInfos'][0]['columns'][3]['formula']=formula
        har['log']['entries'][0]['response']['content']['text']=json.dumps(page)
        _,rows,_=self.parse(har)
        self.assertEqual(next(r for r in rows if r['source_field']=='average_order_value')['card_formula'],formula)
        self.assertEqual(next(r for r in rows if r['source_field']=='sales')['dataset_formula'],formula)
        self.assertEqual(rows[0]['source_sql'],sql)

    def test_cli_multiple_and_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=[]
            for i in range(2):
                p=root/f'fixture-{i}.har';p.write_text(json.dumps(synthetic.make_har()));paths.append(str(p))
            for merge,expected in [(False,8),(True,4)]:
                out=root/str(merge)
                command=[sys.executable,str(ANALYZER),*paths,'--output-root',str(out)]+(['--merge'] if merge else [])
                run=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stderr)
                with (out/'combined_field_lineage.csv').open() as f:
                    self.assertEqual(len(list(csv.DictReader(f))),expected)

    def test_headers_are_not_reported(self):
        har=synthetic.make_har()
        marker='SYNTHETIC-HEADER-DO-NOT-EXPORT'
        for entry in har['log']['entries']:
            entry['request']['headers']=[{'name':'X-Demo','value':marker}]
        summary,rows,filters=self.parse(har)
        self.assertNotIn(marker,json.dumps([summary,rows,filters]))


if __name__=='__main__':
    unittest.main()
