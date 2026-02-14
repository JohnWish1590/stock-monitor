import json
import os

class SiteGenerator:
    def __init__(self, output_dir='docs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_dashboard(self, data, analysis):
        
        def change_color(val): return '#d32f2f' if val > 0 else '#388e3c' if val < 0 else '#666'
        def change_bg(val): return '#ffebee' if val > 2 else '#e8f5e9' if val < -2 else '#fff'

        # 生成美股板块卡片
        sector_cards = ""
        if data.get('us_sectors'):
            sorted_sectors = sorted(data['us_sectors'], key=lambda x: x.get('change_pct', 0), reverse=True)
            for s in sorted_sectors:
                pct = s.get('change_pct', 0)
                sector_cards += f"""
                <div class="sector-card" style="background:{change_bg(pct)}; border-left:4px solid {change_color(pct)}">
                    <div class="sector-header">
                        <span class="sector-name">{s['name']}</span>
                    </div>
                    <div class="sector-change" style="color:{change_color(pct)}">
                        {pct:+.2f}%
                    </div>
                </div>
                """

        # 🔥 核心修改：生成股票行 (美股映射写在名字下面)
        def generate_stock_rows(stocks):
            rows = ""
            if not stocks: return "<tr><td colspan='4'>暂无数据</td></tr>"
            
            for s in sorted(stocks, key=lambda x: x.get('change_pct', 0), reverse=True):
                pct = s.get('change_pct', 0)
                # 获取美股映射，如果没有则不显示
                mapping_tag = ""
                if s.get('us_sector'):
                    mapping_tag = f'<div style="font-size:10px; color:#999; margin-top:2px; background:#f5f5f5; display:inline-block; padding:1px 4px; border-radius:3px;">🇺🇸 {s["us_sector"]}</div>'

                rows += f"""
                <tr>
                    <td>
                        <div style="font-weight:bold;">{s['name']}</div>
                        <div style="font-size:11px; color:#666;">{s['code']}</div>
                        {mapping_tag}
                    </td>
                    <td style="font-size:13px;">{s['sector']}</td>
                    <td style="font-weight:bold; color:{change_color(pct)};">
                        {pct:+.2f}%
                    </td>
                    <td>{s.get('price', 0):.2f}</td>
                </tr>
                """
            return rows

        hk_rows = generate_stock_rows(data['portfolio']['hk_stocks'])
        a_rows = generate_stock_rows(data['portfolio']['a_stocks'])
        
        # AI 分析 HTML
        analysis_html = ""
        if analysis.get('sector_analysis'):
            for sa in analysis['sector_analysis']:
                analysis_html += f"""
                <div class="analysis-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <strong>{sa.get('sector_name','板块')}</strong>
                        <span style="background:#e74c3c; color:white; padding:1px 5px; border-radius:3px; font-size:11px;">{sa.get('impact_level','中')}</span>
                    </div>
                    <p style="margin:0; font-size:13px; color:#555;">{sa.get('reasoning','')}</p>
                </div>
                """

        # 组装 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自选股监控</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #f5f7fa; color: #333; margin:0; padding:15px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        @media(max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
        
        .card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        .card-title {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        
        .sector-card {{ padding: 8px; margin-bottom: 8px; border-radius: 4px; display:flex; justify-content:space-between; align-items:center; }}
        .analysis-card {{ background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #3498db; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; color: #999; font-size: 12px; padding: 8px; border-bottom:1px solid #eee; }}
        td {{ padding: 8px; border-bottom: 1px solid #f9f9f9; vertical-align: middle; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin:0;">🚀 基金经理驾驶舱</h2>
            <div style="font-size:12px; opacity:0.8; margin-top:5px;">更新时间: {data['collected_at']} (北京时间)</div>
        </div>

        <div class="card">
            <div class="card-title">🤖 AI 投研内参</div>
            <div style="background:#e3f2fd; padding:10px; border-radius:4px; margin-bottom:10px; font-size:14px; color:#0d47a1;">
                {analysis.get('market_summary', 'AI 分析暂不可用')}
            </div>
            {analysis_html}
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <div class="card-title">🌎 美股板块映射</div>
                    {sector_cards}
                </div>
                
                <div class="card">
                    <div class="card-title">🎯 重点关注</div>
                    {''.join([f'<div style="background:#fff3e0; padding:8px; border-radius:4px; margin-bottom:5px; border-left:3px solid #ff9800;"><div style="font-weight:bold; font-size:14px;">{p["stock_name"]}</div><div style="font-size:12px; color:#666;">{p["reason"]}</div></div>' for p in analysis.get('top_picks', [])])}
                </div>
            </div>
            
            <div>
                <div class="card">
                    <div class="card-title">🇭🇰 港股持仓</div>
                    <table>
                        <thead><tr><th>代码/映射</th><th>行业</th><th>涨跌</th><th>价格</th></tr></thead>
                        <tbody>{hk_rows}</tbody>
                    </table>
                </div>
                
                <div class="card">
                    <div class="card-title">🇨🇳 A股持仓</div>
                    <table>
                        <thead><tr><th>代码/映射</th><th>行业</th><th>涨跌</th><th>价格</th></tr></thead>
                        <tbody>{a_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        return os.path.join(self.output_dir, 'index.html')

    def generate_json_data(self, data, analysis):
        with open(os.path.join(self.output_dir, 'data.json'), 'w', encoding='utf-8') as f:
            json.dump({'data': data, 'analysis': analysis}, f, ensure_ascii=False)
        return os.path.join(self.output_dir, 'data.json')
