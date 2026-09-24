import subprocess,json,re,os
from pathlib import Path
api=Path(os.environ['API_SOURCE']).read_text()
visibility=api.split('fn visibility_filter',1)[1].split('r#"',1)[1].split('"#',1)[0]
metrics=Path(__file__).with_name('counts.sql').read_text().split('WITH releases AS MATERIALIZED',1)[1].split('COMMIT;',1)[0]
metrics=('WITH releases AS MATERIALIZED'+metrics).replace('public.','pg_temp.').replace("COALESCE(json_agg(counts ORDER BY id),'[]'::json)","COALESCE(jsonb_agg(counts ORDER BY id),'[]'::jsonb)")
fixture='''BEGIN;
CREATE TEMP TABLE products(id int,game_type int);
CREATE TEMP TABLE platforms(id int,active bool,abbreviation text);
CREATE TEMP TABLE product_platforms(product_id int,platform_id int,digital_only bool);
CREATE TEMP TABLE releases(product_id int,platform int,release_region int,digital_only bool,serial text[],release_status int,release_date date);
CREATE TEMP TABLE product_platform_type_overrides(product_id int,platform_id int,game_type int);
CREATE FUNCTION pg_temp.effective_game_type(game int,platform int,fallback int) RETURNS int LANGUAGE sql STABLE AS $$ SELECT coalesce((SELECT o.game_type FROM pg_temp.product_platform_type_overrides o WHERE o.product_id=game AND o.platform_id=platform),fallback) $$;
INSERT INTO products VALUES(1,10),(2,0);
INSERT INTO platforms VALUES(9,true,'PS3'),(38,true,'PSP');
INSERT INTO product_platforms SELECT p.id,pl.id,false FROM products p CROSS JOIN platforms pl;
INSERT INTO releases SELECT p.id,pl.id,1,false,NULL,NULL,'2011-01-01'::date FROM products p CROSS JOIN platforms pl;
INSERT INTO product_platform_type_overrides VALUES(1,9,14);
'''
queries=[]
for platform in [9,38]:
 v=visibility.replace('{unreleased}','false').replace('{platform}',str(platform)).replace('effective_game_type','pg_temp.effective_game_type')
 queries.append(f'SELECT json_build_object(\'platform\',{platform},\'ids\',array_agg(p.id ORDER BY p.id)) FROM products p WHERE true {v};')
r=subprocess.run(['docker','exec','-i',os.environ['PG_CONTAINER'],'psql','-X','-U','postgres','-d',os.environ.get('PG_DATABASE','postgres'),'-At','-v','ON_ERROR_STOP=1'],input=fixture+'\n'.join(queries)+metrics+'ROLLBACK;',text=True,capture_output=True)
assert r.returncode==0,r.stderr
rows=[json.loads(l) for l in r.stdout.splitlines() if l.startswith(('{','['))]
assert rows[0]['ids']==[2] and rows[1]['ids']==[1,2],rows
m={r['id']:r for r in rows[2]};assert m[9]['pal']==1 and m[38]['pal']==2,rows
print('PASS: API and Grafana exclude the PS3 update, preserve PSP expanded game, preserve unrelated games.');print(json.dumps(rows))
