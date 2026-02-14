import yfinance as yf
import pandas as pd
from datetime import datetime
import time

class DataCollector:
    def __init__(self):
        # 你的美股板块映射
        self.us_etfs = {
            "XLK": "科技(映射小米/芯片)",
            "XLY": "可选消费(映射汽车/家电)",
            "XLV": "医疗(映射医药)",
            "XLC": "通讯(映射互联网)",
            "KWEB": "中概股互联(港股风向)",
            "SOXX": "半导体(映射A股芯片)"
        }

    def _format_code(self, code, market):
        """将代码转换为 Yahoo Finance 格式"""
        code = str(code).strip()
        if market == 'HK':
            # 港股：去掉前缀，补足4位，加 .HK (例: 0700 -> 0700.HK)
            clean_code = code.replace('.HK', '')
            return f"{clean_code.zfill(4)}.HK"
        elif market == 'A':
            # A股：保持原后缀 (例: 600519.SS, 000858.SZ)
            # 如果配置里没有后缀，需要自己判断 (6开头.SS, 其他.SZ)
            if '.' in code:
                return code.replace('.SH', '.SS') # YF用SS代表上海
            else:
                return f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
        return code

    def collect_all(self, config):
        print(f"\n🚀 [数据引擎] 启动全网扫描 - {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. 准备股票列表
        tickers_map = {} # {yf_code: {info}}
        
        # 处理美股板块
        for symbol, name in self.us_etfs.items():
            tickers_map[symbol] = {'name': name, 'type': 'us_sector'}

        # 处理港股
        for s in config['hk_stocks']:
            yf_code = self._format_code(s['code'], 'HK')
            tickers_map[yf_code] = {**s, 'type': 'hk_stock'}

        # 处理A股
        for s in config['a_stocks']:
            yf_code = self._format_code(s['code'], 'A')
            tickers_map[yf_code] = {**s, 'type': 'a_stock'}

        # 2. 批量抓取 (一次性抓取几十只，速度极快)
        all_symbols = list(tickers_map.keys())
        # 添加大盘指数
        all_symbols += ["^GSPC", "^IXIC"] 
        
        print(f"📡 正在连接 Yahoo Finance 批量下载 {len(all_symbols)} 只标的...")
        try:
            # group_by='ticker' 确保返回结构清晰
            data = yf.download(all_symbols, period="2d", group_by='ticker', progress=False, threads=True)
        except Exception as e:
            print(f"❌ 下载严重失败: {e}")
            return None

        # 3. 数据清洗与组装
        result = {
            'us_market': {},
            'us_sectors': [],
            'portfolio': {'hk_stocks': [], 'a_stocks': []},
            'collected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 处理大盘
        for idx, name in [("^GSPC", "sp500"), ("^IXIC", "nasdaq")]:
            try:
                hist = data[idx]
                if not hist.empty and len(hist) >= 2:
                    close = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    pct = ((close - prev) / prev) * 100
                    result['us_market'][name] = {'price': round(close, 2), 'change_pct': round(pct, 2)}
                else:
                    result['us_market'][name] = {'price': 0, 'change_pct': 0}
            except:
                result['us_market'][name] = {'price': 0, 'change_pct': 0}

        # 处理个股
        for ticker, info in tickers_map.items():
            try:
                # 获取该股票的历史数据
                hist = data[ticker]
                
                # 如果数据为空（可能停牌或代码错），跳过
                if hist.empty:
                    print(f"⚠️ 无数据: {ticker}")
                    continue

                # 获取最新收盘价（针对时区差异，取最后一行有效数据）
                # 注意：iloc[-1] 在盘中是实时价，盘后是收盘价
                latest = hist.iloc[-1]
                
                # 计算涨跌幅 (如果只有1天数据，设为0)
                change_pct = 0.0
                price = 0.0
                
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    curr_close = hist['Close'].iloc[-1]
                    price = curr_close
                    change_pct = ((curr_close - prev_close) / prev_close) * 100
                elif len(hist) == 1:
                    price = hist['Close'].iloc[-1]

                # ⚠️ 修正 A股可能出现的价格异常 (Yahoo有时候数据会有拆股问题，但通常 .SS/.SZ 是准的)
                # 这里假设 Yahoo 返回的是正常的元单位

                item_data = {
                    'code': ticker,
                    'name': info.get('name', ticker),
                    'price': round(float(price), 2),
                    'change_pct': round(float(change_pct), 2),
                    'sector': info.get('sector', ''),
                    'us_sector': info.get('us_sector', '')
                }

                if info['type'] == 'us_sector':
                    result['us_sectors'].append(item_data)
                elif info['type'] == 'hk_stock':
                    result['portfolio']['hk_stocks'].append(item_data)
                elif info['type'] == 'a_stock':
                    result['portfolio']['a_stocks'].append(item_data)

            except Exception as e:
                print(f"⚠️ 处理 {ticker} 出错: {e}")

        print(f"✅ 数据清洗完成: 港股 {len(result['portfolio']['hk_stocks'])} | A股 {len(result['portfolio']['a_stocks'])}")
        return result
