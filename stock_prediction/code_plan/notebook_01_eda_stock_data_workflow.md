# Workflow Notebook 01: EDA Stock Data (^GSPC 2018–2024)

**File:** `notebooks/01_EDA_stock_data.ipynb`  
**Tujuan:** Exploratory Data Analysis (EDA) komprehensif pada data S&P 500 (2018–2024) untuk memahami karakteristik harga, volatilitas, return, dan pola musiman.

---

## Alur Notebook (11 Tahap + Feature Engineering + Kesimpulan)

### **Stage 1: Setup & Load Data**
- **Cell 1:** Import libraries (pandas, numpy, matplotlib, seaborn, scipy, warnings)
- **Cell 2:** Load raw CSV `GSPC_2018_2024.csv`
  - Parse `Date` sebagai datetime
  - Sort by date, reset index
  - Output: 1,552 trading days, 8 kolom (Date, Open, High, Low, Close, Volume, Dividends, Stock Splits)

### **Stage 2: Data Quality Check**
- **Cell 3:** Info DataFrame + missing values + duplicate rows
  - ✅ Hasil: 0 missing, 0 duplicate → data bersih

### **Stage 3: Deskriptif Statistik**
- **Cell 4:** Hitung summary stats (min, max, mean, std, CV%) untuk Open/High/Low/Close/Volume
  - Close range: 2,237–5,137 USD
  - Volume CV: 24.73% (cukup volatile)

### **Stage 4: Time Series Plot (Close + Volume)**
- **Cell 5:** Plot close price dengan volume, anotasi:
  - COVID-19 crash (Mar 2020)
  - Bear market 2022
  - Simpan: `eda_close_volume.png`

### **Stage 5: Daily Returns Distribution**
- **Cell 6:** Hitung `Daily_Return = pct_change() * 100`
  - Subplot 3 panel: time series, histogram+KDE, box-per-tahun
  - Stats: μ=+0.0499%, σ=1.295%, skew=-0.512, kurtosis=12.92
  - **Insight:** Fat tails (kurtosis tinggi), negative skew (crash lebih ekstrem)
  - Simpan: `eda_daily_return.png`

### **Stage 6: Moving Averages & Volatility**
- **Cell 7:** Hitung MA(20, 50, 200) + rolling volatility (30-day)
  - Plot price dengan 3 MAs + rolling vol
  - Simpan: `eda_ma_volatility.png`

### **Stage 7: OHLC Spread Analysis**
- **Cell 8:** Hitung intraday metrics:
  - `HL_Spread = High - Low` (intraday range)
  - `OC_Spread = Close - Open` (direction)
  - Subplot: HL spread time series, monthly avg, OC direction bar, pie bullish/bearish
  - Bullish days: 841 (54.2%), Bearish: 711 (45.8%)
  - Simpan: `eda_ohlc_spread.png`

### **Stage 8: Correlation Matrix**
- **Cell 9:** Hitung korelasi 7 fitur: Open, High, Low, Close, Volume, Daily_Return, HL_Spread
  - OHLC very high (~1.0), Volume ↔ HL_Spread: 0.59
  - Heatmap simpan: `eda_correlation.png`

### **Stage 9: Seasonal Patterns**
- **Cell 10:** Extract Month & DayOfWeek, hitung mean return per kategori
  - Best months: Nov (+0.23%), Jul (+0.20%)
  - Worst months: Sep (-0.16%), Feb (-0.04%)
  - Best days: Fri, Tue
  - Simpan: `eda_seasonal.png`

### **Stage 10: Cumulative Return & Drawdown**
- **Cell 11:** Hitung `Cum_Return`, `Drawdown` dari peak
  - Plot time series + fill
  - Output: Total cum return +90.33%, max drawdown -33.92%
  - Simpan: `eda_cumreturn_drawdown.png`

### **Stage 11: Summary Stats**
- **Cell 12:** Final ringkasan (table ASCII)
  - Totals, performance per tahun (2018–2024)
  - Volatility annualized: 20.47%

---

## Feature Engineering & Data Processing

### **Stage 12: Create Processed Dataset**
- **Cell 13:** Load raw → drop Dividends/Stock Splits
- **Cell 14:** Create features:
  - `Daily_Return` = pct_change()
  - `HL_Spread` = High - Low
  - `OC_Spread` = Close - Open
  - `MA_20` = rolling(20).mean()
  - `Volatility_30` = rolling(30).std() of daily return
- **Output:** 1,552 × 11 columns → save to `data/processed/stocks/GSPC_2018_2024.csv`
- **Missing:** Daily_Return (1), MA_20 (19), Volatility_30 (30) — expected (rolling window)

---

## Key Findings (Markdown Summary)

### **Main Insights**

1. **Price Trend:** +90.33% cumulative over 6 years (2,695 → 5,130 USD)
2. **Volatility Profile:**
   - Annualized: 20.47%
   - Volatility clustering visible → suitable for LSTM
3. **Distribution Properties:**
   - Negative skew (-0.51): left tail longer → crashes more extreme than rallies
   - Fat tails (kurtosis 12.92): extreme returns happen more often than normal distribution predicts
4. **Seasonal Pattern:**
   - November best, September worst
   - Friday & Tuesday average higher returns
5. **Bull/Bear Balance:** 54.2% bullish days vs 45.8% bearish

### **Implications for Model**
- Data quality excellent (clean, no missing in raw)
- Volatility clustering suggests LSTM can capture autocorrelation
- Fat tails → consider `RobustScaler` or `QuantileTransformer` for normalization
- Strong OHLC correlation → can drop some columns without info loss

---

## Outputs Generated

| Artifact | Description |
|----------|---|
| `eda_close_volume.png` | Close price time series with volume |
| `eda_daily_return.png` | Return distribution & annual breakdown |
| `eda_ma_volatility.png` | Moving averages & rolling volatility |
| `eda_ohlc_spread.png` | Intraday range & direction analysis |
| `eda_correlation.png` | Feature correlation heatmap |
| `eda_seasonal.png` | Monthly & day-of-week patterns |
| `eda_cumreturn_drawdown.png` | Cumulative return & drawdown curves |
| `GSPC_2018_2024.csv` (processed) | Clean dataset with engineered features |

---

## Notebook Metadata

| Property | Value |
|----------|-------|
| **Kernel** | Python 3 (ipykernel) |
| **Status** | Alive & Active |
| **Path** | `notebooks/01_EDA_stock_data.ipynb` |
| **Total Cells** | ~14 (11 EDA + 3 FE + markdown summary) |
| **Execution Time** | ~30–60 seconds (plots included) |

---

**Created:** 2026-06-05  
**Last Analyzed:** Via MCP jupyter tools  
**Purpose:** Template & reference untuk EDA future datasets
