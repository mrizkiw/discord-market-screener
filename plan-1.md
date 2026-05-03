# Discord Bot Plan for Binance Spot Coin Monitoring

## Objective
This document defines a system where a user can chat in Discord and request monitoring for a specific trading pair, for example `ASTERUSDT`, with the strict rule that every pair must be a valid **Binance Spot** symbol.[cite:1][cite:2]

The system must then fetch market data, determine swing high and swing low levels, detect whether a breakout has occurred, evaluate the current market position, calculate an anchored volume profile from a relevant anchor point, and provide actionable insight including what should be done now, possible entry logic, take-profit (TP) targets, and stop-loss (SL) levels.[cite:1][cite:7]

## Product Scope
The system must only accept symbols validated through Binance Spot `GET /api/v3/exchangeInfo`, because this endpoint provides symbol and trading status information for Binance Spot markets.[cite:1][cite:2]

The system must not process futures symbols, margin-only instruments, or pairs that are not in `TRADING` status, so user input must always be filtered into active spot symbols first.[cite:1]

## Discord User Flow
1. A user sends a command such as `/monitor ASTERUSDT` or a natural-language message such as `monitor ASTERUSDT`.
2. The bot validates whether `ASTERUSDT` exists on Binance Spot and is actively tradable.[cite:1][cite:2]
3. The bot fetches OHLCV market data, ideally across multiple timeframes such as 15m, 1h, 4h, and 1d for intraday and swing context.
4. The bot calculates market structure, including swing highs, swing lows, active range, higher highs, lower lows, and breakout state.
5. The bot builds an anchored volume profile from an automatically selected anchor point, such as the most recent swing low in a bullish scenario or the breakout candle in a trend expansion scenario, because anchored volume profile is used from meaningful points such as swing lows, breakout candles, or major events while the move continues to develop.[cite:7][page:2]
6. The bot returns a concise market summary and an action recommendation.

## System Components
### 1. Discord Interface
- Slash command: `/monitor <symbol>`.
- Optional parameter: `/monitor <symbol> <timeframe>`.
- Optional mode: `scalp`, `intraday`, `swing`.
- Short answer in the channel, expanded detail in a thread or embed.

### 2. Market Data Service
- Main source for pair validation: Binance Spot `exchangeInfo`.[cite:1][cite:2]
- Main source for candles/klines: Binance Spot market data endpoints.
- Short-term caching to reduce repeated API requests.
- Symbol metadata storage: tick size, step size, quote asset, and trading status for TP/SL rounding and execution rules.

### 3. Analysis Engine
- Market structure module.
- Breakout detection module.
- Anchored volume profile module.
- Recommendation engine.
- Risk template module.

### 4. Output Engine
- Produces a clean text summary.
- Produces key levels: support, resistance, breakout level, POC, VAH, and VAL.
- Produces action status: buy setup, wait, breakout confirmation, avoid, or manage existing position.

## Pair Validation Rules
Validation rules must be explicit:
- The symbol must be found in Binance Spot `exchangeInfo`.[cite:1][cite:2]
- The symbol must be permitted for spot trading and have `TRADING` status.[cite:1]
- If the symbol is invalid, the bot should respond with either a close symbol suggestion or a correct formatting hint.

Examples:
- Valid: `BTCUSDT`, `ETHUSDT`, `ASTERUSDT` if available and active on Spot.
- Invalid: perpetual futures symbols, typo symbols, or delisted/inactive pairs.

## Swing High and Swing Low Logic
Use a candle pivot approach:
- **Swing high**: the high of a candle is higher than the highs of `n` candles on the left and `n` candles on the right.
- **Swing low**: the low of a candle is lower than the lows of `n` candles on the left and `n` candles on the right.
- Initial parameter: `n = 2` or `n = 3`, then make it adaptive by timeframe if needed.

Additional filters:
- Ignore pivots that are too close together if the price distance is below a minimum ATR-based threshold.
- Prioritize pivots that lead to visible displacement or impulse after the pivot is formed.
- Keep the latest 3 to 5 swings to interpret current structure.

Required output:
- Latest swing high.
- Latest swing low.
- Previous major swing high/low.
- Current structure label: HH, HL, LH, or LL.

