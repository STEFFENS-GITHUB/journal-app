async def test_get_user(client, create_test_user):
    user_id, headers = create_test_user
    response = await client.get(f"/api/user/{user_id}", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]

async def test_delete_user_cascades_journals(client, create_test_user):
    user_id, headers = create_test_user
    response = await client.post("/api/journal/create",
                                 json={"title": "Entry To Orphan", "body": "body", "is_public": True},
                                 headers=headers)
    assert response.status_code == 201
    journal_id = response.json()["id"]

    response = await client.delete(f"/api/user/{user_id}", headers=headers)
    assert response.status_code == 204

    response = await client.get(f"/api/journal/{journal_id}")
    assert response.status_code == 404
