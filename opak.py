from beam import function


@function(name="monthly-expense")
def main():
    expenses = {
        "Januari": 1_500_000,
        "Februari": 1_750_000,
        "Maret": 1_200_000,
        "April": 1_650_000,
        "Mei": 1_450_000,
        "Juni": 1_800_000,
    }

    print("=== LAPORAN PENGELUARAN BULANAN ===")

    total = 0

    for month, amount in expenses.items():
        print(f"{month:10} : Rp{amount:,.0f}")
        total += amount

    average = total / len(expenses)

    print("-----------------------------------")
    print(f"Total      : Rp{total:,.0f}")
    print(f"Rata-rata  : Rp{average:,.0f}")

    return {
        "total": total,
        "average": average,
        "months": len(expenses),
    }