## Breakout Logic
Suggested breakout definitions:
- **Bullish breakout**: a candle close breaks above a relevant swing high or range high.
- **Bearish breakout**: a candle close breaks below a relevant swing low or range low.
- A breakout is stronger when it is supported by volume expansion and price does not immediately fall back into the prior range.

Breakout classification:
- `No breakout`: price is still inside the active range.
- `Valid breakout`: close occurs beyond the level and follow-through is present.
- `Weak breakout`: wick breaks the level but the candle closes back inside.
- `Failed breakout`: price briefly leaves the range and then returns; in volume profile terms this resembles a failed auction, where price cannot maintain acceptance outside the value area and rotates back inward.[page:2]

## Current Position Logic
The bot must always explain where price is positioned right now, for example:
- Above the latest swing high.
- Below the latest swing low.
- In the middle of the range, near POC, meaning a balanced or low-edge condition.
- Retesting the breakout zone.
- Rejecting VAH, VAL, HVN, or LVN.

Interpretation framework:
- **Bullish**: price is above important structure, anchored volume profile is shifting higher, and the value area supports acceptance above the accumulation zone.[page:2]
- **Bearish**: price is below important structure, anchored volume profile is shifting lower, and retests are being rejected.
- **Neutral**: price is back in the middle of the value area or still inside the major range; in volume profile logic, the value area and POC often represent balance or mean-reversion zones.[page:2]

## Anchored Volume Profile
Anchored Volume Profile (AVP) must be a core part of the system. AVP starts from a meaningful point such as a swing low, breakout candle, or reversal pivot, and continues updating as new data arrives.[cite:7][page:2]

Minimum AVP levels to calculate:
- POC (Point of Control), the price level with the highest traded volume in the profile.[page:2]
- VAH (Value Area High).[page:2]
- VAL (Value Area Low).[page:2]
- HVN (High Volume Node) and LVN (Low Volume Node), if implemented.[page:2]

Automatic anchor selection rules:
- If the trend is bullish and a valid higher low has just formed, anchor from that swing low.[cite:7][page:2]
- If a fresh breakout has occurred, anchor from the breakout candle.[cite:7][page:2]
- If there is a sharp reversal, anchor from the pivot candle that started the new impulse.[cite:7][page:2]

AVP interpretation:
- If price is rising and the value area is also shifting higher, the move has better volume support.[page:2]
- If price is rising but the value area remains flat or lags behind, momentum should be treated with caution.[page:2]
- If price breaks beyond VAH or VAL and then returns inside, that can indicate a failed auction or breakout failure.[page:2]

## Recommendation Engine
The system should not only show levels; it must return an explicit action recommendation.

Main recommendation labels:
- `Buy now`.
- `Wait for breakout`.
- `Wait for retest`.
- `Avoid / no trade`.
- `Take partial profit`.
- `Cut loss if level X breaks`.

Example conditions for `Buy now`:
- Bullish structure: HH-HL sequence.
- Price is above POC or has successfully reclaimed POC.
- Retest into VAH, HVN, or breakout level shows bullish rejection.
- Minimum risk-reward meets strategy rules, for example 1:2.

Example conditions for `Avoid / no trade`:
- Price is exactly in the middle of the range and far from a clean invalidation level.
- Breakout has not yet been confirmed.
- AVP shows acceptance in a balanced area, meaning the entry edge is weak.[page:2]

## TP and SL Rules
TP and SL logic should be rule-based, not free-form opinion.

### Long Scenario
- Entry: on valid breakout, breakout retest, or reclaim of POC/VAH/HVN depending on context.
- Main SL: below the nearest swing low, below VAL, or below the low of the confirmation candle.
- Staged TP:
  - TP1 at the nearest resistance or next HVN.
  - TP2 at the previous swing high.
  - TP3 at a range extension or the next psychological level.

### Short Scenario
- Entry: on valid breakdown, failed retest, or rejection from POC/VAL/HVN depending on context.
- Main SL: above the nearest swing high, above VAH, or above the high of the confirmation candle.
- Staged TP:
  - TP1 at the nearest support or next HVN.
  - TP2 at the previous swing low.
  - TP3 at the lower range extension.

