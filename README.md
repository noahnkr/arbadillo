# Arbadillo - Sports Betting Arbitrage Bot

## How to Calculate an Arbitrage Bet?

### First Step: Converting the Odds

We need to find the implied probability for each outcome using the formula: $(1 / \text{Decimal Odds}) \cdot 100$.

To convert American Odds to Decimal Odds, use the formula: $(\text{American Odds} / 100) + 1$ if the American Odds are postive, and $(100 / \text{American Odds}) + 1$ if they are negative.

**Example Sports Book X**
| Team A | |
| - | - |
| American Odds | -125 |
| Decimal Odds | 1.8 |
| Implied Probability | 55.56% |

**Example Sports Book Y**
| Team B | |
| - | - |
| American Odds | +130 |
| Decimal Odds | 2.3 |
| Implied Probability | 43.48% |

### Second Step: Determining if an Opportunity Exists

We need to identify whether or not there is an arbitrage opportunity here. We can determine this using the formula: $A = \text{Implied Prob. Team A} + \text{Implied Prob. Team B}$

- If $A > 1$: No arbitrage opportunity, guarunteed loss of profit.
- If $A = 1$: No arbitrage opportunity, guarunteed to break even.
- If $A < 1$: Arbitrage opportunity, guarunteed profit.

In the example, $A = 0.5556 + 0.4348 = 0.9904$. Since $A < 1$, there is an arbitrage opportunity.

### Third Step: How Much to Wager to Make a Profit

Using the formula $S = \text{Total Bet} \cdot \text{Implied Prob.}$ we can determine the stake for each wager based on how much we want to bet.

Let's keep it simple and bet $100 in total.

**Example Sports Book X**

$S_A = \$100 \cdot 0.5556 = \$55.56$

**Example Sports Book Y**

$S_B = \$100 \cdot 0.4348 = \$43.48$

In this case, if Team A wins, we win $\$55.56 \cdot 1.8 = \$100.98$. If Team B wins, we win $\$43.48 \cdot 2.3 = \$100.98$