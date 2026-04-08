from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from cybersim.models import Action, Observation

from .base import BaseAgent


class UNSWModelDefenseAgent(BaseAgent):
    name = "unsw_model"

    def __init__(self) -> None:
        self._fallback_threshold = 0.55
        self._model: Any = None
        self._feature_columns: list[str] = []
        self._load_model_bundle()

    def _load_model_bundle(self) -> None:
        model_path = (
            Path(__file__).resolve().parents[2] / "artifacts" / "unsw_nb15" / "unsw_nb15_binary_hgb.joblib"
        )
        if not model_path.exists():
            return
        bundle = joblib.load(model_path)
        self._model = bundle.get("model")
        self._feature_columns = bundle.get("feature_columns", [])

    def act(self, observation: Observation) -> Action:
        if self._should_raise_alert(observation):
            return Action(action_type="raise_alert", target=observation.task_name)
        risk = self._estimate_risk(observation)

        brute_force_ip = self._detect_brute_force(observation)
        if brute_force_ip and brute_force_ip not in observation.blocked_ips:
            return Action(action_type="block_ip", target=brute_force_ip, metadata={"risk": risk})

        malware_proc = self._detect_malware_process(observation)
        if malware_proc:
            return Action(action_type="kill_process", target=malware_proc, metadata={"risk": risk})

        exfil_host = self._detect_exfil_host(observation)
        if exfil_host and exfil_host not in observation.isolated_hosts:
            return Action(action_type="isolate_machine", target=exfil_host, metadata={"risk": risk})

        if risk >= self._fallback_threshold:
            return Action(action_type="raise_alert", target=observation.task_name, metadata={"risk": risk})
        return Action(action_type="noop", target="none", metadata={"risk": risk})

    def _should_raise_alert(self, observation: Observation) -> bool:
        if any("message=agent_alert" in a for a in observation.alerts):
            return False
        return any("dns_reconnaissance" in l for l in observation.recent_network_logs) or any(
            "credharvest" in l for l in observation.recent_process_logs
        )

    def _estimate_risk(self, observation: Observation) -> float:
        if self._model is None or not self._feature_columns:
            return 0.0

        row = {col: 0 for col in self._feature_columns}
        last_auth = observation.recent_auth_logs[-1] if observation.recent_auth_logs else ""
        last_net = observation.recent_network_logs[-1] if observation.recent_network_logs else ""

        src_ip = self._extract(last_auth, r"src_ip=([0-9.]+)") or self._extract(last_net, r"dst=([0-9.]+)")
        dst_ip = self._extract(last_net, r"dst=([0-9.]+)") or "0.0.0.0"
        proto = self._extract(last_net, r"protocol=([a-zA-Z0-9]+)") or "tcp"

        row["srcip"] = src_ip or "0.0.0.0"
        row["dstip"] = dst_ip
        row["proto"] = proto
        row["state"] = "CON"
        row["service"] = "ssh"
        row["spkts"] = len(observation.recent_network_logs)
        row["dpkts"] = len(observation.recent_network_logs)
        row["ct_srv_src"] = len(observation.recent_process_logs)
        row["ct_src_ltm"] = len(observation.recent_auth_logs)
        row["ct_state_ttl"] = len([l for l in observation.recent_auth_logs if "failed" in l])
        row["sbytes"] = self._extract_int(last_net, r"bytes_sent=([0-9]+)")
        row["dbytes"] = self._extract_int(last_net, r"bytes_sent=([0-9]+)")

        df = pd.DataFrame([row], columns=self._feature_columns)
        df = self._preprocess_features(df)
        prob = float(self._model.predict_proba(df)[:, 1][0])
        return round(prob, 4)

    @staticmethod
    def _preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in ["srcip", "dstip"]:
            if col in out:
                out[col] = pd.util.hash_pandas_object(out[col].astype(str), index=False).astype("uint64") % 1_000_003
        for col in ["proto", "state", "service"]:
            if col in out:
                out[col] = out[col].astype("category").cat.codes
        for col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        return out.fillna(0)

    @staticmethod
    def _extract(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_int(text: str, pattern: str) -> int:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else 0

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
        for line in reversed(observation.recent_process_logs):
            if "process=encryptor" in line:
                return "encryptor"
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

