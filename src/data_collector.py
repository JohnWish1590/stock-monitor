"""
数据采集模块：获取美股板块ETF + A股/港股实时行情
数据源：
- 美股板块：Yahoo Finance (yfinance)
- A股/港股：东方财富网API (免费，15分钟延迟)
"""

import yfinance as yf
import requests
import json
import pandas as pd
from datetime import datetime
import time

class DataCollector:
    def __init__(self):
        self.us_etfs = {
            "XLK": "Technology",
            "XLV": "Health Care", 
            "XLY": "Consumer Discretionary",
            "XLF": "Financials",
            "XLI": "Industrials",
            "XLE": "Energy",
            "XLB": "Materials",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
            "XLC": "Communication Services"
        }
        
    def get_us_sectors(self):
        """获取美股板块ETF最新数据"""
        print("📊 正在采集美股板块数据...")
        sectors_data = []
        
        for symbol, sector_name in self.us_etfs.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
                    
                    sectors_data.append({
                        "symbol": symbol,
                        "name": sector_name,
                        "price": round(latest['Close'], 2),
                        "change": round(latest['Close'] - prev['Close'], 2),
                        "change_pct": round(change_pct, 2),
                        "volume": int(latest['Volume']),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ 获取 {symbol} 失败: {e}")
                continue
                
        print(f"✅ 成功获取 {len(sectors_data)} 个美股板块数据")
        return sectors_data
    
    def get_cn_stock_data(self, stock_code, market_type='A'):
        """
        从东方财富获取A股/港股实时行情
        market_type: 'A' (A股), 'HK' (港股)
        """
        try:
            if market_type == 'A':
                if stock_code.startswith('6'):
                    secid = f"1.{stock_code.replace('.SH', '').replace('.SZ', '')}"
                else:
                    secid = f"0.{stock_code.replace('.SH', '').replace('.SZ', '')}"
            else:
                code = stock_code.replace('.HK', '')
                secid = f"116.{code}"
            
            url = f"https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170",
                "invt": 2,
                "fltt": 2
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('data'):
                d = data['data']
                price = d.get('f43', 0) / 100 if d.get('f43') else 0
                change = d.get('f44', 0) / 100 if d.get('f44') else 0
                change_pct = d.get('f170', 0) / 100 if d.get('f170') else 0
                volume = d.get('f47', 0)
                
                return {
                    'price': price,
                    'change': change,
                    'change_pct': change_pct,
                    'volume': volume,
                    'timestamp': datetime.now().strftime("%H:%M")
                }
        except Exception as e:
            print(f"⚠️ 获取 {stock_code} 失败: {e}")
            return None
    
    def get_portfolio_data(self, portfolio_config):
        """获取整个自选股的实时数据"""
        print("📈 正在采集自选股数据...")
        
        hk_data = []
        a_data = []
        
        for stock in portfolio_config['hk_stocks']:
            data = self.get_cn_stock_data(stock['code'], 'HK')
            if data:
                hk_data.append({
                    **stock,
                    **data
                })
            time.sleep(0.3)
        
        for stock in portfolio_config['a_stocks']:
            data = self.get_cn_stock_data(stock['code'], 'A')
            if data:
                a_data.append({
                    **stock,
                    **data
                })
            time.sleep(0.3)
        
        print(f"✅ 港股: {len(hk_data)}/{len(portfolio_config['hk_stocks'])} 只成功")
        print(f"✅ A股: {len(a_data)}/{len(portfolio_config['a_stocks'])} 只成功")
        
        return {
            'hk_stocks': hk_data,
            'a_stocks': a_data,
            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def collect_all(self, portfolio_config):
        """采集所有数据"""
        print(f"\n🚀 开始数据采集 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        us_sectors = self.get_us_sectors()
        portfolio = self.get_portfolio_data(portfolio_config)
        
        try:
            sp500 = yf.Ticker("^GSPC").history(period="2d")
            nasdaq = yf.Ticker("^IXIC").history(period="2d")
            
            market_summary = {
                'sp500': {
                    'price': round(sp500.iloc[-1]['Close'], 2),
                    'change_pct': round(((sp500.iloc[-1]['Close'] - sp500.iloc[-2]['Close']) / sp500.iloc[-2]['Close']) * 100, 2)
                },
                'nasdaq': {
                    'price': round(nasdaq.iloc[-1]['Close'], 2),
                    'change_pct': round(((nasdaq.iloc[-1]['Close'] - nasdaq.iloc[-2]['Close']) / nasdaq.iloc[-2]['Close']) * 100, 2)
                }
            }
        except:
            market_summary = {'sp500': {'price': 0, 'change_pct': 0}, 'nasdaq': {'price': 0, 'change_pct': 0}}
        
        return {
            'us_sectors': us_sectors,
            'portfolio': portfolio,
            'us_market': market_summary,
            'collected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
