import json
import datetime
from datetime import date
from datetime import datetime
import calendar
import csv
import sys
import decimal
from decimal import *
import math
from termcolor import colored

from helper_functions import *


with open("json/taxrates.json", "r") as file:
    tax_rates = json.loads(file.read())

gegenkonto = "2801"


def book_payout(payout):
    payout_rows = []
    gegenbuchung = d(0.00) 

    booking_date = datetime.fromisoformat(payout["date"]).strftime("%d%m%Y")

    # Die Fees eines jeden Orders innerhalb eines Payouts werden hier addiert. 
    # Werden später in eine Buchungszeile pro Payout gebucht.
    payout_fees = d(0)

    # Loopt durch alle Stripe Captures, die die Order Infos weiter oben schon dabei haben.
    for j in range(1, len(payout["orders"])):
        capture = payout["orders"][j]

        ###
        booked_capture = book_capture(capture, booking_date)
        ###

        payout_rows.extend(booked_capture["rows"])

        gegenbuchung += booked_capture["total"]
        payout_fees += d(capture["fee"]) / 100
    
    if d(payout["orders"][0]["net"]) / -100 != gegenbuchung - payout_fees:
        print(colored(f"Payout falsch! ({payout['payout_id']})", "red"))
        print("Gegenbuchung: ", gegenbuchung - payout_fees, "Stripe:", d(payout["orders"][0]["net"]) / -100)
        print("Differenz:", gegenbuchung - payout_fees - d(payout["orders"][0]["amount"]) / -100)
        print(str(len(payout["orders"])) + " orders im Payout")
        input()
    else:
        print(colored("Payout passt!", "green"))
        print("Gegenbuchung: ", gegenbuchung - payout_fees, "Stripe:", d(payout["orders"][0]["net"]) / -100)
        print("Differenz:", gegenbuchung - payout_fees - d(payout["orders"][0]["amount"]) / -100)

    ### Abschluss Rows ###
  
    steuer_betrag = d(payout_fees) / 100 * 20

    row = [ 
        "7791", 
        gegenkonto,
        "0",
        booking_date,
        None,
        "EUR",
        str_(payout_fees.quantize(Decimal(".01"), rounding=ROUND_HALF_DOWN)),
        "0",
        str_(r(steuer_betrag)),
        None,
        "0",
        "0",
        "0",
        "BA",
        "0",
        "1",
        "20",
        "1",
        "05",
        "2",
        None,
        None,
        None,
        "Stripe Spesen",
        None,
        None]
    payout_rows.append(row)

    ########## GEGENBUCHUNG ###########

    row = [
        gegenkonto,
        "0",
        "0",
        booking_date,
        None,
        "EUR",
        str_(gegenbuchung - payout_fees),
        "0",
        "0",
        None,
        "0",
        "0",
        "0",
        "BA",
        "0",
        "1",
        "0",
        "0",
        "0",
        "5",
        None,
        None,
        None,
        "Stripe Payout vom {}".format(booking_date),
        None,
        None,
        ]
    payout_rows.append(row)
    
    return payout_rows


