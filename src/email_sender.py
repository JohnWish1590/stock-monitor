import resend
import os
from datetime import datetime

class EmailSender:
    def __init__(self, api_key, from_email):
        resend.api_key = api_key
        self.from_email = from_email
        
    def create_email_html(self, data, analysis):
        # 辅助函数
        def change_color(val): return '#d32f2f' if val > 0 else '#388e3c' if val < 0 else '#666'
        def change_bg(val): return '#ffebee' if val > 2 else '#e8f5e9' if val < -2 else '#f9f9f9'

        # 生成美股板块卡片
        sector_cards = ""
        if data.get('us_sectors'):
            sorted_sectors = sorted(data['us_sectors'], key=lambda x: x.get('change_pct', 0), reverse=True)
            for s in sorted_sectors:
                pct = s.get('change_pct', 0)
                # 🔥 修复点：这里改成 code
                sector_cards += f"""
                <div style="background:{change_bg(pct)}; border-left:4px solid {change_color(pct)}; padding:10px; margin-bottom:8px; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:#666;">
                        <span>{s['name']}</span>
                        <span>{s['code']}</span> 
                    </div>
                    <div style="font-weight:bold; font-size:16px; color:{change_color(pct)};">
                        {pct:+.2f}%
                    </div>
                </div>
                """

        # 生成重点关注
        picks_html = ""
        if analysis.get('top_picks'):
            for pick in analysis['top_picks']:
                picks_html += f"""
                <div style="background:#e3f2fd; padding:10px; margin-bottom:8px; border-left:4px solid #2196f3; border-radius:4px;">
                    <div style="font-weight:bold;">{pick.get('stock_name','')} <span style="font-weight:normal; font-size:12px; color:#666;">{pick.get('stock_code','')}</span></div>
                    <div style="font-size:13px; color:#333; margin-top:4px;">{pick.get('reason','')}</div>
                </div>
                """
        else:
            picks_html = "<div style='color:#999; font-size:12px;'>暂无重点关注</div>"

        # 组装 HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:sans-serif; color:#333; max-width:600px; margin:0 auto;">
            <div style="background:#2c3e50; color:white; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                <h2 style="margin:0;">🚀 基金经理日报</h2>
                <p style="margin:5px 0 0 0; opacity:0.8; font-size:12px;">{data['collected_at']}</p>
            </div>
            
            <div style="padding:20px; border:1px solid #eee; border-top:none;">
                <div style="background:#fff3e0; padding:15px; border-radius:8px; margin-bottom:20px; border-left:4px solid #ff9800;">
                    <h3 style="margin:0 0 5px 0; font-size:16px;">🤖 AI 核心观点</h3>
                    <p style="margin:0; font-size:14px; line-height:1.5;">{analysis.get('market_summary', '数据不足')}</p>
                </div>

                <h3 style="border-bottom:2px solid #eee; padding-bottom:5px;">🌎 美股映射</h3>
                {sector_cards}

                <h3 style="border-bottom:2px solid #eee; padding-bottom:5px; margin-top:25px;">🎯 重点机会</h3>
                {picks_html}
                
                <div style="text-align:center; margin-top:30px; font-size:12px; color:#999;">
                    <a href="https://github.com/JohnWish1590/stock-monitor" style="color:#2196f3;">查看完整看板</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_daily_report(self, to_email, data, analysis):
        try:
            html = self.create_email_html(data, analysis)
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"🚀 [日报] 基金经理投研内参 ({datetime.now().strftime('%m/%d')})",
                "html": html
            }
            email = resend.Emails.send(params)
            print(f"✅ 邮件已发送: {email}")
            return True, email
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False, str(e)
