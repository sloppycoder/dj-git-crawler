DO $$ DECLARE
  r RECORD;
BEGIN
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
    EXECUTE 'DROP TABLE ' || quote_ident(r.tablename) || ' CASCADE';
  END LOOP;
END $$;

DO $$ DECLARE
  r RECORD;
BEGIN
  FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = current_schema()) LOOP
    EXECUTE 'DROP VIEW ' || quote_ident(r.viewname);
  END LOOP;
END $$;