def book_capture(capture, booking_date):
    """
    Returns one or more (if multiple VAT-rates in order) RZL-rows of a stripe capture. 
    Can be either a charge or a refund.
    """
    
    order = parse_order(capture)

    ### Return values ###
    rows = []
    total = d(0)

    ### Check if order has invoice
    if order["invoice"] == "":
        print(f"Order {order['number']} has no invoice")
        input(capture["description"])
    
    ### Check for type of charge
    if capture["type"] in ["charge", "payment"]:
        for value in order:
            if type(order[value]) == d:
                total += order[value]

        if order["type"] == "normal":
            if d(order["10_netto"]) > d(0):

                row = [ 
                    "4010",
                    gegenkonto,
                    "0",
                    booking_date,
                    None,
                    "EUR",
                    "0",
                    str_(order["10_netto"]),
                    str_(order["10_tax"]),
                    None,
                    "0",
                    "0",
                    "0",
                    "BA",
                    "0",
                    "1",
                    "10",
                    "2",
                    "0",
                    "2",
                    None,
                    None,
                    None,
                    order["invoice"],
                    None,
                    None,
                    ]
                rows.append(row)

            if d(order["20_netto"]) > d(0):
                if r(order["20_netto"] / 5) != order["20_tax"]:
                    print(order['number'] + " zickt")
                    input()

                row = [
                    "4020",
                    gegenkonto,
                    "0",
                    booking_date,
                    None,
                    "EUR",
                    "0",
                    str_(order["20_netto"]),
                    str_(order["20_tax"]),
                    None,
                    "0",
                    "0",
                    "0",
                    "BA",
                    "0",
                    "1",
                    "20",
                    "2",
                    "0",
                    "2",
                    None,
                    None,
                    None,
                    order["invoice"],
                    None,
                    None,
                    ]
                rows.append(row)
        elif order["type"] == "IGL":
            row = [
                "4005",
                gegenkonto,
                "0",
                booking_date,
                None,
                "EUR",
                "0",
                str_(order["0_netto"]),
                "0",
                None,
                "0",
                "0",
                "0",
                "BA",
                "0",
                "1",
                "02",
                "2",
                "0",
                "2",
                None,
                None,
                None,
                order["invoice"],
                None,
                order["uid"],
                ]
            rows.append(row)
        elif order["type"] == "export":
            row = [
                "4000",
                gegenkonto,
                "0",
                booking_date,
                None,
                "EUR",
                "0",
                str_(order["0_netto"]),
                "0",
                None,
                "0",
                "0",
                "0",
                "BA",
                "0",
                "1",
                "01",
                "2",
                "0",
                "2",
                None,
                None,
                None,
                order["invoice"],
                None,
                None,
                ]
            rows.append(row)

        ######################
        ### Validate order ###
        ######################
        # Makes sure that totals of parsed order and payout line up
        total = d(0)
        for value in order:
            if type(order[value]) == d:
                total += order[value]
        if total != d(capture["amount"]) / 100:
            print("Totals don't line up", capture["description"])
            print(total, d(capture["amount"]) / 100)
            print(order)
            input()
    
    elif capture["type"] in ["refund", "payment_refund"]:
        amount = d(capture["amount"]) / 100
        total += amount
        if order["type"] == "normal":
            tax_type = str(order["tax_type"])
            if tax_type == "mixed":
                print("you're fucked")

            net = r(amount / (1 + d(order["tax_type"]) / 100))
            tax = amount - net
            
            print(f"Refund for order {order['number']} --> net: {net}, tax: {tax}")

            row = [ 
                "40" + tax_type,
                gegenkonto,
                "0",
                booking_date,
                None,
                "EUR",
                "0",
                str_(net),
                str_(tax),
                None,
                "0",
                "0",
                "0",
                "BA",
                "0",
                "1",
                "10",
                "2",
                "0",
                "2",
                None,
                None,
                None,
                order["invoice"],
                "Erstattung",
                None,
                ]
            rows.append(row)
        elif order["type"] == "IGL":
            row = [
                "4005",
                gegenkonto,
                "0",
                booking_date,
                None,
                "EUR",
                "0",
                amount,
                "0",
                None,
                "0",
                "0",
                "0",
                "BA",
                "0",
                "1",
                "02",
                "2",
                "0",
                "2",
                None,
                None,
                None,
                order["invoice"],
                "Erstattung",
                order["uid"],
                ]
            rows.append(row)
        elif order["type"] == "export":
            row = [
                "4000",
                gegenkonto,
                "0",
                booking_date,
                None,
                "EUR",
                "0",
                amount,
                "0",
                None,
                "0",
                "0",
                "0",
                "BA",
                "0",
                "1",
                "01",
                "2",
                "0",
                "2",
                None,
                None,
                None,
                order["invoice"],
                "Erstattung",
                None,
                ]
            rows.append(row)
    
    ### Make sure rows were generated
    if len(rows) == 0:
        print(capture["description"])
        print(order)
        input("No rows generated")

    return {"rows": rows, "total": total}