Additional rules:
- Compute risk-reward before issuing the final recommendation.
- Do not issue an entry signal if the SL is too far and RR to TP1 is unattractive.
- TP and SL should be rounded using symbol precision if symbol filters are taken from Binance exchange info.[cite:1]

## Bot Output Format
Example Discord response format:

```text
ASTERUSDT - 4H
Status: Bullish retest after breakout
Trend: HH-HL
Swing High: 0.2450
Swing Low: 0.2210
Breakout: Valid breakout above 0.2380
Current Position: Price holding above breakout and above POC
AVP: Bullish, value area shifting higher
POC / VAH / VAL: 0.2392 / 0.2428 / 0.2349
Recommendation: Buy on hold above 0.2390 or on retest 0.2380-0.2392
SL: 0.2338
TP1: 0.2450
TP2: 0.2525
TP3: 0.2600
Notes: Invalidation if price closes back below VAL
```

This format is intentionally compact so a Discord user can instantly understand market condition, key levels, and what action is currently suggested.

## Technical Architecture
Suggested backend components:
- Discord Bot Service, which receives commands and sends responses.
- Market Data Worker, which fetches candles and symbol metadata.
- Analysis Worker, which calculates structure, breakout state, and AVP.
- Rules Engine, which turns analysis results into actionable insight.
- Storage/Cache, which stores the latest analysis per symbol and timeframe.

Recommended stack:
- Python for bot logic and numerical analysis.
- `discord.py` for Discord integration.
- Binance API client or direct HTTP requests for market data.
- Pandas/Numpy for candle and volume profile calculations.
- Redis or in-memory caching for speed.

## Analysis Pipeline
1. Receive symbol from Discord.
2. Validate symbol against Binance Spot.[cite:1][cite:2]
3. Fetch OHLCV data for the main timeframe and optional confirmation timeframes.
4. Calculate swing highs and swing lows.
5. Determine structure: bullish, bearish, or ranging.
6. Detect breakout or failed breakout.
7. Auto-select the AVP anchor.
8. Calculate POC, VAH, VAL, HVN, and LVN.
9. Evaluate current price location relative to structure and value area.
10. Build recommendation output including entry logic, TP, SL, invalidation, and confidence.
11. Return the result to Discord.

## Risk Management and Guardrails
To keep the bot output useful and safer, include these rules:
- Do not return `Buy now` or `Sell now` if the main timeframe candle has not closed yet.
- Show a confidence label: `high`, `medium`, or `low`.
- Show a short reason for why the setup is valid or invalid.
- Limit how many pairs a user can monitor to prevent API abuse.
- Include a disclaimer that the output is rule-based market insight, not guaranteed trading performance.

## Recommended MVP
The first version should focus on core functionality:
- Binance Spot pair input through Discord.
- Automatic pair validation.[cite:1][cite:2]
- One main timeframe, for example 4H.
- Automatic swing high / swing low detection.
- Breakout detection.
- Basic anchored volume profile: POC, VAH, VAL.
- Simple recommendation states: buy, wait, avoid.
- TP1, TP2, and SL.

Phase two features:
- Multi-timeframe confluence.
- Automatic breakout alerts.
- Chart image snapshots posted into Discord.
- Backtesting and setup scoring.
- User-specific watchlists.

## Definition of Done
The project is considered complete when:
- A user can type a symbol in Discord and only active Binance Spot pairs are accepted.[cite:1][cite:2]
- The bot can consistently produce swing highs, swing lows, and breakout state.
- The bot shows current price location relative to structure and anchored volume profile.
- The bot provides an explicit action recommendation with TP and SL.
- The output is compact enough for Discord while still being actionable.

## Important Implementation Note
AVP is most useful when it is anchored from a meaningful point such as a swing low, breakout candle, or reversal pivot, because the concept is designed to evaluate how volume is distributed from that event while the move continues to evolve.[cite:7][page:2]

Pair validation through Binance Spot `exchangeInfo` is also essential so the system does not analyze unavailable or inactive symbols.[cite:1][cite:2]
