import urllib.request
import json

PROJECT_ID = "yxlpuwplaonbagxuwdnq"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4bHB1d3BsYW9uYmFneHV3ZG5xIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE1MDgwMywiZXhwIjoyMTAyNzI2ODAzfQ.W3plXloo24p7Osf_TkIuUdwmGlA3xIdSJ0CRBvQ9grg"
BUCKET = "peblo"

# 1. Ensure bucket 'peblo' exists via Supabase Storage REST API
def ensure_bucket():
    url = f"https://{PROJECT_ID}.supabase.co/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "apikey": SERVICE_ROLE_KEY
    }
    
    # List buckets
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            buckets = json.loads(resp.read().decode())
            print("Existing buckets:", [b['name'] for b in buckets])
            if any(b['name'] == BUCKET for b in buckets):
                print(f"Bucket '{BUCKET}' already exists!")
                return
    except Exception as e:
        print("Error listing buckets:", e)

    # Create bucket
    payload = json.dumps({"id": BUCKET, "name": BUCKET, "public": True}).encode()
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Successfully created public bucket '{BUCKET}'! Response:", resp.read().decode())
    except Exception as e:
        print("Error creating bucket:", e)

# 2. Upload test image
def upload_test_image():
    with open("challenge_assets/banner_good.jpg", "rb") as f:
        data = f.read()

    url = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/{BUCKET}/test/banner_good.jpg"
    headers = {
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "image/jpeg",
        "apikey": SERVICE_ROLE_KEY,
        "x-upsert": "true"
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print("Upload success:", resp.read().decode())
            public_url = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/public/{BUCKET}/test/banner_good.jpg"
            print("Public URL:", public_url)
    except Exception as e:
        print("Error uploading file:", e)

if __name__ == "__main__":
    ensure_bucket()
    upload_test_image()
