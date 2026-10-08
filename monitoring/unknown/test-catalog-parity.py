"""Compare collector to the actual API predicates on a read-only restored database."""
import os,json,subprocess,re
from pathlib import Path
api=Path(os.environ['API_SOURCE']).read_text()
def raw(name):
 body=api.split('fn '+name+'(',1)[1].split('\nfn ',1)[0]
 match=re.search(r'r#"(.*?)"#',body,re.S) or re.search(r'format!\(\s*"(.*?)"',body,re.S)
 return match.group(1)
visibility=raw('visibility_filter').replace('{unreleased}','false').replace('{platform}','pl.id')
physical=raw('physical_region_filter').replace('{platform}','pl.id').replace('{regions}',"ARRAY[unknown_region.region]::text[]")
codes=api.split('let codes = format!(',1)[1].split('"',1)[1].split('"',1)[0].replace('{platform}','pl.id')
query=f"""SELECT json_agg(x) FROM (SELECT pl.id,unknown_region.region,count(*) AS total,count(*) FILTER(WHERE NOT {codes}) AS unknown
FROM platforms pl JOIN product_platforms pp ON pp.platform_id=pl.id JOIN products p ON p.id=pp.product_id
CROSS JOIN (VALUES('europe'),('america'),('japan'),('other')) unknown_region(region)
WHERE pl.active AND pl.id<>6 AND NOT pp.digital_only {visibility} {physical}
GROUP BY pl.id,unknown_region.region) x;"""
collector=Path(__file__).with_name('counts.sql').read_text()
# Same transaction/snapshot for the API and collector, to avoid clock/data skew.
collector=collector.replace('json_agg(counts ORDER BY id)','jsonb_agg(counts ORDER BY id)').replace("'[]'::json","'[]'::jsonb");query=query.replace('json_agg(x)','jsonb_agg(x)')
sql=collector.replace('BEGIN READ ONLY;','BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;').replace('COMMIT;',query+'\nCOMMIT;')
r=subprocess.run(['docker','exec','-i',os.environ['PG_CONTAINER'],'psql','-XAt','-U','postgres','-d',os.environ['PG_DATABASE'],'-v','ON_ERROR_STOP=1'],input=sql,text=True,capture_output=True)
assert r.returncode==0,r.stderr
metrics,expected=[json.loads(line) for line in r.stdout.splitlines() if line.startswith('[')]
expected={(x['id'],x['region']):x for x in expected};checked=0
for m in metrics:
 for region,key in [('europe','pal'),('america','usa'),('japan','jap'),('other','other')]:
  e=expected.get((m['id'],region),{'unknown':0,'total':0})
  assert (m[key],m[key+'_total'])==(e['unknown'],e['total']),(m['platform'],region,m,e)
  checked+=1
print(json.dumps({'platforms':len(metrics),'regional_comparisons':checked,'mismatches':0}))
print(json.dumps([x for x in metrics if x['id'] in (9,32,38)],ensure_ascii=False))
