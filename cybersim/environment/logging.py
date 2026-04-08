from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class LogFactory:
    start_time: datetime

    def _ts(self, tick: int) -> str:
        return (self.start_time + timedelta(seconds=tick * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def auth(self, tick: int, host: str, src_ip: str, user: str, status: str) -> str:
        return (
            f"{self._ts(tick)} auth host={host} src_ip={src_ip} user={user} "
            f"service=ssh status={status}"
        )

    def network(
        self, tick: int, src_host: str, dst: str, dst_port: int, protocol: str, bytes_sent: int, note: str
    ) -> str:
        return (
            f"{self._ts(tick)} net src_host={src_host} dst={dst}:{dst_port} protocol={protocol} "
            f"bytes_sent={bytes_sent} note={note}"
        )

    def process(self, tick: int, host: str, proc: str, pid: int, action: str, parent: str = "systemd") -> str:
        return (
            f"{self._ts(tick)} proc host={host} pid={pid} process={proc} parent={parent} action={action}"
        )

