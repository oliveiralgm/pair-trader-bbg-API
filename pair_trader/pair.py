'''

A Classe Pair cria uma instancia da estrategia de cross-border arbitrage. A estrategia se baseia na cotacao de fechamento
do ativo operado, a cotacao do cambio e o spread requisitado pelo oeprador. Com esses dados ele calcula o preco a ser apregoado
e envia a ordem com os dados pre definidos pelo operador.

Assim que a ordem eh enviada o trader recebe a confirmacao e o sequence number dessa ordem e passa a receber seu status.
Para cada tipo de status recebido o trader chama o callback adequado. Ao mesmo tempo em outro thread sao recebidos o market
data, que sao usados para recalcular o preco de apregoamento e enviar um pedido de alteracao da ordem. Ele nao recebe
confirmacao da alteracao, mas recebe um status de working e o novo preco. Se o novo preco for diferente do preco
calculado ele reenvia o pedido de alteracao.

Ao receber o fill o callback envia a outra perna do trader para fechar o trade ou para abrir outra posicao. O trader fica
nesse loop ate ser requisitado o stop pelo operador ou atingir a posicao maxima requisitada (ainda nao implementado)

Este modulo eh inserido no GUI_Spread_Sniper_II.py '''

'''
CLASSE de Par de Arbitragem
'''

# Importa as dependencias do codigo
import socket
import string
import random
import math
import time
import datetime
import threading
import winsound
from threading import Thread, Lock
import logging
from enum import Enum
import win32com.client as win32
# from pubsub import pub
from wx.lib.pubsub import pub
import wx



