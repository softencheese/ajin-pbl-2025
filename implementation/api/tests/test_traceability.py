from fastapi.testclient import TestClient

def test_traceability_flow(client: TestClient):
    # 1. Create Data Layer
    # Process
    p_proc = client.post("/api/v1/processes/", json={"process_code": "PROC-TRACE", "process_name": "Trace Proc", "process_type": "Manufacturing", "process_order": 10})
    proc_id = p_proc.json()["id"]
    
    # Items
    raw_item = client.post("/api/v1/items/", json={"item_code": "RAW-ITEM", "item_name": "Raw", "item_type": "RAW"}).json()
    prod_item = client.post("/api/v1/items/", json={"item_code": "PROD-ITEM", "item_name": "Prod", "item_type": "WIP"}).json()

    # 2. Receiving Lot
    raw_lot = client.post("/api/v1/lots/receiving", json={
        "item_id": raw_item["id"], "quantity": 100, "production_date": "2023-12-01"
    }).json()

    # 3. Production Lot (consuming Raw)
    prod_lot = client.post("/api/v1/lots/", json={
        "process_id": proc_id,
        "item_id": prod_item["id"],
        "quantity": 10,
        "production_date": "2023-12-02",
        "input_lots": [{"lot_id": raw_lot["id"], "quantity_consumed": 10}]
    }).json()

    # 4. Check Forward Trace (Raw -> Prod)
    res_fwd = client.get(f"/api/v1/trace/forward?lot_number={raw_lot['lot_number']}")
    assert res_fwd.status_code == 200
    data_fwd = res_fwd.json()
    assert data_fwd.get("root_lot_no") == raw_lot["lot_number"]
    assert len(data_fwd.get("produced_lots", [])) > 0
    assert data_fwd["produced_lots"][0]["lot_no"] == prod_lot["lot_number"]

    # 5. Check Backward Trace (Prod -> Raw)
    res_bwd = client.get(f"/api/v1/trace/backward?lot_number={prod_lot['lot_number']}")
    assert res_bwd.status_code == 200
    data_bwd = res_bwd.json()
    assert data_bwd["product"]["lot_no"] == prod_lot["lot_number"]
    assert len(data_bwd["parent_lots"]) > 0
    assert data_bwd["parent_lots"][0]["lot_no"] == raw_lot["lot_number"]

    # 6. Drill Down
    res_dd = client.get(f"/api/v1/trace/drill-down?search={prod_lot['lot_number']}")
    assert res_dd.status_code == 200
    data_dd = res_dd.json()
    assert data_dd["search_type"] == "LOT"
    assert data_dd["search_value"] == prod_lot["lot_number"]
