#!/usr/bin/env python3
"""Construct a fictional HAR entirely in memory. Never reads production inputs."""
import argparse
import json
from pathlib import Path


def make_har():
    fields = [
        {"fdId": "demo-field-day", "name": "day", "fdType": "STRING"},
        {"fdId": "demo-field-store", "name": "store", "fdType": "STRING"},
        {"fdId": "demo-field-orders", "name": "orders", "fdType": "NUMBER", "aggrType": "SUM"},
        {"fdId": "demo-field-sales", "name": "sales", "fdType": "NUMBER", "aggrType": "SUM"},
    ]
    page = {
        "pgId": "demo-page-cafe", "name": "星际咖啡店（完全合成）",
        "cards": [
            {"cdId": "demo-card-summary", "name": "销售与客单价", "cdType": "CHART", "content": {
                "dsId": "demo-dataset-cafe", "chartType": "TABLE", "meta": {"chartMain": {"zoneData": {
                    "row": [fields[1]],
                    "metric": [fields[2],fields[3],{"fdId":"demo-field-average","name":"average_order_value","alias":"客单价","formula":"SUM(sales) / NULLIF(SUM(orders), 0)"}]
                }}}}},
            {"cdId": "demo-selector-store", "name": "门店", "cdType": "SELECTOR", "settings": {"asFilter": {
                "columnMappings": [{"sourceField": {"name":"store","dsId":"demo-dataset-cafe"},
                                    "targetFields": [{"cdId":"demo-card-summary","dsId":"demo-dataset-cafe","name":"store"}]}]
            }}}
        ],
        "dsInfos": [{"dsId":"demo-dataset-cafe","name":"虚构咖啡日汇总","columns":fields,
                     "config":{"tableQuery":{"queryType":"query","query":"SELECT day, store, orders, sales FROM demo.cafe_daily"}}}]
    }
    def entry(path, body):
        return {"request":{"method":"GET","url":"https://bi.example.invalid"+path,"headers":[],"cookies":[]},
                "response":{"status":200,"headers":[],"cookies":[],"content":{"mimeType":"application/json","text":json.dumps(body,ensure_ascii=False)}}}
    return {"log":{"version":"1.2","creator":{"name":"synthetic-fixture-generator","version":"1"},"entries":[
        entry('/api/page/demo-page-cafe',page),
        entry('/api/selector/demo-selector-store/data',{"response":{"count":2,"result":[{"value":"月球站"},{"value":"火星站"}]}})
    ]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('local/synthetic-cafe.har'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # Refuse to overwrite any existing file: it could be a user's real capture.
    with args.output.open('x',encoding='utf-8') as handle:
        json.dump(make_har(),handle,ensure_ascii=False,indent=2)
    print('Created synthetic fixture:',args.output)


if __name__ == '__main__':
    main()
