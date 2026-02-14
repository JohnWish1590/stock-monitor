import google.generativeai as genai
import json
from datetime import datetime
import traceback
import re
import os

class PortfolioAnalyzer:
    def __init__(self, api_key):
        # 1. 打印版本信息，确认库是否升级成功
        import google.generativeai
        print(f"📦 [系统检查] google-generativeai 版本: {google.generativeai.__version__}")
        
        genai.configure(api_key=api_key)
        self.model = None
        
        # 2. 自动寻找可用模型
        print("🔍 [系统检查] 正在扫描可用模型列表...")
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            print(f"📋 [可用模型] 您的API支持: {available_models}")
            
            # 优先找 Flash，其次 Pro，最后随便找一个 Gemini
            target_model = None
            for m in available_models:
                if 'flash' in m and '1.5' in m:
                    target_model = m
                    break
            if not target_model:
                for m in available_models:
                    if 'pro' in m:
                        target_model = m
                        break
            if not target_model and available_models:
                target_model = available_models[0]
                
            if target_model:
                print(f"✅ [模型选定] 自动切换至: {target_model}")
                self.model = genai.GenerativeModel(target_model)
            else:
                print("❌ [严重错误] 未找到任何支持 generateContent 的模型！")
                
        except Exception as e:
            print(f"❌ [列表获取失败] 无法连接 Google API: {e}")
            # 可能是 Key 权限问题或地区问题
        
    def analyze(self, data):
        if not self.model:
            return self._get_fallback_data("未找到可用模型 (权限或地区限制)")

        print(f"🧠 [AI大脑] 正在通过 {self.model.model_name} 分析...")
        
        # 准备数据
        us_text = ", ".join([f"{s['name']}:{s.get('change_pct', 0)}%" for s in data.get('us_sectors', [])])
        
        all_stocks = data['portfolio']['hk_stocks'] + data['portfolio']['a_stocks']
        valid_stocks = [s for s in all_stocks if s.get('price', 0) > 0]
        top_movers = sorted(valid_stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:10]
        stock_text = "\n".join([f"- {s['name']}({s['code']}): {s.get('change_pct', 0)}%" for s in top_movers])

        prompt = f"""
        请以JSON格式分析股市。不要Markdown。
        时间：{datetime.now().strftime('%Y-%m-%d')}
        美股板块：{us_text}
        持仓异动：{stock_text}
        
        JSON结构：
        {{
            "market_summary": "简评",
            "sector_analysis": [],
            "top_picks": [],
            "risk_alerts": [],
            "trading_strategy": "建议"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # 强力清洗
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: text = match.group(0)
            
            analysis_result = json.loads(text)
            analysis_result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("✅ AI 分析成功！")
            return analysis_result

        except Exception as e:
            print(f"❌ 分析过程出错: {e}")
            return self._get_fallback_data(str(e))

    def _get_fallback_data(self, error_msg):
        return {
            "market_summary": f"AI服务异常: {str(error_msg)[:50]}...",
            "sector_analysis": [],
            "top_picks": [],
            "risk_alerts": ["请查看Actions日志中的模型列表"],
            "trading_strategy": "暂停操作",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fallback": True
        }
