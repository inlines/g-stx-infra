\set ON_ERROR_STOP on
\getenv monitor_password PG_MONITOR_PASSWORD
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='gstx_monitor') THEN
 CREATE ROLE gstx_monitor LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='gstx_monitor' AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication)) THEN
 RAISE EXCEPTION 'gstx_monitor already exists with unexpected privileges'; END IF;
END $$;
SELECT format('ALTER ROLE gstx_monitor PASSWORD %L', :'monitor_password') \gexec
GRANT CONNECT ON DATABASE gstx TO gstx_monitor;
GRANT pg_monitor TO gstx_monitor;
ALTER ROLE gstx_monitor SET statement_timeout='5s';
ALTER ROLE gstx_monitor SET default_transaction_read_only=on;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
