from __future__ import annotations

from abc import ABC, abstractmethod

from cybersim.models import Action, Observation


class BaseAgent(ABC):
    name = "base"

    @abstractmethod
    def act(self, observation: Observation) -> Action:
        raise NotImplementedError

