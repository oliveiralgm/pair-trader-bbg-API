import market_data
import market_data_functions


def main():

    open_BBG_Connection()

    t_listen_conn = Thread(target=listenConnections)
    t_subscribe_data = Thread(target=process_events)


    t_listen_conn.start()
    t_subscribe_data.start()

    t_listen_conn.join()
    t_subscribe_data.join()





if __name__ == "__main__":
    print "SimpleSubscriptionExample"
    try:
        main()
    except: KeyboardInterrupt:
        print "Ctrl+C pressed. Stopping..."
