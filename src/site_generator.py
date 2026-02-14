import json
from datetime import datetime
import os

class SiteGenerator:
    def __init__(self, output_dir='docs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_dashboard(self, data, analysis):
        
        def change_color(val):
            if val > 0: return '#d32f2f' # A股红涨
            elif val < 0: return '#388e3c' # A股绿跌
            return '#666'
        
        def change_bg(val):
            if val > 2: return '#ffebee'
            elif val < -2: return '#e8f5e9'
            return '#fff'

        # 生成美股板块卡片
        sector_cards = ""
        if data.get('us_sectors'):
            # 按跌幅排序
            sorted_sectors = sorted(data['us_sectors'], key=lambda x: x['change_pct'], reverse=True)
            for s in sorted_sectors:
                color = change_color(s['change_pct'])
                bg = change_bg(s['change_pct'])
                emoji = "🔥" if s['change_pct'] > 2 else "📈" if s['change_pct'] > 0 else "📉"
                
                # 🔥 修复点：这里原来是 s['symbol']，现在改为 s['code']
                sector_cards += f"""
                <div class="sector-card" style="background:{bg}; border-left:4px solid {color}">
                    <div class="sector-header">
                        <span class="sector-name">{s['name']}</span>
                        <span class="sector-symbol">{s['code']}</span> 
                    </div>
                    <div class="sector-change" style="color:{color}">
                        {emoji} {s['change_pct']:+.2f}%
                    </div>
                    <div class="sector-detail">
                        价格: ${s['price']}
                    </div>
                </div>
                """

        # 生成股票行
        def generate_stock_rows(stocks):
            rows = ""
            if not stocks: return "<tr><td colspan='5'>暂无数据</td></tr>"
            
            valid_stocks = [s for s in stocks]
            
            for stock in sorted(valid_stocks, key=lambda x: x.get('change_pct', 0), reverse=True):
                color = change_color(stock.get('change_pct', 0))
                
                # 🔥 修复点：确保这里也都使用 ['code']
                rows += f"""
                <tr>
                    <td><strong>{stock['name']}</strong><br><small>{stock['code']}</small></td>
                    <td>{stock['sector']}</td>
                    <td style="font-weight:bold; color:{color};">
                        {stock.get('change_pct', 0):+.2f}%
                    </td>
                    <td>{stock.get('price', 0):.2f}</td>
                    <td><span class="us-sector-tag">{stock['us_sector']}</span></td>
                </tr>
                """
            return rows

        hk_rows = generate_stock_rows(data['portfolio']['hk_stocks'])
        a_rows = generate_stock_rows(data['portfolio']['a_stocks'])
        
        # 处理 AI 分析部分
        analysis_html = ""
        if 'sector_analysis' in analysis:
            for sa in analysis['sector_analysis']:
                analysis_html += f"""
                <div class="analysis-card">
                    <div class="analysis-header">
                        <span class="analysis-sector">{sa.get('sector_name', '板块')}</span>
                        <span class="impact-badge">{sa.get('impact_level', '中')}影响</span>
                    </div>
                    <p class="analysis-reason">{sa.get('reasoning', '')}</p>
                    <div class="affected-stocks">关联: {", ".join(sa.get('affected_stocks', []))}</div>
                </div>
                """

        # 处理重点关注
        top_picks_html = ""
        if 'top_picks' in analysis:
            for pick in analysis['top_picks']:
                top_picks_html += f"""
                <div class="pick-card">
                    <div class="pick-header">
                        <span class="pick-name">{pick['stock_name']}</span>
                        <span class="pick-action">{pick['action']}</span>
                    </div>
                    <p class="pick-reason">{pick['reason']}</p>
                </div>
                """

        # 组装 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自选股监控 | {datetime.now().strftime('%m/%d')}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #f5f7fa; color: #333; margin:0; padding:20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media(max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
        
        .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .card-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        
        .sector-card {{ padding: 10px; margin-bottom: 10px; border-radius: 8px; }}
        .sector-header {{ display: flex; justify-content: space-between; }}
        .sector-change {{ font-size: 18px; font-weight: bold; margin: 5px 0; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; color: #888; font-size: 12px; padding: 10px; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        
        .analysis-card, .pick-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #3498db; }}
        .impact-badge {{ background: #e74c3c; color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; float: right; }}
        .us-sector-tag {{ background: #eef2f7; color: #555; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 基金经理驾驶舱</h1>
            <p>数据更新: {data['collected_at']} | 港股: {len(data['portfolio']['hk_stocks'])} | A股: {len(data['portfolio']['a_stocks'])}</p>
        </div>

        <div class="card">
            <div class="card-title">🤖 智能投研日报</div>
            <div style="background:#e8f4fd; padding:15px; border-radius:8px; margin-bottom:15px;">
                <strong>核心观点：</strong> {analysis.get('market_summary', 'AI 分析暂不可用')}
            </div>
            {analysis_html}
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <div class="card-title">🌎 美股/板块映射</div>
                    {sector_cards}
                </div>
                <div class="card">
                    <div class="card-title">🎯 重点关注机会</div>
                    {top_picks_html}
                </div>
            </div>
            
            <div>
                <div class="card">
                    <div class="card-title">HK 港股持仓 ({len(data['portfolio']['hk_stocks'])})</div>
                    <table>
                        <thead><tr><th>代码</th><th>行业</th><th>涨跌</th><th>价格</th><th>映射</th></tr></thead>
                        <tbody>{hk_rows}</tbody>
                    </table>
                </div>
                
                <div class="card">
                    <div class="card-title">CN A股持仓 ({len(data['portfolio']['a_stocks'])})</div>
                    <table>
                        <thead><tr><th>代码</th><th>行业</th><th>涨跌</th><th>价格</th><th>映射</th></tr></thead>
                        <tbody>{a_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated by GitHub Actions & Gemini 1.5 Flash
        </div>
    </div>
</body>
</html>
"""
        
        output_path = os.path.join(self.output_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    def generate_json_data(self, data, analysis):
        output_path = os.path.join(self.output_dir, 'data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'data': data, 'analysis': analysis}, f, ensure_ascii=False, indent=2)
        return output_path
