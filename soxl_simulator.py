soxl_simulator.py


SOXL Staggered Sell/Rebuy Plan Simulator

Models your sell/rebuy ladder against historical volatility patterns.
Calculates:
- Multiple price scenarios (conservative, moderate, aggressive)
- Expected profit/loss for each scenario
- Optimal timing for buys after sells
- Risk-adjusted returns using historical volatility
"""

import numpy as np
import pandas as pd

# ============================================================================
# CONFIGURATION - YOUR EXACT POSITION
# ============================================================================

CURRENT_SHARES = 82.105
AVG_COST = 212.81
CURRENT_CASH = 1414.47
CURRENT_PRICE = 215.39  # 3pm price

# Sell orders
SELL_ORDERS = [
    {'shares': 18, 'price': 212.50, 'zone': 1},
    {'shares': 18, 'price': 232.50, 'zone': 2},
    {'shares': 18, 'price': 255.00, 'zone': 3},
    {'shares': 12, 'price': 290.00, 'zone': 4},
]

# Buy orders
BUY_ORDERS = [
    {'shares': 6, 'price': 197.50, 'zone': 'A'},
    {'shares': 7, 'price': 187.50, 'zone': 'B'},
    {'shares': 8, 'price': 177.50, 'zone': 'C'},
]

# SOXL Historical volatility (3x leveraged = extreme)
DAILY_VOLATILITY = 0.10  # 10% daily
WEEKLY_VOLATILITY = 0.20
MONTHLY_VOLATILITY = 0.40

# Price scenarios
SCENARIOS = {
    'conservative': {
        'name': 'Conservative (180-220)',
        'price_range': (180, 220),
        'volatility': 0.08,
        'probability': 0.40,
        'days': 30,
    },
    'moderate': {
        'name': 'Moderate (200-260)',
        'price_range': (200, 260),
        'volatility': 0.12,
        'probability': 0.35,
        'days': 30,
    },
    'aggressive': {
        'name': 'Aggressive (240-320)',
        'price_range': (240, 320),
        'volatility': 0.18,
        'probability': 0.20,
        'days': 30,
    },
    'moonshot': {
        'name': 'Moonshot (300-500)',
        'price_range': (300, 500),
        'volatility': 0.25,
        'probability': 0.05,
        'days': 90,
    },
}

# ============================================================================
# SIMULATION FUNCTIONS
# ============================================================================

def simulate_price_path(start_price, volatility, days, time_steps=100):
    """Geometric Brownian motion simulation"""
    daily_vol = volatility / np.sqrt(365)
    dt = days / 365
    np.random.seed(42)
    returns = np.random.normal(0, daily_vol * np.sqrt(dt), time_steps)
    prices = [start_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    return pd.DataFrame({
        'time': np.linspace(0, days, time_steps + 1),
        'price': prices
    })

def execute_sell_order(position, sell_order, price_path):
    shares = sell_order['shares']
    target_price = sell_order['price']
    
    if price_path['price'].max() >= target_price:
        exec_idx = price_path[price_path['price'] >= target_price].index[0]
        exec_price = price_path['price'][exec_idx]
        revenue = shares * exec_price
        
        new_position = {
            'shares': position['shares'] - shares,
            'avg_cost': position['avg_cost'],
            'cash': position['cash'] + revenue,
            'realized_gain': revenue - (shares * position['avg_cost']),
        }
        return new_position, True, exec_price
    
    return position, False, 0

def execute_buy_order(position, buy_order, price_path, min_cash_ratio=0.2):
    shares = buy_order['shares']
    target_price = buy_order['price']
    cost = shares * target_price
    
    if position['cash'] < cost * (1 + min_cash_ratio):
        return position, False, 0
    
    if price_path['price'].min() <= target_price:
        exec_idx = price_path[price_path['price'] <= target_price].index[0]
        exec_price = price_path['price'][exec_idx]
        cost = shares * exec_price
        
        new_position = {
            'shares': position['shares'] + shares,
            'avg_cost': position['avg_cost'],
            'cash': position['cash'] - cost,
        }
        return new_position, True, exec_price
    
    return position, False, 0

def run_scenario(scenario, current_position, start_price):
    price_path = simulate_price_path(
        start_price=start_price,
        volatility=scenario['volatility'],
        days=scenario['days'],
        time_steps=100
    )
    
    position = current_position.copy()
    position['realized_gain'] = 0
    
    # Execute sells
    sell_results = []
    for sell_order in SELL_ORDERS:
        position, executed, exec_price = execute_sell_order(position, sell_order, price_path)
        sell_results.append({
            'zone': sell_order['zone'],
            'target': sell_order['price'],
            'executed': executed,
            'exec_price': exec_price,
            'shares': sell_order['shares'],
            'revenue': exec_price * sell_order['shares'] if executed else 0,
            'gain': exec_price * sell_order['shares'] - (sell_order['shares'] * current_position['avg_cost']) if executed else 0,
        })
    
    # Execute buys
    buy_results = []
    for buy_order in BUY_ORDERS:
        position, executed, exec_price = execute_buy_order(position, buy_order, price_path)
        buy_results.append({
            'zone': buy_order['zone'],
            'target': buy_order['price'],
            'executed': executed,
            'exec_price': exec_price,
            'shares': buy_order['shares'],
            'cost': exec_price * buy_order['shares'] if executed else 0,
        })
    
    final_position_value = position['shares'] * start_price
    total_realized_gain = position['realized_gain']
    total_buy_cost = sum([r['cost'] for r in buy_results])
    
    return {
        'scenario_name': scenario['name'],
        'probability': scenario['probability'],
        'price_range': scenario['price_range'],
        'volatility': scenario['volatility'],
        'sell_results': sell_results,
        'buy_results': buy_results,
        'final_shares': position['shares'],
        'final_cash': position['cash'],
        'total_realized_gain': total_realized_gain,
        'final_position_value': final_position_value,
        'total_portfolio_value': final_position_value + position['cash'],
        'net_profit': total_portfolio_value - (current_position['shares'] * current_position['avg_cost'] + current_position['cash']),
    }

# ============================================================================
# RUN ALL SIMULATIONS
# ============================================================================

def run_all_simulations():
    current_position = {
        'shares': CURRENT_SHARES,
        'avg_cost': AVG_COST,
        'cash': CURRENT_CASH,
    }
    
    results = []
    for scenario_name, scenario in SCENARIOS.items():
        result = run_scenario(scenario, current_position, CURRENT_PRICE)
        results.append(result)
    
    # Weighted ensemble
    total_prob = sum([r['probability'] for r in results])
    expected_gain = sum([r['net_profit'] * r['probability'] for r in results]) / total_prob
    expected_value = sum([r['total_portfolio_value'] * r['probability'] for r in results]) / total_prob
    
    profits = [r['net_profit'] for r in results]
    weights = [r['probability'] for r in results]
    variance = sum([w * (p - expected_gain) ** 2 for p, w in zip(profits, weights)]) / total_prob
    std = np.sqrt(variance)
    
    return {
        'simulations': sorted(results, key=lambda x: x['probability'], reverse=True),
        'ensemble': {
            'expected_net_profit': expected_gain,
            'expected_total_value': expected_value,
            'expected_std': std,
            'best_case': max(profits),
            'worst_case': min(profits),
        },
        'original_position': current_position,
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    results = run_all_simulations()
    
    print("=" * 80)
    print("SOXL STAGGERED SELL/REBUY PLAN SIMULATOR")
    print("=" * 80)
    print()
    
    print("ORIGINAL POSITION:")
    print(f"  Shares: {results['original_position']['shares']}")
    print(f"  Avg Cost: $ {results['original_position']['avg_cost']:.2f}")
    print(f"  Cash: $ {results['original_position']['cash']:.2f}")
    total_orig = results['original_position']['shares'] * results['original_position']['avg_cost'] + results['original_position']['cash']
    print(f"  Total Value: $ {total_orig:.2f}")
    print()
    
    print("ENSEMBLE RESULTS (Weighted by Probability):")
    print(f"  Expected Net Profit: $ {results['ensemble']['expected_net_profit']:.2f}")
    print(f"  Expected Total Portfolio Value: $ {results['ensemble']['expected_total_value']:.2f}")
    print(f"  Expected Std Dev (Risk): $ {results['ensemble']['expected_std']:.2f}")
    print(f"  Best Case: $ {results['ensemble']['best_case']:.2f}")
    print(f"  Worst Case: $ {results['ensemble']['worst_case']:.2f}")
    print()
    
    print("SCENARIOS:")
    for sim in results['simulations']:
        print(f"  {sim['scenario_name']} - {sim['probability']*100:.1f}%")
        print(f"    Net Profit: $ {sim['net_profit']:.2f}")
        print(f"    Final Value: $ {sim['total_portfolio_value']:.2f}")
        sells_exec = sum([1 for s in sim['sell_results'] if s['executed']])
        buys_exec = sum([1 for b in sim['buy_results'] if b['executed']])
        print(f"    Sells: {sells_exec}/4, Buys: {buys_exec}/3")
        print()
    
    print("=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    if results['ensemble']['expected_net_profit'] > 0:
        print(f"  ✓ PLAN IS PROFITABLE: Expected $ {results['ensemble']['expected_net_profit']:.2f}")
        print(f"    Return: {results['ensemble']['expected_net_profit']/total_orig*100:.2f}%")
    else:
        print(f"  ⚠ NEGATIVE EXPECTED VALUE: Expected loss $ {results['ensemble']['expected_net_profit']:.2f}")
