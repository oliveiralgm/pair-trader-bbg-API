__author__ = 'gustavo.oliveira'

'''

Este modulo cria a conexao com o servidor de dados do BBG e faz a subscricao de qualquer trader que solicita
subscricao de dados.

Ele subscreve os dados apenas uma vez, caso algum robo subscreva algum dado ja subscrito, o modulo apenas adiciona
a conexao deste robo ao dicionario ja existente e o trader passa a fazer parte da lista de conexoes para as quais
aquele dado deve ser enviado.

Este modulo eh um Stand alone app que deve ser rodado na maquina onde se conectara com o BBG. A maquina deve ter o BBG
instalado, mais ainda, deve ser habilitado para operar o EMSX API no modulo programming.


'''

# Importa as dependencias do codigo
import blpapi
import re
import cProfile
from optparse import OptionParser
import datetime
import socket
import threading
from threading import Thread
import logging
import time
import market_data


# define as opcoes de conexao com a BBG
def parseCmdLine():
    parser = OptionParser(description="Retrieve realtime data.")
    parser.add_option("-a",
                      "--ip",
                      dest="host",
                      help="server name or IP (default: %default)",
                      metavar="ipAddress",
                      default="localhost")
    parser.add_option("-p",
                      dest="port",
                      type="int",
                      help="server port (default: %default)",
                      metavar="tcpPort",
                      default=8194)
    parser.add_option("--me",
                      dest="maxEvents",
                      type="int",
                      help="stop after this many events (default: %default)",
                      metavar="maxEvents",
                      default=1000000)

    (options, args) = parser.parse_args()

    return options

# metodo que escuta as conexoes e faz a associacao da conexao com o trader que faz a subscricao de dados
def listenConnections():

    while(1):

        lstn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lstn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # bind lstn socket to this port
        try:
            # '10.0.0.xx' - comp 1
            # '10.48.8.xxx' - comp 2
            # '10.48.8.xxx' - comp 3
            lstn.bind(('10.48.8.xxx', 2012))
        except:
            print "***** Deu pau na conexao, reinicie por favor *****" # tem que colocar um error handling
            break

        # start listening for contacts from clients (at most 30 at a time)
        lstn.listen(30)

        # aceita a conexao - recebe objeto conexao e Tuple (ip/porta) do cliente
        (clnt,ap) = lstn.accept()

        thread_subscribeAndSend = Thread(target=subscribeandSendData,args=(clnt, ))

        thread_subscribeAndSend.start()


def subscribeandSendData(connection):

    clnt = connection

    connectionMarketData = MarketData()

    connectionMarketData.open_BBG_Connection()


    # recebe dados de subscricao
    dataPair = []
    try:
        # recebe dados do trader
        dataList = clnt.recv(1024)

        dataPair = dataList.split(':')
        dataPair.pop(0)
        # print dataList
        # print dataPair
        for SubscriptData in dataPair:
            print SubscriptData
            # salva no dicionario a conexao e o dado associado
            security = SubscriptData.split(',')[0]
            field = SubscriptData.split(',')[1]
            
            if SubscriptData in client_Dict: # se ja existe subscricao de algum trader para o ativo requisitado
                # lista temporaria para inserir novo trader que subscreveu o mesmo ativo
                client_List = []
                # passa os clientes ja existentes para a lista temp
                client_List = client_Dict[SubscriptData]
                # insere novo client
                client_List.add(clnt)
                # insere a nova lista no dicionario
                client_Dict[SubscriptData] = client_List
                # client_Dict[SubscriptData].append(clnt)
            
                print client_Dict[SubscriptData]
            
            else: # se eh subscricao nova
                # insere o objeto conexao no dicionario
                client_Dict[SubscriptData] = {clnt}
                # debug print
                for clnt_ in client_Dict[SubscriptData]:
            
                    logging.info("socket cliente: " + str(clnt_))
                    logging.info("chave: " + SubscriptData)

        # subscreve os dados se for subscricao nova, caso nao seja apenas inclui a conexao para enviar o dado
            try:
                connectionMarketData.subscribeData(security, field)
            except:
                logging.info('dentro de subscribeandSendData(connection) - Erro em connectionMarketData.subscribeData(security, field)')
    except:
        pass

    connectionMarketData.process_events(clnt)

