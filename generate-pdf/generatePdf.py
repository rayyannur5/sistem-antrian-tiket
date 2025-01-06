import pika
from celery import Celery
import os
import time

celery = Celery(
    'generatePdf',
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery.conf.task_routes = {
    'generatePdf.tasks.process_message': {'queue': 'generate_pdf_worker'},
}


def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ is not available, retrying...")
            time.sleep(5)

@celery.task
def process_message(message):
    print(f"[Worker] Processing message: {message}")
    return f"[Worker] Message processed: {message}"


def subscribe_message():
    connection = connect_to_rabbitmq()
    channel = connection.channel()

    channel.exchange_declare(exchange='generate_pdf', exchange_type='fanout')

    result = channel.queue_declare(queue='generate_pdf_worker', exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange='generate_pdf', queue=queue_name)

    print(" [*] Waiting for messages. To exit press CTRL+C")

    def callback(ch, method, properties, body):
        print(f" [x] Received: {body.decode()}")
        process_message.apply_async(args=[body.decode()])

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    subscribe_message()