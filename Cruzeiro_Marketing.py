import csv
import json
import time
import pika
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
interesses_promocoes = {}
ARQUIVO_CSV = 'itinerarios.csv'
ARQUIVO_HISTORICO = 'historico_precos.csv'
ARQUIVO_MARKETING = 'marketing_queue.csv'

def ler_precos_csv():
    precos = {}
    try:
        with open(ARQUIVO_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                precos[row['Destino']] = int(row['Valor_Pacote'])
    except FileNotFoundError:
        print(f"Arquivo {ARQUIVO_CSV} não encontrado. Criando novo...")
    return precos

def salvar_precos_csv(precos):
    with open(ARQUIVO_HISTORICO, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Verifica se o arquivo está vazio para escrever o cabeçalho
        if csvfile.tell() == 0:
            writer.writerow(['Data_Hora', 'Destino', 'Valor_Antigo', 'Valor_Novo', 'Variacao'])
        
        for destino, preco_novo in precos.items():
            preco_antigo = ler_precos_csv().get(destino, preco_novo)
            variacao = preco_novo - preco_antigo
            writer.writerow([
                time.strftime('%Y-%m-%d %H:%M:%S'),
                destino,
                preco_antigo,
                preco_novo,
                variacao
            ])

@app.route('/api/promocoes/interesse', methods=['POST'])
def registrar_interesse_promocoes():
    """Registra interesse em promoções"""
    try:
        dados = request.json
        cliente_id = dados.get('cliente_id')
        
        if not cliente_id:
            return jsonify({"erro": "cliente_id obrigatório"}), 400
        
        interesses_promocoes[cliente_id] = True
        
        return jsonify({"status": "interesse_registrado"})
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao registrar interesse: {str(e)}"}), 500
@app.route('/api/promocoes/interesse/<cliente_id>', methods=['DELETE'])
def cancelar_interesse_promocoes(cliente_id):
    """Cancela interesse em promoções"""
    try:
        if cliente_id in interesses_promocoes:
            del interesses_promocoes[cliente_id]
        
        return jsonify({"status": "interesse_cancelado"})
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao cancelar interesse: {str(e)}"}), 500


def enviar_notificacao(destino, preco_antigo, preco_novo):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange="promocoes", exchange_type="direct")

    if preco_novo < preco_antigo:
        variacao = preco_antigo - preco_novo
        mensagem = f" Baixa de preço para {destino}! APROVEITE! Agora está R${preco_novo} (↓ R${variacao})"
    else:
        variacao = preco_novo - preco_antigo
        mensagem = f" Aumento de preço em {destino}: Agora foi R${preco_novo} (↑ R${variacao})"
    
    print(mensagem)
 
    channel.basic_publish(exchange="promocoes", routing_key='', body=mensagem)

    print(" [x] Notificação enviada na fila promocoes")
    connection.close()

'''
def simular_mudanca_preco():
    while True:
        precos = ler_precos_csv()
        if not precos:
            print("Nenhum destino encontrado. Adicione destinos ao arquivo CSV.")
            time.sleep(10)
            continue
            
        destino = random.choice(list(precos.keys()))
        preco_antigo = precos[destino]
        mudanca = random.randint(-300, 300)
        preco_novo = max(500, preco_antigo + mudanca)

        if preco_novo != preco_antigo:
            enviar_notificacao(destino, preco_antigo, preco_novo)
            precos[destino] = preco_novo
            salvar_precos_csv({destino: preco_novo})  # Salva apenas o destino alterado

        time.sleep(random.randint(5, 10))
    '''
if __name__ == "__main__":
      app.run(debug=True, host='0.0.0.0', port=5000)



