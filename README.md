# wc-stripe-bookkeeping

How this works:

First you need to enter your credentials in the json folder, into the credentials.json file. Then download all orders and all stripe payout with both python files in the json folder. Then you can run the main file, which will output a csv, which is meant for use in RZL-Bookkeeping software. 

I wrote this for my own use, without having usability in mind. There will be some gotchas, like hardcoded dates in the order downloading scripts, missing order_meta that is expected from my shops, but that are not standard in usual WC installations, and so on. 
