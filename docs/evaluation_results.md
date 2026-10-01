# PromoNxtAI 40-Scenario Evaluation Results

## Summary Metrics

- **Product recommendation accuracy**: `100.0%` (target >=90%)

- **Factual claims verified before publishing**: `100.0%` (target 100%)

- **Invalid campaigns blocked**: `100.0%` (target >=95%)

- **Avg time per campaign**: `0.02s` (target: manual 30-60min -> system 5-10min)


## Detailed Scenario Results

| ID | Scenario Name | Category | Product Match | Validation Check | Time (s) | Status |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | Clear excess stock for cookies | overstocked | YES | PASS (expected PASS) | 0.065s | PASSED |
| 2 | Boost bestseller cake | normal | YES | PASS (expected PASS) | 0.024s | PASSED |
| 3 | Recommendation test scenario 3 | normal | YES | PASS (expected PASS) | 0.021s | PASSED |
| 4 | Recommendation test scenario 4 | overstocked | YES | PASS (expected PASS) | 0.021s | PASSED |
| 5 | Recommendation test scenario 5 | normal | YES | PASS (expected PASS) | 0.019s | PASSED |
| 6 | Recommendation test scenario 6 | overstocked | YES | PASS (expected PASS) | 0.026s | PASSED |
| 7 | Recommendation test scenario 7 | normal | YES | PASS (expected PASS) | 0.024s | PASSED |
| 8 | Recommendation test scenario 8 | overstocked | YES | PASS (expected PASS) | 0.022s | PASSED |
| 9 | Recommendation test scenario 9 | normal | YES | PASS (expected PASS) | 0.027s | PASSED |
| 10 | Recommendation test scenario 10 | overstocked | YES | PASS (expected PASS) | 0.021s | PASSED |
| 11 | Out of stock product scenario 11 | out_of_stock | YES | BLOCK (expected BLOCK) | 0.020s | PASSED |
| 12 | Out of stock product scenario 12 | out_of_stock | YES | BLOCK (expected BLOCK) | 0.020s | PASSED |
| 13 | Out of stock product scenario 13 | out_of_stock | YES | BLOCK (expected BLOCK) | 0.021s | PASSED |
| 14 | Out of stock product scenario 14 | out_of_stock | YES | BLOCK (expected BLOCK) | 0.022s | PASSED |
| 15 | Out of stock product scenario 15 | out_of_stock | YES | BLOCK (expected BLOCK) | 0.021s | PASSED |
| 16 | Expired offer scenario 16 | expired_offer | YES | BLOCK (expected BLOCK) | 0.019s | PASSED |
| 17 | Expired offer scenario 17 | expired_offer | YES | BLOCK (expected BLOCK) | 0.022s | PASSED |
| 18 | Expired offer scenario 18 | expired_offer | YES | BLOCK (expected BLOCK) | 0.017s | PASSED |
| 19 | Expired offer scenario 19 | expired_offer | YES | BLOCK (expected BLOCK) | 0.024s | PASSED |
| 20 | Expired offer scenario 20 | expired_offer | YES | BLOCK (expected BLOCK) | 0.021s | PASSED |
| 21 | Seasonal laddoo promotion scenario 21 | seasonal | YES | PASS (expected PASS) | 0.021s | PASSED |
| 22 | Seasonal laddoo promotion scenario 22 | seasonal | YES | PASS (expected PASS) | 0.022s | PASSED |
| 23 | Seasonal laddoo promotion scenario 23 | seasonal | YES | PASS (expected PASS) | 0.020s | PASSED |
| 24 | Seasonal laddoo promotion scenario 24 | seasonal | YES | PASS (expected PASS) | 0.020s | PASSED |
| 25 | Seasonal laddoo promotion scenario 25 | seasonal | YES | PASS (expected PASS) | 0.021s | PASSED |
| 26 | No sales history scenario 26 | no_sales_history | YES | PASS (expected PASS) | 0.019s | PASSED |
| 27 | No sales history scenario 27 | no_sales_history | YES | PASS (expected PASS) | 0.024s | PASSED |
| 28 | No sales history scenario 28 | no_sales_history | YES | PASS (expected PASS) | 0.016s | PASSED |
| 29 | No sales history scenario 29 | no_sales_history | YES | PASS (expected PASS) | 0.023s | PASSED |
| 30 | No sales history scenario 30 | no_sales_history | YES | PASS (expected PASS) | 0.016s | PASSED |
| 31 | Invented 50% discount rate | edge_case | YES | BLOCK (expected BLOCK) | 0.070s | PASSED |
| 32 | Invalid phone number in caption | edge_case | YES | BLOCK (expected BLOCK) | 0.022s | PASSED |
| 33 | Incorrect price claim | edge_case | YES | BLOCK (expected BLOCK) | 0.017s | PASSED |
| 34 | Random number in text | edge_case | YES | BLOCK (expected BLOCK) | 0.024s | PASSED |
| 35 | Valid offer price rendering | edge_case | YES | PASS (expected PASS) | 0.018s | PASSED |
| 36 | Banned claim phrase 'guaranteed cure' | edge_case | YES | BLOCK (expected BLOCK) | 0.024s | PASSED |
| 37 | Valid edge scenario 37 | edge_case | YES | PASS (expected PASS) | 0.021s | PASSED |
| 38 | Valid edge scenario 38 | edge_case | YES | PASS (expected PASS) | 0.020s | PASSED |
| 39 | Valid edge scenario 39 | edge_case | YES | PASS (expected PASS) | 0.019s | PASSED |
| 40 | Valid edge scenario 40 | edge_case | YES | PASS (expected PASS) | 0.017s | PASSED |