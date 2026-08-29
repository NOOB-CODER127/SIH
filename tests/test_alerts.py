from backend.app.graph.alerts import (
    alert_night_bursts,
    alert_structuring,
    alert_layering,
)


# ============================================================
# 1. NIGHT CALL BURST TESTING
# ============================================================

def test_night_call_burst():

    # Case 1: 8 night calls -> SHOULD trigger
    rows = []

    for i in range(8):
        rows.append({
            "timestamp": f"2026-08-20 02:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    alerts = alert_night_bursts(rows)

    assert len(alerts) == 1
    assert alerts[0]["type"] == "night_call_burst"
    assert alerts[0]["severity"] == "medium"

    # Case 2: Only 7 calls -> SHOULD NOT trigger
    rows = []

    for i in range(7):
        rows.append({
            "timestamp": f"2026-08-20 02:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    alerts = alert_night_bursts(rows)

    assert len(alerts) == 0

    # Case 3: 40% night calls -> SHOULD trigger
    rows = []

    for i in range(4):
        rows.append({
            "timestamp": f"2026-08-20 02:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    for i in range(6):
        rows.append({
            "timestamp": f"2026-08-20 14:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    alerts = alert_night_bursts(rows)

    assert len(alerts) == 1

    # Case 4: 30% night calls -> SHOULD NOT trigger
    rows = []

    for i in range(3):
        rows.append({
            "timestamp": f"2026-08-20 02:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    for i in range(7):
        rows.append({
            "timestamp": f"2026-08-20 14:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333"
        })

    alerts = alert_night_bursts(rows)

    assert len(alerts) == 0


# ============================================================
# 2. STRUCTURING TESTING
# ============================================================

def test_structuring():

    rows = []

    # 5 deposits between ₹45,000 and ₹50,000
    for i in range(5):
        rows.append({
            "timestamp": f"2026-08-{20 + i} 10:00:00",
            "mode": "cash_deposit",
            "amount_inr": 49000,
            "to_account": "ACC1001"
        })

    alerts = alert_structuring(rows)

    # 5 deposits within 7 days -> SHOULD trigger
    assert len(alerts) == 1
    assert alerts[0]["type"] == "structuring"
    assert alerts[0]["severity"] == "high"


# ============================================================
# 3. LAYERING / MULTI-HOP TESTING
# ============================================================

def test_layering():

    rows = [
        {
            "timestamp": "2026-08-20 10:00:00",
            "from_account": "ACC1001",
            "to_account": "ACC2001",
            "amount_inr": 50000
        },
        {
            "timestamp": "2026-08-20 15:00:00",
            "from_account": "ACC2001",
            "to_account": "ACC3001",
            "amount_inr": 45000
        }
    ]

    alerts = alert_layering(rows)

    # 2-hop movement within 24 hours
    # 90% of money retained -> SHOULD trigger
    assert len(alerts) == 1
    assert alerts[0]["type"] == "layering"
    assert alerts[0]["severity"] == "medium"