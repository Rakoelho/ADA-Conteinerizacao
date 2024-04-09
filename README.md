
# Projeto Conteinerização ADA
Criação de um docker compose, com os seguintes serviços:

• Aplicação Fraude
• Minio
• Redis
• RabbitMQ

# Definição de fraude
Transações realizadas em locais distantes em um curto período de tempo, no qual não seria fisicamente impossível que o cliente viajasse. Exemplo: Compra em São Paulo e minutos depois no Rio de Janeiro


# Execução:
1 - Copiar os arquivos para a pasta desejada e executar o comando docker compose up

# Funcionamento
Após iniciar os containers com os serviços Minio, Redis e RabbitMQ o docker compose vai subir um container com a aplicação validador.
Essa aplicação é responsavel por consumir a fila de transações do RabbitMQ e verificar a existência de fraude nas transações.
Em caso de fraude é gerado um relatório que é armazenado no minio.

Alguns segundo depois o docker compose vai subir um container com a aplicação producer.
A aplicação producer é responsável por enviar os dados das transações para o RabbitMQ.

