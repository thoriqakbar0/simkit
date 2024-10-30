import pytest
from fastapi.testclient import TestClient
from main import app, SimConfig, SimResource, SimProcess, SimMetric, SimInsightRule

client = TestClient(app)

def test_run_sim():
    config = SimConfig(
        title="Test Simulation",
        description="A test simulation configuration",
        duration=100,
        resources=[
            SimResource(name="resource1", capacity=2, cost_per_unit=10.0, efficiency_threshold=0.8)
        ],
        processes=[
            SimProcess(
                name="process1",
                duration=5,
                required_resources=["resource1"],
                expected_service_time=5,
                max_acceptable_wait=10
            )
        ],
        entities_per_hour=10,
        target_metrics=[
            SimMetric(name="metric1", target_value=100, unit="count", description="Test metric")
        ],
        insight_rules=[
            SimInsightRule(metric="metric1", condition="above_threshold", threshold=50, recommendation="Increase capacity")
        ],
        business_context="Test context"
    )

    response = client.post("/run-sim", json=config.dict())
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data

    # Check that metrics contain numerical values
    for metric, value in data["metrics"].items():
        if isinstance(value, dict):
            for agg, num in value.items():
                assert isinstance(num, (int, float))
        else:
            assert isinstance(value, (int, float))