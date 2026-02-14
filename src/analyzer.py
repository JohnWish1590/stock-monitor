import google.generativeai as genai
import json
from datetime import datetime
import traceback

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # 🔥 修复核心：换用最稳定的 Flash 模型，确保 API 100% 能通
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def analyze(self, data):
        print("🧠 [AI大脑] Gemini 1.5 Flash 正在进行深度归因...")
        
        # 1. 构建 Prompt
        us_text = "\n".join([f"- {s['name']}({s['code']}): {s['change_pct']:+.2f}%" for s in data['us_sectors']])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        # 过滤掉数据不全的
        valid_stocks = [s for s in all_stocks if s['price'] > 0]
        # 按波动排序取前15个
        top_movers = sorted(valid_stocks, key=lambda x: abs(x['change_pct']), reverse=True)[:15]
        
        stock_text = "\n".join([f"- {s['name']}({s['code']}) [{s['sector']}]: {s['change_pct']:+.2f}%" for s in top_movers])

        prompt = f"""
        你是我（用户）的【首席基金经理】。现在是北京时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}。
        请阅读以下【真实行情数据】，撰写《全球映射与持仓监控日报》。

        【美股/板块表现】
        {us_text}

        【我的持仓重点异动】
        {stock_text}

        【分析要求】：
        1. **深度映射**：必须解释美股板块如何影响我的持仓（如：美股科技跌 -> 导致A股芯片跌）。
        2. **汇率视角**：若涉及出口股，请考虑汇率影响。
        3. **输出格式**：严格的纯 JSON 格式，不要 Markdown 符号。

        【JSON 结构】：
        {{
            "market_summary": "一句话市场定调",
            "sector_analysis": [
                {{
                    "sector_name": "板块名",
                    "impact_level": "高/中/低",
                    "reasoning": "分析逻辑",
                    "affected_stocks": ["股票A", "股票B"]
                }}
            ],
            "top_picks": [
                {{
                    "stock_name": "股票名",
                    "stock_code": "代码",
                    "action": "买入/卖出/持有",
                    "reason": "简短建议"
                }}
            ],
            "risk_alerts": ["风险1", "风险2"],
            "trading_strategy": "操作建议"
        }}
        """

        try:
            # 2. 调用 API
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            text = response.text.strip()
            # 清理可能存在的 markdown 标记
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            
            analysis_result = json.loads(text)
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("✅ AI 分析成功！")
            return analysis_result

        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            traceback.print_exc()
            # 返回兜底数据，防止程序崩溃
            return {
                "market_summary": f"⚠️ AI 服务暂时不可用: {str(e)}",
                "sector_analysis": [],
                "top_picks": [],
                "risk_alerts": ["API 调用异常"],
                "trading_strategy": "暂停操作",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback": True
            }
