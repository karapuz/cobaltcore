"""Tests for the per-entity velocity store.  Run: python -m pytest test_velocity_store.py -q"""

import json
import os
import tempfile

from unittest import main, TestCase

import app.data.compass_access as compass_access

class Test(TestCase):
    def test_get_data(self):
        symbol, year, attributes = "CRM", "2025", []
        compass_access.env_name = "20260920"
        ttm_data = compass_access.getdata(symbol, year)
        annual_data = compass_access.getdata(symbol, year, ttm=False)

        for attr, val in ttm_data.items():
            if annual_data[attr]:
                print(f"{attr} q: {val} y: {annual_data[attr]} {val/annual_data[attr]:.2f} ")
            else:
                print(f"{attr} q: {val} y: {annual_data[attr]} {val}/0 [Zero Val-]")


if __name__ == "__main__":
    main()

"""
python tests/unittests/test_compass_access.py
"""

