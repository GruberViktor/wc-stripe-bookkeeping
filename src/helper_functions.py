import decimal
d = decimal.Decimal

def str_(input):
    return str(input).replace(".", ",")

### Das brauchts weiter unten, um Beträge mit drei Nachkommastellen abzurunden (Notwendig, wenn z.B. ein ganzer Order einen -15% Rabatt bekommen hat)
def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        x = d(value)
        ctx.rounding = decimal.ROUND_DOWN
        return round(x, decimals)

### Die Funktion brauchts damit auch wirklich bei .5 nach oben gerundet wird, und nicht erst bei .50001 oder sowas..  
def r(num):
    num += d(0.0000000001)
    res = num.quantize(d("0.01"), rounding="ROUND_HALF_UP")
    return res

### Kontrolliert ob die Summe der einzelnen addierten Positionen mit der Gesamtsumme (von WC) zusammenpassen. 
def control_for_errors(orders_arg):

    counter = 0
    total = 0

    for j in range(len(orders_arg["line_items"])):
        total += d(orders_arg["line_items"][j]["total"])

    for j in range(len(orders_arg["tax_lines"])):
        total += d(orders_arg["tax_lines"][j]["tax_total"])
        total += d(orders_arg["tax_lines"][j]["shipping_tax_total"])

    for j in range(len(orders_arg["shipping_lines"])):
        total += d(orders_arg["shipping_lines"][j]["total"])

    for j in range(len(orders_arg["fee_lines"])):
        total += d(round_down(orders_arg["fee_lines"][j]["amount"], 2))

    for j in range(len(orders_arg["coupon_lines"])):
        print(
            "Discount:",
            d(orders_arg["coupon_lines"][j]["discount"]),
            orders_arg["number"],
        )

    if d(orders_arg["total"]) == total:
        pass
    else:
        print("Problematic Order:", orders_arg["number"])
        print("WC-Total:", orders_arg["total"])
        print("Berechneter Total:", total)
        print("Differenz:", d(orders_arg["total"]) - d(total), "\n")
        input("Beliebige Taste zum fortfahren")

### Liste aller EU-Länder
EU_countries = [
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "ES",
    "FI",
    "FR",
    # "GB",
    "GR",
    "HR",
    "HU",
    "IE",
    "IT",
    "LI",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
    # "UK",
    "FO"
    ]