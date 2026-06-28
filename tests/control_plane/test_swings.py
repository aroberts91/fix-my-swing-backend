import boto3

def test_create_swing_persists_and_returns_presigned_url(client):
    response = client.post("/swings", json={"contentType": "video/mp4"})

    assert response.status_code == 200

    body = response.json()
    swing_id = body["swingId"]

    assert body["uploadUrl"].startswith("https://")
    assert body["s3Key"] == f"swings/{swing_id}/source.mp4"

    table = boto3.resource("dynamodb", region_name="eu-west-2").Table("test-swings")
    item = table.get_item(Key={"swing_id": swing_id})["Item"]
    assert item["status"] == "uploading"
    assert "expires_at" in item

def test_get_swing_returns_404_for_unknown_id(client):
    response = client.get("/swings/unknown-swing-id")

    assert response.status_code == 404

def test_get_swing_returns_public_view(client):
    response = client.post("/swings", json={"contentType": "video/mp4"})

    swing_id = response.json()["swingId"]

    response = client.get(f"/swings/{swing_id}")

    assert response.status_code == 200

    body = response.json()

    assert "swingId" in body
    assert "s3Key" not in body and "expiresAt" not in body