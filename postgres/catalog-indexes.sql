\set ON_ERROR_STOP on
SET lock_timeout='10s';
SET statement_timeout='10min';
DO $$ DECLARE item record; index_info record; BEGIN
 FOR item IN SELECT * FROM (VALUES
('idx_screenshots_game','screenshots',ARRAY['game']::text[]),
('idx_involved_companies_game','involved_companies',ARRAY['game']::text[]),
('idx_involved_companies_company_game','involved_companies',ARRAY['company','game']::text[]),
('idx_game_franschises_product_franchise','game_franschises',ARRAY['product_id','franschise_id']::text[]),
('idx_game_franschises_franchise_product','game_franschises',ARRAY['franschise_id','product_id']::text[])
 ) AS expected(name, table_name, columns) LOOP
 SELECT i.indisvalid AND i.indisready AS valid, i.indrelid, i.indisunique, i.indpred IS NULL AND i.indexprs IS NULL AS plain, am.amname,
 ARRAY(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY k(num,pos) JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.num ORDER BY k.pos) AS columns
 INTO index_info FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_am am ON am.oid=c.relam WHERE i.indexrelid=to_regclass('public.'||item.name);
 IF NOT FOUND THEN CONTINUE; END IF;
 IF NOT index_info.valid OR index_info.indrelid<>to_regclass('public.'||item.table_name) OR index_info.indisunique OR NOT index_info.plain OR index_info.amname<>'btree' OR index_info.columns<>item.columns THEN
 RAISE EXCEPTION 'Index % missing, invalid, or has an unexpected definition. Inspect it before retrying.',item.name;
 END IF;
 END LOOP;
END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_screenshots_game ON public.screenshots (game);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_involved_companies_game ON public.involved_companies (game);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_involved_companies_company_game ON public.involved_companies (company, game);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_franschises_product_franchise ON public.game_franschises (product_id, franschise_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_franschises_franchise_product ON public.game_franschises (franschise_id, product_id);
DO $$ DECLARE item record; index_info record; BEGIN
 FOR item IN SELECT * FROM (VALUES
('idx_screenshots_game','screenshots',ARRAY['game']::text[]),
('idx_involved_companies_game','involved_companies',ARRAY['game']::text[]),
('idx_involved_companies_company_game','involved_companies',ARRAY['company','game']::text[]),
('idx_game_franschises_product_franchise','game_franschises',ARRAY['product_id','franschise_id']::text[]),
('idx_game_franschises_franchise_product','game_franschises',ARRAY['franschise_id','product_id']::text[])
 ) AS expected(name, table_name, columns) LOOP
 SELECT i.indisvalid AND i.indisready AS valid, i.indrelid, i.indisunique, i.indpred IS NULL AND i.indexprs IS NULL AS plain, am.amname,
 ARRAY(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY k(num,pos) JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.num ORDER BY k.pos) AS columns
 INTO index_info FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_am am ON am.oid=c.relam WHERE i.indexrelid=to_regclass('public.'||item.name);
 IF NOT FOUND OR NOT index_info.valid OR index_info.indrelid<>to_regclass('public.'||item.table_name) OR index_info.indisunique OR NOT index_info.plain OR index_info.amname<>'btree' OR index_info.columns<>item.columns THEN
 RAISE EXCEPTION 'Index % missing, invalid, or has an unexpected definition. Inspect it before retrying.',item.name;
 END IF;
 END LOOP;
END $$;
