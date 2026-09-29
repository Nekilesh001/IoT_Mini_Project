"""
Integration tests for FastAPI ML endpoints.
"""

from fastapi.testclient import TestClient
from api.main import create_app


def test_api_ml_endpoints():
    app = create_app()
    client = TestClient(app)

    # 1. GET /api/ml/status
    res_status = client.get("/api/ml/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "enabled" in data_status
    assert "anomaly_model" in data_status
    assert "rul_model" in data_status

    # 2. GET /api/ml/models
    res_models = client.get("/api/ml/models")
    assert res_models.status_code == 200
    data_models = res_models.json()
    assert len(data_models) >= 2

    # 3. GET /api/ml/metrics
    res_metrics = client.get("/api/ml/metrics")
    assert res_metrics.status_code == 200
    data_metrics = res_metrics.json()
    assert "total_inferences" in data_metrics
    assert "total_inference_ms" in data_metrics

    # 4. GET /api/ml/fleet-summary
    res_fleet = client.get("/api/ml/fleet-summary")
    assert res_fleet.status_code == 200

    # 5. GET /api/ml/inferences
    res_inf = client.get("/api/ml/inferences?limit=10")
    assert res_inf.status_code == 200
    assert isinstance(res_inf.json(), list)
