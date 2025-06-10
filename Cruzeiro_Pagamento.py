import pika
import json
import random




    
def enviar(destino, mensagem):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=destino)

    pacote = {
        "mensagem": mensagem,
    }

    channel.basic_publish(exchange="direct_logs", routing_key=destino, body=json.dumps(pacote))
    print(f"[Pagamento] Situação: {destino} {mensagem}")
    connection.close()

def simular_pagamento():
    pagamento = random.randint(0, 9)
    if pagamento % 2 == 0:
        return True  
    else:
        return False  
def processar(ch, method, props, body):
    dados = json.loads(body)
    reserva_id = dados.get("reserva_id", "desconhecida")
    valor = dados.get("valor", 0)

    print(f"/**Processando pagamento da reserva ID = {reserva_id} no valor de R${valor}")
    aprovado = simular_pagamento()

    status = "aprovado" if aprovado else "recusado"
    mensagem = f"Reserva ID = {reserva_id}; Status: {status}"
   

    if aprovado:
        enviar("pagamento-aprovado;", mensagem)
    else:
        enviar("pagamento-recusado;", mensagem)

def escutar():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="reserva-criada")

    channel.basic_consume(queue="reserva-criada", on_message_callback=processar, auto_ack=True)
    print("[Pagamento] Aguardando reservas...")
    channel.start_consuming()

if __name__ == "__main__":
    escutar()