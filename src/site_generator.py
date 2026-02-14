"""
静态站点生成模块：生成 GitHub Pages 可托管的 HTML 监控面板
"""

import json
from datetime import datetime
import os

class SiteGenerator:
    def __init__(self, output_dir='docs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_dashboard(self, data, analysis):
        """生成完整的监控面板 HTML"""
        
        def change_color(val):
            if val > 0:
                return '#d32f2f'
            elif val < 0:
                return '#388e3c'
            return '#666'
        
        def change_bg(val):
            if val > 2:
                return '#ffebee'
            elif val > 0:
                return '#fff8e1'
            elif val < -2:
                return '#e8f5e9'
            elif val < 0:
                return '#f1f8e9'
            return '#f5f5f5'
        
        # 生成美股板块卡片
        sector_cards = ""
        for s in sorted(data['us_sectors'], key=lambda x: x['change_pct'], reverse=True):
            color = change_color(s['change_pct'])
            bg = change_bg(s['change_pct'])
            emoji = "🔥" if s['change_pct'] > 2 else "📈" if s['change_pct'] > 0 else "📉" if s['change_pct'] < 0 else "➡️"
            
            sector_cards += f"""
            <div class="sector-card" style="background:{bg}; border-left-color:{color}">
                <div class="sector-header">
                    <span class="sector-name">{s['name']}</span>
                    <span class="sector-symbol">{s['symbol']}</span>
                </div>
                <div class="sector-change" style="color:{color}">
                    {emoji} {s['change_pct']:+.2f}%
                </div>
                <div class="sector-detail">
                    价格: ${s['price']} | 涨跌: ${s['change']:+.2f}
                </div>
            </div>
            """
        
        # 生成自选股表格行
        def generate_stock_rows(stocks):
            rows = ""
            for stock in sorted(stocks, key=lambda x: x.get('change_pct', 0), reverse=True):
                color = change_color(stock.get('change_pct', 0))
                bg = change_bg(stock.get('change_pct', 0))
                
                rows += f"""
                <tr style="background:{bg}">
                    <td><strong>{stock['name']}</strong><br><small>{stock['code']}</small></td>
                    <td>{stock['sector']}</td>
                    <td style="font-weight:bold; color:{color}; font-size:16px;">
                        {stock.get('change_pct', 0):+.2f}%
                    </td>
                    <td>¥{stock.get('price', 0):.2f}</td>
                    <td><span class="us-sector-tag">{stock['us_sector']}</span></td>
                </tr>
                """
            return rows
        
        hk_rows = generate_stock_rows(data['portfolio']['hk_stocks'])
        a_rows = generate_stock_rows(data['portfolio']['a_stocks'])
        
        # 生成AI分析卡片
        analysis_html = ""
        if 'sector_analysis' in analysis:
            for sa in analysis['sector_analysis'][:5]:
                impact_color = {"高": "#d32f2f", "中": "#f57c00", "低": "#388e3c"}.get(sa.get('impact_level', '中'), "#666")
                affected = ", ".join(sa.get('affected_stocks', [])[:5])
                
                analysis_html += f"""
                <div class="analysis-card">
                    <div class="analysis-header">
                        <span class="analysis-sector">{sa.get('sector_name', 'N/A')}</span>
                        <span class="impact-badge" style="background:{impact_color}">{sa.get('impact_level', '中')}影响</span>
                    </div>
                    <p class="analysis-reason">{sa.get('reasoning', '')}</p>
                    <div class="affected-stocks">影响: {affected if affected else '无直接关联'}</div>
                </div>
                """
        
        # 生成重点关注
        top_picks_html = ""
        if 'top_picks' in analysis:
            for pick in analysis['top_picks']:
                action_class = {
                    "关注开盘": "action-watch",
                    "持有观察": "action-hold",
                    "逢低关注": "action-buy"
                }.get(pick.get('action', ''), "action-hold")
                
                top_picks_html += f"""
                <div class="pick-card {action_class}">
                    <div class="pick-header">
                        <span class="pick-name">{pick['stock_name']}</span>
                        <span class="pick-code">{pick['stock_code']}</span>
                        <span class="pick-action">{pick['action']}</span>
                    </div>
                    <p class="pick-reason">{pick['reason']}</p>
                </div>
                """
        
        us_m = data['us_market']
                # HTML样式和主体
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自选股监控面板 | {datetime.now().strftime('%m/%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
            background: #f0f2f5; 
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header-meta {{ opacity: 0.9; font-size: 14px; }}
        
        .market-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .market-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
        }}
        .market-label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
        .market-value {{ font-size: 24px; font-weight: bold; }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }}
        @media (max-width: 968px) {{ .main-grid {{ grid-template-columns: 1fr; }} }}
        
        .card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .card-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .sector-card {{
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 12px;
            border-left: 4px solid;
            transition: transform 0.2s;
        }}
        .sector-card:hover {{ transform: translateX(4px); }}
        .sector-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .sector-name {{ font-weight: 600; font-size: 16px; }}
        .sector-symbol {{ color: #999; font-size: 12px; }}
        .sector-change {{ font-size: 20px; font-weight: bold; margin: 4px 0; }}
        .sector-detail {{ font-size: 12px; color: #666; }}
        
        .stock-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .stock-table th {{
            text-align: left;
            padding: 12px;
            background: #f8f9fa;
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .stock-table td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .stock-table tr:hover {{ opacity: 0.8; }}
        .us-sector-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
        }}
        
        .analysis-card {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            border-left: 4px solid #667eea;
        }}
        .analysis-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .analysis-sector {{ font-weight: 600; }}
        .impact-badge {{
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
        }}
        .analysis-reason {{ font-size: 13px; color: #555; margin-bottom: 8px; }}
        .affected-stocks {{ font-size: 12px; color: #888; }}
        
        .pick-card {{
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            border: 2px solid;
        }}
        .pick-card.action-watch {{ background: #fff3e0; border-color: #ff9800; }}
        .pick-card.action-hold {{ background: #e3f2fd; border-color: #2196f3; }}
        .pick-card.action-buy {{ background: #e8f5e9; border-color: #4caf50; }}
        
        .pick-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        .pick-name {{ font-weight: 600; font-size: 16px; }}
        .pick-code {{ color: #666; font-size: 13px; }}
        .pick-action {{
            margin-left: auto;
            background: rgba(0,0,0,0.1);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .pick-reason {{ font-size: 13px; color: #555; line-height: 1.5; }}
        
        .footer {{
            text-align: center;
            padding: 24px;
            color: #999;
            font-size: 12px;
        }}
        
        .update-time {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 自选股全景监控</h1>
            <div class="header-meta">
                美股板块联动分析 | 港股: {len(data['portfolio']['hk_stocks'])}只 | A股: {len(data['portfolio']['a_stocks'])}只 | 
                数据更新: {data['collected_at']}
            </div>
        </div>
        
        <div class="market-overview">
            <div class="market-card">
                <div class="market-label">标普500</div>
                <div class="market-value" style="color:{change_color(us_m['sp500']['change_pct'])}">
                    {us_m['sp500']['change_pct']:+.2f}%
                </div>
            </div>
            <div class="market-card">
                <div class="market-label">纳斯达克</div>
                <div class="market-value" style="color:{change_color(us_m['nasdaq']['change_pct'])}">
                    {us_m['nasdaq']['change_pct']:+.2f}%
                </div>
            </div>
            <div class="market-card">
                <div class="market-label">AI分析状态</div>
                <div class="market-value" style="color:#667eea; font-size:18px;">
                    {'✅ 已生成' if 'generated_at' in analysis else '⚠️ 默认模式'}
                </div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="left-col">
                <div class="card">
                    <div class="card-title">🌐 美股板块表现（夜盘收盘）</div>
                    {sector_cards}
                </div>
                
                <div class="card" style="margin-top:24px;">
                    <div class="card-title">🤖 AI 跨市场联动分析</div>
                    <div style="background:#e3f2fd; padding:12px; border-radius:8px; margin-bottom:16px;">
                        <strong>市场总结：</strong>{analysis.get('market_summary', '分析生成中...')}
                    </div>
                    {analysis_html if analysis_html else '<p style="color:#999;">暂无板块分析数据</p>'}
                </div>
            </div>
            
            <div class="right-col">
                <div class="card">
                    <div class="card-title">🎯 今日重点关注</div>
                    {top_picks_html if top_picks_html else '<p style="color:#999;">暂无特别关注</p>'}
                </div>
                
                <div class="card" style="margin-top:24px;">
                    <div class="card-title">🇭🇰 港股自选股 ({len(data['portfolio']['hk_stocks'])}只)</div>
                    <table class="stock-table">
                        <thead>
                            <tr>
                                <th>名称/代码</th>
                                <th>行业</th>
                                <th>涨跌幅</th>
                                <th>价格</th>
                                <th>美股映射</th>
                            </tr>
                        </thead>
                        <tbody>{hk_rows}</tbody>
                    </table>
                </div>
                
                <div class="card" style="margin-top:24px;">
                    <div class="card-title">🇨🇳 A股自选股 ({len(data['portfolio']['a_stocks'])}只)</div>
                    <table class="stock-table">
                        <thead>
                            <tr>
                                <th>名称/代码</th>
                                <th>行业</th>
                                <th>涨跌幅</th>
                                <th>价格</th>
                                <th>美股映射</th>
                            </tr>
                        </thead>
                        <tbody>{a_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 分析引擎: Gemini 2.0 Flash | 📊 数据来源: Yahoo Finance / 东方财富</p>
            <p>分析生成时间: {analysis.get('generated_at', 'N/A')} | 
               <a href="https://github.com/your-username/stock-monitor" style="color:#667eea;">查看项目源码</a>
            </p>
        </div>
    </div>
    
    <div class="update-time">⏱️ 更新于 {data['collected_at'][-8:]}</div>
</body>
</html>"""
        
        output_path = os.path.join(self.output_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 监控面板已生成: {output_path}")
        return output_path
    
    def generate_json_data(self, data, analysis):
        """生成JSON数据文件"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'us_market': data['us_market'],
            'us_sectors': data['us_sectors'],
            'portfolio': data['portfolio'],
            'analysis': analysis
        }
        
        output_path = os.path.join(self.output_dir, 'data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON数据已生成: {output_path}")
        return output_path
        # HTML头部和样式（接下一条）
