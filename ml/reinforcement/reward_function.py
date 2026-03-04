class RewardFunction:
    @staticmethod
    def booking_reward(price: float, occupancy_probability: float) -> float:
        return price * occupancy_probability

    @staticmethod
    def conversion_reward(booked: bool, price: float, days_to_booking: int) -> float:
        if not booked:
            return 0.0
        time_bonus = max(0.0, 1.0 - days_to_booking / 30.0)
        return price * (1.0 + time_bonus * 0.2)

    @staticmethod
    def revenue_reward(price: float, booked: bool) -> float:
        return price if booked else 0.0
