import time
from pathlib import Path
import psutil


class Performance:
    def __init__(self):
        self.previous_network = None

    def sample(self):
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.home().anchor)
        try:
            battery = psutil.sensors_battery()
        except (OSError, NotImplementedError):
            battery = None
        try:
            network = psutil.net_io_counters()
        except (OSError, NotImplementedError):
            network = None
        now = time.monotonic()
        rate = None
        if network and self.previous_network:
            then, total = self.previous_network
            rate = max(0, (network.bytes_sent + network.bytes_recv - total) / max(now - then, 0.001))
        if network:
            self.previous_network = (now, network.bytes_sent + network.bytes_recv)
        return {"cpu": psutil.cpu_percent(interval=0.1), "memory": memory.percent,
                "available_gb": memory.available / 1024**3, "disk_free_gb": disk.free / 1024**3,
                "network_kbps": rate / 1024 if rate is not None else None,
                "battery": battery.percent if battery else None,
                "rss_mb": psutil.Process().memory_info().rss / 1024**2}


def system_report():
    metrics = Performance().sample()
    lines = [f"RAM: {metrics['memory']:.0f}% • available {metrics['available_gb']:.1f} GB",
             f"Disk free: {metrics['disk_free_gb']:.1f} GB", "Largest visible processes by resident memory:"]
    processes = []
    for process in psutil.process_iter(["name", "memory_info"]):
        try:
            info = process.info
            if info["memory_info"]:
                processes.append((info["memory_info"].rss, info["name"] or "Unknown"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    lines.extend(f"  {name}: {rss / 1024**2:.1f} MB" for rss, name in sorted(processes, reverse=True)[:5])
    return "\n".join(lines)
