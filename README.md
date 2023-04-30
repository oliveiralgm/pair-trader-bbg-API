This is a pair trader system developed in 5 months using Bloomberg's(BBG) EMSX API.

I learned python while developing this system.

It is composed by:
- Market Data Server - recieves marked data coming from BBG in realtime.
- Order Management Server - manages orders recieved from the PairTrader and sends them to BBG then processes callbacks from the orders. Also in realtime.
- PairTrader - has the strategy, pairs, desired margin, sends orders, recieves market data and FX calculation.
- GUI - integrates PairTrader into a GUI built on wx

All files were created into exe files and would be run either in the same computer or from different computers (servers on one, pairtrader on other computers)

There is a folder and a readme for each module of the code.

Any questions send me an email: oliveiralgm@gmail.com
