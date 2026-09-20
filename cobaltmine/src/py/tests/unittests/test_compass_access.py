"""Tests for the per-entity velocity store.  Run: python -m pytest test_velocity_store.py -q"""

import json
import os
import tempfile

from unittest import main, TestCase

import app.data.compass_access as compass_access

class Test(TestCase):
    def test_get_data(self):
        symbol, year, attributes = "AAPL", "2025", []
        data = compass_access.getdata(symbol, year, attributes)
        print(data)

if __name__ == "__main__":
    main()

"""
python tests/unittests/test_compass_access.py
"""

