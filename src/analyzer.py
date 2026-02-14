import google.generativeai as genai
import json
from datetime import datetime, timedelta, timezone
import traceback
import re

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # 优先使用 Flash Lite (速度快/不限流)
        priority_models = [
            'gemini-2.0-flash-lite-preview-02-05',
            'gemini-2.0-flash-lite-001',
            'gemini-2.0-flash'
        ]
        
        self.model = None
        try:
            available = [m.name.replace('models/', '') for m in genai.list_models()]
            for target in priority_models:
                if target in available:
                    self.model = genai.GenerativeModel(target)
                    break
            if not self.model: self.model = genai.GenerativeModel('gemini-2.0-flash')
        except:
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def get_beijing_time(self):
        utc_now = datetime.now(timezone.utc)
        return (utc_now + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

    def analyze(self, data):
        print(f"🧠 [AI大脑] 分析启动...")
        
        us_text = ", ".join([f"{s['name']}:{s.get('change_pct', 0)}%" for s in data.get('us_sectors', [])])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        valid_stocks = [s for s in all_stocks if s.get('price', 0) > 0]
        top_movers = sorted(valid_stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:12]
        stock_text = "\n".join([f"- {s['name']}({s['code']}): {s.get('change_pct', 0)}%" for s in top_movers])

        prompt = f"""
        请以JSON格式输出股市分析。
        【市场数据】美股板块：{us_text}。持仓异动：{stock_text}
        【JSON结构】
        {{
            "market_summary": "简评",
            "sector_analysis": [{{ "sector_name": "板块", "impact_level": "高/中/低", "reasoning": "原因", "affected_stocks": ["股票A"] }}],
            "top_picks": [{{ "stock_name": "股票名", "stock_code": "代码", "action": "关注", "reason": "简述" }}]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: text = match.group(0)
            
            analysis_result = json.loads(text)
            # 🔥 修复：使用北京时间
            analysis_result['generated_at'] = self.get_beijing_time()
            return analysis_result

        except Exception as e:
            return {
                "market_summary": f"AI 连接受限: {str(e)[:50]}...",
                "sector_analysis": [], "top_picks": [],
                "trading_strategy": "暂停操作",
                "generated_at": self.get_beijing_time(),
                "fallback": True
            }
