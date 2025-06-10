import pika
import random
import json


# Bilhete escuta de pagamento, caso seja aprovado ele envia o bilhete gerado SOMENTE p/ Reserva
# Caso o pagamento seja NEGADO, nada acontece (o pagamento recusado envia notificacao direto p/ reserva)

def gerar_bilhete(reserva_id):
    return {
        "reserva_id": reserva_id,
        "bilhete": f"BILHETE-{reserva_id[:5].upper()}-{random.randint(1000,9999)}"
    }

def enviar_bilhete(bilhete):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="bilhete-gerado")

    channel.basic_publish(exchange="", routing_key="bilhete-gerado", body=json.dumps(bilhete))
    print(f"[Bilhete] Pagamento Processando...: {bilhete}")
    connection.close()

def callback(body):
    pacote = json.loads(body)
    mensagem = pacote["mensagem"]
    print(f"[Bilhete] Recebido: {mensagem}")

   

def escutar_pagamentos_aprovados():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="pagamento-aprovado")
    print("escutando pagamento...")

    channel.basic_consume(queue="pagamento-aprovado", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    escutar_pagamentos_aprovados()