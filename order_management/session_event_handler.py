# Classe para handle os eventos da sessao do bloomberg

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

class SessionEventHandler(object):
    '''
    
    Class SessionEventHandler - processes events from bloomberg's order management system
    
    
    methods:
    closeConnection - close all connections if there are any
    processEvent - identifies the event recieved
    processAdminEvent - processes admin events
    processServiceStatusEvent - processes service status events
    processSubscriptionStatusEvent - processes subscription status events
    processMiscEvents - processes other events
    
    '''

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


                    try:

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
             
            else:
                print >> sys.stderr, "Error: Unexpected message"


    def processMiscEvents(self, event):

        print "Processing " + event.eventType() + " event"

        for msg in event:
            print "MESSAGE: %s" % (msg.tostring())
