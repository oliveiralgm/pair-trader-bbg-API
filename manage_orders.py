# classe de gerenciamento de ordens
class ManageOrders():
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

        #  cria as variaveis globais de request para enviar as ordens para o EMSX API
        # global request_Create_order_and_route
        # global request_Create_order_and_route_With_Strat
        # global request_Modify_Route
        # global request_Modify_Route_With_Strat
        # global request_Cancel_Route


        # request_Create_order_and_route_With_Strat = self.service.createRequest("CreateOrderAndRouteWithStrat")
        # request_Create_order_and_route = self.service.createRequest("CreateOrderAndRoute")
        # request_Modify_Route = self.service.createRequest("ModifyRoute")
        # request_Modify_Route_With_Strat = self.service.createRequest("ModifyRouteWithStrat")
        # request_Cancel_Route = self.service.createRequest("CancelRoute")

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
                        # if msg.correlationIds()[0].value() == requestID.value():

                        logging.info(str(clientID) + " - Inside recieveResponseandCallback inside while - Message Type: %s", msg.messageType())
                        # Se eh mensagem de erro
                        if msg.messageType() == ERROR_INFO:
                            errorCode = msg.getElementAsString("ERROR_CODE")
                            errorMessage = msg.getElementAsString("ERROR_MESSAGE")
                            # reason = msg.getElement("reason");
                            # errorcode_reason = reason.getElementAsInteger("errorCode")
                            # description = reason.getElementAsString("description")
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
                            # print clientOrder[emsx_sequence]
                            # print "EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
                            #     emsx_sequence, emsx_route_id, message)
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
                                # print str(client_Dict[clientID])
                                # envia mensagem para o PairTrader com o sequence number e route ID da ordem criada
                                client_Dict[clientID].send(
                                    "1," + str(emsx_sequence) + "," + str(emsx_route_id) + "," + str(message) + ";")
                                logging.info(str(clientID) + " - recieveResponseandCallback - Criou a ordem e enviou a mensagem para %s:  {1, %s:%s:%s}", str(clientID),
                                             str(emsx_sequence), str(emsx_route_id), str(message))
                                # cria a associacao da conexao com o sequence number da ordem para depois poder enviar as info das ordens
                                # para o PairTrader daquela conexao
                                clientOrder[emsx_sequence] = client_Dict[clientID]
                                # print clientOrder[clientID]
                                # print "recebi a mensagem da ordem: " + str(datetime.datetime.utcnow())
                                # print "EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
                                #     emsx_sequence, emsx_route_id, message)
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

        # logging.info("Inside createOrderandRoute inside while - client_Dict[clientID]): " + str(client_Dict[clientID]))
        # timeout = 10

        # try:
        #
        #     while (True):
        #         # recebe um evento do BBG
        #         ev = self.session.nextEvent(timeout)
        #         for msg in ev:
        #             logging.info("Inside createOrderandRoute inside while - Message: " + str(msg))
        #             logging.info("Inside createOrderandRoute inside while - ev.eventType(): " + str(ev.eventType()))
        #             logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #             print msg
        #             # evento eh do tipo RESPONSE
        #             if ev.eventType() == blpapi.Event.RESPONSE:
        #
        #                 logging.info("Processing RESPONSE Event")
        #                 # se a mensagem tem o correlation ID da ordem enviada
        #
        #                 logging.info("Inside createOrderandRoute inside while - clientID: " + str(clientID))
        #                 logging.info("Inside createOrderandRoute inside while - msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #                 logging.info("Inside createOrderandRoute inside while - requestID.value(): " + str(requestID.value()))
        #                 logging.info("Inside createOrderandRoute inside while - Message: %s", (msg.toString()))
        #                 if msg.correlationIds()[0].value() == requestID.value():
        #
        #                     logging.info("Inside createOrderandRoute inside while - Message Type: %s", msg.messageType())
        #                     # Se eh mensagem de erro
        #                     if msg.messageType() == ERROR_INFO:
        #                         errorCode = msg.getElementAsString("ERROR_CODE")
        #                         errorMessage = msg.getElementAsString("ERROR_MESSAGE")
        #                         # reason = msg.getElement("reason");
        #                         # errorcode_reason = reason.getElementAsInteger("errorCode")
        #                         # description = reason.getElementAsString("description")
        #                         # print "Error code reason: " + errorcode_reason
        #                         # print "Error code description: " + description
        #                         print "ERROR CODE: %d\tERROR MESSAGE: %s" ,errorCode, errorMessage
        #                         # envia a mensagem de erro para ser handled no PairTrader
        #                         client_Dict[clientID].send("3, Broker - " + str(broker) + " : " + str(errorMessage))
        #                         # LOG
        #                         logging.info("Inside createOrderandRoute inside while - Deu erro em %s:  %s:%s:%s:%s", str(clientID), str(ticker), str(amount), str(errorCode),
        #                                       str(errorMessage))
        #                         logging.info("Inside createOrderandRoute inside while - Deu erro em %s: %s", str(clientID), str(errorMessage))
        #                     # se eh mensagem de ordem criada
        #                     elif msg.messageType() == CREATE_ORDER_AND_ROUTE:
        #                         logging.info("Inside createOrderandRoute inside while - clientID: " + str(clientID))
        #                         logging.info("Inside createOrderandRoute inside while - msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #                         logging.info("Inside createOrderandRoute inside while - requestID.value(): " + str(requestID.value()))
        #                         logging.info("Inside createOrderandRoute inside while - Message: %s", (msg.toString()))
        #                         # sequence number da ordem
        #                         emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE")
        #                         # route ID da ordem
        #                         emsx_route_id = msg.getElementAsString("EMSX_ROUTE_ID")
        #                         # mensagem da BBG
        #                         message = msg.getElementAsString("MESSAGE")
        #                         # Envia a instrucao de envio de ordem sem estrategia para ser handled pelo PairTrader
        #                         client_Dict[clientID].send(
        #                             "1," + str(emsx_sequence) + "," + str(emsx_route_id) + "," + str(message))
        #                         logging.info("Inside createOrderandRoute inside while - Criou a ordem e enviou a mensagem para %s:  {1, %s:%s:%s}", str(clientID),
        #                                      str(emsx_sequence), str(emsx_route_id), str(message))
        #                         # cria a associacao da conexao com o sequence number da ordem para depois poder enviar as info das ordens
        #                         # para o PairTrader daquela conexao
        #                         clientOrder[emsx_sequence] = client_Dict[clientID]
        #                         # print clientOrder[emsx_sequence]
        #                         # print "EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
        #                         #     emsx_sequence, emsx_route_id, message)
        #                         # logging.INFO("EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
        #                         #     emsx_sequence, emsx_route_id, message))
        #
        #                     # session.stop()
        #                     return
        #                 else:
        #                     print "Message: %s" % (msg.toString())
        #
        # except:
        #     logging.info("Inside createOrderandRoute inside while - deu pau no recebimento de confirmacao de: request_Create_order_and_route")

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

        # logging.info("client_Dict[clientID]): " + str(client_Dict[clientID]))
        # timeout = 10
        #
        # try:
        #
        #     while (True):
        #         # recebe um evento do BBG
        #         ev = self.session.nextEvent(timeout)
        #         for msg in ev:
        #             logging.info("Inside createOrderandRouteWithStrat inside while - Message: " + str(msg))
        #             logging.info("Inside createOrderandRouteWithStrat inside while - ev.eventType(): " + str(ev.eventType()))
        #             logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #             # print str(datetime.datetime.utcnow())
        #             # se evento eh do tipo RESPONSE
        #             if ev.eventType() == blpapi.Event.RESPONSE:
        #
        #                 logging.info("Processing RESPONSE Event: ")
        #                 # Se correlationID eh o mesmo que o enviado
        #                 logging.info("clientID: " + str(clientID))
        #                 logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #                 logging.info("requestID.value(): " + str(requestID.value()))
        #                 logging.info("Message: %s", (msg.toString()))
        #                 if msg.correlationIds()[0].value() == requestID.value():
        #
        #                     logging.info("Message Type: %s", msg.messageType())
        #                     # mensagem de erro
        #                     if msg.messageType() == ERROR_INFO:
        #                         errorCode = msg.getElementAsString("ERROR_CODE")
        #                         errorMessage = msg.getElementAsString("ERROR_MESSAGE")
        #                         # reason = msg.getElement("reason");
        #                         # errorcode_reason = reason.getElementAsInteger("errorCode")
        #                         # description = reason.getElementAsString("description")
        #                         # print "Error code reason: " + errorcode_reason
        #                         # print "Error code description: " + description
        #                         print "ERROR CODE: %d\tERROR MESSAGE: %s" ,errorCode, errorMessage
        #                         client_Dict[clientID].send("3, Broker - " + str(broker) + " : " + str(errorMessage))
        #                         logging.info("Deu erro em %s:  %s:%s:%s:%s", str(clientID), str(ticker), str(amount), str(errorCode),
        #                                       str(errorMessage))
        #                         logging.info("Deu erro em %s: %s", str(clientID), str(errorMessage))
        #                     # mensagem de ordem criada
        #                     elif msg.messageType() == CREATE_ORDER_AND_ROUTE_WITH_STRAT:
        #                         try:
        #                             logging.info("clientID: " + str(clientID))
        #                             logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #                             logging.info("requestID.value(): " + str(requestID.value()))
        #                             logging.info("Message: %s", (msg.toString()))
        #                             emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE")
        #                             emsx_route_id = msg.getElementAsString("EMSX_ROUTE_ID")
        #                             message = msg.getElementAsString("MESSAGE")
        #                             print str(client_Dict[clientID])
        #                             # envia mensagem para o PairTrader com o sequence number e route ID da ordem criada
        #                             client_Dict[clientID].send(
        #                                 "1," + str(emsx_sequence) + "," + str(emsx_route_id) + "," + message)
        #                             logging.info("Criou a ordem e enviou a mensagem para %s:  {1, %s:%s:%s}", str(clientID),
        #                                          str(emsx_sequence), str(emsx_route_id), str(message))
        #                             # cria a associacao da conexao com o sequence number da ordem para depois poder enviar as info das ordens
        #                             # para o PairTrader daquela conexao
        #                             clientOrder[emsx_sequence] = client_Dict[clientID]
        #                             # print clientOrder[clientID]
        #                             # print "recebi a mensagem da ordem: " + str(datetime.datetime.utcnow())
        #                             # print "EMSX_SEQUENCE: %d\tEMSX_ROUTE_ID: %d\tMESSAGE: %s" % (
        #                             #     emsx_sequence, emsx_route_id, message)
        #                         except:
        #                             logging.info("Inside createOrderandRouteWithStrat: deu algum pau no bloco iniciando na linha 562 ")
        #
        #                     # session.stop()
        #                     return
        #                 else:
        #                     logging.info("Message Type: %s", str(msg.messageType()))
        #
        # except:
        #     logging.info("deu pau no recebimento de confirmacao de: request_Create_order_and_route_With_Strat")


    def cancelOrder(self, sequence_num, route_ID, corrID, clientID):

        # Cria os servicos de request
        request_Cancel_Route = self.service.createRequest("CancelRoute")

        routes = request_Cancel_Route.getElement("ROUTES")

        route = routes.appendElement()

        route.getElement("EMSX_SEQUENCE").setValue(sequence_num)
        route.getElement("EMSX_ROUTE_ID").setValue(route_ID)

        # if options.EMSX_TRADER_UUID:            request.set("EMSX_TRADER_UUID", options.EMSX_TRADER_UUID)

        # print "Request: %s" % request_Cancel_Route.toString()

        requestID = blpapi.CorrelationId(corrID)

        try:
            self.session.sendRequest(request_Cancel_Route, correlationId=requestID)
        except:
            logging.info("deu pau no sendRequest: request_Cancel_Route")

        # timeout = 10
        #
        # try:
        #
        #     while (True):
        #
        #         ev = self.session.nextEvent(timeout)
        #         for msg in ev:
        #
        #             if ev.eventType() == blpapi.Event.RESPONSE:
        #
        #                 logging.info("Processing RESPONSE Event")
        #
        #                 if msg.correlationIds()[0].value() == requestID.value():
        #
        #                     logging.info("Message Type: %s", msg.messageType())
        #
        #                     if msg.messageType() == ERROR_INFO:
        #                         errorCode = msg.getElementAsInteger("ERROR_CODE")
        #                         errorMessage = msg.getElementAsString("ERROR_MESSAGE")
        #                         reason = msg.getElement("reason");
        #                         errorcode_reason = reason.getElementAsInteger("errorCode")
        #                         description = reason.getElementAsString("description")
        #                         print "ERROR CODE: %d\tERROR MESSAGE: %s" % (errorCode, errorMessage)
        #                     elif msg.messageType() == CANCEL_ROUTE:
        #                         logging.info("clientID: " + str(clientID))
        #                         logging.info("msg.correlationIds()[0].value(): " + str(msg.correlationIds()[0].value()))
        #                         logging.info("requestID.value(): " + str(requestID.value()))
        #                         logging.info("Message: %s", (msg.toString()))
        #                         status = msg.getElementAsInteger("STATUS")
        #                         message = msg.getElementAsString("MESSAGE")
        #                         client_Dict[clientID].send(
        #                             "2," + str(sequence_num) + "," + str(route_ID) + "," + str(message))
        #                         logging.info("Criou a ordem e enviou a mensagem para %s:  {2, %s:%s:%s}", str(clientID),
        #                                      str(sequence_num), str(route_ID), str(message))
        #                         # print "STATUS: %d\tMESSAGE: %s" % (status, message)
        #
        #                     # session.stop()
        #                     # return
        #                 else:
        #                     pass
        #
        # except:
        #     logging.info("deu pau no recebimento de confirmacao de: request_Cancel_Route")

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

