from domain.value_objects.location import Location
from domain.value_objects.price import Price


class TestLocation:
    def test_distance_same_point(self):
        loc = Location(lat=47.6301, lng=13.0044)
        assert loc.distance_km(loc) == 0.0

    def test_distance_within_radius(self):
        center = Location(lat=47.6301, lng=13.0044)
        nearby = Location(lat=47.6320, lng=13.0050)
        assert center.distance_km(nearby) < 5.0

    def test_is_within_radius(self):
        center = Location(lat=47.6301, lng=13.0044)
        nearby = Location(lat=47.6310, lng=13.0020)
        assert nearby.is_within_radius(center, 5.0)

    def test_is_outside_radius(self):
        center = Location(lat=47.6301, lng=13.0044)
        far_away = Location(lat=48.0, lng=13.5)
        assert not far_away.is_within_radius(center, 5.0)


class TestPrice:
    def test_create_price(self):
        price = Price(amount=100.0)
        assert price.amount == 100.0
        assert price.currency == "EUR"

    def test_adjust_price(self):
        price = Price(amount=100.0)
        adjusted = price.adjust(1.2)
        assert adjusted.amount == 120.0

    def test_negative_price_raises(self):
        try:
            Price(amount=-10.0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
