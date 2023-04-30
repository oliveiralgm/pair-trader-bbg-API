# Importa as dependencias do codigo
import blpapi
import re
import cProfile
from optparse import OptionParser
import datetime
import socket
from threading import Thread
import logging
import time


class MarketData():
    '''
    Class MarketData - opens connection to BBG and subscribes to a security
    
    methods:
    open_BBG_Connection - connects to bbg
    subscribeData - subscribes data for a specific security
    '''

    # inicializa a conexao com o BBG
    def openBBGConnection(self):

        options = parseCmdLine()

        # # Define the socket using the "Context"
        # sock = context.socket(zmq.PUB)
        # sock.bind("tcp://127.0.0.1:5681")
        # Fill SessionOptions
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(options.host)
        sessionOptions.setServerPort(options.port)

        logging.info("Connecting to %s:%d" % (options.host, options.port))

        # Create a Session
        # global session
        self.session = blpapi.Session(sessionOptions)

        # Start a Session
        if not self.session.start():
            logging.info("Failed to start session.")
            return

        if not self.session.openService("//blp/mktdata"):
            logging.info("Failed to open //blp/mktdata")
            return

    # Subscreve os dados do BBG
    def subscribeData(self, security, field):

        #cria a lista de ativos a subscrever
        self.subscriptions = blpapi.SubscriptionList()
        # adiciona o ativo e campo aa lista
        self.subscriptions.add(security,
                          field,
                          "",
                          blpapi.CorrelationId(security + ',' + field))

        # solicita a subscricao
        self.session.subscribe(self.subscriptions)


    def stop_process_events(self):
        self.processEvents = False

    # processa os eventos recebidos do BBG
    def process_events(self, clnt):
        self.sendMktData = threading.Lock()
        self.processEvents = True # booleano para parar o process events
        try:
            # Process received events
            eventCount = 0
            while (self.processEvents):
                #provide timeout to give the chance to Ctrl+C handling:
                event = self.session.nextEvent(1)
                for msg in event:
                    if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:  # event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS or \

                        field = msg.getElementAsString('MKTDATA_EVENT_SUBTYPE')

                        # INITPAINT eh a primeira mensagem com dados recebidos do BBG, este bloco nao esta funcionando
                        # a ideia eh ele suprir o trader com dados iniciais - mas foi resolvido de outra forma:
                        # inicializamos o mkt data primeiro para alimentar o robo de dados
                        if field == 'INITPAINT':
                            pass

                        else: # para qualquer outra mensagem
                            # recebe o ticker da mensagem
                            self.ticker = msg.correlationIds()[0].value()
                            self.ticker = self.ticker.split(",")
                            # cria a chave do dicionario para enviar o dado ao cliente que solicitou a subscricao
                            clntSubData_Key = self.ticker[0] + "," + field
                            logging.info("chave: " + clntSubData_Key)
                            print "chave: " + clntSubData_Key

                            try:
                                # for clnt_ in client_Dict[clntSubData_Key]: # para cada cliente que subscreveu

                                logging.info("in processa_events, socket cliente diz: " + str(clnt))
                                logging.info("in processa_events, chave diz: " + str(clntSubData_Key))
                                logging.info("in processa_events, Valor diz: " + str(msg.getElementAsString(field)))

                                try:
                                    self.sendMktData.acquire()
                                    print str(msg.getElementAsString(field)) + ',' + str(clntSubData_Key) + ':'
                                    self.messageTosend = str(msg.getElementAsString(field)) + ',' + str(clntSubData_Key) + ':'
                                    clnt.send(self.messageTosend)
                                    self.sendMktData.release()
                                except:
                                    logging.info("in processa_events, Erro no clnt.send")
                            except:
                                print "ta dando erro aqui no MKTDATA =====================******"
                    # iniciei um error handling, mas ainda preciso verificar algumas coisa com o BBG
                    elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                        # print event.eventType()
                        try:
                            reason = msg.getElement("reason")
                            errorcode_reason = reason.getElementAsInteger("errorCode")
                            description = reason.getElementAsString("description")
                            logging.info("Error code reason: " + str(errorcode_reason))
                            logging.info("Error code description: " + str(description))
                        except:
                            logging.info("nao existe reason na mensagem")
                    else:
                        print msg

                if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                    eventCount += 1

        finally:
            # Stop the session
            self.session.stop()
            print "Parei a sessao..."
