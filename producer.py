import json
import pika

# Connect to a RabbitMQ server running on the local machine
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host="rabbitmq",
     port=5672,
     virtual_host="/"))

channel = connection.channel()

queue_name = "fila_transacoes"
nome_arquivo = 'transacoes.json'  # Nome do arquivo JSON

# Message attributes
properties = pika.BasicProperties(
    content_type='application/json',      # MIME-type of the message body
    # content_encoding='utf-8',             # Encoding of the message body
    # delivery_mode=2,                      # Make message persistent
    # priority=5,                           # Priority level
    # correlation_id='example_correlation_id',  # Correlate replies with requests
    reply_to='hello',               # Queue name for replies
    expiration='100000',                     # Message expiration period (milliseconds)
    # message_id='unique_message_id',       # Unique identifier for the message
    # timestamp=datetime.now().timestamp(), # Message timestamp
    # type='example_type',                  # Type of the message
    # user_id='user',                       # User ID who sent the message
    # app_id='example_app',                 # Identifier for the application
    # headers={'key': 'value'}              # Application-specific attributes
)


def ler_arquivo_json(nome_arquivo):
    with open(nome_arquivo, 'r') as arquivo:
        dados = json.load(arquivo)
    return dados

dados = ler_arquivo_json(nome_arquivo)

for item in dados:
        # Envio dos dados para a fila
        channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body=json.dumps(item),
                              properties=properties)
        #print(f"[x] Valor '{item}' enviado para o RabbitMQ")
        print(f"Transação '{item['id']}' enviada para o RabbitMQ")


# Close the connection
connection.close()