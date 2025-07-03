import pika
import csv
import json
from flask import Flask, jsonify, request
from datetime import datetime
import threading
app = Flask(__name__)
itinerarios_cabines_disponiveis = {}
def carregar_itinerarios():
    itinerarios = []
    try:
        with open('itinerarios.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                itinerario = {
                    'id': row.get('ID', len(itinerarios) + 1),
                    'destino': row['Destino'],
                    'data_embarque': row['Data_Embarque'],
                    'porto_embarque': row['Porto_Embarque'],
                    'nome_navio': row['Nome_Navio'],
                    'porto_desemb': row['Porto_Desemb'],
                    'lugares_visitados': row['Lugares_Visit'],
                    'num_noites': int(row['Num_Noites']),
                    'valor_pacote': float(row['Valor_Pacote']),
                    'num_cabines': int(row.get('num_cabines', 10))
                }
                itinerarios.append(itinerario)
                if itinerario['id'] not in itinerarios_cabines_disponiveis:
                    itinerarios_cabines_disponiveis[itinerario['id']] = itinerario['num_cabines']
    except FileNotFoundError:
        print("Arquivo itinerarios.csv não encontrado")
    return itinerarios

@app.route('/api/itinerarios', methods=['GET'])
def consultar_itinerarios():
    """API REST para consultar itinerários"""
    destino = request.args.get('destino', '')
    data_embarque = request.args.get('data_embarque', '')
    porto_embarque = request.args.get('porto_embarque', '')
    
    itinerarios = carregar_itinerarios()
    resultados = []
    
    for itinerario in itinerarios:
        if destino and destino.lower() not in itinerario['destino'].lower():
            continue
        if porto_embarque and porto_embarque.lower() not in itinerario['porto_embarque'].lower():
            continue
        if data_embarque:
            try:
                data_filtro = datetime.strptime(data_embarque, '%d/%m/%Y').date()
                data_itinerario = datetime.strptime(itinerario['data_embarque'], '%d/%m/%Y').date()
                if data_itinerario < data_filtro:
                    continue
            except ValueError:
                pass
        # Adiciona cabines disponíveis atualizadas
        itinerario_copy = itinerario.copy()
        itinerario_copy['cabines_disponiveis'] = itinerarios_cabines_disponiveis.get(itinerario['id'], 0)
        if itinerario_copy['cabines_disponiveis'] > 0:
            resultados.append(itinerario_copy)
    return jsonify(resultados)

def processar_reserva(ch, method, properties, body, cabines_disponiveis):
    try:
        dados = json.loads(body)
        itinerario_id = dados.get('itinerario_id')
        cabines_reservadas = dados.get('num_cabines', 1)
        
        if itinerario_id in itinerarios_cabines_disponiveis:
            itinerarios_cabines_disponiveis[itinerario_id] = max(0, 
                itinerarios_cabines_disponiveis[itinerario_id] - cabines_reservadas)
            print(f"[Itinerários] Cabines reduzidas para itinerário {itinerario_id}. "
                  f"Disponíveis: {itinerarios_cabines_disponiveis[itinerario_id]}")
    except Exception as e:
        print(f"Erro ao processar reserva criada: {e}")
        
def processar_reserva_cancelada(ch, method, properties, body, cabines_disponiveis):
    
    try:
        dados = json.loads(body)
        itinerario_id = dados.get('itinerario_id')
        cabines_liberadas = dados.get('num_cabines', 1)
        
        if itinerario_id in itinerarios_cabines_disponiveis:
            itinerarios_cabines_disponiveis[itinerario_id] += cabines_liberadas
            print(f"[Itinerários] Cabines liberadas para itinerário {itinerario_id}. "
                  f"Disponíveis: {itinerarios_cabines_disponiveis[itinerario_id]}")
    except Exception as e:
        print(f"Erro ao processar reserva cancelada: {e}")
def escutar():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="reserva-criada")
    channel.queue_declare(queue='reserva-cancelada')

    channel.basic_consume(queue="reserva-criada", on_message_callback=processar_reserva, auto_ack=True)
    channel.basic_consume(queue='reserva-cancelada', on_message_callback=processar_reserva_cancelada, auto_ack=True)
    
    print("[Itinerarios] Aguardando reservas...")
    channel.start_consuming()
    
if __name__ == '__main__':
    itinerarios = carregar_itinerarios()
    threading.Thread(target=escutar, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5001)