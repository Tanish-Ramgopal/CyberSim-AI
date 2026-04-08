from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List, Tuple

from cybersim.models import Action, Observation, Reward

from .logging import LogFactory


class SimulationEnvironment:
    def __init__(self, task_config: Dict[str, Any], seed: int = 42) -> None:
        self.task_config = task_config
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_ticks = int(task_config.get("max_ticks", 20))
        self.tick = 0

        self.alerts: List[str] = []
        self.auth_logs: List[str] = []
        self.network_logs: List[str] = []
        self.process_logs: List[str] = []
        self.blocked_ips: set[str] = set()
        self.isolated_hosts: set[str] = set()
        self.killed_processes: set[str] = set()

        self.metrics: Dict[str, Any] = {
            "attack_detected": False,
            "mitigated": False,
            "first_response_tick": None,
            "correct_actions": 0,
            "false_positives": 0,
            "wrong_actions": 0,
            "decoy_hits": 0,
            "stage_misses": 0,
            "actions_taken": [],
        }
        self._threat_active = True
        self._init_attack_state()
        self.log_factory = LogFactory(start_time=datetime(2026, 4, 8, 12, 0, 0))

    def _init_attack_state(self) -> None:
        attack = self.task_config["attack_type"]
        if attack == "brute_force":
            self.attack_state = {
                "attacker_ip": self.task_config["attack"]["attacker_ip"],
                "target_host": self.task_config["attack"]["target_host"],
                "target_user": self.task_config["attack"]["target_user"],
                "failures": 0,
                "compromised": False,
            }
        elif attack == "malware_spread":
            self.attack_state = {
                "seed_host": self.task_config["attack"]["seed_host"],
                "infected_hosts": {self.task_config["attack"]["seed_host"]},
                "malware_process": self.task_config["attack"]["malware_process"],
                "lateral_targets": list(self.task_config["attack"]["lateral_targets"]),
                "lateral_interval_ticks": int(self.task_config["attack"].get("lateral_interval_ticks", 2)),
                "noise_hosts": list(self.task_config["attack"].get("noise_hosts", [])),
                "noise_processes": list(self.task_config["attack"].get("noise_processes", [])),
                "noise_events_per_tick": int(self.task_config["attack"].get("noise_events_per_tick", 0)),
            }
        elif attack == "data_exfiltration":
            self.attack_state = {
                "compromised_host": self.task_config["attack"]["compromised_host"],
                "destination": self.task_config["attack"]["destination"],
                "beacon_every_ticks": int(self.task_config["attack"]["beacon_every_ticks"]),
                "exfil_started": False,
                "stage": 0,
                "required_stage": int(self.task_config["attack"].get("required_stage", 1)),
                "decoy_hosts": list(self.task_config["attack"].get("decoy_hosts", [])),
                "fallback_host": self.task_config["attack"].get("fallback_host", self.task_config["attack"]["compromised_host"]),
            }
        else:
            raise ValueError(f"Unknown attack type: {attack}")

    def reset(self) -> Observation:
        self.tick = 0
        self.rng = random.Random(self.seed)
        self.alerts = []
        self.auth_logs = []
        self.network_logs = []
        self.process_logs = []
        self.blocked_ips = set()
        self.isolated_hosts = set()
        self.killed_processes = set()
        self.metrics = {
            "attack_detected": False,
            "mitigated": False,
            "first_response_tick": None,
            "correct_actions": 0,
            "false_positives": 0,
            "wrong_actions": 0,
            "decoy_hits": 0,
            "stage_misses": 0,
            "alert_raised": False,
            "actions_taken": [],
            "reward_total": 0.0,
            "difficulty": self.task_config.get("difficulty", "medium"),
        }
        self._threat_active = True
        self._init_attack_state()
        return self._build_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self._apply_agent_action(action)
        self._generate_attack_activity()
        reward = self._compute_step_reward(action)
        self.tick += 1

        success = self._goal_reached()
        done = success or self.tick >= self.max_ticks
        if done and not success:
            self._threat_active = True
        info = {"metrics": self.metrics.copy(), "success": success}
        return self._build_observation(), reward, done, info

    def _apply_agent_action(self, action: Action) -> None:
        if action.action_type == "noop":
            return

        self.metrics["actions_taken"].append({"tick": self.tick, "action": action.action_type, "target": action.target})
        if self.metrics["first_response_tick"] is None:
            self.metrics["first_response_tick"] = self.tick

        attack = self.task_config["attack_type"]
        target = action.target
        valid = False

        if action.action_type == "block_ip":
            self.blocked_ips.add(target)
            if attack == "brute_force" and target == self.attack_state["attacker_ip"]:
                valid = True
                self.metrics["attack_detected"] = True
                self.metrics["mitigated"] = True
                self._threat_active = False
        elif action.action_type == "kill_process":
            self.killed_processes.add(target)
            if attack == "malware_spread" and target == self.attack_state["malware_process"]:
                valid = True
                self.metrics["attack_detected"] = True
                self.metrics["mitigated"] = True
                self._threat_active = False
        elif action.action_type == "isolate_machine":
            self.isolated_hosts.add(target)
            if attack in {"malware_spread", "data_exfiltration"}:
                expected = (
                    self.attack_state.get("seed_host")
                    if attack == "malware_spread"
                    else self.attack_state.get("compromised_host")
                )
                if attack == "data_exfiltration" and target == expected and self.attack_state.get("stage", 0) < 2:
                    # Wrong path: isolate too early and attacker pivots.
                    self.alerts.append(
                        f"tick={self.tick} severity=medium message=premature_isolation target={target} consequence=attacker_pivot"
                    )
                    self.attack_state["compromised_host"] = self.attack_state.get("fallback_host", expected)
                    self.attack_state["stage"] = 2
                    self.metrics["stage_misses"] += 1
                elif target == expected:
                    if attack == "data_exfiltration" and not self.metrics.get("alert_raised", False):
                        self.metrics["stage_misses"] += 1
                    else:
                        valid = True
                        self.metrics["attack_detected"] = True
                        self.metrics["mitigated"] = True
                        self._threat_active = False
                elif attack == "data_exfiltration" and target in self.attack_state.get("decoy_hosts", []):
                    self.metrics["decoy_hits"] += 1
        elif action.action_type == "raise_alert":
            self.alerts.append(f"tick={self.tick} severity=high message=agent_alert target={target}")
            valid = True
            self.metrics["attack_detected"] = True
            self.metrics["alert_raised"] = True

        if valid:
            self.metrics["correct_actions"] += 1
        else:
            self.metrics["false_positives"] += 1
            self.metrics["wrong_actions"] += 1

    def _generate_attack_activity(self) -> None:
        if not self._threat_active:
            return

        attack = self.task_config["attack_type"]
        if attack == "brute_force":
            self._generate_brute_force()
        elif attack == "malware_spread":
            self._generate_malware_spread()
        elif attack == "data_exfiltration":
            self._generate_data_exfiltration()

    def _generate_brute_force(self) -> None:
        ip = self.attack_state["attacker_ip"]
        host = self.attack_state["target_host"]
        user = self.attack_state["target_user"]
        if ip in self.blocked_ips:
            self.auth_logs.append(self.log_factory.auth(self.tick, host, ip, user, "blocked"))
            return

        self.attack_state["failures"] += 1
        self.auth_logs.append(self.log_factory.auth(self.tick, host, ip, user, "failed"))
        if self.attack_state["failures"] >= int(self.task_config["attack"]["success_after_failures"]):
            self.attack_state["compromised"] = True
            self.auth_logs.append(self.log_factory.auth(self.tick, host, ip, user, "success"))

    def _generate_malware_spread(self) -> None:
        proc = self.attack_state["malware_process"]
        seed_host = self.attack_state["seed_host"]
        if proc not in self.killed_processes:
            self.process_logs.append(self.log_factory.process(self.tick, seed_host, proc, 31337, "spawn"))

        if seed_host in self.isolated_hosts:
            return

        lateral_interval = max(1, int(self.attack_state.get("lateral_interval_ticks", 2)))
        if self.tick > 0 and self.tick % lateral_interval == 0 and self.attack_state["lateral_targets"]:
            target = self.attack_state["lateral_targets"].pop(0)
            self.attack_state["infected_hosts"].add(target)
            self.network_logs.append(
                self.log_factory.network(self.tick, seed_host, target, 445, "tcp", 48000, "smb_lateral_movement")
            )
            self.process_logs.append(self.log_factory.process(self.tick, target, proc, 31337, "spawn", "wmic"))

        # Add realistic noise to make medium difficulty less trivial.
        noise_events = self.attack_state.get("noise_events_per_tick", 0)
        for _ in range(noise_events):
            if not self.attack_state.get("noise_hosts"):
                break
            host = self.rng.choice(self.attack_state["noise_hosts"])
            nproc = self.rng.choice(self.attack_state.get("noise_processes", ["updaterd"]))
            self.process_logs.append(self.log_factory.process(self.tick, host, nproc, self.rng.randint(1100, 9000), "spawn"))
            self.network_logs.append(
                self.log_factory.network(
                    self.tick,
                    host,
                    "repo.internal.corp",
                    443,
                    "https",
                    self.rng.randint(4_000, 45_000),
                    "benign_update_noise",
                )
            )

    def _generate_data_exfiltration(self) -> None:
        host = self.attack_state["compromised_host"]
        if host in self.isolated_hosts:
            return

        destination = self.attack_state["destination"]
        beacon_every = self.attack_state["beacon_every_ticks"]

        if self.tick % beacon_every == 0:
            self.network_logs.append(
                self.log_factory.network(self.tick, host, destination, 443, "https", 1200, "periodic_beacon")
            )
        if self.tick >= 2 and self.attack_state["stage"] < 1:
            self.attack_state["stage"] = 1
            self.network_logs.append(
                self.log_factory.network(self.tick, host, "10.10.4.23", 53, "udp", 9800, "dns_reconnaissance")
            )
        if self.tick >= 4 and self.attack_state["stage"] < 2:
            self.attack_state["stage"] = 2
            self.process_logs.append(self.log_factory.process(self.tick, host, "credharvest", 4133, "spawn", "python"))
        if self.tick >= 6:
            self.attack_state["stage"] = 3
            self.attack_state["exfil_started"] = True
            bytes_sent = 4_000_000 + self.rng.randint(0, 500_000)
            self.network_logs.append(
                self.log_factory.network(self.tick, host, destination, 443, "https", bytes_sent, "bulk_transfer")
            )

        # Decoy path: alternate hosts produce misleading outbound traffic.
        for decoy in self.attack_state.get("decoy_hosts", []):
            if self.tick % 3 == 0:
                decoy_bytes = 1_600_000 + self.rng.randint(0, 1_200_000)
                self.network_logs.append(
                    self.log_factory.network(self.tick, decoy, destination, 443, "https", decoy_bytes, "decoy_transfer")
                )

    def _compute_step_reward(self, action: Action) -> Reward:
        components = {
            "progress": 0.0,
            "efficiency_penalty": 0.0,
            "false_positive_penalty": 0.0,
            "threat_penalty": 0.0,
        }
        reason = "no significant change"

        if action.action_type != "noop":
            components["efficiency_penalty"] = -0.01

        if self.metrics["false_positives"] > 0 and action.action_type != "noop":
            components["false_positive_penalty"] = -0.2
            reason = "invalid action penalty"

        if self.metrics["correct_actions"] > 0 and action.action_type != "noop":
            components["progress"] = 0.25
            reason = "correct defensive action"

        if self._threat_active:
            components["threat_penalty"] = -0.04
        if action.action_type == "noop" and self._threat_active:
            components["threat_penalty"] -= 0.02

        if self._goal_reached():
            components["progress"] += 0.5
            reason = "goal achieved"

        value = sum(components.values())
        value = max(-1.0, min(1.0, round(value, 4)))
        self.metrics["reward_total"] = round(self.metrics["reward_total"] + value, 4)
        return Reward(value=value, components=components, reason=reason)

    def _goal_reached(self) -> bool:
        attack = self.task_config["attack_type"]
        if attack == "brute_force":
            return self.attack_state["attacker_ip"] in self.blocked_ips and self.attack_state["failures"] <= 10
        if attack == "malware_spread":
            return (
                self.attack_state["malware_process"] in self.killed_processes
                or self.attack_state["seed_host"] in self.isolated_hosts
            )
        if attack == "data_exfiltration":
            return (
                self.attack_state["compromised_host"] in self.isolated_hosts
                and self.attack_state.get("stage", 0) >= self.attack_state.get("required_stage", 1)
            )
        return False

    def _build_observation(self) -> Observation:
        auth_logs = self.auth_logs[-8:]
        network_logs = self.network_logs[-8:]
        process_logs = self.process_logs[-8:]

        # Partial observability in medium task: only recent subset visible.
        if self.task_config["attack_type"] == "malware_spread":
            network_logs = network_logs[-4:]
            process_logs = process_logs[-4:]

        auth_logs = self._noisy_view(auth_logs, drop_rate=0.1, shuffle_prob=0.2)
        network_logs = self._noisy_view(network_logs, drop_rate=0.15, shuffle_prob=0.35)
        process_logs = self._noisy_view(process_logs, drop_rate=0.12, shuffle_prob=0.25)

        if self.task_config["attack_type"] == "data_exfiltration" and self.tick % 2 == 1:
            network_logs = network_logs + [
                self.log_factory.network(
                    self.tick,
                    self.rng.choice(self.attack_state.get("decoy_hosts", ["backup-srv-01"])),
                    self.attack_state.get("destination", "198.51.100.44"),
                    443,
                    "https",
                    self.rng.randint(1_500_000, 3_200_000),
                    "decoy_transfer",
                )
            ]

        return Observation(
            tick=self.tick,
            max_ticks=self.max_ticks,
            task_name=self.task_config["task_name"],
            recent_auth_logs=auth_logs,
            recent_network_logs=network_logs,
            recent_process_logs=process_logs,
            alerts=self.alerts[-8:],
            blocked_ips=sorted(self.blocked_ips),
            isolated_hosts=sorted(self.isolated_hosts),
            active_threat=bool(self.rng.random() > 0.25),
            possible_threats=["credential_abuse", "malware_activity", "outbound_anomaly"],
            objective=self.task_config["goal"],
        )

    def _noisy_view(self, logs: List[str], drop_rate: float, shuffle_prob: float) -> List[str]:
        if not logs:
            return logs
        kept = [line for line in logs if self.rng.random() > drop_rate]
        if not kept:
            kept = logs[-2:]
        if self.rng.random() < shuffle_prob:
            self.rng.shuffle(kept)
        return kept[-8:]

    def state(self) -> Dict[str, Any]:
        attack_state = {}
        for key, value in self.attack_state.items():
            if isinstance(value, set):
                attack_state[key] = sorted(value)
            else:
                attack_state[key] = value
        return {
            "tick": self.tick,
            "max_ticks": self.max_ticks,
            "blocked_ips": sorted(self.blocked_ips),
            "isolated_hosts": sorted(self.isolated_hosts),
            "killed_processes": sorted(self.killed_processes),
            "metrics": self.metrics.copy(),
            "threat_active": self._threat_active,
            "attack_state": attack_state,
        }

    def export_all_logs(self) -> Dict[str, List[str]]:
        return {
            "auth_logs": self.auth_logs.copy(),
            "network_logs": self.network_logs.copy(),
            "process_logs": self.process_logs.copy(),
            "alerts": self.alerts.copy(),
        }

    def close(self) -> None:
        return None

