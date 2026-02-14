"""
邮件发送模块：使用 Resend API 发送每日简报
免费额度：100封/天
"""

import resend
import os
from datetime import datetime

class EmailSender:
    def __init__(self, api_key, from_email):
        resend.api_key = api_key
        self.from_email = from_email
        
    def create_email_html(self, data, analysis):
        """生成邮件HTML内容"""
        
        def get_change_color(change):
            if change > 0:
                return "#d32f2f"
            elif change < 0:
                return "#388e3c"
            return "#666666"
        
        def get_change_bg(change):
            if change > 1:
                return "#ffebee"
            elif change < -1:
                return "#e8f5e9"
            return "#f5f5f5"
        
        sector_cards = ""
        for sector in data['us_sectors']:
            color = get_change_color(sector['change_pct'])
            bg = get_change_bg(sector['change_pct'])
            arrow = "📈" if sector['change_pct'] > 0 else "📉" if sector['change_pct'] < 0 else "➡️"
            sector_cards += f"""
            <div style="background:{bg}; border-radius:8px; padding:12px; margin:8px 0; border-left:4px solid {color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; color:#333;">{sector['name']} ({sector['symbol']})</span>
                    <span style="color:{color}; font-weight:bold; font-size:18px;">
                        {arrow} {sector['change_pct']:+.2f}%
                    </span>
                </div>
            </div>
            """
        
        top_picks_html = ""
        if 'top_picks' in analysis and analysis['top_picks']:
            for pick in analysis['top_picks']:
                action_color = {
                    "关注开盘": "#ff9800",
                    "持有观察": "#2196f3", 
                    "逢低关注": "#4caf50"
                }.get(pick.get('action', ''), "#666")
                
                top_picks_html += f"""
                <div style="background:#fff3e0; border-radius:8px; padding:12px; margin:8px 0; border-left:4px solid #ff9800;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:bold; font-size:16px; color:#333;">
                            {pick['stock_name']} ({pick['stock_code']})
                        </span>
                        <span style="background:{action_color}; color:white; padding:4px 12px; border-radius:12px; font-size:12px;">
                            {pick['action']}
                        </span>
                    </div>
                    <p style="margin:0; color:#666; font-size:14px; line-height:1.5;">{pick['reason']}</p>
                </div>
                """
        
        risk_html = ""
        if 'risk_alerts' in analysis and analysis['risk_alerts']:
            risk_html = '<div style="background:#ffebee; border-radius:8px; padding:12px; margin:16px 0;">'
            risk_html += '<h4 style="margin:0 0 8px 0; color:#d32f2f;">⚠️ 风险提示</h4>'
            for risk in analysis['risk_alerts']:
                risk_html += f'<p style="margin:4px 0; color:#666;">• {risk}</p>'
            risk_html += '</div>'
        
        us_market = data['us_market']
        sp500_color = get_change_color(us_market['sp500']['change_pct'])
        nasdaq_color = get_change_color(us_market['nasdaq']['change_pct'])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日盘前简报</title>
</head>
<body style="margin:0; padding:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f0f2f5;">
    <div style="max-width:600px; margin:0 auto; background:white;">
        <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:30px 20px; text-align:center; color:white;">
            <h1 style="margin:0; font-size:24px;">📊 每日盘前简报</h1>
            <p style="margin:10px 0 0 0; opacity:0.9;">{datetime.now().strftime('%Y年%m月%d日')} | 美股夜盘收盘</p>
        </div>
        
        <div style="padding:20px;">
            <div style="background:#e3f2fd; border-radius:12px; padding:16px; margin-bottom:20px; border-left:4px solid #2196f3;">
                <h3 style="margin:0 0 8px 0; color:#1976d2;">🤖 AI 市场洞察</h3>
                <p style="margin:0; color:#333; line-height:1.6;">{analysis.get('market_summary', '市场数据采集中...')}</p>
            </div>
            
            <h3 style="color:#333; margin:20px 0 12px 0; border-bottom:2px solid #eee; padding-bottom:8px;">🌐 美股大盘</h3>
            <div style="display:flex; gap:12px; margin-bottom:20px;">
                <div style="flex:1; background:#f5f5f5; border-radius:8px; padding:12px; text-align:center;">
                    <div style="font-size:12px; color:#666; margin-bottom:4px;">标普500</div>
                    <div style="font-size:20px; font-weight:bold; color:{sp500_color};">
                        {us_market['sp500']['change_pct']:+.2f}%
                    </div>
                </div>
                <div style="flex:1; background:#f5f5f5; border-radius:8px; padding:12px; text-align:center;">
                    <div style="font-size:12px; color:#666; margin-bottom:4px;">纳斯达克</div>
                    <div style="font-size:20px; font-weight:bold; color:{nasdaq_color};">
                        {us_market['nasdaq']['change_pct']:+.2f}%
                    </div>
                </div>
            </div>
            
            <h3 style="color:#333; margin:20px 0 12px 0; border-bottom:2px solid #eee; padding-bottom:8px;">📈 美股板块表现</h3>
            {sector_cards}
            
            <h3 style="color:#333; margin:24px 0 12px 0; border-bottom:2px solid #eee; padding-bottom:8px;">🎯 今日重点关注</h3>
            {top_picks_html if top_picks_html else '<p style="color:#999;">暂无特别关注</p>'}
            
            {risk_html}
            
            <div style="background:#f3e5f5; border-radius:12px; padding:16px; margin-top:20px; border-left:4px solid #9c27b0;">
                <h4 style="margin:0 0 8px 0; color:#7b1fa2;">💡 交易策略</h4>
                <p style="margin:0; color:#333; line-height:1.6;">{analysis.get('trading_strategy', '建议观望，等待开盘方向明确')}</p>
            </div>
            
            <div style="margin-top:30px; padding-top:20px; border-top:1px solid #eee; text-align:center; color:#999; font-size:12px;">
                <p>数据更新时间：{data['collected_at']}</p>
                <p>分析生成时间：{analysis.get('generated_at', 'N/A')}</p>
                <p style="margin-top:12px;">
                    <a href="https://your-username.github.io/stock-monitor/" style="color:#667eea; text-decoration:none;">查看完整监控面板 →</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def send_daily_report(self, to_email, data, analysis):
        """发送每日简报邮件"""
        try:
            html_content = self.create_email_html(data, analysis)
            
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"[盘前简报] {datetime.now().strftime('%m/%d')} 美股{'涨' if data['us_market']['sp500']['change_pct'] > 0 else '跌'} {abs(data['us_market']['sp500']['change_pct']):.1f}% | 关注{len(analysis.get('top_picks', []))}只",
                "html": html_content
            }
            
            response = resend.Emails.send(params)
            print(f"✅ 邮件发送成功: {response['id']}")
            return True, response['id']
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False, str(e)
