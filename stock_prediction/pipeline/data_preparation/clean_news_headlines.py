"""Bersihkan dataset headline berita S&P 500: hapus kolom 'CP' dan pisahkan
menjadi versi 2008-2024 (penuh) serta 2018-2024 (subset)."""

import pandas as pd

RAW_DIR = "stock_prediction/data/raw/news"
SOURCE_FILE = f"{RAW_DIR}/sp500_headlines_2008_2024.csv"
OUTPUT_2008_2024 = f"{RAW_DIR}/sp500_headlines_2008_2024.csv"
OUTPUT_2018_2024 = f"{RAW_DIR}/sp500_headlines_2018_2024.csv"

SPLIT_DATE = "2018-01-01"


def main():
    df = pd.read_csv(SOURCE_FILE)
    df = df.drop(columns=["CP"])

    df.to_csv(OUTPUT_2008_2024, index=False)
    print(f"Tersimpan: {OUTPUT_2008_2024} ({len(df)} baris)")

    df_2018_2024 = df[df["Date"] >= SPLIT_DATE].reset_index(drop=True)
    df_2018_2024.to_csv(OUTPUT_2018_2024, index=False)
    print(f"Tersimpan: {OUTPUT_2018_2024} ({len(df_2018_2024)} baris)")


if __name__ == "__main__":
    main()