class Pair():

    #  Metodo de inicializacao do Par
    def start_pair(self):
        if not self.pairRunning:
            if not self.pair_started: # boolean de par inicializado
                if self.MktDataStarted: # se o tader foi parado e ja tiver o MKT DATA rodando, temos que enviar ordem sem reiniciar a conexao que ja existe
                    print self.cancelOrderSent
                    self.cancelOrderSent = False # reinicia o booleano de envio da ordem para cancelamento que para o fluxo de envio de ordens
                    self.place_order_sent = 0 # se deu erro no envio, atribui o valor VERDADEIRO para impedir que o Trader passe a enviar ordens em loop
                    self.stopModifyRequests = False
                    print self.cancelOrderSent
                    self.place_Order() # envia ordem de place
                else:

                    # boolean = true se o Trader atingiu o limite de volume requisitado
                    self.reachedTotalVolumeTraded = False

                    try:
                        # thread de conexao do market data
                        self.mktData_Thread = Thread(target=self.connect_mktData)
                        # thread de conexao do OMS
                        self.orderManagement_Thread = Thread(target=self.connect_OrderManager)
                    except:
                        # exception para debug
                        print "Deu pau em algum thread"

                    # cria a lista de ativos a subscrever ao mkt data assim como os campos a subscrever
                    self.list_Subscription = [str(self.ticker_Close) + "," + str(self.close_field.name),
                                              str(self.ticker_Place) + "," + str(self.place_field.name),
                                          str(self.ticker_FX) + "," + str(self.FX_field.name)]
                    # for i in list_Subscription:
                    #     print i
                    #
                    # print list_Subscription[0]
                    # print list_Subscription[1]

                    try:
                        self.recievedClosedata = False # boolean para enviar a primeira ordem com dados atualizados
                        self.recievedFXdata = False # boolean para enviar a primeira ordem com dados atualizados
                        self.OMSStarted = False
                        # inicializa o thread de mkt data
                        self.mktData_Thread.start()
                        self.MktDataStarted = True
                        # time.sleep(1)
                        # inicializa o thread do OMS
                        self.pairRunning = True
                        # self.orderManagement_Thread.start()
                    except:
                        # exception para debug
                        print "Deu pau em algum thread"


                # self.newOrderlock = threading.Lock()
                # # incializa o boolean de envio de cancelar ordem como Falso
                # self.cancelOrderSent = False
                # # inicializa o boolean de ordem de apregoamento como Falso
                # self.get_Place_OrderSent(False)
                # self.newOrderlock.acquire()
                # try:
                #     # print para debug
                #     print self.dataPlace
                #     print self.dataClose
                #     # envia a primeira ordem
                #
                #
                #     self.place_Order()
                # except:
                #     lgr.info(str(self.corrID) + " -Deu pau no place order dentro do PairTrader")
                # self.newOrderlock.release()
                # self.pair_started = True

            else:
                pass
                # se par inicializado, envia o status para o GUI de que o par ja esta operando
                # self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str('JA ESTOU OPERANDO'))
                # time.sleep(0.003)

    # metodo de inicializacao dos dados iniciais - chamado dentro do GUI quando carrega os dados da planilha excel
    # Recebe os dados no formato de tres vetores
    def initializeData(self, DataPlace, DataClose, DataFX):

        # '10.0.0.94' - comp casa
        # '10.48.8.102' - comp XP
        # '10.48.8.110' - comp XP Henrique
        # '10.48.8.110' - comp Henrique porta Gustavo
        self.MachineConnection_IP_MKTDATA = ('localhost', 2012)
        print str(self.MachineConnection_IP_MKTDATA)
        self.MachineConnection_IP_OMS = ('localhost', 2011)
        print str(self.MachineConnection_IP_OMS)


        # limite de variacao de preco aceito pelo Trader
        self.thresholdPrice = 0.10
        # limite maximo financeiro por ordem permitido
        self.moneyThreshold = 0.10
        # limites de variacao do Spread realizado e Spread medio
        self.avgspreadThreshold = 0.15
        self.spreadThreshold = 0.90

        self.numberOfCompletePairs = 0
        self.gross_acumulated = 0
        self.average_spread = 0
        self.badspreadcount = 0
        self.spread_captured = 0
        self.gross_PNL_captured = 0
        self.tradedVolume = 0

        # atribui o valor falso ao boolean se o par ja foi inicializado
        self.pairRunning = False
        self.pair_started = False
        self.MktDataStarted = False
        self.stopModifyRequests = False
        self.recievedCancelStatus = False
        self.MarketSpread = 0
        '''
            recebe todos os dados dos pares operados
        '''

        # Volume total a ser operado por este par:

        self.totalPairPosition = DataPlace[placeOrderData.TOTPAIRVOL.value]

        # dados da ordem apregoada
        self.get_Place_Ticker(DataPlace[placeOrderData.TICKER.value])
        self.get_Place_Account(DataPlace[placeOrderData.ACCOUNT.value])
        self.ratio = DataPlace[placeOrderData.RATIO.value]
        self.get_Place_Amount(DataPlace[placeOrderData.AMOUNT.value])
        self.get_Place_Hand_Inst(DataPlace[placeOrderData.HAND_INSTR.value])
        self.get_Place_LmtPrc(DataPlace[placeOrderData.LMTPRC.value])
        self.last_lmtprcPlace = DataPlace[placeOrderData.LMTPRC.value] # O last_lmtprcPlace inicial eh igual ao enviado pela primeira vez
        self.moneyamount_place = float(DataPlace[placeOrderData.LMTPRC.value])*float(DataPlace[placeOrderData.AMOUNT.value])
        self.get_place_Broker(DataPlace[placeOrderData.BROKER.value])
        self.get_place_BrokerStrat(DataPlace[placeOrderData.BROKER_STRATEGY.value])
        # precisa pegar o SIDE do close antes de chamar get_Place_Side
        self.close_Side = DataClose[closeOrderData.SIDE.value]
        self.use_FX = DataPlace[placeOrderData.USEFX.value]
        self.get_Place_Side(DataPlace[placeOrderData.SIDE.value])
        self.get_Place_TIF(DataPlace[placeOrderData.TIF.value])
        self.get_Place_TraderNotes(DataPlace[placeOrderData.TRADER_NOTES.value])
        self.get_Place_Type(DataPlace[placeOrderData.TYPE.value])
        self.Pmargem = DataPlace[placeOrderData.SPREAD_REQ.value]
        self.get_Place_OrderSent(False)
        self.use_FX = DataPlace[placeOrderData.USEFX.value]
        # Define se o broker usa estrategia no envio de ordem ou nao
        if self.place_brokerstrat == "":
            self.get_Place_UseStrat(False)
        else:
            self.get_Place_UseStrat(True)
        self.get_Place_AvgPrice(0)
        self.get_Place_Fill(0)

        # dados da ordem de fechamento da perna
        self.get_Close_Ticker(DataClose[closeOrderData.TICKER.value])
        self.get_Close_Account(DataClose[closeOrderData.ACCOUNT.value])
        # self.get_Close_Amount(DataClose[closeOrderData.AMOUNT.value])
        self.get_Close_Hand_Inst(DataClose[closeOrderData.HAND_INSTR.value])
        self.get_Close_LmtPrc(DataClose[closeOrderData.LMTPRC.value])

        # dicionario que guarda os precos de close para atualizar a ordem de fechamento
        self.ClosePrice = {str(DataPlace[placeOrderData.LMTPRC.value]) : str(DataClose[closeOrderData.LMTPRC.value])}

        self.moneyamount_close = float(DataClose[closeOrderData.LMTPRC.value])*float(self.amount_Close)
        self.last_lmtprcClose = DataClose[closeOrderData.LMTPRC.value] # O last_lmtprcClose inicial eh igual ao enviado pela primeira vez
        self.get_close_Broker(DataClose[closeOrderData.BROKER.value])
        self.get_close_BrokerStrat(DataClose[closeOrderData.BROKER_STRATEGY.value])
        self.get_Close_TIF(DataClose[closeOrderData.TIF.value])
        self.get_Close_TraderNotes(DataClose[closeOrderData.TRADER_NOTES.value])
        self.get_Close_Type(DataClose[closeOrderData.TYPE.value])
        self.get_corrID()
        if self.close_brokerstrat == "":
            self.get_Close_UseStrat(False)
        else:
            self.get_Close_UseStrat(True)

        self.get_Close_AvgPrice(0)
        self.get_Close_Fill(0)
        self.get_Close_OrderSent(False)


        # dados do FX
        self.FX_get_Ticker(DataFX[FXData.TICKER.value])
        # se estiver utilizando o Dolar Futuro Mini - atribuir os valores do CASADO para calculo do Futuro - CASADO
        if self.ticker_FX[0:3] == "WDO":
            self.casado_bid = DataFX[FXData.CASADO_BID.value]
            self.casado_ask = DataFX[FXData.CASADO_ASK.value]
        self.get_FX_Price(DataFX[FXData.PRICE.value])
        # posicao inicial do Trader
        self.position = 'Zerado - ainda nao executou ordens'
        # incializa o vetor dos dados de apregoamento
        self.dataPlace = [self.ticker_Place,
                     self.amount_Place,
                     self.type_Place,
                     self.TIF_Place,
                     self.hand_instr_Place,
                     self.place_Side,
                     self.place_broker,
                     self.place_account,
                     self.place_traderNotes,
                     self.corrID,
                     self.place_brokerstrat,
                     self.place_use_strat,
                     self.place_order_sent,
                     self.place_avgprice,
                     self.place_lmtprc,
                     self.place_fill]
        # incializa o vetor dos dados de fechamento
        self.dataClose = [self.ticker_Close,
                     self.amount_Close,
                     self.type_Close,
                     self.TIF_Close,
                     self.hand_instr_Close,
                     self.close_Side,
                     self.close_broker,
                     self.close_account,
                     self.close_traderNotes,
                     self.corrID,
                     self.close_brokerstrat,
                     self.close_use_strat,
                     self.close_order_sent,
                     self.close_avgprice,
                     self.close_lmtprc,
                     self.close_fill]

        self.fileName = 'Trader -' + str(self.corrID) + '.log'


        lgr.debug(str(self.corrID) + ' -Ordem Fechamento: ' + str(self.dataClose[closeOrderData.TICKER.value]) + ' -' + str(self.dataClose[closeOrderData.SIDE.value]) + '@' + str(self.dataClose[closeOrderData.LMTPRC.value]))
        lgr.debug(str(self.corrID) + ' -Ordem Apregoamento: ' + str(self.dataPlace[placeOrderData.TICKER.value]) + ' -' + str(self.dataPlace[placeOrderData.SIDE.value]) + '@' + str(self.dataPlace[placeOrderData.LMTPRC.value]))
        lgr.debug(str(self.corrID) + ' -FX: ' + str(self.ticker_FX) + ' -' + str(self.Side_FX) + '@' + str(self.price_FX))

        try:
            print self.fileName
            # logging.basicConfig(filename=self.nomeArquivo, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)-10s - %(message)s', )
            # create logger

            self.lgr1 = logging.getLogger(str(self.corrID))
            self.lgr1.setLevel(logging.DEBUG)
            # add a file handler
            self.fh2 = logging.FileHandler(self.fileName)

            self.fh2.setLevel(logging.INFO)

            # create a formatter and set the formatter for the handler.
            self.frmt1 = logging.Formatter('%(asctime)s - %(message)s')

            self.fh2.setFormatter(self.frmt1)
            # add the Handler to the logger

            self.lgr1.addHandler(self.fh2)
        except:
            print "DEU PAU NO LOGGING"
        # lgr.debug('Ordem Fechamento: ' + str(self.ticker_Close) + ' -' + str(self.close_Side) + '@' + str(self.price_Close))
        # lgr.debug('FX: ' + str(self.ticker_FX) + ' -' + str(self.Side_FX) + '@' + str(self.price_FX))
        # cria o arquivo de LOG
        # self.filename = self.dataPlace[placeOrderData.CORRID.value] + "-" + self.dataPlace[placeOrderData.TICKER.value]+ "-" + self.dataPlace[placeOrderData.SIDE.value] + ".log"
        # logging.basicConfig(filename=self.filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)-10s - %(message)s', )

        # self.mktData_Thread = Thread(target=self.connect_mktData)
        #
        # self.list_Subscription = [str(self.ticker_Close) + "," + str(self.close_field.name),
        #               str(self.ticker_FX) + "," + str(self.FX_field.name)]
        #
        # self.mktData_Thread.start()

        # print self.dataPlace
        # print self.dataClose

    '''

        Metodos de atribuicao de valores aos dados dos pares

    '''

    def get_corrID(self):
        self.corrID = id_generator(8)

    #     get ticker
    def get_Place_Ticker(self, ticker_Place):
        self.ticker_Place = ticker_Place

    def get_Close_Ticker(self, ticker_Close):
        self.ticker_Close = ticker_Close

    def FX_get_Ticker(self, ticker_FX):
        self.ticker_FX = ticker_FX

    # get amount
    def get_Place_Amount(self, amount_Place):
        self.amount_Place = int(amount_Place)
        self.amount_Close = int(self.amount_Place * self.ratio)
        print self.amount_Place
        print self.amount_Close

    def get_Close_Amount(self, amount_Close):
        self.amount_Close = amount_Close

    # get order type
    def get_Place_Type(self, type_Place):
        self.type_Place = type_Place

    def get_Close_Type(self, type_Close):
        self.type_Close = type_Close

    # get TIFF
    def get_Place_TIF(self, TIF_Place):
        self.TIF_Place = TIF_Place

    def get_Close_TIF(self, TIF_Close):
        self.TIF_Close = TIF_Close

    # get Handling Instructions
    def get_Place_Hand_Inst(self, HandInst_Place):
        self.hand_instr_Place = HandInst_Place

    def get_Close_Hand_Inst(self, HandInst_Close):
        self.hand_instr_Close = HandInst_Close

    # get trading account
    def get_Place_Account(self, Account_Place):
        self.place_account = Account_Place

    def get_Close_Account(self, Account_Close):
        self.close_account = Account_Close

    # get trader Notes
    def get_Place_TraderNotes(self, traderNotes_Place):
        self.place_traderNotes = traderNotes_Place

    def get_Close_TraderNotes(self, traderNotes_Close):
        self.close_traderNotes = traderNotes_Close

    # get use Strat
    def get_Place_UseStrat(self, useStrat_Place):
        self.place_use_strat = useStrat_Place

    def get_Close_UseStrat(self, useStrat_Close):
        self.close_use_strat = useStrat_Close

    # get order sent
    def get_Place_OrderSent(self, orderSent_Place):
        self.place_order_sent = orderSent_Place

    def get_Close_OrderSent(self, orderSent_Close):
        self.close_order_sent = orderSent_Close

    # get average price
    def get_Place_AvgPrice(self, avgPrice_Place):
        self.place_avgprice = avgPrice_Place

    def get_Close_AvgPrice(self, avgPrice_Close):
        self.close_avgprice = avgPrice_Close

    # get limit price
    def get_Place_LmtPrc(self, lmtPrice_Place):
        self.place_lmtprc = lmtPrice_Place

    def get_Close_LmtPrc(self, lmtPrice_Close):
        self.close_lmtprc = lmtPrice_Close

    # get fill amount
    def get_Place_Fill(self, fill_Place):
        self.place_fill = fill_Place

    def get_Close_Fill(self, fill_Close):
        self.close_fill = fill_Close

    '''
     Pega o Broker e a estrategia do broker
    '''

    def get_place_Broker(self, place_Broker):
        self.place_broker = place_Broker

    def get_close_Broker(self, close_Broker):
        self.close_broker = close_Broker

    def get_place_BrokerStrat(self, place_BrokerStrat):
        self.place_brokerstrat = place_BrokerStrat

    def get_close_BrokerStrat(self, close_BrokerStrat):
        self.close_brokerstrat = close_BrokerStrat

    def Place_broker(self):
        return self.place_broker

    def Close_broker(self):
        return self.close_broker

    def Place_brokerStrat(self):
        return self.place_brokerstrat

    def Close_BokerStrat(self):
        return self.close_brokerstrat

    # Devolve o TICKER

    def Place_Ticker(self):
        return self.ticker_Place

    # print 'Place: ' + self.ticker_Place
    def Close_Ticker(self):
        return self.ticker_Close

    # print 'Close: ' + self.ticker_Close
    def FX_Ticker(self):
        return self.ticker_FX

    # print 'FX: ' + self.ticker_FX

    # Margem requisitada pela operacao - entrada do operador

    def Pmargem(self, Pmargem):
        self.Pmargem = Pmargem
        print 'Margem Op: ' + str(self.Pmargem)

    '''
   /====================================================================================================================
   /PEGA O PRECO DO CLOSE - Embora seja o CLOSE quem define o preco da ordem que apregoa - Se o par vai subscrever
   /BID ou ASK depende de qual lado esta o PLACE - O FX para calcular a margem em preco local tem que ser do mesmo lado
   /do PLACE.
   /====================================================================================================================
    '''

    #  Pega o SIDE do Place e define o side do close e FX

    def get_Place_Side(self, Place_Side):
        self.place_Side = Place_Side

        if self.place_Side == Side.BUY.name:
            self.place_field = field.ASK
            if self.close_Side == '':
                self.close_Side = Side.SELL.name
            else:
                pass
            self.close_field = field.BID
        else:
            self.close_Side = Side.BUY.name
            self.place_field = field.BID
            self.close_field = field.ASK

        # se ADR eh o PLACE =>> o FX segue o SIDE do PLACE (ADR)
        if self.use_FX:
            self.Side_FX = self.place_Side
            self.FX_field = self.place_field
        else: # se ADR eh o CLOSE =>> o FX segue o SIDE do CLOSE (ADR)
            self.Side_FX = self.close_Side
            self.FX_field = self.close_field

    # Pega os precos do CLOSE e FX

    def get_Close_Price(self, Price_Close):
        self.price_Close = Price_Close

    def get_FX_Price(self, price_FX):

        if self.ticker_FX[0:3] == "WDO":

            if self.Side_FX == Side.BUY.name:
                self.price_FX = (price_FX - self.casado_ask)/1000
                # print "Preco FX - (Futuro - casado)/1000 = " + str(self.price_FX)
            else:
                self.price_FX = (price_FX - self.casado_bid)/1000
                # print "Preco FX - (Futuro - casado)/1000 = " + str(self.price_FX)
        else:
            self.price_FX = price_FX


    # define os Publishers para o GUI das informacoes a serem atualizadas pelo Trader

    def SendPlacePrice(self, corrID, placePrice):

        pub.sendMessage('subplacePrice', msg=str(corrID) + ":" + str(placePrice), extra=None)

    def SendclosePrice(self, corrID, closePrice):

        pub.sendMessage('subclosePrice', msg=str(corrID) + ":" + str(closePrice), extra=None)

    def SendOrderStatus(self, msg):

        pub.sendMessage('suborderStatus', msg=str(msg), extra=None)

    def SendTradedVolume(self, corrID, tradedVolume):

        pub.sendMessage('subtradedVolume', msg=str(corrID) + ":" + str(tradedVolume), extra=None)

    def SendPosition(self, corrID, Position):

        pub.sendMessage('subposition', msg=str(corrID) + ":" + str(Position), extra=None)

    def SendRealSpread(self, corrID, realSpread):

        pub.sendMessage('subrealSpread', msg=str(corrID) + ":" + str(realSpread), extra=None)

    def SendAvgSpread(self, corrID, avgSpread):

        pub.sendMessage('subavgSpread', msg=str(corrID) + ":" + str(avgSpread), extra=None)

    def SendLastGross(self, corrID, lastGross):

        pub.sendMessage('sublastGross', msg=str(corrID) + ":" + str(lastGross), extra=None)

    def SendPNL(self, corrID, acumPNL):

        pub.sendMessage('subPNL', msg=str(corrID) + ":" + str(acumPNL), extra=None)

    def SendFXPrice(self, corrID, FXPrice):

        pub.sendMessage('subFXPrice', msg=str(corrID) + ":" + str(FXPrice), extra=None)

    def SendMarketSpread(self, corrID, marketSpread):

        pub.sendMessage('subMarketSpread', msg=str(corrID) + ":" + str(marketSpread), extra=None)

    # metodo de arrendondamento - arredonda de acordo com o threshold definido pelo programador (podendo ser entrada do operado no futuro)
    def arredonda(self, valor, threshold):
        print valor
        print threshold
        numero = str(valor)
        decimal = numero.split(".")
        print decimal
        print decimal[1][2:4]
        try:
            if int(decimal[1][2:4]) > int(threshold):
                teste = math.ceil(float(numero)*100)/100
                print teste
            else:
                teste = round(float(numero),2)
                print teste
            return teste
        except:
            lgr.info(str(self.corrID) + " -Deu pau no arredonda")
            print decimal
            return numero

    def Calc_MarketSpread(self):

        if self.place_Side == Side.BUY.name:
            try:
                if self.use_FX == 1:
                   # calcula preco de apregoamento
                   tempMarketSpread = round((self.close_lmtprc / float(self.price_FX)) - (float(self.marketPlacePrice) / self.ratio), 4)

                else:
                   tempMarketSpread = round((self.close_lmtprc - (float(self.marketPlacePrice) / (float(self.price_FX) * self.ratio))), 4)
            except:
                print "Deu ERRO em Calc_MarketSpread primeiro if, linha 674"
        else:
            try:
                if self.use_FX == 1:
                   tempMarketSpread = -round((self.close_lmtprc / float(self.price_FX)) - (float(self.marketPlacePrice) / self.ratio), 4)

                else:
                   tempMarketSpread = -round((self.close_lmtprc - (float(self.marketPlacePrice) / (float(self.price_FX) * self.ratio))), 4)
            except:
                print "Deu ERRO em Calc_MarketSpread segundo if, linha 683"

        lgr.debug(str(self.corrID) + ' - Margem do Mercado: ' + str(tempMarketSpread))
        print "==>>>> MARKET SPREAD CALCULADO DE :" + str(self.corrID) + " = " + str(tempMarketSpread)

        if str(tempMarketSpread) != str(self.MarketSpread):
            self.SendMarketSpread(self.dataClose[closeOrderData.CORRID.value], str(tempMarketSpread))
            self.MarketSpread = tempMarketSpread

    '''

        O metodo Calc_Place calcula o preco do ativo que vai ser apregoado baseado no preco do ativo que vai fechar a perna
        da arbitragem e do cambio. Toda vez que ha uma alteracao em uma dessas duas variaveis o calculo eh realizado.

        A variavel usa_cambio = 0 define que a multiplicao da margem pelo cambio e direta para converter em moeda local e
        o contrario caso o usa_cambio = 1

    '''

    def Calc_Place(self):
        print "==============>>>>> Margem eh: " + str(self.Pmargem)
        if self.cancelOrderSent: # se enviou ordem de cancelamento parar de calcular preco
            print self.cancelOrderSent
            pass

        else:

            if self.place_Side == Side.BUY.name:

                if self.use_FX == 1:
                    # calcula preco de apregoamento
                    # OBS IMPORTANTE = MARGEM JA VEM COM SINAL NEGATIVO
                    self.price_Place = self.arredonda((((self.close_lmtprc / self.price_FX) - float(self.Pmargem)) * self.ratio),25)
                    if self.price_Place != self.dataPlace[placeOrderData.LMTPRC.value]: # se preco calculado eh diferente do preco armazenado
                        self.dataPlace[placeOrderData.LMTPRC.value] = self.price_Place
                        lgr.info(str(self.corrID) + " -==>> a margem eh: self.Pmargem = " + str(self.Pmargem))
                        lgr.info(str(self.corrID) + " -dataPlace[placeOrderData.LMTPRC.value] = " + str(self.dataPlace[placeOrderData.LMTPRC.value]))
                        self.ClosePrice[str(self.price_Place)] = self.close_lmtprc # atualiza o preco de close deste par
                        lgr.info(str(self.corrID) + " -dataClose[closeOrderData.LMTPRC.value] = " + str(self.dataClose[closeOrderData.LMTPRC.value]))
                        lgr.info(str(self.corrID) + " -self.price_FX = " + str(self.price_FX))
                        lgr.info(str(self.corrID) + " -dataClose[closeOrderData.LMTPRC.value] in Dolar = " + str(self.dataClose[closeOrderData.LMTPRC.value] / self.price_FX))
                        if not self.stopModifyRequests: # se tiver enviado ordem de apregoamento
                            # envia ordem de modify, do contrario nao faz nada - a ordem de fechamento nao eh alterada pelo sistem
                            self.onChange()
                        else:
                            pass
                    else:
                        pass
                else:
                    self.price_Place = self.arredonda((((self.close_lmtprc - float(self.Pmargem)) * float(self.price_FX)) * self.ratio),25)
                    if self.price_Place != self.dataPlace[placeOrderData.LMTPRC.value]:
                        self.dataPlace[placeOrderData.LMTPRC.value] = self.price_Place
                        lgr.info(str(self.corrID) + " -==>> a margem eh: self.Pmargem = " + str(self.Pmargem))
                        lgr.info(str(self.corrID) + " -dataPlace[placeOrderData.LMTPRC.value] = " + str(self.dataPlace[placeOrderData.LMTPRC.value]))
                        self.ClosePrice[str(self.price_Place)] = self.close_lmtprc # atualiza o preco de close deste par
                        lgr.info(str(self.corrID) + " -dataClose[closeOrderData.LMTPRC.value] = " + str(self.dataClose[closeOrderData.LMTPRC.value]))
                        lgr.info(str(self.corrID) + " -self.price_FX = " + str(self.price_FX))
                        print "self.price_FX = " + str(self.price_FX)
                        if not self.stopModifyRequests:
                            self.onChange()
                        else:
                            pass
                    else:
                        pass
            else:
                if self.use_FX == 1:
                    self.price_Place = self.arredonda((((self.close_lmtprc / self.price_FX) + float(self.Pmargem)) * self.ratio),75)
                    if self.price_Place != self.dataPlace[placeOrderData.LMTPRC.value]:
                        self.dataPlace[placeOrderData.LMTPRC.value] = self.price_Place
                        lgr.info(str(self.corrID) + " -==>> a margem eh: self.Pmargem = " + str(self.Pmargem))
                        lgr.info(str(self.corrID) + " -dataPlace[placeOrderData.LMTPRC.value] = " + str(self.dataPlace[placeOrderData.LMTPRC.value]))
                        self.ClosePrice[str(self.price_Place)] = self.close_lmtprc # atualiza o preco de close deste par
                        lgr.info(str(self.corrID) + " -dataClose[closeOrderData.LMTPRC.value] = " + str(self.dataClose[closeOrderData.LMTPRC.value]))
                        lgr.info(str(self.corrID) + " -self.price_FX = " + str(self.price_FX))
                        if not self.stopModifyRequests:
                            self.onChange()
                        else:
                            pass
                    else:
                        pass
                else:
                    self.price_Place = self.arredonda((((self.close_lmtprc + float(self.Pmargem)) * float(self.price_FX)) * self.ratio),75)
                    if self.price_Place != self.dataPlace[placeOrderData.LMTPRC.value]:
                        self.dataPlace[placeOrderData.LMTPRC.value] = self.price_Place
                        lgr.info(str(self.corrID) + " -==>> a margem eh: self.Pmargem = " + str(self.Pmargem))
                        lgr.info(str(self.corrID) + " -dataPlace[placeOrderData.LMTPRC.value] = " + str(self.dataPlace[placeOrderData.LMTPRC.value]))
                        self.ClosePrice[str(self.price_Place)] = self.close_lmtprc # atualiza o preco de close deste par
                        lgr.info(str(self.corrID) + " -dataClose[closeOrderData.LMTPRC.value] = " + str(self.dataClose[closeOrderData.LMTPRC.value]))
                        lgr.info(str(self.corrID) + " -self.price_FX = " + str(self.price_FX))
                        if not self.stopModifyRequests:
                            self.onChange()
                        else:
                            pass
                    else:
                        pass
            lgr.debug(str(self.corrID) + ' - Ordem Fechamento: ' + str(self.dataClose[closeOrderData.TICKER.value]) + ' -' + str(self.dataClose[closeOrderData.SIDE.value]) + '@' + str(self.dataClose[closeOrderData.LMTPRC.value]))
            lgr.debug(str(self.corrID) + ' - Ordem Apregoamento: ' + str(self.dataPlace[placeOrderData.TICKER.value]) + ' -' + str(self.dataPlace[placeOrderData.SIDE.value]) + '@' + str(self.dataPlace[placeOrderData.LMTPRC.value]))
            lgr.debug(str(self.corrID) + ' - FX: ' + str(self.ticker_FX) + ' -' + str(self.Side_FX) + '@' + str(self.price_FX))
            lgr.debug(str(self.corrID) + " -self.price_Place calculado eh: " + str(self.price_Place))

    # Metodo de envio da ordem de apregoamento
    def place_Order(self):
        self.placeOrderLock = threading.Lock()
        try:
            if not self.place_order_sent: # caso o trader tente enviar outra ordem com uma ordem ja no mercado
                # atribui os valores aas variaveis da instrucao para envio ao OMS
                broker = self.dataPlace[placeOrderData.BROKER.value]
                side = self.dataPlace[placeOrderData.SIDE.value]
                amount = self.dataPlace[placeOrderData.AMOUNT.value]
                type = self.dataPlace[placeOrderData.TYPE.value]
                ticker = self.dataPlace[placeOrderData.TICKER.value]
                TIF = self.dataPlace[placeOrderData.TIF.value]
                lmtprc = self.dataPlace[placeOrderData.LMTPRC.value]
                handInst = self.dataPlace[placeOrderData.HAND_INSTR.value]
                corrID = self.corrID
                account = self.dataPlace[placeOrderData.ACCOUNT.value]
                traderNotes = self.dataPlace[placeOrderData.TRADER_NOTES.value]

                print "======= Dados de controle financeiro ======"
                print lmtprc
                print amount
                print self.moneyamount_place
                print self.moneyThreshold
                print (float(lmtprc)*float(amount))
                print (float(self.moneyamount_place)*float(1 + float(self.moneyThreshold)))
                print "======= Dados de controle financeiro ======"





                if self.dataPlace[placeOrderData.USE_STRAT.value]: # se usa estrategia enviar a instrucao com estrategia
                    instructionType = orderinstruction.SEND_ORDER_WITH_STRAT.value
                    brokerStrat = self.dataPlace[placeOrderData.BROKER_STRATEGY.value]
                    # monta a mensagem de instrucao de ordem a ser enviada para o OMS
                    self.messagePlaceOrder = str(instructionType) + "," + str(corrID) + "," + str(ticker) + ":" + str(amount) + ":" + str(
                        type) + ":" + str(TIF) + ":" + str(handInst) + ":" + str(side) + ":" + str(
                        lmtprc) + ":" + str(broker) + ":" + str(account) + ":" + str(traderNotes) + ":" + str(brokerStrat)
                    print self.messagePlaceOrder # print para debug
                else:
                    instructionType = orderinstruction.SEND_ORDER.value #  envia instrucao sem estrategia
                    # monta a mensagem de instrucao de ordem a ser enviada para o OMS
                    self.messagePlaceOrder = str(instructionType) + "," + str(corrID) + "," + str(ticker) + ":" + str(amount) + ":" + str(
                        type) + ":" + str(TIF) + ":" + str(handInst) + ":" + str(side) + ":" + str(
                        lmtprc) + ":" + str(broker) + ":" + str(account) + ":" + str(traderNotes)
                    print self.messagePlaceOrder
                lgr.info(str(self.corrID) + " - place_Order: vai enviar mensagem para o OrderManager %s", self.messagePlaceOrder)
                lgr.debug(str(self.corrID) + ' - place_Order: Ordem Fechamento: ' + str(self.dataClose[closeOrderData.TICKER.value]) + ' -' + str(self.dataClose[closeOrderData.SIDE.value]) + '@' + str(self.dataClose[closeOrderData.LMTPRC.value]))
                lgr.debug(str(self.corrID) + ' - place_Order: Ordem Apregoamento: ' + str(self.dataPlace[placeOrderData.TICKER.value]) + ' -' + str(self.dataPlace[placeOrderData.SIDE.value]) + '@' + str(self.dataPlace[placeOrderData.LMTPRC.value]))
                lgr.debug(str(self.corrID) + ' - place_Order: FX: ' + str(self.ticker_FX) + ' -' + str(self.Side_FX) + '@' + str(self.price_FX))



                print "============ Price control =============="

                print "lmtprc: " + str(lmtprc)
                print "self.last_lmtprcPlace: " + str(self.last_lmtprcPlace)
                print "self.thresholdPrice: " + str(self.thresholdPrice)

                print "============ Price control =============="

                ''' ====================================================================================================================

                    Controle Financeiro - contra envio ordens com Fincaneiro de variacao maior ou menor que x% da primeira ordem

                    ==================================================================================================================== '''
                if ((float(lmtprc)*float(amount)) > (float(self.moneyamount_place)*float(1 + float(self.moneyThreshold)))) | ((float(lmtprc)*float(amount)) < (float(self.moneyamount_place)*float(1 - float(self.moneyThreshold)))):

                    self.stop_pair()
                    wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o volume financeiro da ordem eh 10% maior que o permitido")
                    self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                    "O Trader for parado pois o volume financeiro da ordem eh 10% maior que o permitido")
                    print "(float(lmtprc)*float(amount) = " + str(float(lmtprc)*float(amount))
                    print "self.moneyamount_place = " + str(self.moneyamount_place)

                else:

                    ''' ====================================================================================================================

                    Controle de preco - contra envio de precos com variacao maior que um certo Threshold definido no inicio do programa

                    ==================================================================================================================== '''

                    if ((float(lmtprc) > float(self.last_lmtprcPlace)*(1 + self.thresholdPrice)) | ((float(lmtprc) < float(self.last_lmtprcPlace)*(1 - self.thresholdPrice)))): # se o preco variou mais de "X"% do preco anterior, para o robo e avisa ao operador

                        self.stop_pair()
                        print "========== PRECO TEVE VARIACAO DE MAIS DE 10% DO PRECO ANTERIOR =============="
                        wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
                        self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                        "O Trader for parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
                    else:

                        # self.placeOrderLock.acquire()
                        self.OrderManagerConn.send(self.messagePlaceOrder) # envia a mensagem de instrucao para o OMS
                        self.place_order_sent = 1 # atribui o valor VERDADEIRO ao boolean de envio do ordem de apregoamento
                        # self.placeOrderLock.release()

                    self.last_lmtprcPlace = lmtprc
            else:
                pass
        except:
            lgr.info(str(self.corrID) + " - Deu pau dentro do metodo place_Order")
            if not self.place_order_sent:
                self.place_order_sent = 1 # se deu erro no envio, atribui o valor VERDADEIRO para impedir que o Trader passe a enviar ordens em loop

    # Metodo de envio da ordem de fechamento da perna
    def close_Order(self):
        self.closeOrderLock = threading.Lock()
        broker = self.dataClose[closeOrderData.BROKER.value]
        side = self.dataClose[closeOrderData.SIDE.value]
        amount = self.dataClose[closeOrderData.AMOUNT.value]
        type = self.dataClose[closeOrderData.TYPE.value]
        ticker = self.dataClose[closeOrderData.TICKER.value]
        TIF = self.dataClose[closeOrderData.TIF.value]
        lmtprc = self.dataClose[closeOrderData.LMTPRC.value]
        handInst = self.dataClose[closeOrderData.HAND_INSTR.value]
        corrID = self.corrID
        account = self.dataClose[closeOrderData.ACCOUNT.value]
        traderNotes = self.dataClose[closeOrderData.TRADER_NOTES.value]




        if self.dataClose[closeOrderData.USE_STRAT.value]: # se usa estrategia enviar a instrucao com estrategia
            instructionType = orderinstruction.SEND_ORDER_WITH_STRAT.value
            brokerStrat = self.dataClose[closeOrderData.BROKER_STRATEGY.value]
            # monta a mensagem de instrucao de ordem a ser enviada para o OMS
            self.messageCloseOrder = str(instructionType) + "," + str(corrID) + "," + str(ticker) + ":" + str(amount) + ":" + str(
                type) + ":" + str(TIF) + ":" + str(handInst) + ":" + str(side) + ":" + str(
                lmtprc) + ":" + str(broker) + ":" + str(account) + ":" + str(traderNotes) + ":" + str(brokerStrat)
            print self.messageCloseOrder
        else:
            instructionType = orderinstruction.SEND_ORDER.value #  envia instrucao sem estrategia
            # monta a mensagem de instrucao de ordem a ser enviada para o OMS
            self.messageCloseOrder = str(instructionType) + "," + str(corrID) + "," + str(ticker) + ":" + str(amount) + ":" + str(
                type) + ":" + str(TIF) + ":" + str(handInst) + ":" + str(side) + ":" + str(
                lmtprc) + ":" + str(broker) + ":" + str(account) + ":" + str(traderNotes)
            print self.messageCloseOrder # print de debug

        # LOG
        lgr.info(str(self.corrID) + ' - close_Order: vai enviar mensagem para o OrderManager %s', self.messageCloseOrder)
        lgr.debug(str(self.corrID) + ' - close_Order: Ordem Fechamento: ' + str(self.dataClose[closeOrderData.TICKER.value]) + ' -' + str(self.dataClose[closeOrderData.SIDE.value]) + '@' + str(self.dataClose[closeOrderData.LMTPRC.value]))
        lgr.debug(str(self.corrID) + ' - close_Order: Ordem Apregoamento: ' + str(self.dataPlace[placeOrderData.TICKER.value]) + ' -' + str(self.dataPlace[placeOrderData.SIDE.value]) + '@' + str(self.dataPlace[placeOrderData.LMTPRC.value]))
        lgr.debug(str(self.corrID) + ' - close_Order: FX: ' + str(self.ticker_FX) + ' -' + str(self.Side_FX) + '@' + str(self.price_FX))




        ''' ====================================================================================================================

            Controle Financeiro - contra envio ordens com Fincaneiro de variacao maior ou menor que x% da primeira ordem

            ==================================================================================================================== '''
        if ((float(lmtprc)*float(amount)) > (float(self.moneyamount_close)*float(1 + float(self.moneyThreshold)))) | ((float(lmtprc)*float(amount)) < (float(self.moneyamount_close)*float(1 - float(self.moneyThreshold)))):

            self.stop_pair()
            wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o volume financeiro da ordem eh 10% maior que o permitido")
            self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                            "O Trader for parado pois o volume financeiro da ordem eh 10% maior que o permitido")
            print "(float(lmtprc)*float(amount) = " + str(float(lmtprc)*float(amount))
            print "self.moneyamount_place = " + str(self.moneyamount_place)

        else:

            ''' ====================================================================================================================

                Controle de preco - contra envio de precos com variacao maior que um certo Threshold definido no inicio do programa

                ==================================================================================================================== '''
            if ((float(lmtprc) > float(self.last_lmtprcClose)*(1 + self.thresholdPrice)) | ((float(lmtprc) < float(self.last_lmtprcClose)*(1 - self.thresholdPrice)))) : # se o preco variou mais de "X"% do preco anterior, para o robo e avisa ao operador

                self.stop_pair()
                print "========== PRECO TEVE VARIACAO DE MAIS DE 10% DO PRECO ANTERIOR =============="
                wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
                self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                "O Trader for parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
            else:

                # self.closeOrderLock.acquire()
                self.OrderManagerConn.send(self.messageCloseOrder) # Envia a instrucao de ordem para o OMS
                self.place_order_sent = 0 # atribui o valor FALSO ao boolean de envio do ordem de apregoamento
                # self.closeOrderLock.release()

            self.last_lmtprcClose = lmtprc


    # Metodo de envio de instrucao de cancelamento de ordem
    def cancel_Order(self):
        try:
            print self.orderSeqNumber
            seqNumber = self.orderSeqNumber
            routeID = self.routID
            corrID = self.corrID

            instructionType = orderinstruction.CANCEL_ORDER.value # atribui o valor de tipo de instrucao
            # monta a mensagem de instrucao de cancelamento de ordem a ser enviada para o OMS
            self.messageCancelOrder = str(instructionType) + "," + str(corrID) + "," + str(seqNumber) + ":" + str(routeID)
            # LOG
            lgr.info(str(self.corrID) + " - cancel_Order: vai enviar mensagem para o OrderManager %s", self.messageCancelOrder)
            self.OrderManagerConn.send(self.messageCancelOrder) # Envia a instrucao de cancelamento de ordem para o OMS
            print self.messageCancelOrder
        except:
            lgr.info(str(self.corrID) + " - dentro do cancel_Order: deu pau")

    '''

    onWorking - callback de quando a ordem esta sendo trabalhada no Mercado: quando existe um partial fill que perdura por mais
    de 1s ele cancela a ordem e envia a perna de fechamento. A ideia eh nao ficar mais de 1s esperando fill. (ainda nao implementado)

    '''

    def onWorking(self, lmtprc, fill, seqNum):

        if self.place_order_sent:
            print lmtprc
            print self.dataPlace[placeOrderData.LMTPRC.value]
            if str(lmtprc) != str(self.dataPlace[placeOrderData.LMTPRC.value]):
                # self.dataPlace[placeOrderData.LMTPRC.value] = lmtprc
                print "Entrou aqui..."
                self.onChange()
            else:
                pass

        #
        # print "Sera que chegou aqui?"
        # timePartfill.start()


    # Callback quando recebe um fill
    def onFill(self):
        try:
            if self.cancelOrderSent: # se enviou instrucao de cancelamento de ordem
                quit()  # sai do callback e para de enviar ordem
            else:
                if self.place_order_sent:   # se ultima ordem enviada foi de apregoamento
                    # envia ordem de fechamento
                    self.close_Order()
                else:
                    # envia ordem de apregoamento
                    self.stopModifyRequests = False
                    self.place_Order()
        except:
            # LOG
            lgr.info(str(self.corrID) + " - deu pau no onFill()")

    # Callback quando ha alteracao no preco de apregoamento
    def onChange(self):
        try:
            # atribui valores aas variaveis  da instrucao de alteracao de ordem
            onChangeLock = threading.Lock()
            seqNum = self.orderSeqNumber
            routeID = self.routID
            amount = self.dataPlace[placeOrderData.AMOUNT.value]
            type = self.dataPlace[placeOrderData.TYPE.value]
            ticker = self.dataPlace[placeOrderData.TICKER.value]
            TIF = self.dataPlace[placeOrderData.TIF.value]
            lmtprc = self.dataPlace[placeOrderData.LMTPRC.value]
            corrID = self.corrID



            if self.dataPlace[placeOrderData.USE_STRAT.value]: # se usa estrategia enviar a instrucao com estrategia
                self.instructionType = orderinstruction.MODIFY_ORDER_WITH_STRAT.value # atribui o tipo de instrucao a enviar
                self.brokerStrat = self.dataPlace[placeOrderData.BROKER_STRATEGY.value]
                # constroi a instrucao a ser enviada ao OMS
                self.messageOnChange = str(self.instructionType) + "," + str(corrID) + "," + str(seqNum) + ":" + str(routeID) + ":" + str(amount
                ) + ":" + str(type) + ":" + str(ticker) + ":" + str(TIF) + ":" + str(lmtprc) + ":" + str(self.brokerStrat)
            else:
                self.instructionType = orderinstruction.MODIFY_ORDER.value # atribui o tipo de instrucao a enviar
                # constroi a instrucao a ser enviada ao OMS
                self.messageOnChange = str(self.instructionType) + "," + str(corrID) + "," + str(seqNum) + ":" + str(routeID) + ":" + str(amount
                ) + ":" + str(type) + ":" + str(ticker) + ":" + str(TIF) + ":" + str(lmtprc)

            lgr.info(str(self.corrID) + " :dentro do onChange: vai enviar mensagem para o OrderManager %s", self.messageOnChange)



            ''' ====================================================================================================================

            Controle Financeiro - contra envio ordens com Fincaneiro de variacao maior ou menor que x% da primeira ordem

            ==================================================================================================================== '''
            if ((float(lmtprc)*float(amount)) > (float(self.moneyamount_place)*float(1 + float(self.moneyThreshold)))) | ((float(lmtprc)*float(amount)) < (float(self.moneyamount_place)*float(1 - float(self.moneyThreshold)))):

                self.stop_pair()
                wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o volume financeiro da ordem eh 10% maior que o permitido")
                self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                "O Trader for parado pois o volume financeiro da ordem eh 10% maior que o permitido")
                print "(float(lmtprc)*float(amount) = " + str(float(lmtprc)*float(amount))
                print "self.moneyamount_place = " + str(self.moneyamount_place)
            else:

                ''' ====================================================================================================================

                    Controle de preco - contra envio de precos com variacao maior que um certo Threshold definido no inicio do programa

                    ==================================================================================================================== '''
                print "============ Price control =============="

                print "lmtprc: " + str(lmtprc)
                print "self.last_lmtprcPlace: " + str(self.last_lmtprcPlace)
                print "self.thresholdPrice: " + str(self.thresholdPrice)

                print "============ Price control =============="

                if ((float(lmtprc) > float(self.last_lmtprcPlace)*(1 + self.thresholdPrice)) | ((float(lmtprc) < float(self.last_lmtprcPlace)*(1 - self.thresholdPrice)))) : # se o preco variou mais de "X"% do preco anterior, para o robo e avisa ao operador

                    self.stop_pair()
                    print "========== PRECO TEVE VARIACAO DE MAIS DE 10% DO PRECO ANTERIOR =============="
                    wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
                    self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                    "O Trader for parado pois tentou ajustar uma ordem com variacao 10% maior que o preco anterior")
                    print "(float(lmtprc)*float(amount) = " + str(float(lmtprc)*float(amount))
                    print "self.moneyamount_place = " + str(self.moneyamount_place)
                else:


                    # onChangeLock.acquire()
                    self.OrderManagerConn.send(self.messageOnChange) # envia a instrucao de modificacao de ordem ao OMS
                    # time.sleep(0.001)
                    # onChangeLock.release()

                self.last_lmtprcPlace = lmtprc

        except:
            # LOG
            lgr.info(str(self.corrID) + " :dentro do onChange: O onChange nao concluiu corretamente")

    # Callback quando o operador forca o fill pelo GUI
    def onforceFill(self, lmtprcGUI):
        try:
            # atribui valores aas variaveis  da instrucao de alteracao de ordem
            onChangeLock = threading.Lock()
            seqNum = self.orderSeqNumber
            routeID = self.routID
            amount = self.dataClose[closeOrderData.AMOUNT.value]
            type = self.dataClose[closeOrderData.TYPE.value]
            ticker = self.dataClose[closeOrderData.TICKER.value]
            TIF = self.dataClose[closeOrderData.TIF.value]
            lmtprc = lmtprcGUI
            corrID = self.corrID

            if ((float(lmtprc)*float(amount)) > (float(self.moneyamount_close)*float(1 + float(self.moneyThreshold)))) | ((float(lmtprc)*float(amount)) < (float(self.moneyamount_close)*float(1 - float(self.moneyThreshold)))):

                self.stop_pair()
                wx.MessageBox("O Trader for parado pois o volume financeiro da ordem eh 10% maior que o permitido")

            if self.dataPlace[closeOrderData.USE_STRAT.value]: # se usa estrategia enviar a instrucao com estrategia
                self.instructionType = orderinstruction.MODIFY_ORDER_WITH_STRAT.value # atribui o tipo de instrucao a enviar
                self.brokerStrat = self.dataClose[closeOrderData.BROKER_STRATEGY.value]
                # constroi a instrucao a ser enviada ao OMS
                self.messageOnChange = str(self.instructionType) + "," + str(corrID) + "," + str(seqNum) + ":" + str(routeID) + ":" + str(amount
                ) + ":" + str(type) + ":" + str(ticker) + ":" + str(TIF) + ":" + str(lmtprc) + ":" + str(self.brokerStrat)
            else:
                self.instructionType = orderinstruction.MODIFY_ORDER.value # atribui o tipo de instrucao a enviar
                # constroi a instrucao a ser enviada ao OMS
                self.messageOnChange = str(self.instructionType) + "," + str(corrID) + "," + str(seqNum) + ":" + str(routeID) + ":" + str(amount
                ) + ":" + str(type) + ":" + str(ticker) + ":" + str(TIF) + ":" + str(lmtprc)

            lgr.info(str(self.corrID) + " :dentro do onforceFill: vai enviar mensagem para o OrderManager %s", self.messageOnChange)
            onChangeLock.acquire()
            self.OrderManagerConn.send(self.messageOnChange) # envia a instrucao de modificacao de ordem ao OMS
            time.sleep(0.001)
            onChangeLock.release()
        except:
            # LOG
            lgr.info(str(self.corrID) + " :dentro do onforceFill: O onChange nao concluiu corretamente")

    # Callback para parar o Trader
    def stop_pair(self):
        # atribui o valor VERDADEIRO ao boolean de envio da ordem de cancelamento
        # - ao pedir para parar, entende-se que o operador quer de fato parar o trader
        # portanto, isso ja impede o envio de qq nova ordem
        self.cancelOrderSent = True
        lgr.info(str(self.corrID) + " - in stop_pair, cancelOrderSent = " + str(self.cancelOrderSent))

        try:
            if self.reachedTotalVolumeTraded:
                self.pair_started = True # atribui o boolean de par iniciado para o par nao poder ser reiniciado

            else:
                self.pair_started = False # atribui o boolean de par iniciado para poder re-iniciar o par
                self.cancel_Order() # envia a instrucao de cancelamento da ordem em aberto
        except:
            lgr.info(str(self.corrID) + " :Dentro de stop_pair: Nao conseguiu cancelar a ordem, ou ela nao foi enviada, ou ja foi Filled verificar o blotter")

        self.pairRunning = False
        # self.mktDataConn.close()
        # self.OrderManagerConn.close()
        # time.sleep(0.2)

    # encerra as conexoes com os servidores
    def close_Connections(self):
        self.mktDataConn.close()
        self.OrderManagerConn.close()


    def connect_mktData(self):
        # global mktDataConn
        # create Internet TCP socket
        self.mktDataConn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mktDataConn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # connect to server
        # try:
        print str(time.time())
        try:
            self.mktDataConn.connect(self.MachineConnection_IP_MKTDATA)
        except socket.error as error:
            if error.errno == 10061: # se a conexao foi recusada
                self.stop_pair()
                wx.MessageBox("O servidor de market data nao iniciou, favor verificar")
                self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + ", O servidor de market data nao iniciou, favor verificar e inicializar o Trader novamente")
                quit()
        # self.closedMarketdata = False
        print str(time.time())
        # except:
            # self.closedMarketdata = True
            # self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + ", Market Data nao esta conectado")
            # # wx.MessageBox("Nao conectou ao Mkt Data, favor verificar e reiniciar o trader")
            # self.stop_pair()
            # quit()

        lgr.info(str(self.corrID) + " :Connectou no MktData")
        # mensagem de ativos para subscrever ao aplicativo de Market Data
        subs_1 = ''

        # cria a mensagem para enviar
        for subs in self.list_Subscription:
            subs_1 = subs_1 + ':' + subs
            # print subs_1
        # envia a mensagem de ativos a subscrever
        self.mktDataConn.send(subs_1)  # send k to server

        self.truncMessage = ""
        self.lastRecievedMessage = ""

        while (1):
            print "ENTROU NO MKTDATA =======>>>> "
            try:
                self.mktData = self.mktDataConn.recv(128)  # receive self.mktData from server (up to 1024 bytes)
                print "self.mktData: " + self.mktData
            except socket.error as error:
                if error.errno == 10054: # se caiu a conexao do MKT data avisa e para o Trader para nao ter risco de continuar operando sem dados de mercado
                    self.stop_pair()
                    wx.MessageBox("Conexao com o MKT Data caiu, o trader parou")
                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + ", Caiu a conexao de Market Data, o Trader parou")
                    quit()

            ''' ========================================================================================================
                Este pedaco do codigo do Callback do MKT Data verifica se as mensagens chegam completas.

                Caso nao cheguem ele guarda a parte truncada e concatena com a mensagem recebida em seguida para foramar
                a mensagem completa e ser processada pelo Trader
            ======================================================================================================== '''

            sizeMessage = len(self.mktData) # tamanho da mensagem recebida
            print "sizeMessage: " + str(sizeMessage)
            print "self.mktData[sizeMessage - 1]: " + self.mktData[sizeMessage - 1]
            if self.mktData[sizeMessage - 1] == ":": # se a mensagem vem completa, i.e., o ultimo caracter da mensagem eh :

                if self.truncMessage == "": # se nao existe mensagem cortada do pacote recebido anterior
                    print self.truncMessage
                    self.recievedMktData = self.mktData.split(":") # cria o string para ser preocessado

                else: # se existe mensagem pela metade

                    mktdataaux = self.mktData.split(":")  # separa as mensagens do pacote
                    sizeEndofMessage = len(mktdataaux[0])   # pega o tamanho da primeira mensagem - continuacao da ultima mensagem do pacote anterior
                    endofMessage = self.mktData[0:sizeEndofMessage + 1]  # separa o restante da mensagem que esta guardada
                    jointMessage = str(self.truncMessage) + str(endofMessage)  # concatena para formar a mensagem completa que foi separada durante o envio TCP
                    jointMessage = jointMessage.split(":")  # retira o ":" da mensagem que foi incluida propositalmente
                    print "self.truncMessage: " + str(self.truncMessage)
                    print "endofMessage: " + str(endofMessage)
                    print "jointMessage: " + str(jointMessage)
                    self.recievedMktData = self.mktData.split(":")  # cria o string para ser processado
                    self.recievedMktData[0] = jointMessage[0]  # adiciona a mensagem concatenada perdida na transmissao
                    self.truncMessage = ""  # elimina a mensagem truncada antiga
                    print "self.recievedMktData: " + str(self.recievedMktData)

            else: # caso tenha vindo com uma mensagem truncada

                if self.truncMessage == "":  # se nao existe mensagem cortada do pacote recebido anterior
                    print self.truncMessage
                    self.recievedMktData = self.mktData.split(":")  # cria o string para ser processado
                    self.truncMessage = self.recievedMktData[len(self.recievedMktData) - 1]  # salva a mensagem que veio truncada
                    del self.recievedMktData[len(self.recievedMktData) - 1]  # deleta a ultima mensagem que esta gravada

                else: # se existe mensagem pela metade

                    mktdataaux = self.mktData.split(":")  # separa as mensagens do pacote
                    sizeEndofMessage = len(mktdataaux[0])   # pega o tamanho da primeira mensagem - continuacao da ultima mensagem do pacote anterior
                    endofMessage = self.mktData[0:sizeEndofMessage + 1]  # separa o restante da mensagem que esta guardada
                    jointMessage = str(self.truncMessage) + str(endofMessage)  # concatena para formar a mensagem completa que foi separada durante o envio TCP
                    jointMessage = jointMessage.split(":") # retira o ":" da mensagem que foi incluida propositalmente
                    print "self.truncMessage: " + str(self.truncMessage)
                    print "endofMessage: " + str(endofMessage)
                    print "jointMessage: " + str(jointMessage)
                    self.recievedMktData = self.mktData.split(":")  # cria o string para ser processado
                    self.recievedMktData[0] = jointMessage[0]  # adiciona a mensagem concatenada perdida na transmissao
                    print "self.recievedMktData: " + str(self.recievedMktData)

                    # self.recievedMktData = self.mktData.split(":")  # cria o string para ser processado
                    self.truncMessage = self.recievedMktData[len(self.recievedMktData) - 1]  # salva a mensagem que veio truncada
                    del self.recievedMktData[len(self.recievedMktData) - 1]  # deleta a ultima mensagem que esta gravada

            print "self.recievedMktData: " + str(self.recievedMktData)
            # self.recievedMktData = self.mktData.split(":")
            print str(self.recievedMktData)
            if len(self.recievedMktData) > 2: # se recebeu mais de uma mensagem
                del self.recievedMktData[len(self.recievedMktData) - 1]
                for mktDataMsg in self.recievedMktData: # para cada mensagem dentro do vetor de mensagens

                    if mktDataMsg != self.lastRecievedMessage: # se a mensagem for diferente da ultima recebida

                        print str(mktDataMsg)
                        # separa a mensagem recebida do aplicativo de mkt data
                        self.infos = mktDataMsg.split(',')

                        # se o ticker eh o de fechamento da perna
                        if self.infos[1] == self.ticker_Close:

                            self.get_Close_LmtPrc(float(self.infos[0])) # atribuir o valor do dado recebido ao preco limite do Close
                            self.recievedClosedata = True
                            try:
                                self.Calc_Place()   # recalcula o preco de apregoamento
                                # self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                                self.SendclosePrice(self.dataClose[closeOrderData.CORRID.value], self.dataClose[closeOrderData.LMTPRC.value])
                                # self.recievedClosedata = True
                            except:
                                pass
                        # se o dado eh do place
                        elif self.infos[1] == self.ticker_Place:
                            # dado do mercado para calcular o spread enxergado / NAO EH O PLACE PRICE CALCULADO
                            self.marketPlacePrice = self.infos[0]

                            try:
                                self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                            except:
                                print "====DEU PAU NA CHAMADA DO METODO CALCAMKTSPREAD======"

                        # se o dado eh de cambio
                        elif self.infos[1] == self.ticker_FX:
                            print str(mktDataMsg)

                            self.get_FX_Price(float(self.infos[0])) # atribuir o valor do dado recebido ao preco de FX
                            self.SendFXPrice(str(self.corrID), str(self.price_FX))
                            self.recievedFXdata = True

                            try:
                                self.Calc_Place() # recalcula o preco de apregoamento
                                # self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                                # self.recievedFXdata = True
                            except:
                                # print "Ainda nao tem os dados do Close, vai fazer nada:"
                                pass

            else:
                self.mktDataMsg = self.recievedMktData[0]

                if self.mktDataMsg != self.lastRecievedMessage: # se a ultima mensagem for diferente da ultima recebida



                    print str(self.mktDataMsg)
                    # separa a mensagem recebida do aplicativo de mkt data
                    self.infos = self.mktDataMsg.split(',')

                    # se o ticker eh o de fechamento da perna
                    if self.infos[1] == self.ticker_Close:

                        self.get_Close_LmtPrc(float(self.infos[0])) # atribuir o valor do dado recebido ao preco limite do Close
                        self.recievedClosedata = True
                        try:
                            self.Calc_Place()   # recalcula o preco de apregoamento
                            # self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                            self.SendclosePrice(self.dataClose[closeOrderData.CORRID.value], self.dataClose[closeOrderData.LMTPRC.value])
                            # self.recievedClosedata = True
                        except:
                            pass
                    # se o dado eh do place
                    elif self.infos[1] == self.ticker_Place:
                        # dado do mercado para caluclar o spread enxergado / NAO EH O PLACE PRICE CALCULADO
                        self.marketPlacePrice = self.infos[0]

                        try:
                            self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                        except:
                            print "====DEU PAU NA CHAMADA DO METODO CALCAMKTSPREAD======"

                    # se o dado eh de cambio
                    elif self.infos[1] == self.ticker_FX:


                        self.get_FX_Price(float(self.infos[0])) # atribuir o valor do dado recebido ao preco de FX
                        self.SendFXPrice(str(self.corrID), str(self.price_FX))
                        self.recievedFXdata = True

                        try:
                            self.Calc_Place() # recalcula o preco de apregoamento
                            # self.Calc_MarketSpread()   # recalcula o preco de apregoamento
                            # self.recievedFXdata = True
                        except:
                            # print "Ainda nao tem os dados do Close, vai fazer nada:"
                            pass

            self.lastRecievedMessage = self.mktDataMsg

            print "self.OMSStarted: " + str(self.OMSStarted)
            print "self.recievedFXdata: " + str(self.recievedFXdata)
            print "self.recievedClosedata: " + str(self.recievedClosedata)

            if self.OMSStarted: # se o OMS foi inicializado, pula esta parte
                pass
            else: # caso ainda nao foi incializado
                if self.recievedFXdata and self.recievedClosedata: # espera ter recebido informacoes de mercado para inicializar e enviar a primeira ordem

                    self.orderManagement_Thread = Thread(target=self.connect_OrderManager) # Instancia o thread do OMS

                    self.orderManagement_Thread.start() # inicializa o thread

                    self.OMSStarted = True # seta o booleano de inicializacao do OMS para True
                else:
                    pass

        self.mktDataConn.close()  # close socket

    '''

    O Metodo Connect Order Manager nao apenas conecta com o APP de envio de instrucoes para o EMSX, como recebe as mensagens de
    status das ordens e chama o callback adequado.

    '''

    def connect_OrderManager(self):
        # global OrderManagerConn
        sendClient = threading.Lock()
        # create Internet TCP socket
        self.OrderManagerConn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.OrderManagerConn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # host = sys.argv[1] # server address
        # port = int(sys.argv[2]) # server port

        # connect to server
        try:
            self.OrderManagerConn.connect(self.MachineConnection_IP_OMS)
        except:
            wx.MessageBox("Nao conectou ao OMS")
            quit()

        # self.OrderManagerConn.connect(('10.48.8.102', 2010))
        # self.get_corrID()
        sendClient.acquire()
        self.OrderManagerConn.send(self.corrID) # envia o ID do trader para associar a conexao recebida no app ao trader
        lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: Enviei o corrID: " + self.corrID)
        sendClient.release()
        # time.sleep(50.0/1000.0)
        print "connected to: " + "('10.48.8.102', 2011)"


        self.newOrderlock = threading.Lock()
        # incializa o boolean de envio de cancelar ordem como Falso
        self.cancelOrderSent = False
        # inicializa o boolean de ordem de apregoamento como Falso
        self.get_Place_OrderSent(False)
        self.newOrderlock.acquire()
        try:
            # print para debug
            # print self.dataPlace
            # print self.dataClose
            # envia a primeira ordem


            self.place_Order()
        except:
            lgr.info(str(self.corrID) + " -Deu pau no place order dentro do PairTrader")
        self.newOrderlock.release()
        self.pair_started = True


        # # numero de pares completos - verifica posicao do trader
        # if self.numberOfCompletePairs is None: # se a variavel nao foi inicilizada
        #     self.numberOfCompletePairs = 0 #inicializa e seta para zero
        # else:
        #     pass
        # # variavel de PNL acumulado
        # if self.gross_acumulated is None:
        #     self.gross_acumulated = 0
        # else:
        #     pass
        # # variavel de Spread medio
        # if self.average_spread is None:
        #     self.average_spread = 0
        # else:
        #     pass
        # # variavel de volume operado
        # if self.tradedVolume is None:
        #     self.tradedVolume = 0
        # else:
        #     pass
        # # variavel de PNL bruto do ultimo fechamento
        # if self.gross_acumulated is None:
        #     self.gross_PNL_captured = 0
        # else:
        #     pass
        # # variavel do ultimo spread capturado
        # if self.spread_captured is None:
        #     self.spread_captured = 0
        # else:
        #     pass
        # # contador de bad spread
        # if self.badspreadcount is None:
        #     self.badspreadcount = 0
        # else:
        #     pass



        while (1):
            sendlock = Lock()

            try:
                self.orderMessage = self.OrderManagerConn.recv(1024)  # receive message from OMS (up to 1024 bytes)

                self.orderMessage = self.orderMessage.split(";") # split a mensagem recebida

                lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: Recebu a mensagem: " + str(self.orderMessage)) # print debug

                if len(self.orderMessage) > 2:
                    del self.orderMessage[len(self.orderMessage) - 1] # deleta o ultimo elemento do vetor que eh nulo
                    for _message in self.orderMessage:
                        lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: Recebu a mensagem: " + _message) # print debug
                        self.orderMessage = _message.split(",")


                        lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: Recebu a mensagem: " + str(self.orderMessage)) # print debug
                        # self.orderMessage = self.orderMessage.split(",") # split a mensagem recebida
                        messageType = self.orderMessage[0] # primeiro string eh o tipo de mensagem recebida
                        lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: length of order Message: " + str(len(self.orderMessage))) # debug print

                        # garante que o Callback processa a ultima mensagem recebida
                        # pela velocidade das infos, algumas vezes vem mensagens agregadas
                        # este codigo pega as diversas mensagens e guarda apenas a ultima para ser processada pelo Trader
                        #
                        # As mensagens sao da forma MESSAGETYPE,[MENSAGEM SEPARADA POR ":"]
                        #
                        # Portanto, se ao separar por "," o tamanho do orderMessage for maior que 2, significa que tem mais de uma
                        # mensagem no string - sendo assim ele separa tudo e pega o ultimo para passar para o Callback
                        # if messageType == '4':
                        #     lgr.info(str(self.corrID) + " - Dentro do if messageType == '4' o tamanho do orderMessage recebido: " + str(len(self.orderMessage)))
                        #     lgr.info(str(self.corrID) + " - Dentro do if messageType == '4' o orderMessage e: " + str(self.orderMessage))
                        #     if len(self.orderMessage) > 2:
                        #         lgr.info(str(self.corrID) + " - dentro do messageType == 4:Order Message particionado: " + str(self.orderMessage))
                        #         self.orderMessage = self.orderMessage[0] + "," + self.orderMessage[len(self.orderMessage)-1] # cria a nova mensagem
                        #         self.orderMessage = self.orderMessage.split(",") # faz novamente o split para o trader
                        #         lgr.info(str(self.corrID) + " - dentro do messageType == 4:Novo Order Message: " + str(self.orderMessage))
                        #     else:
                        #         pass
                        # else:
                        #     pass


                        # Publica o status para o Listener no GUI
                        # self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))


                        # Mensagem tipo 1 confirmacao do roteamento da ordem - Order created and routed
                        # recebe o sequence number da ordem e o routeID
                        if messageType == '1':
                            print self.orderMessage
                            lgr.info(str(self.corrID) + " - dentro do messageType == 1: recebeu mensagem do orderManager %s", str(self.orderMessage))
                            self.orderSeqNumber = self.orderMessage[1]
                            self.routID = self.orderMessage[2]
                            message = self.orderMessage[3]
                            lgr.info(str(self.corrID) + " - dentro do messageType == 1: ordem enviada numero: " + message)
                            lgr.info(str(self.corrID) + " - dentro do messageType == 1: ordem enviada numero: " + self.orderSeqNumber)

                        # mensagem de confirmacao do envio de cancelamento de ordem
                        elif messageType == '2':
                            print self.orderMessage
                            lgr.info(str(self.corrID) + " - dentro do messageType == 2: recebeu mensagem do orderManager " + str(self.orderMessage))
                            # Publica o status para o Listener no GUI
                            self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                            lgr.info(" daqui ele esta indo para onde??")

                        # Mensagens de Erro
                        elif messageType == '3':
                            lgr.info(str(self.corrID) + " - dentro do messageType == 3: recebeu mensagem do orderManager " + str(self.orderMessage))
                            lgr.info(str(self.corrID) + " - dentro do messageType == 3: orderMessage[1]: " + str(self.orderMessage[1]))
                            # Publica o status para o Listener no GUI
                            if not self.recievedCancelStatus:
                                self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage[1]))
                            else:
                                pass
                        # mensagens de status das ordens
                        elif messageType == '4':

                            lgr.info(str(self.corrID) + " - dentro do messageType == 4:recebeu mensagem do orderManager %s", str(self.orderMessage))
                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: orderMessage[1]: " + self.orderMessage[1])
                            # prepara a mensagem para triagem
                            self.orderMessage = self.orderMessage[1].split(":")
                            order_Status = self.orderMessage[1]
                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: order_Status: " + order_Status)
                            amount_filled = self.orderMessage[2]
                            avg_price = self.orderMessage[3]
                            lmt_prc = self.orderMessage[4]
                            last_filled_time = self.orderMessage[5]

                            # se status FILLED
                            if order_Status == orderstatus.FILLED.name:

                                # sendlock.acquire()
                                if self.place_order_sent: # se a ordem eh de apregoamento
                                    # captura os dados de preco realizado e montante filled
                                    self.stopModifyRequests = True
                                    self.dataPlace[placeOrderData.AVG_PRC.value] = avg_price
                                    self.dataPlace[placeOrderData.FILL.value] = amount_filled

                                    # Atribui a mensagem de posicao de acordo com o Side da ordem
                                    if self.place_Side == Side.BUY.name:
                                        self.position = 'Long - ' + str(amount_filled) + ' - ' + str(self.ticker_Place) + ' @ ' + str(avg_price)
                                    else:
                                        self.position = 'Short - ' + str(amount_filled) + ' - ' + str(self.ticker_Place) + ' @ ' + str(avg_price)

                                    # Publica a posicao do trader para o Listener no GUI

                                    self.SendPosition(self.dataClose[closeOrderData.CORRID.value],self.position)
                                    self.lgr1.info(str(self.ticker_Place) + ":" + str(self.orderMessage) + " - FX: " + str(self.price_FX))
                                    # wx.Sound.PlaySound('ding.wav', wx.SOUND_SYNC)

                                else: # se for ordem de fechamento
                                    # wx.Sound.PlaySound('fillsound2.wav', wx.SOUND_SYNC)
                                    try:
                                        # atribui mensagem de posicao para ser publicada
                                        self.position = 'Zerada - ultima operacao - ' + str(amount_filled) + ' - ' + str(self.ticker_Close) + ' @ ' + str(avg_price)
                                        self.SendPosition(self.dataClose[closeOrderData.CORRID.value],self.position) # Publica a posicao do trader para o Listener no GUI
                                        self.numberOfCompletePairs = self.numberOfCompletePairs + 1 # calcula o numero de pares completos operados
                                        self.dataClose[closeOrderData.AVG_PRC.value] = avg_price
                                        self.dataClose[closeOrderData.FILL.value] = amount_filled
                                        lgr.debug(str(self.corrID) + " - self.dataPlace[placeOrderData.AVG_PRC.value]: " + self.dataPlace[placeOrderData.AVG_PRC.value])
                                        lgr.debug(str(self.corrID) + " - self.dataPlace[placeOrderData.FILL.value]: " + self.dataPlace[placeOrderData.FILL.value])
                                        lgr.debug(str(self.corrID) + " - self.dataClose[closeOrderData.AVG_PRC.value]: " + self.dataClose[closeOrderData.AVG_PRC.value])
                                        print str(float(self.dataClose[closeOrderData.AVG_PRC.value]) / self.price_FX)
                                        print self.dataClose[closeOrderData.FILL.value]
                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4:Deu pau no primeiro try dentro do Status Filled")

                                    # Calcula as estatisticas e dados dos pares realizados e do trader
                                    try:
                                        lgr.debug(str(self.corrID) + ' - self.dataPlace[placeOrderData.AVG_PRC.value]: ' + str(self.dataPlace[placeOrderData.AVG_PRC.value]))
                                        lgr.debug(str(self.corrID) + ' - self.dataPlace[placeOrderData.FILL.value]: ' + str(self.dataPlace[placeOrderData.FILL.value]))
                                        lgr.debug(str(self.corrID) + ' - avgPrc in Dolars: ' + str(float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio))))
                                        lgr.debug(str(self.corrID) + ' - self.dataClose[closeOrderData.AVG_PRC.value]: ' + str(self.dataClose[closeOrderData.AVG_PRC.value]))
                                        lgr.debug(str(self.corrID) + ' - self.dataClose[closeOrderData.FILL.value]: ' + str(self.dataClose[closeOrderData.FILL.value]))
                                        lgr.debug(str(self.corrID) + ' - self.price_FX: ' + str(self.price_FX))
                                        lgr.debug(str(self.corrID) + ' - self.ratio: ' + str(self.ratio))
                                        if self.use_FX == 1:
                                            try:
                                                if self.place_Side == Side.BUY.name:
                                                    self.spread_captured = round((((float(self.dataClose[closeOrderData.AVG_PRC.value]) /
                                                                                    self.price_FX) * float(self.ratio)) - float(self.dataPlace[placeOrderData.AVG_PRC.value])), 4)
                                                    self.gross_PNL_captured = round(self.spread_captured *
                                                                                     float(self.dataPlace[placeOrderData.FILL.value]), 4)
                                                else:
                                                    self.spread_captured = -round((((float(self.dataClose[closeOrderData.AVG_PRC.value]) / self.price_FX) * float(self.ratio)) - float(self.dataPlace[placeOrderData.AVG_PRC.value])), 4)
                                                    self.gross_PNL_captured = round(self.spread_captured  *
                                                                                     float(self.dataPlace[placeOrderData.FILL.value]), 4)
                                            except:
                                                lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau dentro do primeiro if no calculo do spread")
                                        else:
                                            try:
                                                if self.place_Side == Side.BUY.name:
                                                    self.spread_captured = round(float(self.dataClose[closeOrderData.AVG_PRC.value]) - float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio)), 4)
                                                    self.gross_PNL_captured = round(self.spread_captured *
                                                                                   float(self.dataClose[closeOrderData.FILL.value]), 4)
                                                else:
                                                    self.spread_captured = -round(float(self.dataClose[closeOrderData.AVG_PRC.value]) -
                                                                                  float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio)), 4)
                                                    self.gross_PNL_captured = round(self.spread_captured *
                                                                                    float(self.dataClose[closeOrderData.FILL.value]), 4)
                                            except:
                                                lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau dentro do segundo if no calculo do spread")

                                        try:
                                            self.average_spread = (self.average_spread*(self.numberOfCompletePairs - 1) + self.spread_captured)/self.numberOfCompletePairs

                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do average_spread")

                                        try:
                                            self.gross_acumulated = self.gross_acumulated + self.gross_PNL_captured

                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do gross_acumulated")

                                        try:
                                            self.tradedVolume = (self.numberOfCompletePairs * float(self.dataPlace[placeOrderData.FILL.value]))

                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do tradedVolume ")

                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Spread requested: " + str(self.Pmargem))
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Spread Captured: " + str(self.spread_captured))
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Average Spread: " + str(self.average_spread))
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Gross margin: " + str(self.gross_acumulated))
                                        # publishers para os listeners do GUI
                                        try:
                                            self.SendRealSpread(self.dataClose[closeOrderData.CORRID.value],str(self.spread_captured))
                                            self.SendAvgSpread(self.dataClose[closeOrderData.CORRID.value],str(self.average_spread))
                                            self.SendLastGross(self.dataClose[closeOrderData.CORRID.value],str(self.gross_PNL_captured))
                                            self.SendPNL(self.dataClose[closeOrderData.CORRID.value],str(self.gross_acumulated))
                                            self.SendTradedVolume(self.dataClose[closeOrderData.CORRID.value],str(int(self.tradedVolume)))
                                            self.lgr1.info(str(self.ticker_Close) + ":" + str(self.orderMessage) + " - FX: " + str(self.price_FX) + " - Spread Capturado:" + str(self.spread_captured))
                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no envio do publisher")

                                        '''
                                        ============================Controle de SPREAD MEDIO e SPREAD do Trader=====================

                                         Se o SPREAD ficar abaixo de 10% do requisitado por mais de 5 vezes seguidos, para o trader

                                         Se o PNL estiver muito longe do esperado ou ficar do sinal contrario do Spread requisitado
                                         o Trader parar e envia mensagem.

                                         =========================================================================================== '''

                                        if self.Pmargem > 0: # se o spread requisitado eh maior que zero

                                            if self.average_spread < self.Pmargem*(1 - self.avgspreadThreshold): # se spread medio eh menor que x% do requisitado

                                                if self.spread_captured < self.Pmargem*(1 - self.spreadThreshold): # se spread capturado eh menor que y% do spread requisitado

                                                    self.stop_pair() # para o Trader
                                                    wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " parado pois o Spread realizad foi 90% pior do que o requisitado")
                                                   
                                                else:

                                                    self.badspreadcount = self.badspreadcount + 1 # conta quantas vezes o spread medio ficou abaixo do spread requisitado

                                                    if self.badspreadcount == 10: # se chegou aa decima ocorrencia

                                                        self.stop_pair() # para o Trader
                                                        wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")
                                                        
                                        elif self.Pmargem < 0: # se o spread requisitado eh menor que zero

                                            if self.average_spread < self.Pmargem*(1 + self.avgspreadThreshold):

                                                if self.spread_captured < self.Pmargem*(1 + self.spreadThreshold):

                                                    self.stop_pair()
                                                    wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " parado pois o Spread realizad foi 90% pior do que o requisitado")
                                                    
                                                else:

                                                    self.badspreadcount = self.badspreadcount + 1

                                                    if self.badspreadcount == 10:

                                                        self.stop_pair()
                                                        wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")
                                                       
                                        elif self.Pmargem == 0: # se o spread requisitado eh igual a zero

                                            if self.average_spread < -0.03:

                                                if self.spread_captured < -0.09:

                                                    self.stop_pair()
                                                    wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " foi parado pois o Spread realizado foi U$ -0.09 - o requisitado foi U$ 0.0")
                                                    
                                                else:

                                                    self.badspreadcount = self.badspreadcount + 1

                                                    if self.badspreadcount == 10:

                                                        self.stop_pair()
                                                        wx.MessageBox("O Trader apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior ao valor de U$ -0.03 - o requisitado foi U$ 0.0")
                                                       

                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no calculo do spread")



                                try:

                                    # se chegou ao limite de posicao requisitado pelo operador
                                    if str(int(self.tradedVolume)) == str(self.totalPairPosition):
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Chegou no limite de posicao requisitado - Trader vai parar")
                                        # para o trader
                                        self.reachedTotalVolumeTraded = True
                                        self.stop_pair()
                                        self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + " Posicao maxima alcancada - Algoritmo Parou,FIM")
                                    else:
                                        # caso nao tenha chegado ao limite, chama o callback onFill
                                        # print str(datetime.datetime.now())
                                        self.onFill()
                                        # print str(datetime.datetime.now())
                                        # Publica o status para o Listener no GUI1
                                        self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: executou o onFill() ")
                                    # sendlock.release()
                                except:
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no onFill!!! Verificar!!")

                            # Se ordem rejeitada por alguma razao - para o trader e envia mensagem para o GUI
                            elif order_Status == orderstatus.REJECTED.name:
                                lgr.info(str(self.corrID) + " - dentro do messageType == 4: Ordem foi rejeitada, verificar e reiniciar o robot!")

                                sendlock.acquire()
                                self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + "Ordem foi rejeitada - verificar e reiniciar!")
                                sendlock.release()
                                return

                            # Se ordem "WORKING" envia precos para o GUI e chama a Callback onWorking
                            elif order_Status == orderstatus.WORKING.name:
                                print lmt_prc
                                print amount_filled
                                print self.orderSeqNumber

                                # sendlock.acquire()

                                if self.place_order_sent:
                                    self.dataClose[closeOrderData.LMTPRC.value] = self.ClosePrice[str(lmt_prc)]  # atualiza o preco de close deste par com o preco relativo ao preco sendo trabalhado
                                else:
                                    pass

                                self.SendclosePrice(self.dataClose[closeOrderData.CORRID.value], self.dataClose[closeOrderData.LMTPRC.value])
                                self.SendPlacePrice(self.dataPlace[placeOrderData.CORRID.value], self.dataPlace[placeOrderData.LMTPRC.value])
                                # envia o FX recebido para atualizar o GUI
                                # sendlock.release()
                                # global timePartfill
                                # # if timePartfill.is_alive:
                                # timePartfill.stop()
                                #
                                # print "passou por aqui"
                                #
                                # timePartfill = TimerClass()
                                self.onWorking(lmt_prc, amount_filled, self.orderSeqNumber)
                                # Publica o status para o Listener no GUI1
                                if self.place_order_sent:
                                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                                else:
                                    pass
                            # se ordem em algum desses estados - nao faz nada (por enquanto)
                            elif order_Status == orderstatus.CXLRPRQ.name:
                                pass
                            elif order_Status == orderstatus.CXLREQ.name:
                                pass
                            elif order_Status == orderstatus.REPPEN.name:
                                pass
                            elif order_Status == orderstatus.SENT.name:
                                pass
                            # se ordem cancelada - envia status de posicao para o GUI e para as conexoes para evitar envio de novas ordens
                            elif order_Status == orderstatus.CANCEL.name:
                                self.recievedCancelStatus = True
                                print order_Status

                                try:
                                    sendlock.acquire()
                                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + "Ordem: " + str(self.orderSeqNumber) + " foi cancelada - ALGO PARADO - a posicao do robo eh: " + self.position)
                                    # self.mktDataConn.send("============Chegou ao fim============")
                                    # self.mktDataConn.send("fim")
                                    sendlock.release()
                                    # self.stop_pair()
                                    # self.OrderManagerConn.close()
                                except:
                                    lgr.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: - deu algum pau")

                                self.close_Connections()

                                # try:
                                #     self.mktDataConn.close()
                                # except:
                                #     pass
                                #     # logging.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: Nao conseguiu fechar a conexao do MKT data")
                                # try:
                                #      self.OrderManagerConn.close()
                                # except:
                                #     pass
                                #     # logging.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: Nao conseguiu fechar a conexao do OMS")


                else:
                    lgr.info(str(self.corrID) + " - Dentro de else no connect_OrderManager: Recebu a mensagem: " + str(self.orderMessage)) # print debug
                    # self.orderMessage = self.orderMessage[0]
                    # lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: Recebu a mensagem: " + self.orderMessage) # print debug
                    self.orderMessage = self.orderMessage[0].split(",") # split o primeiro elemento da mensagem recebida
                    messageType = self.orderMessage[0] # primeiro string eh o tipo de mensagem recebida
                    lgr.info(str(self.corrID) + " - Dentro de connect_OrderManager: length of order Message: " + str(len(self.orderMessage))) # debug print

                    # garante que o Callback processa a ultima mensagem recebida
                    # pela velocidade das infos, algumas vezes vem mensagens agregadas
                    # este codigo pega as diversas mensagens e guarda apenas a ultima para ser processada pelo Trader
                    #
                    # As mensagens sao da forma MESSAGETYPE,[MENSAGEM SEPARADA POR ":"]
                    #
                    # Portanto, se ao separar por "," o tamanho do orderMessage for maior que 2, significa que tem mais de uma
                    # mensagem no string - sendo assim ele separa tudo e pega o ultimo para passar para o Callback
                    # if messageType == '4':
                    #     lgr.info(str(self.corrID) + " - Dentro do if messageType == '4' o tamanho do orderMessage recebido: " + str(len(self.orderMessage)))
                    #     lgr.info(str(self.corrID) + " - Dentro do if messageType == '4' o orderMessage e: " + str(self.orderMessage))
                    #     if len(self.orderMessage) > 2:
                    #         lgr.info(str(self.corrID) + " - dentro do messageType == 4:Order Message particionado: " + str(self.orderMessage))
                    #         self.orderMessage = self.orderMessage[0] + "," + self.orderMessage[len(self.orderMessage)-1] # cria a nova mensagem
                    #         self.orderMessage = self.orderMessage.split(",") # faz novamente o split para o trader
                    #         lgr.info(str(self.corrID) + " - dentro do messageType == 4:Novo Order Message: " + str(self.orderMessage))
                    #     else:
                    #         pass
                    # else:
                    #     pass


                    # Publica o status para o Listener no GUI
                    # self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))


                    # Mensagem tipo 1 confirmacao do roteamento da ordem - Order created and routed
                    # recebe o sequence number da ordem e o routeID
                    if messageType == '1':
                        print self.orderMessage
                        lgr.info(str(self.corrID) + " - dentro do messageType == 1: recebeu mensagem do orderManager %s", self.orderMessage)
                        self.orderSeqNumber = self.orderMessage[1]
                        self.routID = self.orderMessage[2]
                        message = self.orderMessage[3]
                        lgr.info(str(self.corrID) + " - dentro do messageType == 1: ordem enviada numero: " + message)
                        lgr.info(str(self.corrID) + " - dentro do messageType == 1: ordem enviada numero: " + self.orderSeqNumber)

                    # mensagem de confirmacao do envio de cancelamento de ordem
                    elif messageType == '2':
                        print self.orderMessage
                        lgr.info(str(self.corrID) + " - dentro do messageType == 2: recebeu mensagem do orderManager " + str(self.orderMessage))
                        # Publica o status para o Listener no GUI1
                        self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                        lgr.info(" daqui ele esta indo para onde??")

                    # Mensagens de Erro
                    elif messageType == '3':
                        lgr.info(str(self.corrID) + " - dentro do messageType == 3: recebeu mensagem do orderManager " + str(self.orderMessage))
                        lgr.info(str(self.corrID) + " - dentro do messageType == 3: orderMessage[1]: " + str(self.orderMessage[1]))
                        # Publica o status para o Listener no GUI
                        if not self.recievedCancelStatus:
                            self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage[1]))
                        else:
                            pass
                    # mensagens de status das ordens
                    elif messageType == '4':

                        lgr.info(str(self.corrID) + " - dentro do messageType == 4:recebeu mensagem do orderManager %s", str(self.orderMessage))
                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: orderMessage[1]: " + str(self.orderMessage[1]))
                        # prepara a mensagem para triagem
                        self.orderMessage = self.orderMessage[1].split(":")
                        order_Status = self.orderMessage[1]
                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: order_Status: " + order_Status)
                        amount_filled = self.orderMessage[2]
                        avg_price = self.orderMessage[3]
                        lmt_prc = self.orderMessage[4]
                        last_filled_time = self.orderMessage[5]

                        # se status FILLED
                        if order_Status == orderstatus.FILLED.name:

                            # sendlock.acquire()
                            if self.place_order_sent: # se a ordem eh de apregoamento
                                # captura os dados de preco realizado e montante filled
                                self.stopModifyRequests = True
                                self.dataPlace[placeOrderData.AVG_PRC.value] = avg_price
                                self.dataPlace[placeOrderData.FILL.value] = amount_filled

                                # Atribui a mensagem de posicao de acordo com o Side da ordem
                                if self.place_Side == Side.BUY.name:
                                    self.position = 'Long - ' + str(amount_filled) + ' - ' + str(self.ticker_Place) + ' @ ' + str(avg_price)
                                else:
                                    self.position = 'Short - ' + str(amount_filled) + ' - ' + str(self.ticker_Place) + ' @ ' + str(avg_price)

                                # Publica a posicao do trader para o Listener no GUI

                                self.SendPosition(self.dataClose[closeOrderData.CORRID.value],self.position)
                                self.lgr1.info(str(self.ticker_Place) + ":" + str(self.orderMessage) + " - FX: " + str(self.price_FX))
                                # wx.Sound.PlaySound('ding.wav', wx.SOUND_SYNC)

                            else: # se for ordem de fechamento
                                # wx.Sound.PlaySound('fillsound2.wav', wx.SOUND_SYNC)
                                try:
                                    # atribui mensagem de posicao para ser publicada
                                    self.position = 'Zerada - ultima operacao - ' + str(amount_filled) + ' - ' + str(self.ticker_Close) + ' @ ' + str(avg_price)
                                    self.SendPosition(self.dataClose[closeOrderData.CORRID.value],self.position) # Publica a posicao do trader para o Listener no GUI
                                    self.numberOfCompletePairs = self.numberOfCompletePairs + 1 # calcula o numero de pares completos operados
                                    self.dataClose[closeOrderData.AVG_PRC.value] = avg_price
                                    self.dataClose[closeOrderData.FILL.value] = amount_filled
                                    lgr.debug(str(self.corrID) + " - self.dataPlace[placeOrderData.AVG_PRC.value]: " + self.dataPlace[placeOrderData.AVG_PRC.value])
                                    lgr.debug(str(self.corrID) + " - self.dataPlace[placeOrderData.FILL.value]: " + self.dataPlace[placeOrderData.FILL.value])
                                    lgr.debug(str(self.corrID) + " - self.dataClose[closeOrderData.AVG_PRC.value]: " + self.dataClose[closeOrderData.AVG_PRC.value])
                                    print str(float(self.dataClose[closeOrderData.AVG_PRC.value]) / self.price_FX)
                                    print self.dataClose[closeOrderData.FILL.value]
                                except:
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4:Deu pau no primeiro try dentro do Status Filled")

                                # Calcula as estatisticas e dados dos pares realizados e do trader
                                try:
                                    lgr.debug(str(self.corrID) + ' - self.dataPlace[placeOrderData.AVG_PRC.value]: ' + str(self.dataPlace[placeOrderData.AVG_PRC.value]))
                                    lgr.debug(str(self.corrID) + ' - self.dataPlace[placeOrderData.FILL.value]: ' + str(self.dataPlace[placeOrderData.FILL.value]))
                                    lgr.debug(str(self.corrID) + ' - avgPrc in Dolars: ' + str(float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio))))
                                    lgr.debug(str(self.corrID) + ' - self.dataClose[closeOrderData.AVG_PRC.value]: ' + str(self.dataClose[closeOrderData.AVG_PRC.value]))
                                    lgr.debug(str(self.corrID) + ' - self.dataClose[closeOrderData.FILL.value]: ' + str(self.dataClose[closeOrderData.FILL.value]))
                                    lgr.debug(str(self.corrID) + ' - self.price_FX: ' + str(self.price_FX))
                                    lgr.debug(str(self.corrID) + ' - self.ratio: ' + str(self.ratio))
                                    if self.use_FX == 1:
                                        try:
                                            if self.place_Side == Side.BUY.name:
                                                self.spread_captured = round((((float(self.dataClose[closeOrderData.AVG_PRC.value]) /
                                                                                self.price_FX) * float(self.ratio)) - float(self.dataPlace[placeOrderData.AVG_PRC.value])), 4)
                                                self.gross_PNL_captured = round(self.spread_captured *
                                                                                 float(self.dataPlace[placeOrderData.FILL.value]), 4)
                                            else:
                                                self.spread_captured = -round((((float(self.dataClose[closeOrderData.AVG_PRC.value]) / self.price_FX) * float(self.ratio)) - float(self.dataPlace[placeOrderData.AVG_PRC.value])), 4)
                                                self.gross_PNL_captured = round(self.spread_captured  *
                                                                                 float(self.dataPlace[placeOrderData.FILL.value]), 4)
                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau dentro do primeiro if no calculo do spread")
                                    else:
                                        try:
                                            if self.place_Side == Side.BUY.name:
                                                self.spread_captured = round(float(self.dataClose[closeOrderData.AVG_PRC.value]) - float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio)), 4)
                                                self.gross_PNL_captured = round(self.spread_captured *
                                                                               float(self.dataClose[closeOrderData.FILL.value]), 4)
                                            else:
                                                self.spread_captured = -round(float(self.dataClose[closeOrderData.AVG_PRC.value]) -
                                                                              float((float(self.dataPlace[placeOrderData.AVG_PRC.value]) / self.price_FX) / float(self.ratio)), 4)
                                                self.gross_PNL_captured = round(self.spread_captured *
                                                                                float(self.dataClose[closeOrderData.FILL.value]), 4)
                                        except:
                                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau dentro do segundo if no calculo do spread")

                                    try:
                                        self.average_spread = (self.average_spread*(self.numberOfCompletePairs - 1) + self.spread_captured)/self.numberOfCompletePairs

                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do average_spread")

                                    try:
                                        self.gross_acumulated = self.gross_acumulated + self.gross_PNL_captured

                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do gross_acumulated")

                                    try:
                                        self.tradedVolume = (self.numberOfCompletePairs * float(self.dataPlace[placeOrderData.FILL.value]))

                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no bloco de calculo dos indicadores do tradedVolume ")

                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Spread requested: " + str(self.Pmargem))
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Spread Captured: " + str(self.spread_captured))
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Average Spread: " + str(self.average_spread))
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Gross margin: " + str(self.gross_acumulated))
                                    # publishers para os listeners do GUI
                                    try:
                                        self.SendRealSpread(self.dataClose[closeOrderData.CORRID.value],str(self.spread_captured))
                                        self.SendAvgSpread(self.dataClose[closeOrderData.CORRID.value],str(self.average_spread))
                                        self.SendLastGross(self.dataClose[closeOrderData.CORRID.value],str(self.gross_PNL_captured))
                                        self.SendPNL(self.dataClose[closeOrderData.CORRID.value],str(self.gross_acumulated))
                                        self.SendTradedVolume(self.dataClose[closeOrderData.CORRID.value],str(int(self.tradedVolume)))
                                        self.lgr1.info(str(self.ticker_Close) + ":" + str(self.orderMessage) + " - FX: " + str(self.price_FX) + " - Spread Capturado:" + str(self.spread_captured))
                                    except:
                                        lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no envio do publisher")

                                    '''
                                    ============================Controle de SPREAD MEDIO e SPREAD do Trader=====================

                                     Se o SPREAD ficar abaixo de 10% do requisitado por mais de 5 vezes seguidos, para o trader

                                     Se o PNL estiver muito longe do esperado ou ficar do sinal contrario do Spread requisitado
                                     o Trader parar e envia mensagem.

                                     =========================================================================================== '''

                                    if self.Pmargem > 0: # se o spread requisitado eh maior que zero

                                        if self.average_spread < self.Pmargem*(1 - self.avgspreadThreshold): # se spread medio eh menor que x% do requisitado

                                            if self.spread_captured < self.Pmargem*(1 - self.spreadThreshold): # se spread capturado eh menor que y% do spread requisitado

                                                self.stop_pair() # para o Trader
                                                wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread realizado foi 90% pior do que o requisitado")
                                                self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread realizado foi 90% pior do que o requisitado")

                                            else:

                                                self.badspreadcount = self.badspreadcount + 1 # conta quantas vezes o spread medio ficou abaixo do spread requisitado

                                                if self.badspreadcount == 10: # se chegou aa decima ocorrencia

                                                    self.stop_pair() # para o Trader
                                                    wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")
                                                    self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")

                                    elif self.Pmargem < 0: # se o spread requisitado eh menor que zero

                                        if self.average_spread < self.Pmargem*(1 + self.avgspreadThreshold):

                                            if self.spread_captured < self.Pmargem*(1 + self.spreadThreshold):

                                                self.stop_pair()
                                                wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread realizado foi 90% pior do que o requisitado")
                                                self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread realizado foi 90% pior do que o requisitado")
                                            else:

                                                self.badspreadcount = self.badspreadcount + 1

                                                if self.badspreadcount == 10:

                                                    self.stop_pair()
                                                    wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")
                                                    self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread medio esta ha 10 ocorrencias inferior a 10% do valor requisitado")

                                    elif self.Pmargem == 0: # se o spread requisitado eh igual a zero

                                        if self.average_spread < -0.03:

                                            if self.spread_captured < -0.09:

                                                self.stop_pair()
                                                wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread realizado foi U$ -0.09 - o requisitado foi U$ 0.0")
                                                self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread realizado foi U$ -0.09 - o requisitado foi U$ 0.0")

                                            else:

                                                self.badspreadcount = self.badspreadcount + 1

                                                if self.badspreadcount == 10:

                                                    self.stop_pair()
                                                    wx.MessageBox("O Trader + apregoando: " + str(self.ticker_Place) + " parado pois o Spread medio esta ha 10 ocorrencias inferior ao valor de U$ -0.03 - o requisitado foi U$ 0.0")
                                                    self.SendEmail("gustavo.oliveira@xpsecurities.com;henrique.cardoso@xpsecurities.com", "Erro no Trader: " + str(self.corrID) + " apregoando: " + str(self.ticker_Place),
                                                               "O Trader for parado pois o Spread medio esta ha 10 ocorrencias inferior ao valor de U$ -0.03 - o requisitado foi U$ 0.0")


                                except:
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no calculo do spread")


                            try:

                                # se chegou ao limite de posicao requisitado pelo operador
                                if str(int(self.tradedVolume)) == str(self.totalPairPosition):
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: Chegou no limite de posicao requisitado - Trader vai parar")
                                    # para o trader
                                    self.reachedTotalVolumeTraded = True
                                    self.stop_pair()
                                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + " Posicao maxima alcancada - Algoritmo Parou,FIM")
                                else:
                                    # caso nao tenha chegado ao limite, chama o callback onFill
                                    # print str(datetime.datetime.now())
                                    self.onFill()
                                    # print str(datetime.datetime.now())
                                    # Publica o status para o Listener no GUI1
                                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                                    lgr.info(str(self.corrID) + " - dentro do messageType == 4: executou o onFill() ")
                                # sendlock.release()
                            except:
                                lgr.info(str(self.corrID) + " - dentro do messageType == 4: Deu pau no onFill!!! Verificar!!")

                        # Se ordem rejeitada por alguma razao - para o trader e envia mensagem para o GUI
                        elif order_Status == orderstatus.REJECTED.name:
                            lgr.info(str(self.corrID) + " - dentro do messageType == 4: Ordem foi rejeitada, verificar e reiniciar o robot!")

                            sendlock.acquire()
                            self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + "Ordem foi rejeitada - verificar e reiniciar!")
                            sendlock.release()
                            return

                        # Se ordem "WORKING" envia precos para o GUI e chama a Callback onWorking
                        elif order_Status == orderstatus.WORKING.name:
                            print lmt_prc
                            print amount_filled
                            print self.orderSeqNumber


                            if self.place_order_sent:
                                    self.dataClose[closeOrderData.LMTPRC.value] = self.ClosePrice[str(lmt_prc)]  # atualiza o preco de close deste par com o preco relativo ao preco sendo trabalhado
                            else:
                                pass
                            # sendlock.acquire()
                            self.SendclosePrice(self.dataClose[closeOrderData.CORRID.value], self.dataClose[closeOrderData.LMTPRC.value])
                            self.SendPlacePrice(self.dataPlace[placeOrderData.CORRID.value], self.dataPlace[placeOrderData.LMTPRC.value])
                            # envia o FX recebido para atualizar o GUI
                            # sendlock.release()
                            # global timePartfill
                            # # if timePartfill.is_alive:
                            # timePartfill.stop()
                            #
                            # print "passou por aqui"
                            #
                            # timePartfill = TimerClass()
                            self.onWorking(lmt_prc, amount_filled, self.orderSeqNumber)
                            # Publica o status para o Listener no GUI1
                            if self.place_order_sent:
                                    self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + str(self.orderMessage))
                            else:
                                pass
                        # se ordem em algum desses estados - nao faz nada (por enquanto)
                        elif order_Status == orderstatus.CXLRPRQ.name:
                            pass
                        elif order_Status == orderstatus.CXLREQ.name:
                            pass
                        elif order_Status == orderstatus.REPPEN.name:
                            pass
                        elif order_Status == orderstatus.SENT.name:
                            pass

                        # se ordem cancelada - envia status de posicao para o GUI e para as conexoes para evitar envio de novas ordens
                        elif order_Status == orderstatus.CANCEL.name:
                            self.recievedCancelStatus = True
                            print order_Status

                            try:
                                sendlock.acquire()
                                self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + "," + "Ordem: " + str(self.orderSeqNumber) + " foi cancelada - ALGO PARADO - a posicao do robo eh: " + self.position)
                                sendlock.release()
                                # self.stop_pair()
                                # self.OrderManagerConn.close()
                            except:
                                lgr.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: - deu algum pau")
                            # try:
                            #     self.mktDataConn.close()
                            # except:
                            #     pass
                            #     # logging.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: Nao conseguiu fechar a conexao do MKT data")
                            # try:
                            #      self.OrderManagerConn.close()
                            # except:
                            #     pass
                            #     # logging.info(str(self.corrID) + " :dentro do elif order_Status == orderstatus.CANCEL.name: Nao conseguiu fechar a conexao do OMS")


            except:
                print "Deu pau na chamada de callbacks"
                sendlock.acquire()
                self.SendOrderStatus(str(self.dataPlace[placeOrderData.CORRID.value]) + ", O trader: " + str(self.dataPlace[placeOrderData.CORRID.value]) + " ==> " + "Deu erro na chamada de Callback, a ultima mensagem recebida foi: " + str(self.orderMessage))
                lgr.info("O trader: " + str(self.dataPlace[placeOrderData.CORRID.value]) + " ==> " + "Deu erro na chamada de Callback, a ultima mensagem recebida foi: " + str(self.orderMessage))
                sendlock.release()
                break

        # self.OrderManagerConn.close()  # close socket
