__author__ = 'gustavo.oliveira'

'''

Este sistema de gerenciamenteo de ordens foi desenvolvido com o objetivo de receber informacoes de ordens do EMSX API da
Bloomberg e enviar aos Traders que estiverem conectados e subscritos nele. Tanto a conexao com a BBG quanto com os
Traders sao feitas atraves do protocolo TCP. Os Traders sao totalmente independentes deste modulo, podendo, inclusive,
terem estrategias totalmente diversas entre si. O objetivo foi efetivamente esse, poder conectar diversas estrategias em
um mesmo OMS sem que houvesse a necessidade de alteracao do OMS. Outro ponto importante de ter o OMS independente do Trader
e poder controlar as ordens enviadas de uma forma independente, sendo possivel, em um futuro proximo, criar um firewall
acoplado para maior seguranca e controle das ordens.

Este modulo eh um Stand alone app que deve ser rodado na maquina onde se conectara com o BBG. A maquina deve ter o BBG
instalado, mais ainda, deve ser habilitado para operar o EMSX API no modulo programming.

--------DISCLAIMER ------
Este codigo eh propriedade da XP Securities, LLC. Esta eh uma versao beta que nao deve ser rodada sem supervisao
do autor e nao deve ser distribuida.

'''

# Importa as dependencias do codigo
import blpapi
import socket
import datetime
from enum import Enum
import time
import sys
import string
import random
from threading import Thread
import threading
import wx
import logging

# guarda nomes do API do bloomberg em variaveis estaticas
ERROR_INFO = blpapi.Name("ErrorInfo")
CREATE_ORDER_AND_ROUTE = blpapi.Name("CreateOrderAndRoute")
CREATE_ORDER_AND_ROUTE_WITH_STRAT = blpapi.Name("CreateOrderAndRouteWithStrat")
MODIFY_ROUTE = blpapi.Name("ModifyRoute")
MODIFY_ROUTE_WITH_STRAT = blpapi.Name("ModifyRouteWithStrat")
CANCEL_ROUTE = blpapi.Name("CancelRoute")

ORDER_ROUTE_FIELDS = blpapi.Name("OrderRouteFields")

SLOW_CONSUMER_WARNING = blpapi.Name("SlowConsumerWarning")
SLOW_CONSUMER_WARNING_CLEARED = blpapi.Name("SlowConsumerWarningCleared")

SESSION_STARTED = blpapi.Name("SessionStarted")
SESSION_TERMINATED = blpapi.Name("SessionTerminated")
SESSION_STARTUP_FAILURE = blpapi.Name("SessionStartupFailure")
SESSION_CONNECTION_UP = blpapi.Name("SessionConnectionUp")
SESSION_CONNECTION_DOWN = blpapi.Name("SessionConnectionDown")

SERVICE_OPENED = blpapi.Name("ServiceOpened")
SERVICE_OPEN_FAILURE = blpapi.Name("ServiceOpenFailure")

SUBSCRIPTION_FAILURE = blpapi.Name("SubscriptionFailure")
SUBSCRIPTION_STARTED = blpapi.Name("SubscriptionStarted")
SUBSCRIPTION_TERMINATED = blpapi.Name("SubscriptionTerminated")

EXCEPTIONS = blpapi.Name("exceptions")
FIELD_ID = blpapi.Name("fieldId")
REASON = blpapi.Name("reason")
CATEGORY = blpapi.Name("category")
DESCRIPTION = blpapi.Name("description")

# define o tipo de servico subscrito pelo Order Management System -
# emapisvc_beta => ambiente de testes
# emapisvc => ambiente de Prod
d_service = "//blp/emapisvc_beta"
d_host = "localhost"
d_port = 8194

# enumerador dos tipos de instrucoes recebidos das estrategias
class orderinstruction(Enum):
    SEND_ORDER              = 1
    SEND_ORDER_WITH_STRAT   = 2
    MODIFY_ORDER            = 3
    MODIFY_ORDER_WITH_STRAT = 4
    CANCEL_ORDER            = 5

# gerador de string aleatorio utilizado para criar o ID das estrategias - acredito que nao eh utilizado aqui
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#  cria o arquivo de Log
logging.basicConfig(filename='OrderManager.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(threadName)-10s - %(message)s', )

