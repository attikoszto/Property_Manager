from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    amount: float
    currency: str = "EUR"

    def adjust(self, factor: float) -> "Price":
        return Price(amount=round(self.amount * factor, 2), currency=self.currency)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative")
