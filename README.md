README.md

# SOXL Staggered Sell/Rebuy Plan Simulator

Models your sell/rebuy ladder against historical volatility patterns for SOXL (3x leveraged semiconductor ETF).

## Features
- Multiple price scenarios (conservative, moderate, aggressive, moonshot)
- Expected profit/loss calculations for each scenario
- Optimal timing for buys after sells
- Risk-adjusted returns using historical volatility
- Weighted ensemble analysis with probability-based expectations

## Your Position (Configured)
- **Shares:** 82.105
- **Avg Cost:** $212.81
- **Cash:** $1,414.47
- **Current Price:** $215.39

## Sell Ladder (4 Zones)
| Zone | Shares | Target Price |
|------|--------|--------------|
| 1 | 18 | $212.50 |
| 2 | 18 | $232.50 |
| 3 | 18 | $255.00 |
| 4 | 12 | $290.00 |

## Buy Ladder (3 Zones)
| Zone | Shares | Target Price |
|------|--------|--------------|
| A | 6 | $197.50 |
| B | 7 | $187.50 |
| C | 8 | $177.50 |

## Scenarios
| Scenario | Price Range | Volatility | Probability |
|----------|-------------|------------|-------------|
| Conservative | 180-220 | 8% | 40% |
| Moderate | 200-260 | 12% | 35% |
| Aggressive | 240-320 | 18% | 20% |
| Moonshot | 300-500 | 25% | 5% |

## Requirements
```bash
pip install numpy pandas
```

## Usage
```bash
python soxl_simulator.py
```

## How It Works
The simulator uses **geometric Brownian motion** to model price paths based on historical volatility, time horizon, and random price returns. It executes your sell/buy orders against each simulated price path.

## Risk Considerations
SOXL is a **3x leveraged ETF** with extreme volatility. This simulator models that risk but past volatility ≠ future volatility, leveraged decay affects long-term returns, and gap risk exists.