# abre conexao TCP para receber instrucoes de ordens e enviar mensagem de retorno apenas - o envio de info de ordens sera por outra funcao
def listenConnections():
    # dicionario de clientes relacionando a conexao recebida com o ID do trader
    global client_Dict
    # dicionario que relaciona a ordem com a conexao
    global clientOrder
    # instancia o dicionario
    clientOrder = dict()
    # instancia o dicionario
    client_Dict = dict()

    # cria o socket para receber conexao dos traders
    lstn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # set NO DELAY para o socket
    lstn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # bind lstn socket to this port
    # '10.0.0.94' - comp casa
    # '10.48.8.102' - comp XP
    # '10.48.8.110' - comp XP Henrique
    lstn.bind(('localhost', 2011))
    print "Connected to ('localhost', 2011)"

    # start listening for contacts from clients (at most 30 at a time)
    lstn.listen(30)
    while (1):
        # aceita a conexao - recebe objeto conexao e Tuple (ip/porta) do cliente
        (clnt, ap) = lstn.accept()

        # fica escutando mensagem do Trader - primeira mensagem do trader eh o seu clientID para identificacao
        clientID = clnt.recv(1024)

        # inicia o thread de recebimento de instrucoes dos traders associado aa conexao recebida
        thread_receive = Thread(target=receiveInstructions, args=(clnt, clientID, ))



        # print "Client ID dentro do listenConnections eh: " + clientID
        # alimenta o dicionario de clientes com o clientID recebido e a respectiva conexao
        if clientID in client_Dict: # se ja cliente com ID e conexao
            del client_Dict[clientID] # elimina o elemento do dicionario
            client_Dict[clientID] = clnt # cria outro elemento
        else:
            client_Dict[clientID] = clnt
        # print "Novo Cliente: " + str(clnt)
        logging.info("Dicionario de Clientes conectados: " + str(client_Dict))
        # LOG
        logging.info("                                       ")
        logging.info("========================================================")
        logging.info("Aceitou cliente %s com o ID %s", ap, clientID)
        logging.info("========================================================")
        logging.info("                                       ")
        # inicializa o thread de recebimento de instrucoes
        thread_receive.start()






