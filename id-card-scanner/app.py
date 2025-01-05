# service2/app.py
import cv2
import json
import numpy as np
import ocr
import time
import cnn_detect
from keras.preprocessing import image
from PIL import Image
from flask import Flask, jsonify, request
from celery import Celery
import os
import random

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure Celery
celery = Celery(
    app.name,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)


@app.route('/scan-id', methods=['POST'])
def scan_id():
    task = process_scan_id.apply_async()
    return jsonify({'task_id': task.id}), 202


@app.route('/scan', methods=['POST'])
def scan():
    start_time = time.time()

    if 'image' not in request.files:
        finish_time = time.time() - start_time

        return jsonify({
            'error': True,
            'message': "Foto wajib ada"
        })
    else:
        try:
            imagefile = request.files['image'].read()
            npimg = np.frombuffer(imagefile, np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

            fileimage = request.files['image'].stream
            fileimage = Image.open(fileimage)
            isimagektp = cnn_detect.main(fileimage)

            if isimagektp:
                (nik, nama, tempat_lahir, tgl_lahir, jenis_kelamin, agama,
                status_perkawinan, provinsi, kabupaten, alamat, rt_rw, 
                kel_desa, kecamatan, pekerjaan, kewarganegaraan) = ocr.main(image)

                finish_time = time.time() - start_time

                if not nik or not nama or not provinsi or not kabupaten:
                    return jsonify({
                        'error': True,
                        'message': 'Resolusi foto terlalu rendah, silakan coba lagi.'
                    })

                return jsonify({
                    'error': False,
                    'message': 'Proses OCR Berhasil',
                    'result': {
                        'nik': str(nik),
                        'nama': str(nama),
                        'tempat_lahir': str(tempat_lahir),
                        'tgl_lahir': str(tgl_lahir),
                        'jenis_kelamin': str(jenis_kelamin),
                        'agama': str(agama),
                        'status_perkawinan': str(status_perkawinan),
                        'pekerjaan': str(pekerjaan),
                        'kewarganegaraan': str(kewarganegaraan),
                        'alamat': {
                            'name': str(alamat),
                            'rt_rw': str(rt_rw),
                            'kel_desa': str(kel_desa),
                            'kecamatan': str(kecamatan),
                            'kabupaten': str(kabupaten),
                            'provinsi': str(provinsi)
                        },
                        'time_elapsed': str(round(finish_time, 3))
                    }
                })
            else:
                return jsonify({
                    'error': True,
                    'message': 'Foto yang diunggah haruslah foto E-KTP'
                })
        except Exception as e:
            print(e)
            return jsonify({
                'error': True,
                'message': 'Maaf, KTP tidak terdeteksi'
            })


@celery.task
def process_scan_id():
    return "tes" # Simulate scanned ID


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = process_scan_id.AsyncResult(task_id)
    if task.state == 'PENDING':
        return jsonify({'status': 'pending', 'task': task.result}), 202
    elif task.state == 'SUCCESS':
        return jsonify({'status': 'success', 'id_card_number': task.result}), 200
    else:
        return jsonify({'status': 'failure'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
