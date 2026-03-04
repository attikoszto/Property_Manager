from collections import defaultdict

import numpy as np

from core.constants import PRICE_MULTIPLIER_OPTIONS


class MultiArmedBandit:
    """Epsilon-greedy multi-armed bandit for price multiplier selection.

    Training signals come exclusively from internal booking data
    (conversions, revenue, time-to-booking). External competitor
    pricing must not be used as a reward signal.
    """

    def __init__(self, arms: list[float] | None = None, epsilon: float = 0.1):
        self.arms = arms or PRICE_MULTIPLIER_OPTIONS
        self.epsilon = epsilon
        self.counts: dict[float, int] = defaultdict(int)
        self.values: dict[float, float] = defaultdict(float)

    def select_arm(self) -> float:
        if np.random.random() < self.epsilon:
            return float(np.random.choice(self.arms))

        best_arm = self.arms[0]
        best_value = -float("inf")
        for arm in self.arms:
            if self.counts[arm] == 0:
                return arm
            if self.values[arm] > best_value:
                best_value = self.values[arm]
                best_arm = arm

        return best_arm

    def update(self, arm: float, reward: float) -> None:
        self.counts[arm] += 1
        n = self.counts[arm]
        self.values[arm] += (reward - self.values[arm]) / n

    def get_stats(self) -> dict[float, dict]:
        return {
            arm: {"count": self.counts[arm], "avg_reward": round(self.values[arm], 4)}
            for arm in self.arms
        }
