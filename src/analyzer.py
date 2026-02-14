import google.generativeai as genai
import json
from datetime import datetime
import traceback
import re

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # 🎯 根据你的日志，精准打击！
        # 优先级列表：只选 Flash 系列，避开 Pro (Pro 额度太低会报 429)
        # Gemini 2.0 Flash 是目前最强且免费额度最好的模型
        priority_models = [
            'gemini-2.0-flash',          # 首选：性能强，额度高
            'gemini-2.0-flash-lite-001', # 备选：极速，几乎不限流
            'gemini-2.5-flash',          # 尝鲜：新版 Flash
            'gemini-1.5-flash'           # 兜底
        ]
        
        self.model = None
        
        print("🔍 [系统检查] 正在匹配最佳 Flash 模型...")
        try:
            # 获取用户实际拥有的模型列表
            available = [m.name.replace('models/', '') for m in genai.list_models()]
            
            # 匹配逻辑
            for target in priority_models:
                if target in available:
                    print(f"✅ [模型锁定] 成功切换至: {target} (高额度/低延迟)")
                    self.model = genai.GenerativeModel(target)
                    break
            
            # 如果都没匹配上（极小概率），强行试一下 2.0 Flash
            if not self.model:
                print("⚠️ 未在列表中匹配到预设模型，强行使用 gemini-2.0-flash")
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                
        except Exception as e:
            print(f"❌ 模型列表获取失败，尝试盲连: {e}")
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze(self, data):
        print(f"🧠 [AI大脑] 正在通过 {self.model.model_name} 进行光速分析...")
        
        # 准备数据
        us_text = ", ".join([f"{s['name']}:{s.get('change_pct', 0)}%" for s in data.get('us_sectors', [])])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        valid_stocks = [s for s in all_stocks if s.get('price', 0) > 0]
        # 取前 12 个波动大的
        top_movers = sorted(valid_stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:12]
        stock_text = "\n".join([f"- {s['name']}({s['code']}): {s.get('change_pct', 0)}%" for s in top_movers])

        prompt = f"""
        请以标准JSON格式输出股市分析。禁止Markdown。
        时间：{datetime.now().strftime('%Y-%m-%d')}
        
        【市场数据】
        美股板块：{us_text}
        持仓异动：{stock_text}

        【JSON结构要求】
        {{
            "market_summary": "简短定调",
            "sector_analysis": [
                {{
                    "sector_name": "板块",
                    "impact_level": "高/中/低",
                    "reasoning": "原因",
                    "affected_stocks": ["股票A"]
                }}
            ],
            "top_picks": [
                {{
                    "stock_name": "股票名",
                    "stock_code": "代码",
                    "action": "关注",
                    "reason": "简述"
                }}
            ]
        }}
        """

        try:
            # 调用 API
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # 清洗
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: text = match.group(0)
            
            analysis_result = json.loads(text)
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("✅ AI 分析成功！")
            return analysis_result

        except Exception as e:
            # 如果是 429 (限流)，打印特定提示
            if "429" in str(e):
                print("❌ 额度超限 (429)。请稍后再试，或检查 API 配额。")
            else:
                print(f"❌ 分析失败: {e}")
            
            return {
                "market_summary": f"AI 连接受限: {str(e)[:50]}...",
                "sector_analysis": [],
                "top_picks": [],
                "trading_strategy": "暂停操作",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback": True
            }
