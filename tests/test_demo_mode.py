from backend.app.demo_data import demo_domains, demo_records


def test_demo_data_is_deterministic():
    domains = demo_domains()
    records = demo_records("example.com")

    assert domains[0].domain == "example.com"
    assert records[0].id == "rec-001"
    assert records[0].data == "3.0.3.205"
