import pandas as pd
from datetime import datetime, timedelta
import calendar

# === 1. Load input datasets ===
# Replace with your actual file paths or database queries
dpld_current = pd.read_csv("DPLD_current.csv")
dpld_prev = pd.read_csv("DPLD_prev.csv")
dpld_preprev = pd.read_csv("DPLD_preprev.csv")
lnld = pd.read_csv("LNLD.csv")

# === 2. Compute report dates ===
today = datetime.today()
reptdate = datetime(today.year, today.month, 1)
prv_reptdate = reptdate - timedelta(days=1)
ssreptdate = datetime(prv_reptdate.year, prv_reptdate.month, 1)
pprv_reptdate = ssreptdate - timedelta(days=1)

REPTMON = reptdate.month
REPTYEAR = reptdate.year
RDATE = reptdate.strftime("%d/%m/%Y")
PREPTMON = prv_reptdate.month
PPREPTMON = pprv_reptdate.month

# === 3. Combine DPLD datasets ===
dpld_all = pd.concat([dpld_current, dpld_prev, dpld_preprev], ignore_index=True)

# === 4. Prepare LNLD dataset ===
# You would need to adjust these column names based on your actual CSV layout
lnld = lnld.rename(columns={
    "ACCTNO": "acctno",
    "TRANDT": "trandt",
    "TRANAMT": "tranamt",
    "TRANCODE": "trancode",
    "FEEPLAN": "feeplan"
})
# Filter cost center range
lnld = lnld[~((lnld["COSTCTR"] < 3000) | (lnld["COSTCTR"] > 3999))]
lnld = lnld[~lnld["COSTCTR"].isin([4043, 4048])]

# === 5. Merge DPLD and LNLD by keys ===
tranx = pd.merge(lnld, dpld_all, on=["acctno", "trandt", "tranamt"], how="inner")

# === 6. Apply formats ===
tcode_map = {
    310: "LOAN DISBURSEMENT",
    750: "PRINCIPAL INCREASE (PROGRESSIVE LOAN RELEASE)",
    752: "DEBITING FOR INSURANCE PREMIUM",
    753: "DEBITING FOR LEGAL FEE",
    754: "DEBITING FOR OTHER PAYMENTS",
    760: "MANUAL FEE ASSESSMENT FOR PAYMENT TO 3RD PARTY",
}

feefmt_map = {
    "QR": "QUIT RENT", "LF": "LEGAL FEE & DISBURSEMENT", "VA": "VALUATION FEE",
    "IP": "INSURANCE PREMIUM", "PA": "PROFESSIONAL/OTHERS", "AC": "ADVERTISEMENT FEE",
    "MC": "MAINTENANCE CHARGES", "RE": "REPOSSESSION CHARGES", "RI": "REPAIR CHARGES",
    "SC": "STORAGE CHARGES", "SF": "SEARCH FEE", "TC": "TOWING CHARGES", "99": "MISCELLANEOUS EXPENSES"
}

tranx["tranamt1"] = tranx["tranamt"] / 1000
tranx["value"] = 1
tranx["trnxdesc"] = tranx["trancode"].map(tcode_map)
tranx.loc[(tranx["trancode"] == 760) & tranx["feeplan"].notna(), "trnxdesc"] = \
    tranx["feeplan"].map(feefmt_map)

# === 7. Report 1: Summary of all cheques issued ===
summary = (
    tranx.groupby("value")["tranamt1"]
    .agg(NUMBER_OF_CHEQUES="count", VALUE_OF_CHEQUES_RM000="sum")
    .reset_index()
)
print("\nREPORT ID : EIBQEPC1")
print("PUBLIC BANK BERHAD")
print(f"CHEQUES ISSUED BY THE BANK AS AT {RDATE}")
print(summary)

# === 8. Report 2: Top 5 by number of cheques ===
tran1 = tranx.groupby("trnxdesc", dropna=False)["tranamt1"].agg(UNIT="count", SUM="sum").reset_index()
tran1 = tran1.sort_values(by="UNIT", ascending=False)
tran1["COUNT"] = range(1, len(tran1) + 1)
top5_by_number = tran1.head(5)
print("\nTOP 5 PAYMENTS BY NUMBER OF CHEQUES")
print(top5_by_number[["COUNT", "trnxdesc", "UNIT", "SUM"]])

# === 9. Report 3: Top 5 by total value ===
tran2 = tranx.groupby("trnxdesc", dropna=False)["tranamt1"].agg(UNIT="count", SUM="sum").reset_index()
tran2 = tran2.sort_values(by="SUM", ascending=False)
tran2["COUNT"] = range(1, len(tran2) + 1)
top5_by_value = tran2.head(5)
print("\nTOP 5 PAYMENTS BY VALUE OF CHEQUES")
print(top5_by_value[["COUNT", "trnxdesc", "UNIT", "SUM"]])
