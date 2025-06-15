import json
import uuid
from datetime import datetime
import pika
import threading
import requests
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
reservas = {}
conexoes_sse = {}
MS_ITINERARIOS_URL = "http://localhost:5001"
MS_PAGAMENTO_URL = "http://localhost:5002"

@app.route('/api/reservas', methods=['POST'])
def criar_reserva():
    dados = request.json
    required_fields = ['itinerario_id', 'data_embarque', 'num_passageiros', 'num_cabines']
    for field in required_fields:
        if field not in dados:
            return jsonify({"erro": f"Campo obrigatório: {field}"}), 400
    reserva_id = str(uuid.uuid4())
    reserva = {
            "reserva_id": reserva_id,
            "itinerario_id": dados['itinerario_id'],
            "data_embarque": dados['data_embarque'],
            "num_passageiros": dados['num_passageiros'],
            "num_cabines": dados['num_cabines'],
            "valor_total": dados.get('valor_total', 0),
            "status": "pendente",
            "data_criacao": datetime.now().isoformat()
        }
    reservas[reserva_id] = reserva
    publicar_reserva("reserva-criada", reserva)   
        # Solicita link de pagamento
    try:
            pagamento_response = requests.post(f"{MS_PAGAMENTO_URL}/api/pagamento", json={
                "reserva_id": reserva_id,
                "valor": reserva["valor_total"],
                "moeda": "BRL"
            })
            
            if pagamento_response.status_code == 200:
                link_pagamento = pagamento_response.json().get("link_pagamento")
                reserva["link_pagamento"] = link_pagamento
    except Exception as e:
            print(f"Erro ao solicitar link de pagamento: {e}")
        
    return jsonify({
            "reserva_id": reserva_id,
            "status": "criada",
            "link_pagamento": reserva.get("link_pagamento", "")
        })
@app.route('/api/reservas/<reserva_id>', methods=['DELETE'])
def cancelar_reserva(reserva_id):
    try:
        if reserva_id not in reservas:
            return jsonify({"erro": "Reserva não encontrada"}), 404
        
        reserva = reservas[reserva_id]
        reserva["status"] = "cancelada"
        # Publica evento de cancelamento
        publicar_reserva("reserva-cancelada", reserva)
        enviar_notificacao_sse(reserva_id, {
            "tipo": "reserva_cancelada",
            "reserva_id": reserva_id,
            "mensagem": "Sua reserva foi cancelada"
        })
        
        return jsonify({"status": "cancelada"})   
    except Exception as e:
        return jsonify({"erro": f"Erro ao cancelar reserva: {str(e)}"}), 500   
@app.route('/api/sse/<cliente_id>')
def stream_sse(cliente_id):
    """Endpoint SSE para cliente específico"""
    def event_stream():
        while True:
            # Mantém conexão aberta
            yield f"data: {json.dumps({'tipo': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Verifica se há mensagens pendentes
            if cliente_id in conexoes_sse:
                mensagem = conexoes_sse[cliente_id]
                yield f"data: {json.dumps(mensagem)}\n\n"
                del conexoes_sse[cliente_id]
    
    return Response(event_stream(), mimetype="text/event-stream")        
def publicar_reserva(itinerario, numero_passageiros):
    mensagem = "criada com sucesso!"
    reserva_id = str(uuid.uuid4())
    valor_total = itinerario['Valor_Pacote'] * numero_passageiros

    dados_reserva = {
        "reserva_id": reserva_id,
        "valor": valor_total
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='reserva-criada')

    channel.basic_publish(
        exchange='',
        routing_key='reserva-criada',
        body=json.dumps(dados_reserva)
    )

    print(f"\nSituação da reserva: {mensagem}")
    connection.close()
def enviar_notificacao_sse(cliente_id, mensagem):
    conexoes_sse[cliente_id] = mensagem
def callback_pagamento(body):
    pacote = json.loads(body)
    mensagem = pacote['mensagem']
    print(f"\nSituação do pagamento: {mensagem}")
    if ('mensagem'== 'Pagamento aprovado'):
        reserva_id = pacote.get('reserva_id')
        print(f"\n[Reserva] Pagamento aprovado para reserva {reserva_id}: {pacote}")
        enviar_notificacao_sse(reserva_id, {
            "tipo": "pagamento_aprovado",
            "reserva_id": reserva_id,
            "mensagem": "Pagamento aprovado! Gerando bilhete..."
        })
    else:
        reserva_id = pacote.get('reserva_id')
        print(f"\n[Reserva] Pagamento recusado para reserva {reserva_id}: {pacote}")
        enviar_notificacao_sse(reserva_id, {
            "tipo": "pagamento_recusado",
            "reserva_id": reserva_id,
            "mensagem": "Pagamento recusado! Sua reserva foi cancelada."
        })           
def callback_bilhete(body):
    bilhete = json.loads(body)
    reserva_id = bilhete.get('reserva_id')
    print(f"\n[Reserva] Tudo certo por aqui! Gerando reserva...: {bilhete}")    
    print(f"\nID da Reserva: {reserva_id}")
    print(bilhete)
    enviar_notificacao_sse(reserva_id, {
                "tipo": "bilhete_gerado",
                "reserva_id": reserva_id,
                "bilhete": bilhete,
                "mensagem": "Bilhete gerado com sucesso! Sua reserva está confirmada."
            })
    print(f"[Reserva] Bilhete gerado para reserva {reserva_id}: {bilhete}")
def escutar_respostas():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='pagamento-aprovado')
    channel.queue_declare(queue='pagamento-recusado')
    channel.queue_declare(queue='bilhete-gerado')
    channel.basic_consume(queue='pagamento-aprovado', on_message_callback=callback_pagamento, auto_ack=True)
    channel.basic_consume(queue='pagamento-recusado', on_message_callback=callback_pagamento, auto_ack=True)
    channel.basic_consume(queue='bilhete-gerado', on_message_callback=callback_bilhete, auto_ack=True)
    print("aguardando reservas...")
    channel.start_consuming()
    
if __name__ == "__main__":
    escutar_respostas()