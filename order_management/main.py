import manage_orders_functions


def main():
    # cria os threads

    # thread que escuta as conexoes dos Traders
    t = Thread(target=manage_orders_functions.listen_connections)
    # Thread que recebe informacoes das ordens do BBG e envia para os Traders
    t2 = Thread(target=manage_orders_functions.send_order_info)

    # inicializa os threads
    t.start()
    t2.start()


if __name__=="__main__":
    main()
