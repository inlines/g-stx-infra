-- Regional card semantics from catalog_serials::selected_sql + default visibility.
-- Shared semantics with Unknown API: digital-only releases are excluded.
-- Exact regional releases, including digital-only ones, block Worldwide fallback.
BEGIN READ ONLY;
SET LOCAL statement_timeout = '20s';
SET LOCAL lock_timeout = '2s';
WITH releases AS MATERIALIZED (
 SELECT r.*, (r.release_status IS DISTINCT FROM 5 AND r.release_date <= EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)) AS released, EXISTS(SELECT 1 FROM unnest(r.serial) s WHERE btrim(s)<>'') AS known
 FROM public.releases r JOIN public.platforms pl ON pl.id=r.platform AND pl.active=true AND pl.id<>6
), flags AS (
 SELECT product_id,platform,
   bool_or(released) AS visible,
   bool_or(NOT digital_only AND released AND known) AS physical,
   bool_or(release_region=1) AS pal, bool_or(release_region=2) AS usa,
   bool_or(release_region=5) AS jap, bool_or(release_region=8) AS ww,
   bool_or(release_region IS NULL OR release_region NOT IN (1,2,5)) AS other,
   bool_or(release_region=1 AND NOT digital_only AND released) AS physical_pal,
   bool_or(release_region=2 AND NOT digital_only AND released) AS physical_usa,
   bool_or(release_region=5 AND NOT digital_only AND released) AS physical_jap,
   bool_or(release_region=8 AND NOT digital_only AND released) AS physical_ww,
   bool_or((release_region IS NULL OR release_region NOT IN (1,2,5)) AND NOT digital_only AND released) AS physical_other,
   bool_or(release_region=1 AND NOT digital_only AND released AND known) AS known_pal,
   bool_or(release_region=2 AND NOT digital_only AND released AND known) AS known_usa,
   bool_or(release_region=5 AND NOT digital_only AND released AND known) AS known_jap,
   bool_or(release_region=8 AND NOT digital_only AND released AND known) AS known_ww,
   bool_or((release_region IS NULL OR release_region NOT IN (1,2,5)) AND NOT digital_only AND released AND known) AS known_other
 FROM releases GROUP BY product_id,platform
), eligible AS (
 SELECT f.* FROM flags f JOIN public.products p ON p.id=f.product_id
 WHERE f.visible
 AND (public.effective_game_type(p.id,f.platform,p.game_type) NOT IN (1,2,4,13,6,5,14) OR public.effective_game_type(p.id,f.platform,p.game_type) IS NULL
      OR (f.platform=7 AND public.effective_game_type(p.id,f.platform,p.game_type) IN (2,4) AND f.physical))
 AND EXISTS(SELECT 1 FROM public.product_platforms pp WHERE pp.product_id=p.id
            AND pp.platform_id=f.platform AND pp.digital_only=false)
), regional AS (
 SELECT e.product_id,e.platform,r.region,r.present,r.known FROM eligible e
 CROSS JOIN LATERAL (VALUES
 ('pal',CASE WHEN COALESCE(e.pal,false) THEN COALESCE(e.physical_pal,false) ELSE COALESCE(e.physical_ww,false) END,
    CASE WHEN COALESCE(e.pal,false) THEN COALESCE(e.known_pal,false) ELSE COALESCE(e.known_ww,false) END),
 ('usa',CASE WHEN COALESCE(e.usa,false) THEN COALESCE(e.physical_usa,false) ELSE COALESCE(e.physical_ww,false) END,
    CASE WHEN COALESCE(e.usa,false) THEN COALESCE(e.known_usa,false) ELSE COALESCE(e.known_ww,false) END),
 ('jap',CASE WHEN COALESCE(e.jap,false) THEN COALESCE(e.physical_jap,false) ELSE COALESCE(e.physical_ww,false) END,
    CASE WHEN COALESCE(e.jap,false) THEN COALESCE(e.known_jap,false) ELSE COALESCE(e.known_ww,false) END),
 ('other',COALESCE(e.physical_other,false),COALESCE(e.known_other,false))
 ) r(region,present,known)
), counts AS (
 SELECT pl.id,
   CASE pl.id WHEN 7 THEN 'PS1' WHEN 8 THEN 'PS2' WHEN 9 THEN 'PS3'
     WHEN 38 THEN 'PSP' WHEN 48 THEN 'PS4' WHEN 167 THEN 'PS5' WHEN 32 THEN 'SATURN'
     ELSE COALESCE(NULLIF(pl.abbreviation,''),'PLATFORM_'||pl.id) END AS platform,
   count(DISTINCT r.product_id) FILTER (WHERE r.present AND NOT r.known) AS total,
   count(*) FILTER (WHERE r.region='pal' AND r.present AND NOT r.known) AS pal,
   count(*) FILTER (WHERE r.region='usa' AND r.present AND NOT r.known) AS usa,
   count(*) FILTER (WHERE r.region='jap' AND r.present AND NOT r.known) AS jap,
   count(*) FILTER (WHERE r.region='other' AND r.present AND NOT r.known) AS other,
   count(*) FILTER (WHERE r.region='pal' AND r.present) AS pal_total,
   count(*) FILTER (WHERE r.region='usa' AND r.present) AS usa_total,
   count(*) FILTER (WHERE r.region='jap' AND r.present) AS jap_total,
   count(*) FILTER (WHERE r.region='other' AND r.present) AS other_total
 FROM public.platforms pl LEFT JOIN regional r ON r.platform=pl.id
 WHERE pl.active=true AND pl.id<>6 GROUP BY pl.id,pl.abbreviation
)
SELECT COALESCE(json_agg(counts ORDER BY id),'[]'::json) FROM counts;
COMMIT;
