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

2027Q2 REVENUE - 11345000000.0 --> 11345000000.0                                                                                                                    
2027Q2 FREE_CASH_FLOW - 1098000000.0 --> 1098000000.0                                                                                                               
2027Q2 TOTAL_DEBT - 41743000000.0 --> 41743000000.0                                                                                                                 
2027Q2 CASH_AND_EQ - 8310000000.0 --> 8310000000.0                                                                                                                  
2027Q2 INTEREST - 473000000.0 --> 473000000.0                                                                                                                       
2027Q2 SHORT_TERM_DEBT - 0.0 --> 0.0                                                                                                                                
2027Q2 OPERATING_CASH_FLOW - 1269000000.0 --> 1269000000.0                                                                                                          
2027Q2 INCOME_TAX_EXPENSE - 1026000000.0 --> 1026000000.0                                                                                                           
2027Q2 EBITDA - 5025000000.0 --> 5025000000.0                                                                                                                       

2027Q1 REVENUE - 11133000000.0 --> 22478000000.0                                                                                                                    
2027Q1 FREE_CASH_FLOW - 6556000000.0 --> 7654000000.0                                                                                                               
2027Q1 TOTAL_DEBT - 41884000000.0 --> 41743000000.0                                                                                                                 
2027Q1 CASH_AND_EQ - 8935000000.0 --> 8310000000.0                                                                                                                  
2027Q1 INTEREST - 317000000.0 --> 790000000.0                                                                                                                       
2027Q1 SHORT_TERM_DEBT - 0.0 --> 0.0                                                                                                                                
2027Q1 OPERATING_CASH_FLOW - 6701000000.0 --> 7970000000.0                                                                                                          
2027Q1 INCOME_TAX_EXPENSE - 614000000.0 --> 1640000000.0                                                                                                            
2027Q1 EBITDA - 4023000000.0 --> 9048000000.0                                                                                                                       

2026Q4 REVENUE - 11201000000.0 --> 33679000000.0                                                                                                                    
2026Q4 FREE_CASH_FLOW - 5323000000.0 --> 12977000000.0                                                                                                              
2026Q4 TOTAL_DEBT - 17176000000.0 --> 41743000000.0                                                                                                                 
2026Q4 CASH_AND_EQ - 7327000000.0 --> 8310000000.0                                                                                                                  
2026Q4 INTEREST - 0.0 --> 790000000.0                                                                                                                               
2026Q4 SHORT_TERM_DEBT - 4000000000.0 --> 0.0                                                                                                                       
2026Q4 OPERATING_CASH_FLOW - 5464000000.0 --> 13434000000.0                                                                                                         
2026Q4 INCOME_TAX_EXPENSE - 685000000.0 --> 2325000000.0                                                                                                            
2026Q4 EBITDA - 3748000000.0 --> 12796000000.0                                                                                                                      

2026Q3 REVENUE - 10259000000.0 --> 43938000000.0                                                                                                                    
2026Q3 FREE_CASH_FLOW - 2177000000.0 --> 15154000000.0                                                                                                              
2026Q3 TOTAL_DEBT - 11139000000.0 --> 41743000000.0                                                                                                                 
2026Q3 CASH_AND_EQ - 8978000000.0 --> 8310000000.0                                                                                                                  
2026Q3 INTEREST - 67000000.0 --> 857000000.0                                                                                                                        
2026Q3 SHORT_TERM_DEBT - 0.0 --> 0.0                                                                                                                                
2026Q3 OPERATING_CASH_FLOW - 2316000000.0 --> 15750000000.0
2026Q3 INCOME_TAX_EXPENSE - 426000000.0 --> 2751000000.0
2026Q3 EBITDA - 3005000000.0 --> 15801000000.0
           
income_tax_expense q: 2751000000.0 y: 2063000000 1.33 
revenue q: 43938000000.0 y: 41525000000 1.06 
ebitda q: 15801000000.0 y: 13151000000 1.20 
free_cash_flow q: 15154000000.0 y: 14402000000 1.05 
debt q: 41743000000.0 y: 17176000000 2.43  
total_debt q: 41743000000.0 y: 17176000000 2.43 
net_debt q: 33433000000.0 y: 9849000000 3.39 
interest q: 857000000.0 y: 324000000 2.65  
operating_cash_flow q: 15750000000.0 y: 14996000000 1.05 
short_term_debt q: 0.0 y: 4000000000 0.00  

"""

