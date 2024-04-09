import json
import pika
import redis
import io
import re
from datetime import datetime, timedelta
from minio import Minio
from io import BytesIO

queue_name = "fila_transacoes"

def consumindo_mensagem(ch, method, properties, body):
    transacao_atual = json.loads(body)
    #print(f"Mensagem index {transacao_atual["index"]} recebida:", transacao_atual)
    numero_conta = transacao_atual["conta"]
    value = transacao_atual["valor"]
    cidade = transacao_atual["cidade"]
    datahora = transacao_atual["datahora"]
    transacao_anterior = redis_conn.get(numero_conta)
    if transacao_anterior is None:
        redis_conn.set(numero_conta, json.dumps(transacao_atual))
    else:
        redis_conn.set(numero_conta, json.dumps(transacao_atual))
        #transactions = [transacao_atual]
        transacao_antes = json.loads(transacao_anterior)
        cidade_anterior = transacao_antes["cidade"]
        datahora_anterior = transacao_antes["datahora"]
        # Convertendo as strings de data e hora para objetos datetime
        datahora = datetime.fromisoformat(datahora)
        datahora_anterior = datetime.fromisoformat(datahora_anterior)
        if cidade != cidade_anterior and abs(datahora - datahora_anterior) < timedelta(minutes=5):
            #Criando Relatório
            # Inicializa um objeto BytesIO
            relatorio = io.BytesIO()
            relatorio.write(f"Conta: {transacao_atual['conta']}\n".encode('utf-8'))
            relatorio.write(f"Cliente: {transacao_atual['nome']}\n\n".encode('utf-8'))
            relatorio.write(f"Transação Suspeita:\n".encode('utf-8'))
            relatorio.write(f"ID: {transacao_atual['id']}\n".encode('utf-8'))
            relatorio.write(f"Valor: {transacao_atual['valor']}\n".encode('utf-8')) 
            relatorio.write(f"Cidade: {transacao_atual['cidade']}\n".encode('utf-8')) 
            relatorio.write(f"Data e Hora: {transacao_atual['datahora']}\n\n".encode('utf-8')) 
            relatorio.write(f"Transação Anterior:\n".encode('utf-8'))
            relatorio.write(f"ID: {transacao_antes['id']}\n".encode('utf-8'))
            relatorio.write(f"Valor: {transacao_antes['valor']}\n".encode('utf-8')) 
            relatorio.write(f"Cidade: {transacao_antes['cidade']}\n".encode('utf-8')) 
            relatorio.write(f"Data e Hora: {transacao_antes['datahora']}\n".encode('utf-8'))
            relatorio.seek(0)
            
            #Conectando ao Minio
            minio_conn = Minio(
                endpoint="minio:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                secure=False,
            )
            bucket_name = "relatorios-fraude"
            bucket_exists = minio_conn.bucket_exists(bucket_name)
            if bucket_exists == False:
                minio_conn.make_bucket(bucket_name)
                print(f"Bucket {bucket_name} ja existe!")
            #else:
                #minio_conn.make_bucket(bucket_name)
                #print("Bucket criado com sucesso!")
            
            
            minio_conn.put_object(
                bucket_name = bucket_name,
                object_name = f"relatorio_conta-{transacao_atual['conta']}-ID-{transacao_atual['id']}.txt",
                data = relatorio,
                length = relatorio.getbuffer().nbytes,
                content_type="text/plain",
            )
            
            # Definir o nome da política e o conteúdo JSON
            #policy_name = "read-write-policy"
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                              "AWS": ["*"]

                                },
                        "Action": [
                            "s3:GetObject",
                        ],
                        "Resource": [
                             f"arn:aws:s3:::{bucket_name}/*"
                        ]
                    }
                ]
            }
            
            try:
                # Adicionar a política ao MinIO
                #minio_conn.set_bucket_policy(bucket_name, policy_content)
                minio_conn.set_bucket_policy(bucket_name, json.dumps(policy))
                print(f"Política adicionada com sucesso ao bucket 'example-bucket'.")
            except ResponseError as err:
                print(f"Erro ao adicionar a política: {err}")
            
                        
            get_url = minio_conn.get_presigned_url(
                method="GET",
                bucket_name = bucket_name,
                object_name = f"relatorio_conta-{transacao_atual['conta']}-ID-{transacao_atual['id']}.txt",
            )
            
            # Substituir "minio" por "127.0.0.1"
            get_url = re.sub(r'minio', '127.0.0.1', get_url)

            # Remover tudo após o caractere "?"
            get_url = re.sub(r'\?.*', '', get_url)
            
            print(f"Possível Fraude em andamento na conta {transacao_atual['conta']}, transação Nº {transacao_atual['index']}, id {transacao_atual['id']}.")
            print("Relatório:")
            print(get_url)
            
            #print(f"Download URL: [GET]({get_url})")
            
            redis_conn.set(f"relatorio_conta-{transacao_atual['conta']}-ID-{transacao_atual['id']}.txt", get_url)
            
        else:
            print("Transação Validada com sucesso.")
            
            

    

# Conectando ao Redis
redis_conn = redis.Redis(host="redis", port=6379, db=0)
#print("Conectado ao Redis")

# Conectando ao RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq", port=5672, virtual_host="/")
)
channel = connection.channel()
#print("Conectado ao RabbitHQ")

channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange="amq.fanout", queue=queue_name)




channel.basic_consume(
    queue=queue_name,
    on_message_callback=consumindo_mensagem,
    auto_ack=True,
)

print("Esperando por mensagens. Para sair pressione CTRL+C")
channel.start_consuming()
