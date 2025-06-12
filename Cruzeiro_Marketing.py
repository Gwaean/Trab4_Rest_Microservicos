import pika
import csv
import time
import random

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

def subscribe_marketing(nome):
    with open(ARQUIVO_MARKETING, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(['Nome'])
        writer.writerow([nome])
    print(f"Inscrição realizada para {nome}.")


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
if __name__ == "__main__":
    simular_mudanca_preco()
'''



