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
from payout_filter import *
from book_payout import *

d = decimal.Decimal

###########
shop = "LF"
quarter = 1
year = 2021
###########

with open(f"json/orders-{shop}.json", "r") as file:
    order_list = json.loads(file.read())
with open(f"json/Stripe_payouts_{shop}.json", "r") as file:
    payout_list = json.loads(file.read())

payout_filtered = parse_payout(payout_list, order_list, quarter, year)

#################################
### Loop through every payout ###
#################################
rows = []
for i in reversed(range(len(payout_filtered))):
    rows.extend(book_payout(payout_filtered[i]))

############################
### Save all rows to csv ###
############################
if not os.path.exists('import'):
    os.mkdir('import')
with open(f"import/Import-{shop}-Q{str(quarter)}-{str(year)}.csv", "w") as csv_file:
    csvwriter = csv.writer(csv_file, delimiter=";")
    for row in rows:
        csvwriter.writerow(row)