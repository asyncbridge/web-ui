import os
import flask
from flask import request
from flask import Response
import time
import logging
import json
import datetime
import werkzeug
from PIL import Image
from io import BytesIO
import exifutil
import base64
import cv2
import requests
import numpy as np
import anno_func
import base64
from clova import ClovaMyPet

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "/tmp/crested_gecko_detection_uploads"
#UPLOAD_FOLDER = "c:\\crested_gecko_detection_uploads"

DETECTED_IMAGE_OUTPUT_WIDTH = 512

HOSTNAME = 'localhost'
POST_API_URI_TASK_01 = 'http://'+HOSTNAME+':5001/detect_object?embed_image=false'
POST_API_URI_TASK_02 = 'http://'+HOSTNAME+':5002/detect_object?embed_image=false'
POST_API_URI_TASK_03 = 'http://'+HOSTNAME+':5003/detect_object?embed_image=false'

app = flask.Flask(__name__)

# added - draw bounding box and label for tt100k
def showAnnsBBoxTT100K(image, annotations):
    
    if len(annotations) == 0 :
       logging.error("showAnnsBBoxTT100K: there are no items in annotations.")
       return image

    text_color = (0, 0, 0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    #font_scale = 0.8 * (image.shape[1]/768)
    font_scale = 0.6
    margin = 5
    thickness = 2

    for ann in annotations:

        #font_scale = (image.shape[1] * image.shape[0]) / (1000*1000)
        color = (0,255,0)
        x = int(ann["bbox"]["xmin"])
        y = int(ann["bbox"]["ymin"])
        xw = int(ann["bbox"]["xmax"])
        yh = int(ann["bbox"]["ymax"])

        #class_name = ann["class_name"] + " %d" % (ann["probability"]*100.0) + "%"
        class_name = ann["category"]

        image = cv2.rectangle(image, (x, y), (xw, yh), color, 1)

        size = cv2.getTextSize(class_name, font, font_scale, thickness)

        text_width = size[0][0]

        ty = y - 20 - margin
        ty_e = y
        txt_y = y - 10

        if ty < 0:
          ty = y
          ty_e = y + 20 + margin
          txt_y = y + 15

        image = cv2.rectangle(image, (x, ty),
                      (x + int(text_width) + margin, ty_e), color, -1)
        image = cv2.putText(image, class_name, (x + margin, txt_y), font, font_scale, text_color,
                    thickness)

    return image

# added - draw bounding box and label
def showAnnsBBox(image, annotations):

    if len(annotations) == 0 :
       logging.error("showAnnsBBox: there are no items in annotations.")
       return image

    text_color = (0, 0, 0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    #font_scale = 0.8 * (image.shape[1]/768)
    font_scale = 0.6
    margin = 5
    thickness = 2

    for ann in annotations:

        #font_scale = (image.shape[1] * image.shape[0]) / (1000*1000)
        color = (int(ann["color"]["red"]), int(ann["color"]["green"]), int(ann["color"]["blue"]))
        x = int(ann["bounding_box"]["left"])
        y = int(ann["bounding_box"]["top"])
        xw = int(ann["bounding_box"]["right"])
        yh = int(ann["bounding_box"]["bottom"])

        #class_name = ann["class_name"] + " %d" % (ann["probability"]*100.0) + "%"
        class_name = ann["class_name"] 

        image = cv2.rectangle(image, (x, y), (xw, yh), color, 1)

        size = cv2.getTextSize(class_name, font, font_scale, thickness)

        text_width = size[0][0]

        ty = y - 20 - margin
        ty_e = y
        txt_y = y - 10

        if ty < 0:
          ty = y
          ty_e = y + 20 + margin
          txt_y = y + 15
 
        image = cv2.rectangle(image, (x, ty),
                      (x + int(text_width) + margin, ty_e), color, -1)
        image = cv2.putText(image, class_name, (x + margin, txt_y), font, font_scale, text_color,
                    thickness)


    return image

def resize_image(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    resized = cv2.resize(image, dim, interpolation=inter)

    return resized

def resize_image_pil(image_pil, width=None, height=None):
    dim = None
    w, h = image_pil.size

    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    resized = image_pil.resize(dim)

    return resized


def embed_image_html(image):
    """Creates an image embedded in HTML base64 format."""
    #image_output_width = DETECTED_IMAGE_OUTPUT_WIDTH

    #if image.shape[1] < image_output_width:
    #   image_output_width = image.shape[1]

    #image_pil = resize_image(image, width=image_output_width)
    image_pil = image
    # image_pil = Image.fromarray((255 * image).astype('uint8'))
    image_pil = Image.fromarray((image_pil).astype('uint8'))
    # image_pil = image_pil.resize((256, 256))
    stream = BytesIO()
    image_pil.save(stream, format='jpeg')
    # data = string_buf.getvalue().encode('base64').replace('\n', '')
    data = base64.b64encode(stream.getvalue()).decode('utf-8').replace('\n', '')
    return 'data:image/jpg;base64,' + data


def http_error_response(error_msg, status_code):
    data = {
        'status_code': status_code,
        'msg': error_msg
    }

    js = json.dumps(data)

    res = Response(js, status=status_code, mimetype='application/json')
    logger.error(error_msg)
    return res


def http_success_response(message, result):
    data = {
        'status_code': 200,
        'msg': message,
        'result': result
    }

    js = json.dumps(data)

    res = Response(js, status=200, mimetype='application/json')
    return res

@app.route('/')
def index():
    return flask.render_template('index.html', has_result=False)

@app.route('/task01')
def detect_task01():
    return flask.render_template('detect_coco.html', has_result=False)

@app.route('/task02')
def detect_task02():
    return flask.render_template('detect_crested_gecko.html', has_result=False)

@app.route('/task03')
def detect_task03():
    return flask.render_template('detect_tt100k.html', has_result=False)

@app.route('/task04')
def detect_task04():
    return flask.render_template('clova_mypet.html', has_result=False)

@app.route('/task01_classify_upload', methods=['POST'])
def classify_upload_task01():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if flask.request.files['submitImageFile'].filename == '':
        return http_error_response("There is no image file.", 412)

    try:
        imagefile = flask.request.files['submitImageFile']
        logging.info('imagefile: %s', imagefile)

        filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
                    werkzeug.secure_filename(imagefile.filename)
        filename = os.path.join(UPLOAD_FOLDER, filename_)

        imagefile.save(filename)

        im = Image.open(filename)

        if hasattr(im, '_getexif'):
           exif = im._getexif()

           if exif is not None and 274 in exif:
              orientation = exif[274]
              im = exifutil.apply_orientation(im, orientation)

        logging.info('Image.open : %s', im)

        file_split = os.path.splitext(filename)

        if file_split[1] == '.png':
            new_filename = file_split[0]+".jpg"

            logging.info('New file name(png->jpg) is Saving to %s.', new_filename)
            im = im.convert('RGB')
            os.remove(filename) # remove png 
            filename = new_filename

        image_output_width = DETECTED_IMAGE_OUTPUT_WIDTH
        width, height = im.size

        if width < DETECTED_IMAGE_OUTPUT_WIDTH:
           image_output_width = width

        im = resize_image_pil(im, image_output_width)
        im.save(filename,"JPEG")

        #imagefile.save(filename)
        logging.info('Saving to %s.', filename)

        multipart_form_data = {
            'submitImageFile': (imagefile.filename, open(filename, 'rb'))
        }
 
        response = requests.post(POST_API_URI_TASK_01, files=multipart_form_data)

    except Exception as err:
        logging.info('Uploaded image open error: %s', err)

        if os.path.exists(filename):
            os.remove(filename)
            logging.info('Uploaded image file is removed: %s', filename)

        return flask.render_template(
            'detect_coco.html', has_result=True,
            result=(False, 'Cannot open uploaded image.')
        )

    json_result = json.loads(response.text)

    detected_result = json_result["result"]["data"][0]["detected_results"]
    im_arr = exifutil.open_oriented_im(filename)
    detected_image = showAnnsBBox(im_arr, detected_result)
    embed_detected_image = embed_image_html(detected_image)
    elapsed_time = json_result["result"]["data"][1]["elapsed_time"]

    num_of_result = len(detected_result)

    #embed_detected_image = json_result["result"]["data"][1]["detected_embed_image"]

    if os.path.exists(filename):
        os.remove(filename)
        logging.info('Uploaded image file is removed: %s', filename)

    return flask.render_template('detect_coco.html', has_result=True, result=(True, num_of_result, detected_result, elapsed_time),
                                                                  imagesrc=embed_detected_image)






@app.route('/task02_classify_upload', methods=['POST'])
def classify_upload_task02():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if flask.request.files['submitImageFile'].filename == '':
        return http_error_response("There is no image file.", 412)

    try:
        imagefile = flask.request.files['submitImageFile']
        logging.info('imagefile: %s', imagefile)

        filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
                    werkzeug.secure_filename(imagefile.filename)
        filename = os.path.join(UPLOAD_FOLDER, filename_)

        imagefile.save(filename)
 
        im = Image.open(filename)
        
        if hasattr(im, '_getexif'):
           exif = im._getexif()
           
           if exif is not None and 274 in exif:
              orientation = exif[274]
              im = exifutil.apply_orientation(im, orientation)

        logging.info('Image.open : %s', im) 

        file_split = os.path.splitext(filename)

        if file_split[1] == '.png': 
            new_filename = file_split[0]+".jpg"
           
            logging.info('New file name(png->jpg) is Saving to %s.', new_filename)
            im = im.convert('RGB')
            os.remove(filename) # remove png 
            filename = new_filename

        image_output_width = DETECTED_IMAGE_OUTPUT_WIDTH
        width, height = im.size

        if width < DETECTED_IMAGE_OUTPUT_WIDTH:
           image_output_width = width
        
        im = resize_image_pil(im, image_output_width)        
        im.save(filename,"JPEG") 

        #imagefile.save(filename)
        logging.info('Saving to %s.', filename)

        multipart_form_data = {
            'submitImageFile': (imagefile.filename, open(filename, 'rb'))
        }

        response = requests.post(POST_API_URI_TASK_02, files=multipart_form_data)

    except Exception as err:
        logging.info('Uploaded image open error: %s', err)

        if os.path.exists(filename):
            os.remove(filename)
            logging.info('Uploaded image file is removed: %s', filename)

        return flask.render_template(
            'detect_crested_gecko.html', has_result=True,
            result=(False, 'Cannot open uploaded image.')
        )

    json_result = json.loads(response.text)

    detected_result = json_result["result"]["data"][0]["detected_results"]
    im_arr = exifutil.open_oriented_im(filename)
    detected_image = showAnnsBBox(im_arr, detected_result)
    embed_detected_image = embed_image_html(detected_image)
    elapsed_time = json_result["result"]["data"][1]["elapsed_time"]

    num_of_result = len(detected_result)

    #embed_detected_image = json_result["result"]["data"][1]["detected_embed_image"]

    if os.path.exists(filename):
        os.remove(filename)
        logging.info('Uploaded image file is removed: %s', filename)

    return flask.render_template('detect_crested_gecko.html', has_result=True, result=(True, num_of_result, detected_result, elapsed_time),
                                                                  imagesrc=embed_detected_image)


@app.route('/task03_classify_upload', methods=['POST'])
def classify_upload_task03():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if flask.request.files['submitImageFile'].filename == '':
        return http_error_response("There is no image file.", 412)

    try:
        imagefile = flask.request.files['submitImageFile']
        logging.info('imagefile: %s', imagefile)

        filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
                    werkzeug.secure_filename(imagefile.filename)
        filename = os.path.join(UPLOAD_FOLDER, filename_)

        imagefile.save(filename)
 
        im = Image.open(filename)
        
        if hasattr(im, '_getexif'):
           exif = im._getexif()
           
           if exif is not None and 274 in exif:
              orientation = exif[274]
              im = exifutil.apply_orientation(im, orientation)

        logging.info('Image.open : %s', im) 

        file_split = os.path.splitext(filename)

        if file_split[1] == '.png': 
            new_filename = file_split[0]+".jpg"
           
            logging.info('New file name(png->jpg) is Saving to %s.', new_filename)
            im = im.convert('RGB')
            os.remove(filename) # remove png 
            filename = new_filename

        multipart_form_data = {
            'submitImageFile': (imagefile.filename, open(filename, 'rb'))
        }

        response = requests.post(POST_API_URI_TASK_03, files=multipart_form_data)

        '''
        image_output_width = DETECTED_IMAGE_OUTPUT_WIDTH
        width, height = im.size

        if width < DETECTED_IMAGE_OUTPUT_WIDTH:
           image_output_width = width
        
        im = resize_image_pil(im, image_output_width)        
        im.save(filename,"JPEG") 

        #imagefile.save(filename)
        logging.info('Saving to %s.', filename)
        '''

        '''
        multipart_form_data = {
            'submitImageFile': (imagefile.filename, open(filename, 'rb'))
        }

        response = requests.post(POST_API_URI_TASK_03, files=multipart_form_data)
        '''
    except Exception as err:
        logging.info('Uploaded image open error: %s', err)

        if os.path.exists(filename):
            os.remove(filename)
            logging.info('Uploaded image file is removed: %s', filename)

        return flask.render_template(
            'detect_tt100k.html', has_result=True,
            result=(False, 'Cannot open uploaded image.')
        )

    json_result = json.loads(response.text)

    detected_result = json_result["result"]["data"][0]["detected_results"]["imgs"]["0"]["objects"]
   
    im_arr = exifutil.open_oriented_im(filename)
    detected_image = showAnnsBBoxTT100K(im_arr, detected_result)
    embed_detected_image = embed_image_html(detected_image)
    elapsed_time = json_result["result"]["data"][1]["elapsed_time"]
    num_of_result = len(detected_result)
 
    #embed_detected_image = json_result["result"]["data"][1]["detected_embed_image"]

    if os.path.exists(filename):
        os.remove(filename)
        logging.info('Uploaded image file is removed: %s', filename)

    return flask.render_template('detect_tt100k.html', has_result=True, result=(True, num_of_result, detected_result, elapsed_time),
                                                                  imagesrc=embed_detected_image)

@app.route('/task04_mypet', methods=['POST'])
def task04_mypet():
   signatureCEK = ''
   message = ''

   if 'SignatureCEK' in request.headers:
     signatureCEK = request.headers['SignatureCEK']

   data = request.get_json()
   requestBody = json.dumps(data)
   
   print("request body: "+requestBody)
   print("signatureCEK type: ")
   print(type(signatureCEK))
   print("signatureCEK: "+signatureCEK)   
 
   iclova = ClovaMyPet()
   isValid = iclova.verifySignature(requestBody, signatureCEK)
   
   if isValid == True:
     return http_success_response("Ok", "Signature CEK is valid.")
   else:
     return http_error_response("Signature CEK is invalid.", 401)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=False, host='0.0.0.0', port=5000)
