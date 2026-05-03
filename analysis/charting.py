import io
import pandas as pd
import mplfinance as mpf
from models.market import StructureResult, AVPResult

def generate_chart(symbol: str, df: pd.DataFrame, structure: StructureResult, avp: AVPResult) -> io.BytesIO:
    df_chart = df.copy()
    if not isinstance(df_chart.index, pd.DatetimeIndex):
        df_chart.set_index('timestamp', inplace=True)
        
    df_chart['ema34'] = df_chart['close'].ewm(span=34, adjust=False).mean()
        
    df_chart = df_chart.iloc[-100:]
    
    lines = []
    colors = []
    
    if structure.latest_swing_high:
        lines.append(structure.latest_swing_high)
        colors.append('red')
    if structure.latest_swing_low:
        lines.append(structure.latest_swing_low)
        colors.append('green')
        
    if avp.poc:
        lines.append(avp.poc)
        colors.append('orange')
    if avp.vah:
        lines.append(avp.vah)
        colors.append('blue')
    if avp.val:
        lines.append(avp.val)
        colors.append('blue')

    buf = io.BytesIO()
    
    # Dark mode theme for Discord
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True, base_mpf_style='nightclouds')
    
    kwargs = dict(
        type='candle',
        volume=True,
        style=s,
        title=f"\n{symbol} Structure & Volume Profile",
        ylabel='Price',
        ylabel_lower='Volume',
        figratio=(12, 8),
        figscale=1.0,
        tight_layout=True,
        returnfig=True
    )
    
    ap = mpf.make_addplot(df_chart['ema34'], color='fuchsia', width=1.5)
    
    if lines:
        kwargs['hlines'] = dict(hlines=lines, colors=colors, linestyle='--', linewidths=1.5, alpha=0.7)
        
    fig, axlist = mpf.plot(df_chart, addplot=ap, **kwargs)
    
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    return buf
