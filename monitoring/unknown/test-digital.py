from pathlib import Path
import re,subprocess,json,os
ROOT=Path(__file__).resolve().parents[2]
api=Path(os.environ['API_SOURCE']).read_text()
physical=api.split('fn physical_region_filter')[1].split('format!(',1)[1].split('"',1)[1].split('"',1)[0]
codes=api.split('let codes = format!(',1)[1].split('"',1)[1].split('"',1)[0]
physical=physical.replace('{platform}','48').replace('{regions}',"ARRAY[unknown_region.region]::text[]")
codes=codes.replace('{platform}','48')
fixture='''BEGIN;
CREATE FUNCTION pg_temp.effective_game_type(game int,platform int,fallback int) RETURNS int LANGUAGE sql IMMUTABLE AS $$ SELECT fallback $$;
CREATE TEMP TABLE products(id int,game_type int);
CREATE TEMP TABLE platforms(id int,active bool,abbreviation text);
CREATE TEMP TABLE product_platforms(product_id int,platform_id int,digital_only bool);
CREATE TEMP TABLE releases(product_id int,platform int,release_region int,digital_only bool,serial text[],release_status int,release_date bigint);
INSERT INTO platforms VALUES(48,true,'PS4');
INSERT INTO products SELECT i,0 FROM generate_series(1,11)i;
INSERT INTO product_platforms SELECT i,48,i=7 FROM generate_series(1,11)i;
INSERT INTO releases VALUES
(1,48,1,true,NULL,NULL,1577836800),
(2,48,1,false,NULL,NULL,1577836800),
(3,48,1,false,ARRAY['CUSA-12345'],NULL,1577836800),
(4,48,1,true,NULL,NULL,1577836800),
(4,48,8,false,NULL,NULL,1577836800),
(5,48,1,true,ARRAY['DIGITAL'],NULL,1577836800),
(5,48,1,false,NULL,NULL,1577836800),
(6,48,8,true,NULL,NULL,1577836800),
(7,48,1,false,NULL,NULL,1577836800),
(8,48,1,false,NULL,NULL,NULL),
(9,48,1,false,NULL,5,NULL),
(10,48,1,false,NULL,NULL,4102444800),
(11,48,1,false,ARRAY['CUSA-KNOWN'],NULL,1577836800),
(11,48,5,false,NULL,5,NULL);
'''
queries=[]
for region in ['europe','america','japan','other']:
 queries.append(f"SELECT json_build_object('region','{region}','total',count(*),'unknown',count(*) FILTER (WHERE NOT {codes})) FROM products p CROSS JOIN (VALUES ('{region}')) unknown_region(region) WHERE EXISTS(SELECT 1 FROM product_platforms pp WHERE pp.product_id=p.id AND NOT pp.digital_only) {physical};")
metrics=(ROOT/'monitoring/unknown/counts.sql').read_text().split('WITH releases AS MATERIALIZED',1)[1].split('COMMIT;')[0]
metrics='WITH releases AS MATERIALIZED'+metrics.replace('public.','pg_temp.')
sql=fixture+'\n'.join(queries)+metrics+'ROLLBACK;'

r=subprocess.run(['docker','exec','-i',os.environ['PG_CONTAINER'],'psql','-U','postgres','-At','-v','ON_ERROR_STOP=1'],input=sql,text=True,capture_output=True)
assert r.returncode==0,r.stderr
rows=[json.loads(l) for l in r.stdout.splitlines() if l.startswith(('{','['))]
a=rows[:4];m=rows[4][0]
for item,key in zip(a,['pal','usa','jap','other']):
 assert (item['total'],item['unknown'])==(m[key+'_total'],m[key]),(item,m)
assert (a[0]['total'],a[0]['unknown'])==(5,3),a
assert all((x['total'],x['unknown'])==(1,1) for x in a[1:]),a
print('PASS: API and metrics agree on digital-only, mixed, physical-known, physical-unknown, Worldwide precedence and platform-level digital exclusion.')
print(json.dumps(rows,indent=2))
