```
  Used OOP and API programming to built and Automated trading system for a broker dealer generated revenue in avoided costs of $300k a year. 
    Tools:
      - Algorithms
      - OOP
      - Multithreading
      - Logging
      - GUI
      - API real-time data processing
      - cross-boarder arbitrage model
      - Order Management Architecture
      
```


This is a pair trader system developed in 5 months using Bloomberg's(BBG) EMSX API.

I learned python while developing this system.

It is composed by:
- Market Data Server - subscribes to marked data coming from BBG in realtime connects to PairTrader and sends market data to it.
- Order Management Server - manages orders recieved from the PairTrader and sends them to BBG then processes callbacks from the orders. Also in realtime.
- PairTrader - has the strategy, pairs, desired margin, sends orders, recieves market data and does FX calculation.
- GUI - integrates PairTrader into a GUI built on wx

All files were compiled into exe files and would be run either on the same computer or on different computers (servers on one, pairtrader on other computers)

