from app.schemas.waybill import OperationMode, WaybillMapRequest


def test_operation_mode_default_is_safe():
    payload = {
        "session_id": "a",
        "sender": {"name": "x", "phone": "1", "address": "a", "national_code": "1234567890"},
        "receiver": {"name": "y", "phone": "2", "address": "b"},
        "origin": {"province": "p", "city": "c", "address": "a", "coordinates": {"lat": 1, "lng": 1}},
        "destination": {
            "province": "p2",
            "city": "c2",
            "address": "a2",
            "coordinates": {"lat": 2, "lng": 2},
        },
        "cargo": {"weight": 1000},
        "vehicle": {},
        "financial": {},
    }

    req = WaybillMapRequest.model_validate(payload)
    assert req.operation_mode == OperationMode.SAFE


def test_operation_mode_accepts_full():
    payload = {
        "operation_mode": "full",
        "session_id": "a",
        "sender": {"name": "x", "phone": "1", "address": "a", "national_code": "1234567890"},
        "receiver": {"name": "y", "phone": "2", "address": "b"},
        "origin": {"province": "p", "city": "c", "address": "a", "coordinates": {"lat": 1, "lng": 1}},
        "destination": {
            "province": "p2",
            "city": "c2",
            "address": "a2",
            "coordinates": {"lat": 2, "lng": 2},
        },
        "cargo": {"weight": 1000},
        "vehicle": {},
        "financial": {},
    }

    req = WaybillMapRequest.model_validate(payload)
    assert req.operation_mode == OperationMode.FULL
