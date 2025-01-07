import pika
from celery import Celery, signature
import os
import time
import json
from fpdf import FPDF
from datetime import datetime
import qrcode
import os

celery = Celery(
    'generatePdf',
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery.conf.task_routes = {
    'generatePdf.process_message': {'queue': 'generate_pdf_worker'},
}


def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ is not available, retrying...")
            time.sleep(5)

def publish_send_email(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    # channel.exchange_declare(exchange='send_email', exchange_type='fanout')
    channel.basic_publish(exchange='send_email', routing_key='send_email_worker', body=message)
    connection.close()


@celery.task(name='generatePdf.process_message')
def process_message(message):

    #parse message
    data = json.loads(message)
    print(data)

    
    # generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data['nik'])
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    filepathQR = 'shared/' + data['nik'] + '.png'
    img.save(filepathQR)

    # generate PDF
    pdf = FPDF(orientation='L', unit='mm', format='A5')
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(5, 5, 200, 138, style='F') 

    # Header
    pdf.set_font("Arial", style='B', size=16)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, txt=data['event_name'], ln=True, align='C')

    # Separator
    pdf.set_line_width(0.5)
    pdf.line(5, 20, 205, 20)

    # Event details
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(0, 10, txt=f"Lokasi: Jatim Expo", ln=True, align='L')
    pdf.cell(0, 10, txt=f"Waktu: {datetime.now()}", ln=True, align='L')

    # User details
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, txt="Detail Pemesan", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Nama: {data['name']}", ln=True, align='L')
    pdf.cell(0, 10, txt=f"NIK: {data['nik']}", ln=True, align='L')


    # Add QR code to the ticket
    pdf.image(filepathQR, x=150, y=40, w=40, h=40)

    # Footer
    pdf.ln(20)
    pdf.set_font("Arial", style='I', size=10)
    pdf.cell(0, 10, txt="Tunjukkan tiket ini saat masuk ke acara.", ln=True, align='C')

    # Save PDF
    filepathPDF = f"shared/{data['nik']}_tiket_konser.pdf"
    pdf.output(filepathPDF)

    # Clean up QR code file
    os.remove(filepathQR)

    publish_send_email(json.dumps({"email": data['email'], "pdfpath": filepathPDF}))

    return f"[Worker] Message processed: {message}"


def subscribe_message():
    connection = connect_to_rabbitmq()
    channel = connection.channel()

    channel.exchange_declare(exchange='generate_pdf', exchange_type='fanout')

    queue_name = 'generate_pdf_worker'

    channel.queue_bind(exchange='generate_pdf', queue=queue_name, routing_key='generate_pdf_worker')

    print(" [*] Waiting for messages. To exit press CTRL+C")

    def callback(ch, method, properties, body):
        print(f" [x] Received: {body.decode()}")
        signature('generatePdf.process_message', args=[body.decode()]).apply_async(queue='generate_pdf_worker')
        # process_message.apply_async(args=[body.decode()])

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


if __name__ == '__main__':  
    subscribe_message()