import json
from datetime import date
import calendar


def parse_payout(payouts, orders, quarter, year):

    ### Set Date Margins
    beginning = date(year, (quarter - 1) * 3 + 1, 1)
    end = date(year, quarter * 3, calendar.monthrange(year, quarter * 3)[1])

    ### Filter payouts by date
    payout_filtered = []
    for i in range(len(payouts)):
        datum = date(
            int(payouts[i]["date"][:4]),
            int(payouts[i]["date"][5:7]),
            int(payouts[i]["date"][8:10]),
            )
        if beginning <= datum and end >= datum:
            payout_filtered.append(payouts[i])

    ### Append WC Order object
    for i in range(len(payout_filtered)):
        for j in range(1, len(payout_filtered[i]["orders"])):
            capture = payout_filtered[i]["orders"][j]
            if capture["type"] in ["charge", "payment"]:
                ordernumber = capture["description"][-4:]
            elif capture["type"] == "refund":
                ordernumber = capture["description"][-5:-1]

            for k in range(len(orders)):
                if orders[k]["number"] == ordernumber.strip():
                    payout_filtered[i]["orders"][j]["wc-order"] = orders[k]
                    break
    
    return payout_filtered