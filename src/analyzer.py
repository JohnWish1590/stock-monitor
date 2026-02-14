import google.generativeai as genai
import json
from datetime import datetime
import traceback

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # 🔥 核心修改：使用 Pro 模型，智商更高
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    def analyze(self, data):
        print("🧠 [AI大脑] Gemini 1.5 Pro 正在进行深度归因...")
        
        # 1. 构建 Prompt (注入灵魂)
        # 将数据转为字符串供 AI 阅读
        us_text = "\n".join([f"- {s['name']}({s['code']}): {s['change_pct']:+.2f}%" for s in data['us_sectors']])
        
        # 挑选波动大的股票展示，避免 token 溢出
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        # 按涨跌幅绝对值排序，取前 15 个重点分析
        top_movers = sorted(all_stocks, key=lambda x: abs(x['change_pct']), reverse=True)[:15]
        stock_text = "\n".join([f"- {s['name']}({s['code']}) [{s['sector']}]: {s['change_pct']:+.2f}% (现价: {s['price']})" for s in top_movers])

        prompt = f"""
        你是我（用户）的【首席基金经理】和【头号幕僚】。现在是北京时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}。
        
        请阅读以下【真实行情数据】，为我撰写一份《全球映射与持仓监控日报》。

        【宏观锚点：昨夜美股/板块】
        {us_text}
        (注：XLK=科技, SOXX=半导体, KWEB=中概/港股情绪)

        【我的持仓表现 (重点关注)】
        {stock_text}

        【分析指令 - 必须严格执行】：
        1. **人设**：你是专业的实战派基金经理。语言犀利、直接，拒绝“今日股市震荡”这种废话。
        2. **核心逻辑（Mapping）**：
           - 必须分析**美股映射**：比如“昨夜美股半导体(SOXX)跌了，导致今天你的A股恒玄科技跟着杀跌”。
           - **汇率视角**：如果涉及出海股（如乐歌、巨星），必须结合汇率（人民币升值=利空）分析。
        3. **输出格式**：必须是标准的 **JSON** 格式，不要Markdown代码块，不要废话。

        【JSON 结构要求】：
        {{
            "market_summary": "一句话定调（例如：美股科技崩盘，A股被动杀跌，建议防守）",
            "sector_analysis": [
                {{
                    "sector_name": "板块名（如：硬科技）",
                    "impact_level": "高/中/低",
                    "reasoning": "深度归因（结合美股和个股表现）",
                    "affected_stocks": ["股票A", "股票B"]
                }}
            ],
            "top_picks": [
                {{
                    "stock_name": "股票名",
                    "stock_code": "代码",
                    "action": "买入/卖出/持有/观望",
                    "reason": "具体的战术建议（如：超跌反弹，博弈35元支撑）"
                }}
            ],
            "risk_alerts": ["风险提示1", "风险提示2"],
            "trading_strategy": "总结性的操作建议（100字以内）"
        }}
        """

        try:
            # 2. 调用 API
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # 3. 解析结果
            # 1.5 Pro 通常会很听话地返回 JSON，直接解析
            text = response.text.strip()
            # 去掉可能存在的 markdown 符号
            if text.startswith("```json"):
                text = text[7:-3]
            
            analysis_result = json.loads(text)
            
            # 补充时间戳
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("✅ AI 分析成功！")
            return analysis_result

        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            traceback.print_exc()
            # 返回一个“假”的分析结果，防止网页报错，但内容会提示错误
            return {
                "market_summary": f"⚠️ AI 大脑暂时掉线: {str(e)}",
                "sector_analysis": [],
                "top_picks": [],
                "risk_alerts": ["API 调用失败，请检查 Key 或 网络"],
                "trading_strategy": "暂停操作",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback": True
            }