# funcao que recebe as instrucoes dos clientes e envia para a BBG - cada trader tem seu proprio thread desta funcao
#
def receiveInstructions(clnt, clientID):
    # lock para o thread
    lockInstruction = threading.Lock()
    # logging.info("ClientID: " + str(clientID))
    # define o gerenciador de ordens
    # global orderManager
    # instancia o gerenciador de ordens
    orderManager = ManageOrders()
    # abre a conexao com a Bloomberg
    orderManager.open_BBG_Connection()
    thread_response = Thread(target=orderManager.recieveResponseandCallback, args=(clientID, ))
    thread_response.start()
    time.sleep(0.03) # para dar tempo suficiente para abrir a conexao com o bbg

    while (1):
        try:
            # print "dentro de recieveInstructions o cliente eh: " + str(clnt)
            logging.info("Inside recieveInstructions the client is: %s", str(clnt))
            try:
                # recebe as instrucoes dos clientes
                trader_message = clnt.recv(1024)
                logging.info("Inside recieveInstructions - Recieved the message: %s from trader: %s", str(trader_message), str(clnt))
                # print "acabou de chegar a mensagem: " + str(trader_message)
            except:
                print "nao tem mais robos conectados, vou parar!"
                orderManager.closeBBGconnection() # encerra a conexao deste robo com o  bbg
                # LOG
                logging.info("Inside recieveInstructions - Trader %s disconnected, exiting the loop - line 133", str(clnt))
                break
            # print "Mensagem recebida: " + trader_message + ": " + str(clnt)
            # transforma a mensagem em um vetor com strings
            trader_message = trader_message.split(",")
            # primeiro string do vetor eh o tipo de mensagem que o trader esta enviando
            instructionType = trader_message[0]
            # segundo string eh o clientID
            clientID = trader_message[1]
            # print trader_message[1]
            # print instructionType
            # print clientID
            # o segundo string eh composto das informacoes da ordem a ser enviada, separado por ":"
            orderData = trader_message[2]
            # print orderData
            # LOG
            logging.info("Recebeu a mensagem %s do trader %s", trader_message, clientID)

            #Instrucao de envio de ordens sem estrategia
            if instructionType == str(orderinstruction.SEND_ORDER.value):
                try:
                    # dados da ordem a ser enviada
                    orderData = orderData.split(":")
                    ticker = orderData[0]
                    amount = orderData[1]
                    type = orderData[2]
                    tif = orderData[3]
                    handinstr = orderData[4]
                    side = orderData[5]
                    lmtprc = orderData[6]
                    # lmtprc = 13.14
                    broker = orderData[7]
                    account = orderData[8]
                    tradernote = orderData[9]
                    corrID = id_generator(10)
                    # print ticker
                    # print type
                    # print tif
                    # print side
                    # print handinstr
                    # print lmtprc
                    # print amount
                    # print type
                    # print lmtprc
                    # print broker
                    # print account
                    # print tradernote

                    # lock o thread para enviar a ordem
                    lockInstruction.acquire()
                    # LOG
                    logging.info("Vou enviar a ordem: %s %s %s @ %s to %s", str(side), str(amount), str(ticker), str(lmtprc), str(clientID))
                    # envia a ordem atraves da conexao com o BBG
                    orderManager.createOrderandRoute(ticker, amount, type, tif, handinstr, side, lmtprc, broker,
                                                     account, tradernote, corrID, clientID)
                    logging.info("Voltei de enviar a ordem para %s", clientID)
                    lockInstruction.release()
                    # orderManager.createOrderandRoute()
                except:
                    logging.info("deu pau em instruction type SEND_ORDER")

            # Instrucao de envio de ordens com estrategia
            elif instructionType == str(orderinstruction.SEND_ORDER_WITH_STRAT.value):
                try:
                    # dados da ordem a ser enviada
                    orderData = orderData.split(":")
                    ticker = orderData[0]
                    amount = orderData[1]
                    type = orderData[2]
                    tif = orderData[3]
                    handinstr = orderData[4]
                    side = orderData[5]
                    lmtprc = orderData[6]
                    corrID = id_generator(10)
                    broker = orderData[7]
                    account = orderData[8]
                    tradernote = orderData[9]
                    brokerstrat = orderData[10]

                    # print ticker
                    # print amount
                    # print type
                    # print lmtprc
                    # print broker
                    # print account
                    # lock o thread para enviar a ordem
                    lockInstruction.acquire()
                    # logging.info("Vou enviar a ordem: %s %s %s @ %s to $s", str(side), str(amount), str(ticker), str(lmtprc), str(clientID))
                    # envia a ordem atraves da conexao com o BBG
                    orderManager.createOrderandRouteWithStrat(ticker, amount, type, tif, handinstr, side, lmtprc,
                                                              broker, account,tradernote, brokerstrat, corrID, clientID)
                    # logging.info("Voltei de enviar a ordem para %s", clientID)
                    lockInstruction.release()
                    # orderManager.createOrderandRouteWithStrat("BBVA US Equity", vol, "LMT", "GTX","ALGO","BUY",lmtprc,"ETGO","btx34579834","ALGORITMO","FAN",corrID, clientID, clnt)
                except:
                    logging.info("deu pau em instruction type SEND_ORDER_WITH_STRAT")

            # Instrucao de modificacao de ordem sem estrategia
            elif instructionType == str(orderinstruction.MODIFY_ORDER.value):
                try:
                    # dados da ordem a ser modificada
                    orderData = orderData.split(":")
                    sequence_num = orderData[0]
                    route_ID = orderData[1]
                    amount = orderData[2]
                    type = orderData[3]
                    ticker = orderData[4]
                    tif = orderData[5]
                    lmtprc = orderData[6]
                    corrID = id_generator(10)
                    # print ticker
                    # print amount
                    # print type
                    # print lmtprc
                    # lock o thread para enviar a ordem
                    lockInstruction.acquire()
                    # envia a ordem atraves da conexao com o BBG
                    orderManager.modifyOrder(sequence_num, route_ID, amount, type, ticker, tif, lmtprc, corrID,
                                             clientID)
                    lockInstruction.release()
                except:
                    logging.info("deu pau em instruction type MODIFY_ORDER")


            # Instrucao de modificacao de ordem com estrategia
            elif instructionType == str(orderinstruction.MODIFY_ORDER_WITH_STRAT.value):
                try:
                    # dados da ordem a ser modificada
                    orderData = orderData.split(":")
                    sequence_num = orderData[0]
                    route_ID = orderData[1]
                    amount = orderData[2]
                    type = orderData[3]
                    ticker = orderData[4]
                    tif = orderData[5]
                    lmtprc = orderData[6]
                    brokerstrat = orderData[7]
                    # corrID = id_generator(10)
                    # print ticker
                    # print amount
                    # print type
                    # print lmtprc
                    # lock o thread para enviar a ordem
                    lockInstruction.acquire()
                    # envia a ordem atraves da conexao com o BBG
                    orderManager.modifyOrderWithStrat(sequence_num, route_ID, amount, type, ticker, tif, lmtprc,
                                                      brokerstrat, corrID, clientID)
                    lockInstruction.release()
                except:
                    logging.info("deu pau em instruction type MODIFY_ORDER_WITH_STRAT")

            # Instrucao de cancelamento de ordem
            elif instructionType == str(orderinstruction.CANCEL_ORDER.value):
                try:
                    # dados da ordem a ser cancelada
                    orderData = orderData.split(":")
                    sequence_num = orderData[0]
                    route_ID = orderData[1]
                    # lock o thread para enviar a ordem
                    lockInstruction.acquire()
                    # envia a ordem atraves da conexao com o BBG
                    orderManager.cancelOrder(sequence_num, route_ID, corrID, clientID)
                    lockInstruction.release()
                except:
                    logging.info("deu pau em instruction type CANCEL_ORDER")
            else:
                pass

        except:
            logging.info("Alguma coisa deu errada na instrucao %s do trader %s", trader_message, clientID)
            # print trader_message
            # lockInstruction.release()
            print "Deu algum pau!"
            break





def main():
    # cria os threads

    # thread que escuta as conexoes dos Traders
    t = Thread(target=listenConnections)
    # Thread que recebe informacoes das ordens do BBG e envia para os Traders
    t2 = Thread(target=sendOrderInfo)

    # inicializa os threads
    t.start()
    t2.start()


main()
