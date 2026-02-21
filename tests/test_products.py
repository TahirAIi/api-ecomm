from unittest.mock import patch


EMBEDDING_TASK = "app.tasks.embedding_tasks.generate_product_embedding.delay"


def _product_payload(category_uuid):
    return {
        "name": "Test Product",
        "description": "A test product",
        "price": 29.99,
        "stock_quantity": 10,
        "category_uuids": [str(category_uuid)],
    }


@patch(EMBEDDING_TASK)
def test_create_product_as_superuser(mock_embed, client, auth_headers_superuser, test_category):
    resp = client.post(
        "/api/v1/products",
        json=_product_payload(test_category.uuid),
        headers=auth_headers_superuser,
    )
    assert resp.status_code == 201


@patch(EMBEDDING_TASK)
def test_create_product_as_regular_user(mock_embed, client, auth_headers_regular, test_category):
    resp = client.post(
        "/api/v1/products",
        json=_product_payload(test_category.uuid),
        headers=auth_headers_regular,
    )
    assert resp.status_code == 403


@patch(EMBEDDING_TASK)
def test_create_product_negative_price(mock_embed, client, auth_headers_superuser, test_category):
    payload = _product_payload(test_category.uuid)
    payload["price"] = -5.0
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_headers_superuser,
    )
    assert resp.status_code == 422


@patch(EMBEDDING_TASK)
def test_create_product_zero_price(mock_embed, client, auth_headers_superuser, test_category):
    payload = _product_payload(test_category.uuid)
    payload["price"] = 0
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_headers_superuser,
    )
    assert resp.status_code == 422


@patch(EMBEDDING_TASK)
def test_create_product_negative_stock(mock_embed, client, auth_headers_superuser, test_category):
    payload = _product_payload(test_category.uuid)
    payload["stock_quantity"] = -1
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_headers_superuser,
    )
    assert resp.status_code == 422


def test_list_products(client):
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200


@patch(EMBEDDING_TASK)
def test_get_product_by_uuid(mock_embed, client, auth_headers_superuser, test_category):
    create_resp = client.post(
        "/api/v1/products",
        json=_product_payload(test_category.uuid),
        headers=auth_headers_superuser,
    )
    product_uuid = create_resp.json()["uuid"]
    resp = client.get(f"/api/v1/products/{product_uuid}")
    assert resp.status_code == 200
    assert resp.json()["uuid"] == product_uuid


def test_get_product_not_found(client):
    resp = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@patch(EMBEDDING_TASK)
def test_update_product_as_regular_user(mock_embed, client, auth_headers_superuser, auth_headers_regular, test_category):
    create_resp = client.post(
        "/api/v1/products",
        json=_product_payload(test_category.uuid),
        headers=auth_headers_superuser,
    )
    product_uuid = create_resp.json()["uuid"]
    resp = client.put(
        f"/api/v1/products/{product_uuid}",
        json={"name": "Updated Name"},
        headers=auth_headers_regular,
    )
    assert resp.status_code == 403
