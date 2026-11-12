from zivra.system.performance import Performance
from zivra.system import performance


def test_optional_sensors_do_not_disable_monitoring(monkeypatch):
    def unavailable():
        raise FileNotFoundError("No battery interface")
    monkeypatch.setattr(performance.psutil, "sensors_battery", unavailable)
    monkeypatch.setattr(performance.psutil, "net_io_counters", unavailable)
    sample = Performance().sample()
    assert sample["battery"] is None
    assert sample["network_kbps"] is None
    assert 0 <= sample["memory"] <= 100
    assert sample["disk_free_gb"] > 0
