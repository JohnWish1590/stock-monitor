import google.generativeai as genai
import json
from datetime import datetime
import traceback

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # 这里不指定模型，在调用时指定
        
    def analyze(self, data):
        # 1. 准备数据
        us_text = "\n".join([f"- {s['name']}({s['code']}): {s['change_pct']:+.2f}%" for s in data['us_sectors']])
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        valid_stocks = [s for s in all_stocks if s['price'] > 0]
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
        3. **输出格式**：纯 JSON 格式。

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

        # 🔥 核心逻辑：模型梯队尝试 🔥
        # 1. 先试最好的 Pro (逻辑最强)
        # 2. 不行就试 Flash (速度最快)
        # 3. 还是不行就试 Pro 1.0 (兼容性最强)
        models_to_try = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for model_name in models_to_try:
            print(f"🧠 [AI大脑] 正在尝试唤醒 {model_name} ...")
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # 如果成功拿到结果，解析并返回
                text = response.text.strip()
                if text.startswith("```json"): text = text[7:-3]
                elif text.startswith("```"): text = text[3:-3]
                
                analysis_result = json.loads(text)
                analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"✅ {model_name} 分析成功！")
                return analysis_result

            except Exception as e:
                print(f"⚠️ {model_name} 调用失败: {e}")
                continue # 尝试下一个模型

        # 如果所有模型都失败
        print("❌ 所有 AI 模型均不可用")
        return {
            "market_summary": "⚠️ AI 服务连接失败，请检查 API Key 或 网络",
            "sector_analysis": [],
            "top_picks": [],
            "risk_alerts": ["无法连接 Google AI"],
            "trading_strategy": "暂停操作",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fallback": True
        }
