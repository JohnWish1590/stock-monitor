"""
AI 分析模块：使用 Gemini API 进行跨市场联动分析和涨跌归因
"""

import google.generativeai as genai
import json
from datetime import datetime

class PortfolioAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    def create_analysis_prompt(self, data):
        """构建分析提示词"""
        
        sectors_text = "\n".join([
            f"- {s['name']} ({s['symbol']}): {s['change_pct']:+.2f}%"
            for s in data['us_sectors']
        ])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        sorted_stocks = sorted(all_stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:8]
        
        stocks_text = "\n".join([
            f"- {s['name']} ({s['code']}): {s.get('change_pct', 0):+.2f}% [{s['sector']}]"
            for s in sorted_stocks
        ])
        
        us_market = data['us_market']
        
        prompt = f"""你是一位专业的跨市场投资分析师。请基于以下数据生成今日盘前策略简报：

【美股夜盘收盘数据】
标普500: {us_market['sp500']['change_pct']:+.2f}%
纳斯达克: {us_market['nasdaq']['change_pct']:+.2f}%

板块表现：
{sectors_text}

【用户持仓重点关注】（按波动排序）
{stocks_text}

请生成结构化的JSON分析报告，包含以下字段：
1. market_summary: 市场整体判断（1-2句话）
2. sector_analysis: 板块分析数组，每个板块包含：
   - sector_name: 板块名称
   - performance: 表现描述
   - impact_level: 影响程度（高/中/低）
   - affected_stocks: 影响的具体股票列表（从用户持仓中匹配）
   - reasoning: 逻辑说明
3. top_picks: 今日重点关注股票数组（3-5只），包含：
   - stock_name: 股票名称
   - stock_code: 代码
   - reason: 关注理由
   - action: 建议操作（关注开盘/持有观察/逢低关注）
4. risk_alerts: 风险提示数组
5. trading_strategy: 整体交易策略建议（1-2句话）

注意：
- 重点关注美股板块与用户持仓的映射关系
- 科技板块(XLK)影响小米、金蝶、比亚迪电子、恒玄科技等
- 可选消费(XLY)影响美团、理想汽车、安踏、比亚迪、美的等  
- 医疗(XLV)影响复星医药、再鼎医药、固生堂等
- 分析要具体，不要泛泛而谈
- 使用中文输出

请直接返回JSON格式，不要包含markdown标记或其他说明文字。"""
        return prompt
    
    def analyze(self, data):
        """执行AI分析"""
        print("🤖 正在调用 Gemini AI 进行分析...")
        
        try:
            prompt = self.create_analysis_prompt(data)
            response = self.model.generate_content(prompt)
            
            response_text = response.text
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis_result = json.loads(response_text.strip())
            
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            analysis_result['data_timestamp'] = data['collected_at']
            
            print("✅ AI 分析完成")
            return analysis_result
            
        except Exception as e:
            print(f"⚠️ AI 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(data)
    
    def _fallback_analysis(self, data):
        """备用分析"""
        return {
            "market_summary": "美股隔夜表现平稳，建议关注板块轮动机会",
            "sector_analysis": [],
            "top_picks": [],
            "risk_alerts": ["AI分析服务暂时不可用，请手动判断"],
            "trading_strategy": "建议观望，等待开盘后的市场方向明确",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_timestamp": data['collected_at'],
            "fallback": True
        }
