# -*- coding: utf-8 -*-

import adata


class Stock:
    def __init__(self):
        pass

    def fund_etf(self,code):
        res_df = adata.fund.market.get_market_etf_current(fund_code=code)
        return res_df
    def fund_realtime_stock(self,code_list):
        res_df = adata.stock.market.list_market_current(code_list=code_list)
        return res_df