# pair-trader-bbg-API


This is a cross boarder pair trader based on Bloomberg's API. Built in 2015-2016 it probably needs multiple upgrades to work.
It isn't supposed to be a high frequency system, the speed of the market data and order management is limited by the API speed - ~200ms - which is pretty slow, but worked for it's purpose which was cross boarder arbi.

This whole system was built in 3 months - oct-dec 2015. Built entirely by me, and needing to be expedited, I can't say I am proud of the code organization and structure. It should be much better structured, but I wasn't exactly focused on that at the time. Nowadays, I would structure this in a more efficient and clean way.

Developed for a brazilian broker dealer, all comments are in portuguese. 

The whole system has 3 files:
- An order management server - connects to Bloomberg API and connects to the strategy software.
- A market data server - connects to bloomberg data API and sends data to the strategy software.
- Strategy software - manages the strategy based on the data from the marked data server and sends/receives data to/from the order management server.

## Order Management Server:

Has a listener function:
  - listens and connects to the client (pair trade) - strategy software
  - Accepts connections
  - Starts a thread for receive instructions function (one for each pair trade)

Receive instructions function:
  - creates an instance of Class ManageOrders
  - creates a thread on the recieveResponseandCallback method
  - recieves instructions for that pair, parses and processes instructions

Class ManageOrders:
This class has the following methods:
  - open Bloomberg connection
  - close Bloomberg connection
  - receives and processes response event from bbg api
  - creates and routes orders
  - creates and routes orders with strategy
  - cancel order
  - modify order
  - modify order with strategy
  - close info connection

Finally we create 2 threads
  - one for listener function - starts listening to connection from the strategy software
  - one for receive instructions function - processes orders from strategy, sends to bloomberg, sends back order status


## Market Data Server

## Pair Trader GUI
