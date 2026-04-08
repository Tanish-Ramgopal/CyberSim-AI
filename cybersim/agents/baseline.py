from __future__ import annotations

import re
from collections import Counter

from cybersim.models import Action, Observation

from .base import BaseAgent


class BaselineDefenseAgent(BaseAgent):
    name = "baseline"

    def act(self, observation: Observation) -> Action:
        if self._should_raise_alert(observation):
            return Action(action_type="raise_alert", target=observation.task_name)

        brute_force_ip = self._detect_brute_force(observation)
        if brute_force_ip and brute_force_ip not in observation.blocked_ips:
            return Action(action_type="block_ip", target=brute_force_ip)

        malware_proc = self._detect_malware_process(observation)
        if malware_proc:
            return Action(action_type="kill_process", target=malware_proc)

        exfil_host = self._detect_exfil_host(observation)
        if exfil_host and exfil_host not in observation.isolated_hosts:
            return Action(action_type="isolate_machine", target=exfil_host)

        return Action(action_type="noop", target="none")

    def _detect_brute_force(self, observation: Observation) -> str | None:
        failed_ips: Counter[str] = Counter()
        for line in observation.recent_auth_logs:
            if "status=failed" in line:
                match = re.search(r"src_ip=([0-9.]+)", line)
                if match:
                    failed_ips[match.group(1)] += 1
        for ip, count in failed_ips.items():
            if count >= 3:
                return ip
        return None

    def _detect_malware_process(self, observation: Observation) -> str | None:
        suspicious_names = ("encryptor", "wanna", "ransom", "locker", "stealer")
        for line in reversed(observation.recent_process_logs):
            for name in suspicious_names:
                if f"process={name}" in line:
                    return name
            if "action=spawn" in line and "parent=wmic" in line:
                match = re.search(r"process=([a-zA-Z0-9_.-]+)", line)
                if match:
                    return match.group(1)
        return None

    def _detect_exfil_host(self, observation: Observation) -> str | None:
        for line in reversed(observation.recent_network_logs):
            if "note=bulk_transfer" not in line:
                continue
            bytes_match = re.search(r"bytes_sent=([0-9]+)", line)
            host_match = re.search(r"src_host=([a-zA-Z0-9_.-]+)", line)
            if bytes_match and host_match and int(bytes_match.group(1)) > 2_000_000:
                return host_match.group(1)
        return None

    def _should_raise_alert(self, observation: Observation) -> bool:
        if any("message=agent_alert" in a for a in observation.alerts):
            return False
        suspicious = 0
        for line in observation.recent_network_logs:
            if "dns_reconnaissance" in line or "periodic_beacon" in line:
                suspicious += 1
        for line in observation.recent_process_logs:
            if "credharvest" in line:
                suspicious += 2
        return suspicious >= 2

