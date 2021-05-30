import stripe
import sys
from datetime import datetime
import json
import time

with open("credentials.json", "r") as file:
    shops = json.loads(file.read())["Stripe"]

for shop in shops:
    stripe.api_key = shop["key"]
    payouts = stripe.Payout.list(
        arrival_date={"gt":"{}".format(
            int( datetime(2020,11,1,00,00).timestamp() )
                ),
                
                "lt":"{}".format(
            int( datetime.now().timestamp() )
                ) 
            }
    )
            
    payouts_list = []
    for i in payouts.auto_paging_iter():
        payouts_list.append(i)

    print("Start..")
    time1 = time.time()

    balance_transactions = []
    meine_payouts = []

    for i in range(len(payouts_list)):
        datum = datetime.fromtimestamp(payouts_list[i]["arrival_date"]).isoformat()
        meine_payouts.append( {"payout_id": payouts_list[i]["id"], "date": datum } )

        # tx_list = []
        # while True:
        #     starting_after = ""
        #     tx = stripe.BalanceTransaction.list( payout=payouts_list[i]["id"], limit=100, starting_after=starting_after )
        #     tx_laenge = 0 
        #     for item in tx:
        #         tx_list.append(item)

        #     if tx["has_more"] == False:
        #         break
        #     else:
        #         starting_after = tx

        tx_list = []
        tx = stripe.BalanceTransaction.list( payout=payouts_list[i]["id"], limit=100 )
        for item in tx.auto_paging_iter():
            tx_list.append(item)
        # tx_laenge = 0 
        # for item in tx:
        #     tx_list.append(item)    
            

        meine_payouts[i]["orders"] = tx_list

    time2 = time.time()
    print("Ende.. Dauer:{} sekunden".format(time2-time1))

    #print(meine_payouts)


    json_file = open(f"Stripe_payouts_{shop['name']}.json", "w")
    json_file.write(json.dumps(meine_payouts))
    json_file.close()