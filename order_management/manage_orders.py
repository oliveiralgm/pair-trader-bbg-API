# classe de gerenciamento de ordens

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


class ManageOrders():
    '''
    Class ManageOrders - connects Bloombergs(BBG) EMSX API, gets order info from PairTrader and sends to BBG, recieves order status
    from BBG and sends to PairTrader to be processed.
    
    methods:
    open_BBG_Connection - opens connection with bloomberg EMSX API
    closeBBGconnection - closes connections with bbg api
    recieveResponseandCallback - recieves response to the command sent from bbg
    createOrderandRoute - creates an order and routes to bbg through a specific broker
    createOrderandRouteWithStrat - creates an order with a strategy and routes to bbg through a specific broker
    cancelOrder - cancels an order
    modifyOrder - modifies and order
    modifyOrderWithStrat - modifies and order with strategy
    
    '''
    # cria a conexao com o BBG e os requests para envio de instrucoes
    def open_BBG_Connection(self):
        # define a que computador vai se conectar
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(d_host)
        sessionOptions.setServerPort(d_port)

        logging.info("Connecting to %s:%d", str(d_host), d_port)
        # cria a variavel sessao do Bloomberg
        # global session
        # define o tipo de sessao
        self.session = blpapi.Session(sessionOptions)

        # Start a Session
        if not self.session.start():
            wx.MessageBox("Failed to start session with Bloomberg - please check and try again")
            return

        if not self.session.openService(d_service):
            print "Failed to open //blp/mktdata"
            return
        # define o tipo de servico
        self.service = self.session.getService(d_service)


    def closeBBGconnection(self):
        self.session.stop()


    def recieveResponseandCallback(self, clientID):
        logging.info("Iniciou o recieveResponseandCallback - linha 388")
        try:
            while (True):
                # recebe um evento do BBG
                # logging.info("Esta esperando o evento em recieveResponseandCallback - linha 392")
                ev = self.session.nextEvent(10)
                # logging.info("Inside recieveResponseandCallback - received event: " + str(ev))
                for msg in ev:
                    # logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Message: " + str(msg))
                    # logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - ev.eventType(): " + str(ev.eventType()))
                    # logging.info(str(clientID) + " - msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))

                    print msg
                    # evento eh do tipo RESPONSE
                    if ev.eventType() == blpapi.Event.RESPONSE:

                        logging.info(str(clientID) + " - Processing RESPONSE Event")
                        # se a mensagem tem o correlation ID da ordem enviada

                        # logging.info("Inside createOrderandRoute inside while - clientID: " + str(clientID))
                        # logging.info("Inside createOrderandRoute inside while - msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
                        # logging.info("Inside createOrderandRoute inside while - requestID.value(): " + str(requestID.value()))
                        # logging.info("Inside createOrderandRoute inside while - Message: %s", (msg.toString()))

                        logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Message Type: %s", msg.messageType())
                        # Se eh mensagem de erro
                        if msg.messageType() == ERROR_INFO:
                            errorCode = msg.getElementAsString("ERROR_CODE")
                            errorMessage = msg.getElementAsString("ERROR_MESSAGE")

                            # print "Error code reason: " + errorcode_reason
                            # print "Error code description: " + description
                            logging.info(str(clientID) + " - ERROR CODE: " + str(errorCode) + " - ERROR MESSAGE: " + str(errorMessage))
                            # envia a mensagem de erro para ser handled no PairTrader
                            client_Dict[clientID].send("3, Error Message - " + str(errorMessage) + ";")
                            # LOG
                            logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Deu erro em %s:  %s:%s", str(clientID), str(errorCode),
                                          str(errorMessage))
                            logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Deu erro em %s: %s", str(clientID), str(errorMessage))
                        # se eh mensagem de ordem criada
                        elif msg.messageType() == CREATE_ORDER_AND_ROUTE:
                            # logging.info("Inside createOrderandRoute inside while - clientID: " + str(clientID))
                            # logging.info("Inside createOrderandRoute inside while - msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
                            # logging.info("Inside createOrderandRoute inside while - requestID.value(): " + str(requestID.value()))
                            # logging.info("Inside createOrderandRoute inside while - Message: %s", (msg.toString()))
                            # sequence number da ordem
                            emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE")
                            # route ID da ordem
                            emsx_route_id = msg.getElementAsString("EMSX_ROUTE_ID")
                            # mensagem da BBG
                            message = msg.getElementAsString("MESSAGE")
                            # Envia a instrucao de envio de ordem sem estrategia para ser handled pelo PairTrader
                            client_Dict[clientID].send(
                                "1," + str(emsx_sequence) + "," + str(emsx_route_id) + "," + str(message) + ";")
                            logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Criou a ordem e enviou a mensagem para %s:  {1, %s:%s:%s}", str(clientID),
                                         str(emsx_sequence), str(emsx_route_id), str(message))
                            # cria a associacao da conexao com o sequence number da ordem para depois poder enviar as info das ordens
                            # para o PairTrader daquela conexao
                            clientOrder[emsx_sequence] = client_Dict[clientID]

                            # logging.INFO("EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
                            #     emsx_sequence, emsx_route_id, message))

                        # session.stop()
                        elif msg.messageType() == CREATE_ORDER_AND_ROUTE_WITH_STRAT:
                            try:
                                # logging.info("clientID: " + str(clientID))
                                # logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
                                # logging.info("requestID.value(): " + str(requestID.value()))
                                # logging.info("Message: %s", (msg.toString()))
                                emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE")
                                emsx_route_id = msg.getElementAsString("EMSX_ROUTE_ID")
                                message = msg.getElementAsString("MESSAGE")

                                # envia mensagem para o PairTrader com o sequence number e route ID da ordem criada
                                client_Dict[clientID].send(
                                    "1," + str(emsx_sequence) + "," + str(emsx_route_id) + "," + str(message) + ";")
                                logging.info(str(clientID) + " - recieveResponseandCallback - Criou a ordem e enviou a mensagem para %s:  {1, %s:%s:%s}", str(clientID),
                                             str(emsx_sequence), str(emsx_route_id), str(message))
                                # cria a associacao da conexao com o sequence number da ordem para depois poder enviar as info das ordens
                                # para o PairTrader daquela conexao
                                clientOrder[emsx_sequence] = client_Dict[clientID]

                            except:
                                logging.info(str(clientID) + " - Inside recieveResponseandCallback: deu algum pau no bloco iniciando na linha 4787 ")

                        elif msg.messageType() == CANCEL_ROUTE:
                            # logging.info("clientID: " + str(clientID))
                            # logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
                            # logging.info("requestID.value(): " + str(requestID.value()))
                            # logging.info("Message: %s", (msg.toString()))
                            status = msg.getElementAsInteger("STATUS")
                            message = msg.getElementAsString("MESSAGE")
                            client_Dict[clientID].send(
                                "2," + str(status) + ","  + str(message) + ";")
                            logging.info(str(clientID) + " - recieveResponseandCallback - Criou a ordem e enviou a mensagem para %s:  {2, %s:%s)", str(clientID),
                                         str(status), str(message))
                        elif msg.messageType() == SESSION_TERMINATED:
                            logging.info(str(clientID) + " - Session Terminated...")
                        elif msg.messageType() == SESSION_STARTED:
                            logging.info(str(clientID) + " - Session Started...")
                        elif msg.messageType() == SESSION_STARTUP_FAILURE:
                            logging.info(str(clientID) + " - Session Startup Failure...")
                        elif msg.messageType() == SESSION_CONNECTION_DOWN:
                            logging.info(str(clientID) + " - Session Connection Down...")
                        elif msg.messageType() == SERVICE_OPENED:
                            logging.info(str(clientID) + " - Service Opened...")
                        elif msg.messageType() == SERVICE_OPEN_FAILURE:
                            logging.info(str(clientID) + " - Service Open Failure...")
                        elif msg.messageType() == SUBSCRIPTION_FAILURE:
                            logging.info(str(clientID) + " - Subscription Failure...")
                        elif msg.messageType() == SUBSCRIPTION_STARTED:
                            logging.info(str(clientID) + " - Subscription Started...")
                        elif msg.messageType() == SUBSCRIPTION_TERMINATED:
                            logging.info(str(clientID) + " - Subscription Terminated...")
                    else:
                        print "Message: %s" % (msg.toString())

        except:
            logging.info("Inside recieveResponseandCallback - deu pau no recebimento de confirmacao")


    # metodo de envio de ordens sem estrategia
    def createOrderandRoute(self, ticker, amount, orderType, TIF, Hand_Instruction, Side, lmtPrice, broker, account,
                            emsx_Notes, corrID, clientID):
        # Cria os servicos de request
        request_Create_order_and_route = self.service.createRequest("CreateOrderAndRoute")

        logging.info("Dentro do createOrderandRoute: " + str(ticker) + ": " + str(amount) + "; " + str(orderType) + ":" +
                     str(TIF) + ": " + str(Hand_Instruction) + ": " + str(Side) + ": " + str(lmtPrice) +
                     ": " + str(broker) + ": " + str(account) + ":" + str(emsx_Notes) + ":" + str(corrID) + ":" + str(clientID))

        # Seta as variaves para enviar a ordem com as informacoes recebidas do trader

        request_Create_order_and_route.set("EMSX_TICKER", ticker)
        request_Create_order_and_route.set("EMSX_AMOUNT", amount)
        request_Create_order_and_route.set("EMSX_ORDER_TYPE", orderType)
        request_Create_order_and_route.set("EMSX_TIF", TIF)
        request_Create_order_and_route.set("EMSX_HAND_INSTRUCTION", Hand_Instruction)
        request_Create_order_and_route.set("EMSX_SIDE", Side)
        request_Create_order_and_route.set("EMSX_ACCOUNT", account)
        request_Create_order_and_route.set("EMSX_LIMIT_PRICE", lmtPrice)
        request_Create_order_and_route.set("EMSX_BROKER", broker)
        request_Create_order_and_route.set("EMSX_NOTES", emsx_Notes)

        '''
            Outros campos que podem ser utilizados para envio caso necessario
        '''

        # request_Create_order_and_route.set("EMSX_INSTRUCTIONS", emsx_Instructions);
        # if options.EMSX_ACCOUNT:                request.set("EMSX_ACCOUNT",options.EMSX_ACCOUNT);
        # if options.EMSX_LIMIT_PRICE:            request.set("EMSX_LIMIT_PRICE", options.EMSX_LIMIT_PRICE);
        # if options.EMSX_CFD_FLAG:               request.set("EMSX_CFD_FLAG", options.EMSX_CFD_FLAG);
        # if options.EMSX_CLEARING_ACCOUNT:       request.set("EMSX_CLEARING_ACCOUNT", options.EMSX_CLEARING_ACCOUNT);
        # if options.EMSX_CLEARING_FIRM:          request.set("EMSX_CLEARING_FIRM", options.EMSX_CLEARING_FIRM);
        # if options.EMSX_EXCHANGE_DESTINATION:   request.set("EMSX_EXCHANGE_DESTINATION", options.EMSX_EXCHANGE_DESTINATION);
        # if options.EMSX_EXEC_INSTRUCTIONS:      request.set("EMSX_EXEC_INSTRUCTIONS", options.EMSX_EXEC_INSTRUCTIONS);
        # if options.EMSX_GET_WARNINGS:           request.set("EMSX_GET_WARNINGS", options.EMSX_GET_WARNINGS);
        # if options.EMSX_GTD_DATE:               request.set("EMSX_GTD_DATE", options.EMSX_GTD_DATE);
        # if options.EMSX_LOCATE_BROKER:          request.set("EMSX_LOCATE_BROKER", options.EMSX_LOCATE_BROKER);
        # if options.EMSX_LOCATE_ID:              request.set("EMSX_LOCATE_ID", options.EMSX_LOCATE_ID);
        # if options.EMSX_LOCATE_REQ:             request.set("EMSX_LOCATE_REQ", options.EMSX_LOCATE_REQ);
        # if options.EMSX_NOTES:                  request.set("EMSX_NOTES", options.EMSX_NOTES);
        # if options.EMSX_ODD_LOT:                request.set("EMSX_ODD_LOT", options.EMSX_ODD_LOT);
        # if options.EMSX_ORDER_ORIGIN:           request.set("EMSX_ORDER_ORIGIN", options.EMSX_ORDER_ORIGIN);
        # if options.EMSX_ORDER_REF_ID:           request.set("EMSX_ORDER_REF_ID", options.EMSX_ORDER_REF_ID);
        # if options.EMSX_P_A:                    request.set("EMSX_P_A", options.EMSX_P_A);
        # if options.EMSX_RELEASE_TIME:           request.set("EMSX_RELEASE_TIME", options.EMSX_RELEASE_TIME);
        # if options.EMSX_SETTLE_DATE:            request.set("EMSX_SETTLE_DATE", options.EMSX_SETTLE_DATE);
        # if options.EMSX_STOP_PRICE:             request.set("EMSX_STOP_PRICE", options.EMSX_STOP_PRICE);

        # imprime a ordem de envio
        logging.info("Inside createOrderandRoute inside while - Request: %s",  request_Create_order_and_route.toString())

        # set the request correlation ID
        requestID = blpapi.CorrelationId(corrID)
        # logging.info("Inside createOrderandRoute inside while - RequestID: "+ str(requestID))
        try:
            # send the request to BBG with corresponding Correlation ID to identify it
            self.session.sendRequest(request_Create_order_and_route, correlationId=requestID)
        except:
            logging.info("Inside createOrderandRoute inside while - deu pau no sendRequest: request_Create_order_and_route")

    # metodo de envio de ordens com estrategia
    def createOrderandRouteWithStrat(self, ticker, amount, orderType, TIF, Hand_Instruction, Side, lmtPrice, broker,
                                     account, emsx_Notes, stratName, corrID, clientID):
        # Cria os servicos de request
        request_Create_order_and_route_With_Strat = self.service.createRequest("CreateOrderAndRouteWithStrat")

        logging.info("Dentro do createOrderandRouteWithStrat: " + str(ticker) + ": " + str(amount) + ": " + str(orderType) + ":" +
             str(TIF) + ": " + str(Hand_Instruction) + ": " + str(Side) + ": " + str(lmtPrice) +
             ": " + str(broker) + ": " + str(account) + ": " + str(emsx_Notes) + ": " + str(stratName) +
                     ": " + str(corrID) + ": " + str(clientID))

        # define as variaves para enviar a ordem com as informacoes recebidas do trader

        request_Create_order_and_route_With_Strat.set("EMSX_TICKER", ticker)
        request_Create_order_and_route_With_Strat.set("EMSX_AMOUNT", amount)
        request_Create_order_and_route_With_Strat.set("EMSX_ORDER_TYPE", orderType)
        request_Create_order_and_route_With_Strat.set("EMSX_TIF", TIF)
        request_Create_order_and_route_With_Strat.set("EMSX_HAND_INSTRUCTION", Hand_Instruction)
        request_Create_order_and_route_With_Strat.set("EMSX_SIDE", Side)
        request_Create_order_and_route_With_Strat.set("EMSX_ACCOUNT", account)
        request_Create_order_and_route_With_Strat.set("EMSX_LIMIT_PRICE", lmtPrice)
        request_Create_order_and_route_With_Strat.set("EMSX_BROKER", broker)
        request_Create_order_and_route_With_Strat.set("EMSX_NOTES", emsx_Notes)

        '''
            Outros campos que podem ser utilizados para envio caso necessario
        '''

        # request_Create_order_and_route_With_Strat.set("EMSX_EXEC_INSTRUCTIONS", emsx_Instructions);
        # if options.EMSX_CFD_FLAG:               request.set("EMSX_CFD_FLAG", options.EMSX_CFD_FLAG);
        # if options.EMSX_CLEARING_ACCOUNT:       request.set("EMSX_CLEARING_ACCOUNT", options.EMSX_CLEARING_ACCOUNT);
        # if options.EMSX_CLEARING_FIRM:          request.set("EMSX_CLEARING_FIRM", options.EMSX_CLEARING_FIRM);
        # if options.EMSX_EXCHANGE_DESTINATION:   request.set("EMSX_EXCHANGE_DESTINATION", options.EMSX_EXCHANGE_DESTINATION);
        # if options.EMSX_EXEC_INSTRUCTIONS:      request.set("EMSX_EXEC_INSTRUCTIONS", options.EMSX_EXEC_INSTRUCTIONS);
        # if options.EMSX_GET_WARNINGS:           request.set("EMSX_GET_WARNINGS", options.EMSX_GET_WARNINGS);
        # if options.EMSX_GTD_DATE:               request.set("EMSX_GTD_DATE", options.EMSX_GTD_DATE);
        # if options.EMSX_LOCATE_BROKER:          request.set("EMSX_LOCATE_BROKER", options.EMSX_LOCATE_BROKER);
        # if options.EMSX_LOCATE_ID:              request.set("EMSX_LOCATE_ID", options.EMSX_LOCATE_ID);
        # if options.EMSX_LOCATE_REQ:             request.set("EMSX_LOCATE_REQ", options.EMSX_LOCATE_REQ);
        # if options.EMSX_NOTES:                  request.set("EMSX_NOTES", options.EMSX_NOTES);
        # if options.EMSX_ODD_LOT:                request.set("EMSX_ODD_LOT", options.EMSX_ODD_LOT);
        # if options.EMSX_ORDER_ORIGIN:           request.set("EMSX_ORDER_ORIGIN", options.EMSX_ORDER_ORIGIN);
        # if options.EMSX_ORDER_REF_ID:           request.set("EMSX_ORDER_REF_ID", options.EMSX_ORDER_REF_ID);
        # if options.EMSX_P_A:                    request.set("EMSX_P_A", options.EMSX_P_A);
        # if options.EMSX_RELEASE_TIME:           request.set("EMSX_RELEASE_TIME", options.EMSX_RELEASE_TIME);
        # if options.EMSX_SETTLE_DATE:            request.set("EMSX_SETTLE_DATE", options.EMSX_SETTLE_DATE);
        # if options.EMSX_STOP_PRICE:             request.set("EMSX_STOP_PRICE", options.EMSX_STOP_PRICE);

        # Define os valores de Estrategia da ordem a ser enviada

        strategy = request_Create_order_and_route_With_Strat.getElement('EMSX_STRATEGY_PARAMS')
        strategy.setElement('EMSX_STRATEGY_NAME', stratName)

        indicator = strategy.getElement('EMSX_STRATEGY_FIELD_INDICATORS')
        data = strategy.getElement('EMSX_STRATEGY_FIELDS')

        params = []
        for param in params:
            parts = param.split("=", 1)
            indicator.appendElement().setElement("EMSX_FIELD_INDICATOR", 1 if parts[1] == "" else 0)
            data.appendElement().setElement("EMSX_FIELD_DATA", parts[1])

        logging.info("Request: %s", request_Create_order_and_route_With_Strat.toString())

        # set the request correlation ID
        requestID = blpapi.CorrelationId(corrID)
        # logging.info("RequestID: "+ str(requestID))

        try:
            # send the request to BBG with corresponding Correlation ID to identify it
            self.session.sendRequest(request_Create_order_and_route_With_Strat, correlationId=requestID)
        except:
            logging.info("deu pau no sendRequest: request_Create_order_and_route_With_Strat")


    def cancelOrder(self, sequence_num, route_ID, corrID, clientID):

        # Cria os servicos de request
        request_Cancel_Route = self.service.createRequest("CancelRoute")

        routes = request_Cancel_Route.getElement("ROUTES")

        route = routes.appendElement()

        route.getElement("EMSX_SEQUENCE").setValue(sequence_num)
        route.getElement("EMSX_ROUTE_ID").setValue(route_ID)

        # if options.EMSX_TRADER_UUID:            request.set("EMSX_TRADER_UUID", options.EMSX_TRADER_UUID)

        requestID = blpapi.CorrelationId(corrID)

        try:
            self.session.sendRequest(request_Cancel_Route, correlationId=requestID)
        except:
            logging.info("deu pau no sendRequest: request_Cancel_Route")


    def modifyOrder(self, sequence_num, route_ID, amount, lmt, ticker, TIF, lmtPrice, corrID, clientID):

        # Cria os servicos de request
        request_Modify_Route = self.service.createRequest("ModifyRoute")


        request_Modify_Route.set("EMSX_SEQUENCE", sequence_num)
        request_Modify_Route.set("EMSX_ROUTE_ID", route_ID)
        request_Modify_Route.set("EMSX_AMOUNT", amount)
        request_Modify_Route.set("EMSX_ORDER_TYPE", lmt)
        request_Modify_Route.set("EMSX_TICKER", ticker)
        request_Modify_Route.set("EMSX_TIF", TIF)
        request_Modify_Route.set("EMSX_LIMIT_PRICE", lmtPrice)
        # if options.EMSX_ACCOUNT:                request.set("EMSX_ACCOUNT", options.EMSX_ACCOUNT)
        # if options.EMSX_CLEARING_ACCOUNT:       request.set("EMSX_CLEARING_ACCOUNT", options.EMSX_CLEARING_ACCOUNT)
        # if options.EMSX_CLEARING_FIRM:          request.set("EMSX_CLEARING_FIRM", options.EMSX_CLEARING_FIRM)
        # if options.EMSX_COMM_TYPE:              request.set("EMSX_COMM_TYPE", options.EMSX_COMM_TYPE)
        # if options.EMSX_EXCHANGE_DESTINATION:   request.set("EMSX_EXCHANGE_DESTINATION", options.EMSX_EXCHANGE_DESTINATION)
        # if options.EMSX_GET_WARNINGS:           request.set("EMSX_GET_WARNINGS", options.EMSX_GET_WARNINGS)
        # if options.EMSX_GTD_DATE:               request.set("EMSX_GTD_DATE", options.EMSX_GTD_DATE)

        # if options.EMSX_LOCATE_BROKER:          request.set("EMSX_LOCATE_BROKER", options.EMSX_LOCATE_BROKER)
        # if options.EMSX_LOCATE_ID:              request.set("EMSX_LOCATE_ID", options.EMSX_LOCATE_ID)
        # if options.EMSX_LOCATE_REQ:             request.set("EMSX_LOCATE_REQ", options.EMSX_LOCATE_REQ)
        # if options.EMSX_NOTES:                  request.set("EMSX_NOTES", options.EMSX_NOTES)
        # if options.EMSX_ODD_LOT:                request.set("EMSX_ODD_LOT", options.EMSX_ODD_LOT)
        # if options.EMSX_P_A:                    request.set("EMSX_P_A", options.EMSX_P_A)
        # if options.EMSX_STOP_PRICE:             request.set("EMSX_STOP_PRICE", options.EMSX_STOP_PRICE)
        # if options.EMSX_TRADER_NOTES:           request.set("EMSX_TRADER_NOTES", options.EMSX_TRADER_NOTES)
        # if options.EMSX_USER_COMM_RATE:         request.set("EMSX_USER_COMM_RATE", options.EMSX_USER_COMM_RATE)
        # if options.EMSX_USER_FEES:              request.set("EMSX_USER_FEES", options.EMSX_USER_FEES)

        # print "Request: %s" % request_Modify_Route.toString()

        requestID = blpapi.CorrelationId(corrID)
        try:
            self.session.sendRequest(request_Modify_Route, correlationId=requestID)
        except:
            logging.info("deu pau no recebimento de confirmacao de: request_Modify_Route")

        '''
            A parte de receber a resposta da modificacao da ordem foi ignorada. Isso foi feito pois a confirmacao
            chegava a demorar 200ms para chegar adicionando muita latencia ao sistema, ja que alteracao de preco limite
            eh um dos processos mais frequentes devido aa natureza da estrategia.
        '''

            # timeout = 500
            #
            # try:
            #
            #     while(True):
            #
            #         ev=session.nextEvent(timeout)
            #         for msg in ev:
            #
            #             if ev.eventType() == blpapi.Event.RESPONSE:
            #
            #                 print "Processing RESPONSE Event"
            #
            #                 if msg.correlationIds()[0].value() == requestID.value():
            #
            #                     print "Message Type: %s" % msg.messageType()
            #
            #                     if msg.messageType() == ERROR_INFO:
            #                         errorCode = msg.getElementAsInteger("ERROR_CODE")
            #                         errorMessage = msg.getElementAsString("ERROR_MESSAGE")
            #                         print "ERROR CODE: %d\tERROR MESSAGE: %s" % (errorCode,errorMessage)
            #                     elif msg.messageType() == MODIFY_ROUTE:
            #                         message = msg.getElementAsString("MESSAGE")
            #                         client_Dict[clientID].send("3," + str(sequence_num) + "," + str(route_ID) + "," + message)
            #                         logging.info("Criou a ordem e enviou a mensagem para %s:  {3, %s:%s:%s}", clientID, str(emsx_sequence), str(emsx_route_id), message)
            #                         print "EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (sequence_num,route_ID,message)
            #
            #                     # session.stop()
            #                     return
            #                 else:
            #                     print "Message: %s" % (msg.toString())
            #
            #             break
            #
            # except:
            #     logging.info("deu pau no recebimento de confirmacao de: request_Modify_Route")


    def modifyOrderWithStrat(self, sequence_num, route_ID, amount, lmt, ticker, TIF, lmtPrice, strat_name, corrID,
                             clientID):

        # Cria os servicos de request
        request_Modify_Route_With_Strat = self.service.createRequest("ModifyRouteWithStrat")

        request_Modify_Route_With_Strat.set("EMSX_SEQUENCE", sequence_num)
        request_Modify_Route_With_Strat.set("EMSX_ROUTE_ID", route_ID)
        request_Modify_Route_With_Strat.set("EMSX_AMOUNT", amount)
        request_Modify_Route_With_Strat.set("EMSX_ORDER_TYPE", lmt)
        request_Modify_Route_With_Strat.set("EMSX_TICKER", ticker)
        request_Modify_Route_With_Strat.set("EMSX_TIF", TIF)
        request_Modify_Route_With_Strat.set("EMSX_LIMIT_PRICE", lmtPrice)
        # if options.EMSX_ACCOUNT:                request.set("EMSX_ACCOUNT", options.EMSX_ACCOUNT)
        # if options.EMSX_CLEARING_ACCOUNT:       request.set("EMSX_CLEARING_ACCOUNT", options.EMSX_CLEARING_ACCOUNT)
        # if options.EMSX_CLEARING_FIRM:          request.set("EMSX_CLEARING_FIRM", options.EMSX_CLEARING_FIRM)
        # if options.EMSX_COMM_TYPE:              request.set("EMSX_COMM_TYPE", options.EMSX_COMM_TYPE)
        # if options.EMSX_EXCHANGE_DESTINATION:   request.set("EMSX_EXCHANGE_DESTINATION", options.EMSX_EXCHANGE_DESTINATION)
        # if options.EMSX_GET_WARNINGS:           request.set("EMSX_GET_WARNINGS", options.EMSX_GET_WARNINGS)
        # if options.EMSX_GTD_DATE:               request.set("EMSX_GTD_DATE", options.EMSX_GTD_DATE)

        # if options.EMSX_LOCATE_BROKER:          request.set("EMSX_LOCATE_BROKER", options.EMSX_LOCATE_BROKER)
        # if options.EMSX_LOCATE_ID:              request.set("EMSX_LOCATE_ID", options.EMSX_LOCATE_ID)
        # if options.EMSX_LOCATE_REQ:             request.set("EMSX_LOCATE_REQ", options.EMSX_LOCATE_REQ)
        # if options.EMSX_NOTES:                  request.set("EMSX_NOTES", options.EMSX_NOTES)
        # if options.EMSX_ODD_LOT:                request.set("EMSX_ODD_LOT", options.EMSX_ODD_LOT)
        # if options.EMSX_P_A:                    request.set("EMSX_P_A", options.EMSX_P_A)
        # if options.EMSX_STOP_PRICE:             request.set("EMSX_STOP_PRICE", options.EMSX_STOP_PRICE)
        # if options.EMSX_TRADER_NOTES:           request.set("EMSX_TRADER_NOTES", options.EMSX_TRADER_NOTES)
        # if options.EMSX_USER_COMM_RATE:         request.set("EMSX_USER_COMM_RATE", options.EMSX_USER_COMM_RATE)
        # if options.EMSX_USER_FEES:              request.set("EMSX_USER_FEES", options.EMSX_USER_FEES)

        strategy = request_Modify_Route_With_Strat.getElement('EMSX_STRATEGY_PARAMS')
        strategy.setElement('EMSX_STRATEGY_NAME', strat_name)

        indicator = strategy.getElement('EMSX_STRATEGY_FIELD_INDICATORS')
        data = strategy.getElement('EMSX_STRATEGY_FIELDS')

        params = []
        for param in params:
            parts = param.split("=", 1)
            indicator.appendElement().setElement("EMSX_FIELD_INDICATOR", 1 if parts[1] == "" else 0)
            data.appendElement().setElement("EMSX_FIELD_DATA", parts[1])

        # print "Request: %s" % request_Modify_Route_With_Strat.toString()

        requestID = blpapi.CorrelationId(corrID)

        try:
            self.session.sendRequest(request_Modify_Route_With_Strat, correlationId=requestID)
        except:
            logging.info("deu pau no recebimento de confirmacao de: request_Modify_Route_With_Strat")

        '''
            A parte de receber a resposta da modificacao da ordem foi ignorada. Isso foi feito pois a confirmacao
            chegava a demorar 200ms para chegar adicionando muita latencia ao sistema, ja que alteracao de preco limite
            eh um dos processos mais frequentes devido aa natureza da estrategia.
        '''

            # timeout = 500
            #
            # try:
            #
            #     while(True):
            #
            #         ev=session.nextEvent(timeout)
            #         for msg in ev:
            #
            #             if ev.eventType() == blpapi.Event.RESPONSE:
            #
            #                 print "Processing RESPONSE Event"
            #
            #                 if msg.correlationIds()[0].value() == requestID.value():
            #
            #                     print "Message Type: %s" % msg.messageType()
            #
            #                     if msg.messageType() == ERROR_INFO:
            #                         errorCode = msg.getElementAsInteger("ERROR_CODE")
            #                         errorMessage = msg.getElementAsString("ERROR_MESSAGE")
            #                         print "ERROR CODE: %d\tERROR MESSAGE: %s" % (errorCode,errorMessage)
            #                     elif msg.messageType() == MODIFY_ROUTE_WITH_STRAT:
            #                         # emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE")
            #                         # emsx_route_id = msg.getElementAsInteger("EMSX_ROUTE_ID")
            #                         message = msg.getElementAsString("MESSAGE")
            #                         try:
            #                             client_Dict[clientID].send("3," + str(sequence_num) + "," + str(route_ID) + "," + message)
            #                             logging.info("Criou a ordem e enviou a mensagem para %s:  {3, %s:%s:%s}", str(clientID), str(sequence_num), str(route_ID), str(message))
            #                         except:
            #                             logging.info("deu pau no envio da mensagem: %s - para %s: ", "3," + str(sequence_num) + "," + str(route_ID) + "," + message, clientID)
            #                         print "EMSX_SEQUENCE: %s\tEMSX_ROUTE_ID: %s\tMESSAGE: %s" % (sequence_num,route_ID,message)
            #
            #                     # session.stop()
            #                     return
            #                 else:
            #                     print "Message: %s" % (msg.toString())
            #
            # except:
            #     logging.info("deu pau no recebimento de confirmacao de: request_Modify_Route_With_Strat")

