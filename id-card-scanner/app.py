from flask import Flask, jsonify, request
from celery import Celery
import os
import cv2
import json
import numpy as np
import ocr
import time
from PIL import Image
from io import BytesIO
from keras.models import load_model
import numpy as np



app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure Celery
celery = Celery(
    app.name,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)


@app.route('/scan', methods=['POST'])
def scan_id():
    if 'image' not in request.files:
        return jsonify({
            'error': True,
            'message': "Foto wajib ada"
        })
    else:
        image = request.files['image']
        
        file_bytes = image.read()

        task = process_scan.apply_async()
        return jsonify({'task_id': task.id}), 202


@celery.task
def process_scan():

    start_time = time.time()
    try:

        npimg = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)  # Decode file ke OpenCV image

        pil_image = Image.open(BytesIO(file_bytes))

        img = pil_image.resize((150, 150))
        img = np.array(img)
        img = np.expand_dims(img, axis=0)
        saved_model = load_model("model/model.h5", compile=False)
        saved_model.make_predict_function()
        prediction = saved_model.predict(img)

        isimagektp = prediction[0][0] == 0
        # isimagektp = True

        if isimagektp:
            (nik, nama, tempat_lahir, tgl_lahir, jenis_kelamin, agama,
            status_perkawinan, provinsi, kabupaten, alamat, rt_rw, 
            kel_desa, kecamatan, pekerjaan, kewarganegaraan) = ocr.main(image)

            finish_time = time.time() - start_time

            if not nik:
                return json.dumps({
                    'error': True,
                    'message': 'Resolusi foto terlalu rendah, silakan coba lagi.'
                })

            return json.dumps({
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
            return json.dumps({
                'error': True,
                'message': 'Foto yang diunggah haruslah foto E-KTP'
            })
    except Exception as e:
        print(e)
        return json.dumps({
            'error': True,
            'message': 'Maaf, KTP tidak terdeteksi',
            'e': e
        })



@app.route('/status', methods=['GET'])
def get_status():
    task_id = request.args.get('id')
    print(task_id)
    task = process_scan.AsyncResult(task_id)
    if task.state == 'PENDING':
        return jsonify({'status': 'pending', 'task': task.result}), 202
    elif task.state == 'SUCCESS':
        return jsonify({'status': 'success', 'value': json.loads(task.result)}), 200
    else:
        return jsonify({'status': 'failure'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