def parse_order(capture):
    
    if capture.get("source"):
        order = capture["wc-order"]
    else:
        order = capture

    # print(order["number"], order["total"])
    def validate():
        validation = d(0)
        for value in order_data:
            if type(order_data[value]) == d:
                validation += order_data[value]
        # return validation == d(order["total"]), validation
        try:
            return validation == d(capture["amount"])/100, validation
        except:
            return validation == d(order["total"]), validation

    order_data = {
        "type": None,
        "tax_type": None,
        "invoice": "",
        "0_netto": d(0),
        "0_tax": d(0),
        "10_netto": d(0),
        "10_tax": d(0),
        "20_netto": d(0),
        "20_tax": d(0),
        "exempt": None,
        "uid": None,
        "number": order["number"]
        }

    ############################
    ### Determine Order Type ###
    ############################

    ### Tax exemption check
    for i in range(len(order["meta_data"])):

        if order["meta_data"][i]["key"] == "is_vat_exempt":
            order_data["exempt"] = order["meta_data"][i]["value"]

        elif order["meta_data"][i]["key"] == "_billing_eu_vat":
            if order["meta_data"][i]["value"] != "":
                uid = order["meta_data"][i]["value"]
                country = order["billing"]["country"]

                if not uid[:2].upper() == country:
                    uid = f'{country}{uid}'.replace(" ", "")
                else:
                    uid = uid.upper().replace(" ", "")
                
                order_data["uid"] = uid

        elif order["meta_data"][i]["key"] == "_bewpi_invoice_pdf_path":
                order_data["invoice"] = order["meta_data"][i]["value"][5:-4]

    ### Autofill country if no shipping is provided (Workshops)
    if order["shipping"]["country"] == "":
        order["shipping"]["country"] = "AT"
        print("Shipping country automatically set")

    ### Determine order type - by country and exemption status
    if (order["shipping"]["country"] in EU_countries 
        and order_data["exempt"] == "yes"):
        order_data["type"] = "IGL"
    elif (order["shipping"]["country"] in EU_countries
        and order_data["exempt"] != "yes"
        and order_data["exempt"] != None
        ):
        order_data["type"] = "normal"
    elif order["shipping"]["country"] not in EU_countries:
        order_data["type"] = "export"

    if order["number"] in ["1891", "1889", ]:
        order_data["type"] = "normal"
        order_data["tax_type"] = 10 
    
    ### Ask for type if unable to determine
    if order_data["type"] == None:
        if order["billing"]["country"] == "AT":
            order_data["type"] = "normal"
        else:
            while True:
                print(f"Order von {order['billing']['last_name']}, {order['billing']['company']} fiel durch die Ritzen. ID: {order['id']}")
                antwort = input("exempt? (y or n)")
                if antwort == "y":
                    order_data["type"] = "IGL"
                    break
                elif antwort == "n":
                    order_data["type"] = "normal"
                    break
                else: 
                    print("(y)es or (n)o")

    ########################
    ### Calculate totals ###
    ########################
    ### Go through each kind of possible charge within one order
    for lines in [
                order["line_items"],
                order["shipping_lines"],
                order["fee_lines"]
                ]:

        ### Go through each position within charge
        for i in range(len(lines)):
            item = lines[i]

            ### Ignore if zero-value position
            if d(item["total"]) == d("0"):
                continue
            
            ### Determine applicable tax rate of item
            if order_data["type"] == "normal":
                try:
                    for rate in item["taxes"]:
                        if rate["total"] != "":
                            tax_rate = d(tax_rates[order["website"]][str(rate["id"])]["rate"])
                except:
                    print("COULD NOT DETERMINE TAX RATE")
            else:
                tax_rate = d(0)
            
            ### Add net price to applicable subtotal 
            if lines == order["line_items"] and order_data["type"] == "normal":
                ### price * quanitity helps avoid rounding errors ("price" is not yet rounded, while "total" is)
                order_data[str(int(tax_rate)) + "_netto"] += d(item["price"]) * item["quantity"]
                # order_data[str(int(tax_rate)) + "_netto"] += d(item["subtotal"])
            
            elif lines == order["line_items"] and order_data["type"] != "normal":
                order_data[str(int(tax_rate)) + "_netto"] += d(item["total"])
            
            else:   
                ### Shipping lines and fee lines 
                net = (d(item["total"]) + d(item["total_tax"])) / ((100 + tax_rate) / 100 )
                order_data[str(int(tax_rate)) + "_netto"] += net

    ### Correct single orders...
    if order["number"] == "2372":
        order_data["0_netto"] += d(25)
    if order["number"] == "1953":
        order_data["10_netto"] = d(59.26)
    if order["number"] == "1392":
        order_data["10_netto"] = d(82.76)
        order_data["10_tax"] = d(8.28)

    #################################################
    ### Determine Order Type and Calculate Taxes ####
    #################################################
    if order_data["10_netto"] > d(0):
        order_data["tax_type"] = 10
        order_data["10_tax"] = r(order_data["10_netto"] / 10)
    if order_data["20_netto"] > d(0):
        order_data["tax_type"] = 20
        order_data["20_tax"] = r(order_data["20_netto"] / 5)
    if order_data["0_netto"] > d(0):
        order_data["tax_type"] = 0
    if order_data["10_netto"] > d(0) and order_data["20_netto"] > d(0):
        order_data["tax_type"] = "mixed"
        input("MIXED")

    ## Rounding
    for value in order_data:
        if type(order_data[value]) == d:
            order_data[value] = r(order_data[value])
    
    ####################
    ### Coupon Lines ###
    ####################
    for line in order["coupon_lines"]:
        for meta in line["meta_data"]:
            if meta["key"] == "coupon_data":
                coupon = meta["value"]
                if coupon["discount_type"] == "percent":
                    for tax in ["0", "10", "20"]:
                        order_data[tax + "_netto"] = r(order_data[tax + "_netto"] * (1 - d(coupon["amount"]) / 100))
                        order_data[tax + "_tax"] = r(order_data[tax + "_tax"] * (1 - d(coupon["amount"]) / 100))
    
    ##################
    ### Validation ###
    ##################
    validation = validate()
    try: 
        if (validation[1] != d(capture["amount"])/100 
            and order_data["0_netto"] > d(0)):
            order_data["0_netto"] = d(capture["amount"])/100
    except KeyError:
        pass
    
    validation = validate()
    if validation[0] == False:
        print(colored(f"Validation of order {order_data['number']} failed", "red"))
        try:
            print(f"Calculated from WC: {validation[1]}, Order total: {d(capture['wc-order']['total'])}")
            print(f"Stripe Amount: {d(capture['amount'])/100}")
        except KeyError:
            print(f"Calculated from WC: {validation[1]}, Order total: {d(order['total'])}")
            
       
        with open("single_order.json", "w+") as file:
            file.write(json.dumps(capture))

        diff = abs(validation[1] - d(order["total"]))
        tax_rates_ = ["0", "10", "20"]

        print(f"Difference: {diff}")
        counter = 1
        for tax_rate in tax_rates_:
            print(f"{counter}: Tax rate: {tax_rate} -->", order_data[tax_rate + "_netto"], order_data[tax_rate + "_tax"])
            counter += 1
        

        while True:
            print("Which position would you like to edit? (Or do: \u0332Nothing? \u0332Reverse Charge?")
            tax_rate_selection = input()
            if tax_rate_selection == "":
                continue
            if tax_rate_selection == "n":
                break
            if tax_rate_selection == "r":
                for position in order_data:
                    if order_data[position] == d():
                        order_data[position] *= -1
                break
            if int(tax_rate_selection) in range(1,4):
                tax_rate_selection = tax_rates_[int(tax_rate_selection) - 1]

                while True:
                    print("Should totals (1) or tax (2) be edited? ")
                    tax_or_totals = int(input())
                    if tax_or_totals == 1:
                        tax_or_totals = "netto"
                        break
                    elif tax_or_totals == 2:
                        tax_or_totals = "tax"
                        break
                while True:
                    print(f"Add (+) or subtract (-) difference ({diff})?")
                    add_or_subtract = str(input())
                    if add_or_subtract in ["+", "-"]:
                        break

                if add_or_subtract == "+":
                    order_data[tax_rate_selection + "_" + tax_or_totals] += diff

                elif add_or_subtract == "-":
                    order_data[tax_rate_selection + "_" + tax_or_totals] -= diff
                    
                print(order_data[tax_rate_selection + "_" + tax_or_totals])

                break
            
        
        
        print(order_data)
            
    
    return order_data 