def closeInfoConnection():
    eventHandler.closeConnection()

def sendOrderInfo():
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(d_host)
    sessionOptions.setServerPort(d_port)

    print "Connecting to %s:%d" % (d_host, d_port)
    global eventHandler
    global session
    eventHandler = SessionEventHandler()

    session = blpapi.Session(sessionOptions, eventHandler.processEvent)

    if not session.start():
        wx.MessageBox("Failed to start session with Bloomberg - please check and try again")
        return

    try:
        # Wait for enter key to exit application
        print "Press ENTER to quit"
        raw_input()
    finally:
        session.stop()

# Classe para handle os eventos da sessao do bloomberg
class SessionEventHandler(object):

    # encerra as conexoes se existirem
    def closeConnection(self):
        if bool(client_Dict): # se existem conexoes no servidor
            wx.MessageBox("Ainda existem Traders conectados no OMS, por favor parar todos e repetir a operacao")
        else:
            session.stop()
    # decide qual tipo de evento deve ser processado e qual metodo chamar
    def processEvent(self, event, session):
        try:
            if event.eventType() == blpapi.Event.ADMIN:
                self.processAdminEvent(event)

            elif event.eventType() == blpapi.Event.SESSION_STATUS:
                self.processSessionStatusEvent(event, session)

            elif event.eventType() == blpapi.Event.SERVICE_STATUS:
                self.processServiceStatusEvent(event, session)

            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                self.processSubscriptionStatusEvent(event)

            elif event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                self.processSubscriptionDataEvent(event)

            else:
                self.processMiscEvents(event)

        except blpapi.Exception as e:
            print "Exception:  %s" % e.description()
        return False

    # metodo processa eventos de admin
    def processAdminEvent(self, event):
        print "Processing ADMIN event"

        for msg in event:

            if msg.messageType() == SLOW_CONSUMER_WARNING:
                print "Warning: Entered Slow Consumer status"
            elif msg.messageType() == SLOW_CONSUMER_WARNING_CLEARED:
                print "Slow consumer status cleared"

    # metodo processa eventos de Status
    def processSessionStatusEvent(self, event, session):
        print "Processing SESSION_STATUS event"

        for msg in event:

            if msg.messageType() == SESSION_STARTED:
                print "Session started..."
                session.openServiceAsync(d_service)

            elif msg.messageType() == SESSION_STARTUP_FAILURE:
                print >> sys.stderr, "Error: Session startup failed"

            elif msg.messageType() == SESSION_TERMINATED:
                print >> sys.stderr, "Error: Session has been terminated"

            elif msg.messageType() == SESSION_CONNECTION_UP:
                print "Session connection is up"

            elif msg.messageType() == SESSION_CONNECTION_DOWN:
                print >> sys.stderr, "Error: Session connection is down"

    # metodo processa eventos de Status do Servico
    def processServiceStatusEvent(self, event, session):
        print "Processing SERVICE_STATUS event"

        for msg in event:
            # servico aberto
            if msg.messageType() == SERVICE_OPENED:
                print "Service opened..."
                # para o servico de ordens nao de rotas
                # orderTopic = d_service + "/order?fields="
                # orderTopic = orderTopic + "API_SEQ_NUM,"
                # orderTopic = orderTopic + "EMSX_ACCOUNT,"
                # orderTopic = orderTopic + "EMSX_AMOUNT,"
                # orderTopic = orderTopic + "EMSX_ARRIVAL_PRICE,"
                # orderTopic = orderTopic + "EMSX_ASSET_CLASS,"
                # orderTopic = orderTopic + "EMSX_ASSIGNED_TRADER,"
                # orderTopic = orderTopic + "EMSX_AVG_PRICE,"
                # orderTopic = orderTopic + "EMSX_BASKET_NAME,"
                # orderTopic = orderTopic + "EMSX_BASKET_NUM,"
                # orderTopic = orderTopic + "EMSX_BROKER,"
                # orderTopic = orderTopic + "EMSX_BROKER_COMM,"
                # orderTopic = orderTopic + "EMSX_BSE_AVG_PRICE,"
                # orderTopic = orderTopic + "EMSX_BSE_FILLED,"
                # orderTopic = orderTopic + "EMSX_CFD_FLAG,"
                # orderTopic = orderTopic + "EMSX_COMM_DIFF_FLAG,"
                # orderTopic = orderTopic + "EMSX_COMM_RATE,"
                # orderTopic = orderTopic + "EMSX_CURRENCY_PAIR,"
                # orderTopic = orderTopic + "EMSX_DATE,"
                # orderTopic = orderTopic + "EMSX_DAY_AVG_PRICE,"
                # orderTopic = orderTopic + "EMSX_DAY_FILL,"
                # orderTopic = orderTopic + "EMSX_DIR_BROKER_FLAG,"
                # orderTopic = orderTopic + "EMSX_EXCHANGE,"
                # orderTopic = orderTopic + "EMSX_EXCHANGE_DESTINATION,"
                # orderTopic = orderTopic + "EMSX_EXEC_INSTRUCTION,"
                # orderTopic = orderTopic + "EMSX_FILL_ID,"
                # orderTopic = orderTopic + "EMSX_FILLED,"
                # orderTopic = orderTopic + "EMSX_GTD_DATE,"
                # orderTopic = orderTopic + "EMSX_HAND_INSTRUCTION,"
                # orderTopic = orderTopic + "EMSX_IDLE_AMOUNT,"
                # orderTopic = orderTopic + "EMSX_INVESTOR_ID,"
                # orderTopic = orderTopic + "EMSX_ISIN,"
                # orderTopic = orderTopic + "EMSX_LIMIT_PRICE,"
                # orderTopic = orderTopic + "EMSX_NOTES,"
                # orderTopic = orderTopic + "EMSX_NSE_AVG_PRICE,"
                # orderTopic = orderTopic + "EMSX_NSE_FILLED,"
                # orderTopic = orderTopic + "EMSX_ORD_REF_ID,"
                # orderTopic = orderTopic + "EMSX_ORDER_TYPE,"
                # orderTopic = orderTopic + "EMSX_ORIGINATE_TRADER,"
                # orderTopic = orderTopic + "EMSX_ORIGINATE_TRADER_FIRM,"
                # orderTopic = orderTopic + "EMSX_PERCENT_REMAIN,"
                # orderTopic = orderTopic + "EMSX_PM_UUID,"
                # orderTopic = orderTopic + "EMSX_PORT_MGR,"
                # orderTopic = orderTopic + "EMSX_PORT_NAME,"
                # orderTopic = orderTopic + "EMSX_PORT_NUM,"
                # orderTopic = orderTopic + "EMSX_POSITION,"
                # orderTopic = orderTopic + "EMSX_PRINCIPAL,"
                # orderTopic = orderTopic + "EMSX_PRODUCT,"
                # orderTopic = orderTopic + "EMSX_QUEUED_DATE,"
                # orderTopic = orderTopic + "EMSX_QUEUED_TIME,"
                # orderTopic = orderTopic + "EMSX_REASON_CODE,"
                # orderTopic = orderTopic + "EMSX_REASON_DESC,"
                # orderTopic = orderTopic + "EMSX_REMAIN_BALANCE,"
                # orderTopic = orderTopic + "EMSX_ROUTE_ID,"
                # orderTopic = orderTopic + "EMSX_ROUTE_PRICE,"
                # orderTopic = orderTopic + "EMSX_SEC_NAME,"
                # orderTopic = orderTopic + "EMSX_SEDOL,"
                # orderTopic = orderTopic + "EMSX_SEQUENCE,"
                # orderTopic = orderTopic + "EMSX_SETTLE_AMOUNT,"
                # orderTopic = orderTopic + "EMSX_SETTLE_DATE,"
                # orderTopic = orderTopic + "EMSX_SIDE,"
                # orderTopic = orderTopic + "EMSX_START_AMOUNT,"
                # orderTopic = orderTopic + "EMSX_STATUS,"
                # orderTopic = orderTopic + "EMSX_STEP_OUT_BROKER,"
                # orderTopic = orderTopic + "EMSX_STOP_PRICE,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_END_TIME,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_PART_RATE1,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_PART_RATE2,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_START_TIME,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_STYLE,"
                # orderTopic = orderTopic + "EMSX_STRATEGY_TYPE,"
                # orderTopic = orderTopic + "EMSX_TICKER,"
                # orderTopic = orderTopic + "EMSX_TIF,"
                # orderTopic = orderTopic + "EMSX_TIME_STAMP,"
                # orderTopic = orderTopic + "EMSX_TRAD_UUID,"
                # orderTopic = orderTopic + "EMSX_TRADE_DESK,"
                # orderTopic = orderTopic + "EMSX_TRADER,"
                # orderTopic = orderTopic + "EMSX_TRADER_NOTES,"
                # orderTopic = orderTopic + "EMSX_TS_ORDNUM,"
                # orderTopic = orderTopic + "EMSX_TYPE,"
                # orderTopic = orderTopic + "EMSX_UNDERLYING_TICKER,"
                # orderTopic = orderTopic + "EMSX_USER_COMM_AMOUNT,"
                # orderTopic = orderTopic + "EMSX_USER_COMM_RATE,"
                # orderTopic = orderTopic + "EMSX_USER_FEES,"
                # orderTopic = orderTopic + "EMSX_USER_NET_MONEY,"
                # orderTopic = orderTopic + "EMSX_WORK_PRICE,"
                # orderTopic = orderTopic + "EMSX_WORKING,"
                # orderTopic = orderTopic + "EMSX_YELLOW_KEY"

                # define o os Topicos que serao subscritos
                routeTopic = d_service + "/route?fields="
                routeTopic = routeTopic + "API_SEQ_NUM,"
                routeTopic = routeTopic + "EMSX_AMOUNT,"
                routeTopic = routeTopic + "EMSX_AVG_PRICE,"
                routeTopic = routeTopic + "EMSX_BROKER,"
                routeTopic = routeTopic + "EMSX_BROKER_COMM,"
                routeTopic = routeTopic + "EMSX_BSE_AVG_PRICE,"
                routeTopic = routeTopic + "EMSX_BSE_FILLED,"
                routeTopic = routeTopic + "EMSX_CLEARING_ACCOUNT,"
                routeTopic = routeTopic + "EMSX_CLEARING_FIRM,"
                routeTopic = routeTopic + "EMSX_COMM_DIFF_FLAG,"
                routeTopic = routeTopic + "EMSX_COMM_RATE,"
                routeTopic = routeTopic + "EMSX_CURRENCY_PAIR,"
                routeTopic = routeTopic + "EMSX_CUSTOM_ACCOUNT,"
                routeTopic = routeTopic + "EMSX_DAY_AVG_PRICE,"
                routeTopic = routeTopic + "EMSX_DAY_FILL,"
                routeTopic = routeTopic + "EMSX_EXCHANGE_DESTINATION,"
                routeTopic = routeTopic + "EMSX_EXEC_INSTRUCTION,"
                routeTopic = routeTopic + "EMSX_EXECUTE_BROKER,"
                routeTopic = routeTopic + "EMSX_FILL_ID,"
                routeTopic = routeTopic + "EMSX_FILLED,"
                routeTopic = routeTopic + "EMSX_GTD_DATE,"
                routeTopic = routeTopic + "EMSX_HAND_INSTRUCTION,"
                routeTopic = routeTopic + "EMSX_IS_MANUAL_ROUTE,"
                routeTopic = routeTopic + "EMSX_LAST_FILL_DATE,"
                routeTopic = routeTopic + "EMSX_LAST_FILL_TIME,"
                routeTopic = routeTopic + "EMSX_LAST_MARKET,"
                routeTopic = routeTopic + "EMSX_LAST_PRICE,"
                routeTopic = routeTopic + "EMSX_LAST_SHARES,"
                routeTopic = routeTopic + "EMSX_LIMIT_PRICE,"
                routeTopic = routeTopic + "EMSX_MISC_FEES,"
                routeTopic = routeTopic + "EMSX_ML_LEG_QUANTITY,"
                routeTopic = routeTopic + "EMSX_ML_NUM_LEGS,"
                routeTopic = routeTopic + "EMSX_ML_PERCENT_FILLED,"
                routeTopic = routeTopic + "EMSX_ML_RATIO,"
                routeTopic = routeTopic + "EMSX_ML_REMAIN_BALANCE,"
                routeTopic = routeTopic + "EMSX_ML_STRATEGY,"
                routeTopic = routeTopic + "EMSX_ML_TOTAL_QUANTITY,"
                routeTopic = routeTopic + "EMSX_NOTES,"
                routeTopic = routeTopic + "EMSX_NSE_AVG_PRICE,"
                routeTopic = routeTopic + "EMSX_NSE_FILLED,"
                routeTopic = routeTopic + "EMSX_ORDER_TYPE,"
                routeTopic = routeTopic + "EMSX_P_A,"
                routeTopic = routeTopic + "EMSX_PERCENT_REMAIN,"
                routeTopic = routeTopic + "EMSX_PRINCIPAL,"
                routeTopic = routeTopic + "EMSX_QUEUED_DATE,"
                routeTopic = routeTopic + "EMSX_QUEUED_TIME,"
                routeTopic = routeTopic + "EMSX_REASON_CODE,"
                routeTopic = routeTopic + "EMSX_REASON_DESC,"
                routeTopic = routeTopic + "EMSX_REMAIN_BALANCE,"
                routeTopic = routeTopic + "EMSX_ROUTE_CREATE_DATE,"
                routeTopic = routeTopic + "EMSX_ROUTE_CREATE_TIME,"
                routeTopic = routeTopic + "EMSX_ROUTE_ID,"
                routeTopic = routeTopic + "EMSX_ROUTE_LAST_UPDATE_TIME,"
                routeTopic = routeTopic + "EMSX_ROUTE_PRICE,"
                routeTopic = routeTopic + "EMSX_SEQUENCE,"
                routeTopic = routeTopic + "EMSX_SETTLE_AMOUNT,"
                routeTopic = routeTopic + "EMSX_SETTLE_DATE,"
                routeTopic = routeTopic + "EMSX_STATUS,"
                routeTopic = routeTopic + "EMSX_STOP_PRICE,"
                routeTopic = routeTopic + "EMSX_STRATEGY_END_TIME,"
                routeTopic = routeTopic + "EMSX_STRATEGY_PART_RATE1,"
                routeTopic = routeTopic + "EMSX_STRATEGY_PART_RATE2,"
                routeTopic = routeTopic + "EMSX_STRATEGY_START_TIME,"
                routeTopic = routeTopic + "EMSX_STRATEGY_STYLE,"
                routeTopic = routeTopic + "EMSX_STRATEGY_TYPE,"
                routeTopic = routeTopic + "EMSX_TIF,"
                routeTopic = routeTopic + "EMSX_TIME_STAMP,"
                routeTopic = routeTopic + "EMSX_TYPE,"
                routeTopic = routeTopic + "EMSX_URGENCY_LEVEL,"
                routeTopic = routeTopic + "EMSX_USER_COMM_AMOUNT,"
                routeTopic = routeTopic + "EMSX_USER_COMM_RATE,"
                routeTopic = routeTopic + "EMSX_USER_FEES,"
                routeTopic = routeTopic + "EMSX_USER_NET_MONEY,"
                routeTopic = routeTopic + "EMSX_WORKING"

                print "Topic: %s" % routeTopic  # orderTopic

                subscriptionID = blpapi.CorrelationId(1)
                # cria a lista de subscricao
                subscriptions = blpapi.SubscriptionList()
                # adiciona os topicos aa lista
                subscriptions.add(topic=routeTopic, correlationId=subscriptionID)

                # subscreve ao BBG para poder receber todos os fields do route topic acima
                session.subscribe(subscriptions)

            elif msg.messageType() == SERVICE_OPEN_FAILURE:
                print >> sys.stderr, "Error: Service failed to open"

    # processa o status da subscricao de informacao das ordens
    def processSubscriptionStatusEvent(self, event):
        print "Processing SUBSCRIPTION_STATUS event"

        for msg in event:

            if msg.messageType() == SUBSCRIPTION_STARTED:
                print "Subscription started..."

            elif msg.messageType() == SUBSCRIPTION_FAILURE:
                print >> sys.stderr, "Error: Subscription failed"

            elif msg.messageType() == SUBSCRIPTION_TERMINATED:
                print >> sys.stderr, "Error: Subscription terminated"
                print >> sys.stderr, "MESSAGE: %s" % msg.tostring()

    # processa os eventos de dados recebidos das ordens enviadas
    def processSubscriptionDataEvent(self, event):
        # print "Processing SUBSCRIPTION_DATA event"

        for msg in event:

            if msg.messageType() == ORDER_ROUTE_FIELDS:

                event_status = msg.getElementAsInteger("EVENT_STATUS")

                if event_status == 1:
                    print "Heartbeat..."

                else:
                    # estas sao todas as variaveis que podem ser recebidas pelo sistema

                    # api_seq_num = msg.getElementAsInteger("API_SEQ_NUM") if msg.hasElement("API_SEQ_NUM") else 0
                    # emsx_amount = msg.getElementAsInteger("EMSX_AMOUNT") if msg.hasElement("EMSX_AMOUNT") else 0
                    # emsx_broker = msg.getElementAsString("EMSX_BROKER") if msg.hasElement("EMSX_BROKER") else ""
                    # emsx_broker_comm = msg.getElementAsFloat("EMSX_BROKER_COMM") if msg.hasElement(
                    #     "EMSX_BROKER_COMM") else 0
                    # emsx_bse_avg_price = msg.getElementAsFloat("EMSX_BSE_AVG_PRICE") if msg.hasElement(
                    #     "EMSX_BSE_AVG_PRICE") else 0
                    # emsx_bse_filled = msg.getElementAsInteger("EMSX_BSE_FILLED") if msg.hasElement(
                    #     "EMSX_BSE_FILLED") else 0
                    # emsx_clearing_account = msg.getElementAsString("EMSX_CLEARING_ACCOUNT") if msg.hasElement(
                    #     "EMSX_CLEARING_ACCOUNT") else ""
                    # emsx_clearing_firm = msg.getElementAsString("EMSX_CLEARING_FIRM") if msg.hasElement(
                    #     "EMSX_CLEARING_FIRM") else ""
                    # emsx_comm_diff_flag = msg.getElementAsString("EMSX_COMM_DIFF_FLAG") if msg.hasElement(
                    #     "EMSX_COMM_DIFF_FLAG") else ""
                    # emsx_comm_rate = msg.getElementAsFloat("EMSX_COMM_RATE") if msg.hasElement("EMSX_COMM_RATE") else 0
                    # emsx_currency_pair = msg.getElementAsString("EMSX_CURRENCY_PAIR") if msg.hasElement(
                    #     "EMSX_CURRENCY_PAIR") else ""
                    # emsx_custom_account = msg.getElementAsString("EMSX_CUSTOM_ACCOUNT") if msg.hasElement(
                    #     "EMSX_CUSTOM_ACCOUNT") else ""
                    # emsx_day_avg_price = msg.getElementAsFloat("EMSX_DAY_AVG_PRICE") if msg.hasElement(
                    #     "EMSX_DAY_AVG_PRICE") else 0
                    # emsx_day_fill = msg.getElementAsInteger("EMSX_DAY_FILL") if msg.hasElement("EMSX_DAY_FILL") else 0
                    # emsx_exchange_destination = msg.getElementAsString("EMSX_EXCHANGE_DESTINATION") if msg.hasElement(
                    #     "EMSX_EXCHANGE_DESTINATION") else ""
                    # emsx_exec_instruction = msg.getElementAsString("EMSX_EXEC_INSTRUCTION") if msg.hasElement(
                    #     "EMSX_EXEC_INSTRUCTION") else ""
                    # emsx_execute_broker = msg.getElementAsString("EMSX_EXECUTE_BROKER") if msg.hasElement(
                    #     "EMSX_EXECUTE_BROKER") else ""
                    # emsx_fill_id = msg.getElementAsInteger("EMSX_FILL_ID") if msg.hasElement("EMSX_FILL_ID") else 0
                    # emsx_gtd_date = msg.getElementAsInteger("EMSX_GTD_DATE") if msg.hasElement("EMSX_GTD_DATE") else 0
                    # emsx_hand_instruction = msg.getElementAsString("EMSX_HAND_INSTRUCTION") if msg.hasElement(
                    #     "EMSX_HAND_INSTRUCTION") else ""
                    # emsx_is_manual_route = msg.getElementAsInteger("EMSX_IS_MANUAL_ROUTE") if msg.hasElement(
                    #     "EMSX_IS_MANUAL_ROUTE") else 0
                    # emsx_last_fill_date = msg.getElementAsInteger("EMSX_LAST_FILL_DATE") if msg.hasElement(
                    #     "EMSX_LAST_FILL_DATE") else 0
                    # emsx_last_market = msg.getElementAsString("EMSX_LAST_MARKET") if msg.hasElement(
                    #     "EMSX_LAST_MARKET") else ""
                    # emsx_last_price = msg.getElementAsFloat("EMSX_LAST_PRICE") if msg.hasElement(
                    #     "EMSX_LAST_PRICE") else 0
                    # emsx_last_shares = msg.getElementAsInteger("EMSX_LAST_SHARES") if msg.hasElement(
                    #     "EMSX_LAST_SHARES") else 0
                    # emsx_misc_fees = msg.getElementAsFloat("EMSX_MISC_FEES") if msg.hasElement("EMSX_MISC_FEES") else 0
                    # emsx_ml_leg_quantity = msg.getElementAsInteger("EMSX_ML_LEG_QUANTITY") if msg.hasElement(
                    #     "EMSX_ML_LEG_QUANTITY") else 0
                    # emsx_ml_num_legs = msg.getElementAsInteger("EMSX_ML_NUM_LEGS") if msg.hasElement(
                    #     "EMSX_ML_NUM_LEGS") else 0
                    # emsx_ml_percent_filled = msg.getElementAsFloat("EMSX_ML_PERCENT_FILLED") if msg.hasElement(
                    #     "EMSX_ML_PERCENT_FILLED") else 0
                    # emsx_ml_ratio = msg.getElementAsFloat("EMSX_ML_RATIO") if msg.hasElement("EMSX_ML_RATIO") else 0
                    # emsx_ml_remain_balance = msg.getElementAsFloat("EMSX_ML_REMAIN_BALANCE") if msg.hasElement(
                    #     "EMSX_ML_REMAIN_BALANCE") else 0
                    # emsx_ml_strategy = msg.getElementAsString("EMSX_ML_STRATEGY") if msg.hasElement(
                    #     "EMSX_ML_STRATEGY") else ""
                    # emsx_ml_total_quantity = msg.getElementAsInteger("EMSX_ML_TOTAL_QUANTITY") if msg.hasElement(
                    #     "EMSX_ML_TOTAL_QUANTITY") else 0
                    # emsx_notes = msg.getElementAsString("EMSX_NOTES") if msg.hasElement("EMSX_NOTES") else ""
                    # emsx_nse_avg_price = msg.getElementAsFloat("EMSX_NSE_AVG_PRICE") if msg.hasElement(
                    #     "EMSX_NSE_AVG_PRICE") else 0
                    # emsx_nse_filled = msg.getElementAsInteger("EMSX_NSE_FILLED") if msg.hasElement(
                    #     "EMSX_NSE_FILLED") else 0
                    # emsx_order_type = msg.getElementAsString("EMSX_ORDER_TYPE") if msg.hasElement(
                    #     "EMSX_ORDER_TYPE") else ""
                    # emsx_p_a = msg.getElementAsString("EMSX_P_A") if msg.hasElement("EMSX_P_A") else ""
                    # emsx_percent_remain = msg.getElementAsFloat("EMSX_PERCENT_REMAIN") if msg.hasElement(
                    #     "EMSX_PERCENT_REMAIN") else 0
                    # emsx_principle = msg.getElementAsFloat("EMSX_PRINCIPAL") if msg.hasElement("EMSX_PRINCIPAL") else 0
                    # emsx_queued_date = msg.getElementAsInteger("EMSX_QUEUED_DATE") if msg.hasElement(
                    #     "EMSX_QUEUED_DATE") else 0
                    # emsx_queued_time = msg.getElementAsInteger("EMSX_QUEUED_TIME") if msg.hasElement(
                    #     "EMSX_QUEUED_TIME") else 0
                    # emsx_reason_code = msg.getElementAsString("EMSX_REASON_CODE") if msg.hasElement(
                    #     "EMSX_REASON_CODE") else ""
                    # emsx_reason_desc = msg.getElementAsString("EMSX_REASON_DESC") if msg.hasElement(
                    #     "EMSX_REASON_DESC") else ""
                    # emsx_remain_balance = msg.getElementAsFloat("EMSX_REMAIN_BALANCE") if msg.hasElement(
                    #     "EMSX_REMAIN_BALANCE") else 0
                    # emsx_route_create_date = msg.getElementAsInteger("EMSX_ROUTE_CREATE_DATE") if msg.hasElement(
                    #     "EMSX_ROUTE_CREATE_DATE") else 0
                    # emsx_route_create_time = msg.getElementAsInteger("EMSX_ROUTE_CREATE_TIME") if msg.hasElement(
                    #     "EMSX_ROUTE_CREATE_TIME") else 0
                    # emsx_route_id = msg.getElementAsInteger("EMSX_ROUTE_ID") if msg.hasElement("EMSX_ROUTE_ID") else 0
                    # emsx_route_last_update_time = msg.getElementAsInteger(
                    #     "EMSX_ROUTE_LAST_UPDATE_TIME") if msg.hasElement("EMSX_ROUTE_LAST_UPDATE_TIME") else 0
                    # emsx_route_price = msg.getElementAsFloat("EMSX_ROUTE_PRICE") if msg.hasElement(
                    #     "EMSX_ROUTE_PRICE") else 0
                    # emsx_settle_amount = msg.getElementAsFloat("EMSX_SETTLE_AMOUNT") if msg.hasElement(
                    #     "EMSX_SETTLE_AMOUNT") else 0
                    # emsx_settle_date = msg.getElementAsInteger("EMSX_SETTLE_DATE") if msg.hasElement(
                    #     "EMSX_SETTLE_DATE") else 0
                    # emsx_stop_price = msg.getElementAsFloat("EMSX_STOP_PRICE") if msg.hasElement(
                    #     "EMSX_STOP_PRICE") else 0
                    # emsx_strategy_end_time = msg.getElementAsInteger("EMSX_STRATEGY_END_TIME") if msg.hasElement(
                    #     "EMSX_STRATEGY_END_TIME") else 0
                    # emsx_strategy_part_rate1 = msg.getElementAsFloat("EMSX_STRATEGY_PART_RATE1") if msg.hasElement(
                    #     "EMSX_STRATEGY_PART_RATE1") else 0
                    # emsx_strategy_part_rate2 = msg.getElementAsFloat("EMSX_STRATEGY_PART_RATE2") if msg.hasElement(
                    #     "EMSX_STRATEGY_PART_RATE2") else 0
                    # emsx_strategy_start_time = msg.getElementAsInteger("EMSX_STRATEGY_START_TIME") if msg.hasElement(
                    #     "EMSX_STRATEGY_START_TIME") else 0
                    # emsx_strategy_style = msg.getElementAsString("EMSX_STRATEGY_STYLE") if msg.hasElement(
                    #     "EMSX_STRATEGY_STYLE") else ""
                    # emsx_strategy_type = msg.getElementAsString("EMSX_STRATEGY_TYPE") if msg.hasElement(
                    #     "EMSX_STRATEGY_TYPE") else ""
                    # emsx_tif = msg.getElementAsString("EMSX_TIF") if msg.hasElement("EMSX_TIF") else ""
                    # emsx_time_stamp = msg.getElementAsInteger("EMSX_TIME_STAMP") if msg.hasElement(
                    #     "EMSX_TIME_STAMP") else 0
                    # emsx_type = msg.getElementAsString("EMSX_TYPE") if msg.hasElement("EMSX_TYPE") else ""
                    # emsx_urgency_level = msg.getElementAsInteger("EMSX_URGENCY_LEVEL") if msg.hasElement(
                    #     "EMSX_URGENCY_LEVEL") else ""
                    # emsx_user_comm_amount = msg.getElementAsFloat("EMSX_USER_COMM_AMOUNT") if msg.hasElement(
                    #     "EMSX_USER_COMM_AMOUNT") else 0
                    # emsx_user_comm_rate = msg.getElementAsFloat("EMSX_USER_COMM_RATE") if msg.hasElement(
                    #     "EMSX_USER_COMM_RATE") else 0
                    # emsx_user_fees = msg.getElementAsFloat("EMSX_USER_FEES") if msg.hasElement("EMSX_USER_FEES") else 0
                    # emsx_user_net_money = msg.getElementAsFloat("EMSX_USER_NET_MONEY") if msg.hasElement(
                    #     "EMSX_USER_NET_MONEY") else 0
                    # emsx_working = msg.getElementAsInteger("EMSX_WORKING") if msg.hasElement("EMSX_WORKING") else 0



                    # api_seq_num = msg.getElementAsInteger("API_SEQ_NUM") if msg.hasElement("API_SEQ_NUM") else 0
                    # emsx_account = msg.getElementAsString("EMSX_ACCOUNT") if msg.hasElement("EMSX_ACCOUNT") else ""
                    # emsx_amount = msg.getElementAsInteger("EMSX_AMOUNT") if msg.hasElement("EMSX_AMOUNT") else 0
                    # emsx_arrival_price = msg.getElementAsFloat("EMSX_ARRIVAL_PRICE") if msg.hasElement("EMSX_ARRIVAL_PRICE") else 0
                    # emsx_asset_class = msg.getElementAsString("EMSX_ASSET_CLASS") if msg.hasElement("EMSX_ASSET_CLASS") else ""
                    # emsx_assigned_trader = msg.getElementAsString("EMSX_ASSIGNED_TRADER") if msg.hasElement("EMSX_ASSIGNED_TRADER") else ""
                    # emsx_avg_price = msg.getElementAsFloat("EMSX_AVG_PRICE") if msg.hasElement("EMSX_AVG_PRICE") else 0
                    # emsx_basket_name = msg.getElementAsString("EMSX_BASKET_NAME") if msg.hasElement("EMSX_BASKET_NAME") else ""
                    # emsx_basket_num = msg.getElementAsInteger("EMSX_BASKET_NUM") if msg.hasElement("EMSX_BASKET_NUM") else 0
                    # emsx_broker = msg.getElementAsString("EMSX_BROKER") if msg.hasElement("EMSX_BROKER") else ""
                    # emsx_broker_comm = msg.getElementAsFloat("EMSX_BROKER_COMM") if msg.hasElement("EMSX_BROKER_COMM") else 0
                    # emsx_bse_avg_price = msg.getElementAsFloat("EMSX_BSE_AVG_PRICE") if msg.hasElement("EMSX_BSE_AVG_PRICE") else 0
                    # emsx_bse_filled = msg.getElementAsInteger("EMSX_BSE_FILLED") if msg.hasElement("EMSX_BSE_FILLED") else 0
                    # emsx_cfd_flag = msg.getElementAsString("EMSX_CFD_FLAG") if msg.hasElement("EMSX_CFD_FLAG") else ""
                    # emsx_comm_diff_flag = msg.getElementAsString("EMSX_COMM_DIFF_FLAG") if msg.hasElement("EMSX_COMM_DIFF_FLAG") else ""
                    # emsx_comm_rate = msg.getElementAsFloat("EMSX_COMM_RATE") if msg.hasElement("EMSX_COMM_RATE") else 0
                    # emsx_currency_pair = msg.getElementAsString("EMSX_CURRENCY_PAIR") if msg.hasElement("EMSX_CURRENCY_PAIR") else ""
                    # emsx_date = msg.getElementAsInteger("EMSX_DATE") if msg.hasElement("EMSX_DATE") else 0
                    # emsx_day_avg_price = msg.getElementAsFloat("EMSX_DAY_AVG_PRICE") if msg.hasElement("EMSX_DAY_AVG_PRICE") else 0
                    # emsx_day_fill = msg.getElementAsInteger("EMSX_DAY_FILL") if msg.hasElement("EMSX_DAY_FILL") else 0
                    # emsx_dir_broker_flag = msg.getElementAsString("EMSX_DIR_BROKER_FLAG") if msg.hasElement("EMSX_DIR_BROKER_FLAG") else ""
                    # emsx_exchange = msg.getElementAsString("EMSX_EXCHANGE") if msg.hasElement("EMSX_EXCHANGE") else ""
                    # emsx_exchange_destination = msg.getElementAsString("EMSX_EXCHANGE_DESTINATION") if msg.hasElement("EMSX_EXCHANGE_DESTINATION") else ""
                    # emsx_exec_instruction = msg.getElementAsString("EMSX_EXEC_INSTRUCTION") if msg.hasElement("EMSX_EXEC_INSTRUCTION") else ""
                    # emsx_fill_id = msg.getElementAsInteger("EMSX_FILL_ID") if msg.hasElement("EMSX_FILL_ID") else 0
                    # emsx_filled = msg.getElementAsInteger("EMSX_FILLED") if msg.hasElement("EMSX_FILLED") else 0
                    # emsx_gtd_date = msg.getElementAsInteger("EMSX_GTD_DATE") if msg.hasElement("EMSX_GTD_DATE") else 0
                    # emsx_hand_instruction = msg.getElementAsString("EMSX_HAND_INSTRUCTION") if msg.hasElement("EMSX_HAND_INSTRUCTION") else ""
                    # emsx_idle_amount = msg.getElementAsInteger("EMSX_IDLE_AMOUNT") if msg.hasElement("EMSX_IDLE_AMOUNT") else 0
                    # emsx_investor_id = msg.getElementAsString("EMSX_INVESTOR_ID") if msg.hasElement("EMSX_INVESTOR_ID") else ""
                    # emsx_isin = msg.getElementAsString("EMSX_ISIN") if msg.hasElement("EMSX_ISIN") else ""
                    # emsx_limit_price = msg.getElementAsFloat("EMSX_LIMIT_PRICE") if msg.hasElement("EMSX_LIMIT_PRICE") else 0
                    # emsx_notes = msg.getElementAsString("EMSX_NOTES") if msg.hasElement("EMSX_NOTES") else ""
                    # emsx_nse_avg_price = msg.getElementAsFloat("EMSX_NSE_AVG_PRICE") if msg.hasElement("EMSX_NSE_AVG_PRICE") else 0
                    # emsx_nse_filled = msg.getElementAsInteger("EMSX_NSE_FILLED") if msg.hasElement("EMSX_NSE_FILLED") else 0
                    # emsx_ord_ref_id = msg.getElementAsString("EMSX_ORD_REF_ID") if msg.hasElement("EMSX_ORD_REF_ID") else ""
                    # emsx_order_type = msg.getElementAsString("EMSX_ORDER_TYPE") if msg.hasElement("EMSX_ORDER_TYPE") else ""
                    # emsx_originate_trader = msg.getElementAsString("EMSX_ORIGINATE_TRADER") if msg.hasElement("EMSX_ORIGINATE_TRADER") else ""
                    # emsx_originate_trader_firm = msg.getElementAsString("EMSX_ORIGINATE_TRADER_FIRM") if msg.hasElement("EMSX_ORIGINATE_TRADER_FIRM") else ""
                    # emsx_percent_remain = msg.getElementAsFloat("EMSX_PERCENT_REMAIN") if msg.hasElement("EMSX_PERCENT_REMAIN") else 0
                    # emsx_pm_uuid = msg.getElementAsInteger("EMSX_PM_UUID") if msg.hasElement("EMSX_PM_UUID") else 0
                    # emsx_port_mgr = msg.getElementAsString("EMSX_PORT_MGR") if msg.hasElement("EMSX_PORT_MGR") else ""
                    # emsx_port_name = msg.getElementAsString("EMSX_PORT_NAME") if msg.hasElement("EMSX_PORT_NAME") else ""
                    # emsx_port_num = msg.getElementAsInteger("EMSX_PORT_NUM") if msg.hasElement("EMSX_PORT_NUM") else 0
                    # emsx_position = msg.getElementAsString("EMSX_POSITION") if msg.hasElement("EMSX_POSITION") else ""
                    # emsx_principle = msg.getElementAsFloat("EMSX_PRINCIPAL") if msg.hasElement("EMSX_PRINCIPAL") else 0
                    # emsx_product = msg.getElementAsString("EMSX_PRODUCT") if msg.hasElement("EMSX_PRODUCT") else ""
                    # emsx_queued_date = msg.getElementAsInteger("EMSX_QUEUED_DATE") if msg.hasElement("EMSX_QUEUED_DATE") else 0
                    # emsx_queued_time = msg.getElementAsInteger("EMSX_QUEUED_TIME") if msg.hasElement("EMSX_QUEUED_TIME") else 0
                    # emsx_reason_code = msg.getElementAsString("EMSX_REASON_CODE") if msg.hasElement("EMSX_REASON_CODE") else ""
                    # emsx_reason_desc = msg.getElementAsString("EMSX_REASON_DESC") if msg.hasElement("EMSX_REASON_DESC") else ""
                    # emsx_remain_balance = msg.getElementAsFloat("EMSX_REMAIN_BALANCE") if msg.hasElement("EMSX_REMAIN_BALANCE") else 0
                    # emsx_route_id = msg.getElementAsInteger("EMSX_ROUTE_ID") if msg.hasElement("EMSX_ROUTE_ID") else 0
                    # emsx_route_price = msg.getElementAsFloat("EMSX_ROUTE_PRICE") if msg.hasElement("EMSX_ROUTE_PRICE") else 0
                    # emsx_sec_name = msg.getElementAsString("EMSX_SEC_NAME") if msg.hasElement("EMSX_SEC_NAME") else ""
                    # emsx_sedol = msg.getElementAsString("EMSX_SEDOL") if msg.hasElement("EMSX_SEDOL") else ""
                    # emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE") if msg.hasElement("EMSX_SEQUENCE") else 0
                    # emsx_settle_amount = msg.getElementAsFloat("EMSX_SETTLE_AMOUNT") if msg.hasElement("EMSX_SETTLE_AMOUNT") else 0
                    # emsx_settle_date = msg.getElementAsInteger("EMSX_SETTLE_DATE") if msg.hasElement("EMSX_SETTLE_DATE") else 0
                    # emsx_side = msg.getElementAsString("EMSX_SIDE") if msg.hasElement("EMSX_SIDE") else ""
                    # emsx_start_amount = msg.getElementAsInteger("EMSX_START_AMOUNT") if msg.hasElement("EMSX_START_AMOUNT") else 0
                    # emsx_status = msg.getElementAsString("EMSX_STATUS") if msg.hasElement("EMSX_STATUS") else ""
                    # emsx_step_out_broker = msg.getElementAsString("EMSX_STEP_OUT_BROKER") if msg.hasElement("EMSX_STEP_OUT_BROKER") else ""
                    # emsx_stop_price = msg.getElementAsFloat("EMSX_STOP_PRICE") if msg.hasElement("EMSX_STOP_PRICE") else 0
                    # emsx_strategy_end_time = msg.getElementAsInteger("EMSX_STRATEGY_END_TIME") if msg.hasElement("EMSX_STRATEGY_END_TIME") else 0
                    # emsx_strategy_part_rate1 = msg.getElementAsFloat("EMSX_STRATEGY_PART_RATE1") if msg.hasElement("EMSX_STRATEGY_PART_RATE1") else 0
                    # emsx_strategy_part_rate2 = msg.getElementAsFloat("EMSX_STRATEGY_PART_RATE2") if msg.hasElement("EMSX_STRATEGY_PART_RATE2") else 0
                    # emsx_strategy_style = msg.getElementAsString("EMSX_STRATEGY_STYLE") if msg.hasElement("EMSX_STRATEGY_STYLE") else ""
                    # emsx_strategy_type = msg.getElementAsString("EMSX_STRATEGY_TYPE") if msg.hasElement("EMSX_STRATEGY_TYPE") else ""
                    # emsx_ticker = msg.getElementAsString("EMSX_TICKER") if msg.hasElement("EMSX_TICKER") else ""
                    # emsx_tif = msg.getElementAsString("EMSX_TIF") if msg.hasElement("EMSX_TIF") else ""
                    # emsx_time_stamp = msg.getElementAsInteger("EMSX_TIME_STAMP") if msg.hasElement("EMSX_TIME_STAMP") else 0
                    # emsx_trad_uuid = msg.getElementAsInteger("EMSX_TRAD_UUID") if msg.hasElement("EMSX_TRAD_UUID") else 0
                    # emsx_trade_desk = msg.getElementAsString("EMSX_TRADE_DESK") if msg.hasElement("EMSX_TRADE_DESK") else ""
                    # emsx_trader = msg.getElementAsString("EMSX_TRADER") if msg.hasElement("EMSX_TRADER") else ""
                    # emsx_trader_notes = msg.getElementAsString("EMSX_TRADER_NOTES") if msg.hasElement("EMSX_TRADER_NOTES") else ""
                    # emsx_ts_ordnum = msg.getElementAsInteger("EMSX_TS_ORDNUM") if msg.hasElement("EMSX_TS_ORDNUM") else 0
                    # emsx_type = msg.getElementAsString("EMSX_TYPE") if msg.hasElement("EMSX_TYPE") else ""
                    # emsx_underlying_ticker = msg.getElementAsString("EMSX_UNDERLYING_TICKER") if msg.hasElement("EMSX_UNDERLYING_TICKER") else ""
                    # emsx_user_comm_amount = msg.getElementAsFloat("EMSX_USER_COMM_AMOUNT") if msg.hasElement("EMSX_USER_COMM_AMOUNT") else 0
                    # emsx_user_comm_rate = msg.getElementAsFloat("EMSX_USER_COMM_RATE") if msg.hasElement("EMSX_USER_COMM_RATE") else 0
                    # emsx_user_fees = msg.getElementAsFloat("EMSX_USER_FEES") if msg.hasElement("EMSX_USER_FEES") else 0
                    # emsx_user_net_money = msg.getElementAsFloat("EMSX_USER_NET_MONEY") if msg.hasElement("EMSX_USER_NET_MONEY") else 0
                    # emsx_user_work_price = msg.getElementAsFloat("EMSX_WORK_PRICE") if msg.hasElement("EMSX_WORK_PRICE") else 0
                    # emsx_working = msg.getElementAsInteger("EMSX_WORKING") if msg.hasElement("EMSX_WORKING") else 0
                    # emsx_yellow_key = msg.getElementAsString("EMSX_YELLOW_KEY") if msg.hasElement("EMSX_YELLOW_KEY") else ""

                    # as informacoes que estao sendo utilizadas nesta versao
                    emsx_status = msg.getElementAsString("EMSX_STATUS") if msg.hasElement("EMSX_STATUS") else ""
                    emsx_sequence = msg.getElementAsString("EMSX_SEQUENCE") if msg.hasElement("EMSX_SEQUENCE") else 0
                    emsx_limit_price = msg.getElementAsFloat("EMSX_LIMIT_PRICE") if msg.hasElement(
                        "EMSX_LIMIT_PRICE") else 0
                    emsx_last_fill_time = msg.getElementAsInteger("EMSX_LAST_FILL_TIME") if msg.hasElement(
                        "EMSX_LAST_FILL_TIME") else 0
                    emsx_filled = msg.getElementAsInteger("EMSX_FILLED") if msg.hasElement("EMSX_FILLED") else 0
                    emsx_avg_price = msg.getElementAsFloat("EMSX_AVG_PRICE") if msg.hasElement("EMSX_AVG_PRICE") else 0

                    # print "MESSAGE: CorrelationID(%d)   Status(%d)" % (msg.correlationIds()[0].value(), event_status)
                    # print emsx_ticker
                    # print emsx_sequence
                    # print emsx_status
                    # print emsx_filled
                    # print emsx_avg_price
                    # print emsx_limit_price
                    try:
                        # print "Vou tentar imprimir client_Dict[emsx_sequence]"
                        # print clientOrder
                        # print str(clientOrder[str(emsx_sequence)])
                        sendLock = threading.Lock()
                        try:
                            if emsx_sequence in clientOrder:
                                sendLock.acquire()
                                # envia a mensagem para ser handled pelo Pairtrader e
                                clientOrder[emsx_sequence].send(
                                    "4," + str(emsx_sequence) + ":" + str(emsx_status) + ":" + str(emsx_filled) + ":" + str(
                                        emsx_avg_price) + ":" + str(emsx_limit_price) + ":" + str(emsx_last_fill_time) + ";")
                                # LOG
                                logging.info("Enviou a mensagem para: 4,%s:%s:%s:%s:%s", str(emsx_sequence),
                                             str(emsx_status), str(emsx_filled), str(emsx_avg_price), str(emsx_limit_price) + ":" +  str(emsx_last_fill_time))
                                sendLock.release()
                            else:
                                pass
                        except:
                            logging.info("deu pau no envio de orderInfo: %s:%s:%s:%s:%s", str(emsx_sequence),
                                         str(emsx_status), str(emsx_filled), str(emsx_avg_price), str(emsx_limit_price))

                        if emsx_status == "FILLED":
                            # se a ordem for filled retira a ordem do dicionario
                            clientOrder.pop(emsx_sequence, None)

                    except:
                        logging.info("deu pau na tentativa de envio de route info")
                        # print "API_SEQ_NUM: %d" % (api_seq_num)
                        # print "EMSX_ACCOUNT: %s" % (emsx_account)
                        # print "EMSX_AMOUNT: %d" % (emsx_amount)
                        # print "EMSX_ARRIVAL_PRICE: %d" % (emsx_arrival_price)
                        # print "EMSX_ASSET_CLASS: %s" % (emsx_asset_class)
                        # print "EMSX_ASSIGNED_TRADER: %s" % (emsx_assigned_trader)
                        # print "EMSX_AVG_PRICE: %d" % (emsx_avg_price)
                        # print "EMSX_BASKET_NAME: %s" % (emsx_basket_name)
                        # print "EMSX_BASKET_NUM: %d" % (emsx_basket_num)
                        # print "EMSX_BROKER: %s" % (emsx_broker)
                        # print "EMSX_BROKER_COMM: %d" % (emsx_broker_comm)
                        # print "EMSX_BSE_AVG_PRICE: %d" % (emsx_bse_avg_price)
                        # print "EMSX_BSE_FILLED: %d" % (emsx_bse_filled)
                        # print "EMSX_CFD_FLAG: %s" % (emsx_cfd_flag)
                        # print "EMSX_COMM_DIFF_FLAG: %s" % (emsx_comm_diff_flag)
                        # print "EMSX_COMM_RATE: %d" % (emsx_comm_rate)
                        # print "EMSX_CURRENCY_PAIR: %s" % (emsx_currency_pair)
                        # print "EMSX_DATE: %d" % (emsx_date)
                        # print "EMSX_DAY_AVG_PRICE: %d" % (emsx_day_avg_price)
                        # print "EMSX_DAY_FILL: %d" % (emsx_day_fill)
                        # print "EMSX_DIR_BROKER_FLAG: %s" % (emsx_dir_broker_flag)
                        # print "EMSX_EXCHANGE: %s" % (emsx_exchange)
                        # print "EMSX_EXCHANGE_DESTINATION: %s" % (emsx_exchange_destination)
                        # print "EMSX_EXEC_INSTRUCTION: %s" % (emsx_exec_instruction)
                        # print "EMSX_FILL_ID: %d" % (emsx_fill_id)
                        # print "EMSX_FILLED: %d" % (emsx_filled)
                        # print "EMSX_GTD_DATE: %d" % (emsx_gtd_date)
                        # print "EMSX_HAND_INSTRUCTION: %s" % (emsx_hand_instruction)
                        # print "EMSX_IDLE_AMOUNT: %d" % (emsx_idle_amount)
                        # print "EMSX_INVESTOR_ID: %s" % (emsx_investor_id)
                        # print "EMSX_ISIN: %s" % (emsx_isin)
                        # print "EMSX_LIMIT_PRICE: %d" % (emsx_limit_price)
                        # print "EMSX_NOTES: %s" % (emsx_notes)
                        # print "EMSX_NSE_AVG_PRICE: %d" % (emsx_nse_avg_price)
                        # print "EMSX_NSE_FILLED: %d" % (emsx_nse_filled)
                        # print "EMSX_ORD_REF_ID: %s" % (emsx_ord_ref_id)
                        # print "EMSX_ORDER_TYPE: %s" % (emsx_order_type)
                        # print "EMSX_ORIGINATE_TRADER: %s" % (emsx_originate_trader)
                        # print "EMSX_ORIGINATE_TRADER_FIRM: %s" % (emsx_originate_trader_firm)
                        # print "EMSX_PERCENT_REMAIN: %d" % (emsx_percent_remain)
                        # print "EMSX_PM_UUID: %d" % (emsx_pm_uuid)
                        # print "EMSX_PORT_MGR: %s" % (emsx_port_mgr)
                        # print "EMSX_PORT_NAME: %s" % (emsx_port_name)
                        # print "EMSX_PORT_NUM: %d" % (emsx_port_num)
                        # print "EMSX_POSITION: %s" % (emsx_position)
                        # print "EMSX_PRINCIPAL: %d" % (emsx_principle)
                        # print "EMSX_PRODUCT: %s" % (emsx_product)
                        # print "EMSX_QUEUED_DATE: %d" % (emsx_queued_date)
                        # print "EMSX_QUEUED_TIME: %d" % (emsx_queued_time)
                        # print "EMSX_REASON_CODE: %s" % (emsx_reason_code)
                        # print "EMSX_REASON_DESC: %s" % (emsx_reason_desc)
                        # print "EMSX_REMAIN_BALANCE: %d" % (emsx_remain_balance)
                        # print "EMSX_ROUTE_ID: %d" % (emsx_route_id)
                        # print "EMSX_ROUTE_PRICE: %d" % (emsx_route_price)
                        # print "EMSX_SEC_NAME: %s" % (emsx_sec_name)
                        # print "EMSX_SEDOL: %s" % (emsx_sedol)
                        # print "EMSX_SEQUENCE: %d" % (emsx_sequence)
                        # print "EMSX_SETTLE_AMOUNT: %d" % (emsx_settle_amount)
                        # print "EMSX_SETTLE_DATE: %d" % (emsx_settle_date)
                        # print "EMSX_SIDE: %s" % (emsx_side)
                        # print "EMSX_START_AMOUNT: %d" % (emsx_start_amount)
                        # print "EMSX_STATUS: %s" % (emsx_status)
                        # print "EMSX_STEP_OUT_BROKER: %s" % (emsx_step_out_broker)
                        # print "EMSX_STOP_PRICE: %d" % (emsx_stop_price)
                        # print "EMSX_STRATEGY_END_TIME: %d" % (emsx_strategy_end_time)
                        # print "EMSX_STRATEGY_PART_RATE1: %d" % (emsx_strategy_part_rate1)
                        # print "EMSX_STRATEGY_PART_RATE2: %d" % (emsx_strategy_part_rate2)
                        # print "EMSX_STRATEGY_STYLE: %s" % (emsx_strategy_style)
                        # print "EMSX_STRATEGY_TYPE: %s" % (emsx_strategy_type)
                        # print "EMSX_TICKER: %s" % (emsx_ticker)
                        # print "EMSX_TIF: %s" % (emsx_tif)
                        # print "EMSX_TIME_STAMP: %d" % (emsx_time_stamp)
                        # print "EMSX_TRAD_UUID: %d" % (emsx_trad_uuid)
                        # print "EMSX_TRADE_DESK: %s" % (emsx_trade_desk)
                        # print "EMSX_TRADER: %s" % (emsx_trader)
                        # print "EMSX_TRADER_NOTES: %s" % (emsx_trader_notes)
                        # print "EMSX_TS_ORDNUM: %d" % (emsx_ts_ordnum)
                        # print "EMSX_TYPE: %s" % (emsx_type)
                        # print "EMSX_UNDERLYING_TICKER: %s" % (emsx_underlying_ticker)
                        # print "EMSX_USER_COMM_AMOUNT: %d" % (emsx_user_comm_amount)
                        # print "EMSX_USER_COMM_RATE: %d" % (emsx_user_comm_rate)
                        # print "EMSX_USER_FEES: %d" % (emsx_user_fees)
                        # print "EMSX_USER_NET_MONEY: %d" % (emsx_user_net_money)
                        # print "EMSX_WORK_PRICE: %d" % (emsx_user_work_price)
                        # print "EMSX_WORKING: %d" % (emsx_working)
                        # print "EMSX_YELLOW_KEY: %s" % (emsx_yellow_key)

            else:
                print >> sys.stderr, "Error: Unexpected message"


    def processMiscEvents(self, event):

        print "Processing " + event.eventType() + " event"

        for msg in event:
            print "MESSAGE: %s" % (msg.tostring())
