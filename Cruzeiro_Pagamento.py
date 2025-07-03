import pika
import json
import random
import threading
import requests
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


pagamentos_pendentes = {}

@app.route('/api/pagamento', methods=['POST'])
def solicitar_link_pagamento():
    """API REST para solicitar link de pagamento"""
    try:
        dados = request.json
        reserva_id = dados.get('reserva_id')
        valor = dados.get('valor', 0)
        moeda = dados.get('moeda', 'BRL')
        
        if not reserva_id:
            return jsonify({"erro": "reserva_id obrigatório"}), 400
        
        # Simula integração com sistema externo de pagamento
        link_pagamento = f"https://pagamento-externo.com/pay/{reserva_id}"
        
        pagamentos_pendentes[reserva_id] = {
            "valor": valor,
            "moeda": moeda,
            "status": "pendente"
        }
        
        threading.Thread(target=simular_processamento_pagamento, 
                        args=(reserva_id, valor)).start()
        
        return jsonify({
            "link_pagamento": link_pagamento,
            "status": "link_gerado"
        })
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar link: {str(e)}"}), 500

@app.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    """Webhook para receber notificações do sistema externo"""
    try:
        dados = request.json
        transacao_id = dados.get('reserva_id') 
        status = dados.get('status')  # 'autorizado' ou 'recusado'
        
        if transacao_id and transacao_id in pagamentos_pendentes:
            pagamentos_pendentes[transacao_id]["status"] = status
        
            if status == 'autorizado':
                enviar_pagamento("pagamento-aprovado", transacao_id)
            else:
                enviar_pagamento("pagamento-recusado", transacao_id)
        
        return jsonify({"status": "webhook_processado"})
        
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"erro": "Erro no webhook"}), 500

def simular_processamento_pagamento(reserva_id, valor):
    """Simula processamento assíncrono do pagamento externo"""
    time.sleep(random.randint(5, 15))
    status = 'autorizado' if random.random() > 0.3 else 'recusado'  
    webhook_data = {
        "transacao_id": reserva_id,
        "status": status,
        "valor": valor
    }
    
    
   
    try:
        requests.post("http://localhost:5002/webhook/pagamento", json=webhook_data)
    except Exception:
        # Se não conseguir chamar webhook, processa diretamente
        if status == 'autorizado':
            enviar_pagamento("pagamento-aprovado", reserva_id)
        else:
            enviar_pagamento("pagamento-recusado", reserva_id)   
            
def enviar_pagamento(fila, reserva_id):
      connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
      channel = connection.channel()
      channel.queue_declare(queue=fila)
        
      mensagem = {
            "reserva_id": reserva_id,
            "status": fila.replace("pagamento-", "")
        }
        
      channel.basic_publish(
            exchange='',
            routing_key=fila,
            body=json.dumps(mensagem)
        )
        
      print(f"[Pagamento] Evento publicado em {fila}: {reserva_id}")
      connection.close()

def processar(ch, method, props, body):
   dados = json.loads(body)
   reserva_id = dados.get("reserva_id")
   valor = dados.get("valor_total", 0)  # Valor total da reserva
   print(f"/**Processando pagamento da reserva ID = {reserva_id} no valor de R${valor}")
   simular_processamento_pagamento(reserva_id, valor)

def escutar():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="reserva-criada")
    channel.basic_consume(queue="reserva-criada", on_message_callback=processar, auto_ack=True)
    print("[Pagamento] Aguardando reservas...")
    channel.start_consuming()

if __name__ == "__main__":
    threading.Thread(target=escutar, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5002)