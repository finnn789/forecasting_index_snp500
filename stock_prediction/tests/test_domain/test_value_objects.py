"""Tests untuk domain value objects: DateRange dan TickerSymbol."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.value_objects import DateRange, TickerSymbol
from app.core.settings import settings


class TestDateRange:
    def test_valid_date_range(self):
        dr = DateRange(start=date(2020, 1, 1), end=date(2024, 1, 1))
        assert dr.start == date(2020, 1, 1)
        assert dr.end == date(2024, 1, 1)

    def test_date_range_validation_end_before_start(self):
        with pytest.raises(ValidationError):
            DateRange(start=date(2024, 1, 1), end=date(2020, 1, 1))

    def test_date_range_same_start_end(self):
        dr = DateRange(start=date(2022, 6, 1), end=date(2022, 6, 1))
        assert dr.start == dr.end

    def test_date_range_contains_true(self):
        dr = DateRange(start=date(2020, 1, 1), end=date(2024, 12, 31))
        assert dr.contains(date(2022, 6, 15)) is True

    def test_date_range_contains_false(self):
        dr = DateRange(start=date(2020, 1, 1), end=date(2024, 12, 31))
        assert dr.contains(date(2019, 12, 31)) is False
        assert dr.contains(date(2025, 1, 1)) is False

    def test_date_range_contains_boundary(self):
        dr = DateRange(start=date(2020, 1, 1), end=date(2024, 12, 31))
        assert dr.contains(date(2020, 1, 1)) is True
        assert dr.contains(date(2024, 12, 31)) is True

    def test_date_range_from_settings(self):
        dr = DateRange.from_settings()
        expected_start = date.fromisoformat(settings.data_filter_start)
        expected_end = date.fromisoformat(settings.data_filter_end)
        assert dr.start == expected_start
        assert dr.end == expected_end

    def test_to_pandas_query(self):
        dr = DateRange(start=date(2018, 1, 2), end=date(2024, 3, 4))
        start_str, end_str = dr.to_pandas_query()
        assert start_str == "2018-01-02"
        assert end_str == "2024-03-04"

    def test_frozen(self):
        dr = DateRange(start=date(2020, 1, 1), end=date(2024, 1, 1))
        with pytest.raises(Exception):
            dr.start = date(2021, 1, 1)


class TestTickerSymbol:
    def test_valid_ticker(self):
        t = TickerSymbol(symbol="AAPL")
        assert t.symbol == "AAPL"

    def test_ticker_uppercase(self):
        t = TickerSymbol(symbol="gspc")
        assert t.symbol == "GSPC"

    def test_ticker_with_dot(self):
        t = TickerSymbol(symbol="BRK.B")
        assert t.symbol == "BRK.B"

    def test_ticker_invalid_chars(self):
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="INVALID TICKER!")

    def test_ticker_too_long(self):
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="TOOLONGSYMBOL")

    def test_ticker_empty(self):
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="")

    def test_ticker_str(self):
        t = TickerSymbol(symbol="MSFT")
        assert str(t) == "MSFT"

    def test_default_ticker(self):
        assert TickerSymbol.DEFAULT.symbol == "GSPC"

    def test_frozen(self):
        t = TickerSymbol(symbol="AAPL")
        with pytest.raises(Exception):
            t.symbol = "MSFT"
