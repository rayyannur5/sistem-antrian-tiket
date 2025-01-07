from celery import Celery, signature
import pika
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import time

celery = Celery(
    'sendEmail',
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery.conf.task_routes = {
    'sendEmail.process_email': {'queue': 'send_email_worker'},
}

def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ is not available, retrying...")
            time.sleep(5)

@celery.task(name='sendEmail.process_email')
def process_email(message):
    data = json.loads(message)

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "saput185@gmail.com"  # Ganti dengan email Anda
    smtp_password = "hhaewycnzksmsarl"    # Ganti dengan App Password Gmail

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = data['email']
    msg["Subject"] = 'Pembelian Tiket Konser'

    msg.attach(MIMEText('Selamat pembayaran tiket anda berhasil', "plain"))

    # Attach PDF
    with open(data['pdfpath'], "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(data['pdfpath'])}")
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print("Email sent successfully!")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def subscribe_message():
    connection = connect_to_rabbitmq()
    channel = connection.channel()

    channel.exchange_declare(exchange='send_email', exchange_type='fanout')

    queue_name = 'send_email_worker'

    channel.queue_bind(exchange='send_email', queue=queue_name, routing_key='send_email_worker')

    print(" [*] Waiting for messages. To exit press CTRL+C")

    def callback(ch, method, properties, body):
        print(f" [x] Received: {body.decode()}")
        signature('sendEmail.process_email', args=[body.decode()]).apply_async(queue='send_email_worker')
        # process_message.apply_async(args=[body.decode()])

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':  
    subscribe_message()