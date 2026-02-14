import google.generativeai as genai
import json
from datetime import datetime
import traceback
import re

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # 🔥 核心修改：使用 'gemini-pro' (v1.0)
        # 这是一个全球通用的模型，虽然没有 1.5 聪明，但绝对不会 404
        self.model = genai.GenerativeModel('gemini-pro')
        
    def analyze(self, data):
        print("🧠 [AI大脑] Gemini Pro (v1.0) 正在启动兼容模式...")
        
        # 1. 准备数据
        # v1.0 处理长文本能力稍弱，我们精简一下 Prompt
        us_text = ", ".join([f"{s['name']}:{s.get('change_pct', 0)}%" for s in data.get('us_sectors', [])])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        # 简单过滤
        valid_stocks = [s for s in all_stocks if s.get('price', 0) > 0]
        # 取前 10 个波动大的
        top_movers = sorted(valid_stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:10]
        
        stock_text = "\n".join([f"- {s['name']}({s['code']}): {s.get('change_pct', 0)}%" for s in top_movers])

        # v1.0 需要更明确的 JSON 指令
        prompt = f"""
        角色：金融分析师
        时间：{datetime.now().strftime('%Y-%m-%d')}
        
        【市场数据】
        美股板块：{us_text}
        持仓异动：{stock_text}

        【任务】
        分析美股板块对持仓的影响。如有出口股考虑汇率。
        
        【输出要求】
        必须只输出一段纯 JSON 代码，不要 markdown 标记，不要```符号。
        格式如下：
        {{
            "market_summary": "简短的市场定调",
            "sector_analysis": [
                {{
                    "sector_name": "板块名",
                    "impact_level": "高",
                    "reasoning": "原因",
                    "affected_stocks": ["股票名"]
                }}
            ],
            "top_picks": [
                {{
                    "stock_name": "股票名",
                    "stock_code": "代码",
                    "action": "持有",
                    "reason": "建议"
                }}
            ]
        }}
        """

        try:
            # 2. 调用 API
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # 3. 清洗数据 (v1.0 比较啰嗦，可能会加 ```json)
            # 使用正则提取 JSON 部分
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            analysis_result = json.loads(text)
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("✅ AI 分析成功！(Gemini Pro)")
            return analysis_result

        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            # traceback.print_exc() 
            # 返回兜底数据，保证网页能生成，不报错退出
            return {
                "market_summary": f"AI 连接受限 (Gemini Pro): {str(e)[:50]}",
                "sector_analysis": [],
                "top_picks": [],
                "risk_alerts": ["请检查网络或Key配额"],
                "trading_strategy": "暂停操作",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback": True
            }
