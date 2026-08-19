-- ==============================================================================
-- Peblo TV Mini — Supabase Storage Bucket Row Level Security (RLS) Policies
-- Bucket Name: peblo
-- ==============================================================================

-- 1. Enable Row Level Security (RLS) on storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 2. Allow Public Read Access (SELECT) for all objects in the 'peblo' bucket
-- Enables child viewer apps and CDN visitors to view published catalog.json and artwork images
CREATE POLICY "Public Read Access for Peblo Bucket"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'peblo');

-- 3. Allow Authenticated Users / Service Role to Upload (INSERT) objects in the 'peblo' bucket
CREATE POLICY "Authenticated Upload Access for Peblo Bucket"
ON storage.objects
FOR INSERT
TO authenticated, service_role
WITH CHECK (bucket_id = 'peblo');

-- 4. Allow Authenticated Users / Service Role to Update (UPDATE) objects in the 'peblo' bucket
CREATE POLICY "Authenticated Update Access for Peblo Bucket"
ON storage.objects
FOR UPDATE
TO authenticated, service_role
USING (bucket_id = 'peblo');

-- 5. Allow Authenticated Users / Service Role to Delete (DELETE) objects in the 'peblo' bucket
CREATE POLICY "Authenticated Delete Access for Peblo Bucket"
ON storage.objects
FOR DELETE
TO authenticated, service_role
USING (bucket_id = 'peblo');
