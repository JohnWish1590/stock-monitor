#!/usr/bin/env python3
"""
自选股监控系统主程序
每日定时执行：采集数据 → AI分析 → 生成站点 → 发送邮件
"""

import os
import sys
import json
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import DataCollector
from analyzer import PortfolioAnalyzer
from site_generator import SiteGenerator
from email_sender import EmailSender

def load_config():
    """加载配置"""
    with open('data/portfolio.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("="*60)
    print(f"🚀 自选股监控系统启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 1. 加载配置
        print("\n📋 步骤1: 加载自选股配置...")
        config = load_config()
        print(f"   港股: {len(config['hk_stocks'])} 只")
        print(f"   A股: {len(config['a_stocks'])} 只")
        
        # 2. 采集数据
        print("\n📊 步骤2: 采集市场数据...")
        collector = DataCollector()
        market_data = collector.collect_all(config)
        
        # 3. AI分析
        print("\n🤖 步骤3: AI智能分析...")
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            print("   ⚠️ 未设置 GEMINI_API_KEY，使用默认分析")
            analysis = {
                "market_summary": "AI分析未启用，请查看原始数据",
                "sector_analysis": [],
                "top_picks": [],
                "trading_strategy": "建议参考美股板块表现自行判断",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback": True
            }
        else:
            analyzer = PortfolioAnalyzer(gemini_key)
            analysis = analyzer.analyze(market_data)
        
        # 4. 生成静态站点
        print("\n🌐 步骤4: 生成监控面板...")
        generator = SiteGenerator(output_dir='docs')
        generator.generate_dashboard(market_data, analysis)
        generator.generate_json_data(market_data, analysis)
        
        # 5. 发送邮件简报
        print("\n📧 步骤5: 发送邮件简报...")
        resend_key = os.getenv('RESEND_API_KEY')
        to_email = os.getenv('TO_EMAIL')
        
        if resend_key and to_email:
            sender = EmailSender(
                api_key=resend_key,
                from_email="Stock Monitor <onboarding@resend.dev>"
            )
            success, msg = sender.send_daily_report(to_email, market_data, analysis)
            if success:
                print(f"   ✅ 邮件已发送至 {to_email}")
            else:
                print(f"   ❌ 邮件发送失败: {msg}")
        else:
            print("   ⚠️ 未设置 RESEND_API_KEY 或 TO_EMAIL，跳过邮件发送")
        
        print("\n" + "="*60)
        print("✅ 所有任务执行完成！")
        print("="*60)
        
        # 输出摘要
        print(f"\n📈 今日摘要:")
        print(f"   标普500: {market_data['us_market']['sp500']['change_pct']:+.2f}%")
        print(f"   纳斯达克: {market_data['us_market']['nasdaq']['change_pct']:+.2f}%")
        print(f"   关注个股: {len(analysis.get('top_picks', []))} 只")
        print(f"   面板地址: https://your-username.github.io/stock-monitor/")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
