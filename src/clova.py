import os
import abc
import json
import redis
from flask import request
from flask import Response
from base64 import b64encode, b64decode, urlsafe_b64decode
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_DB = os.environ.get('REDIS_DB')

def responseTemplate():
    data = {}

    data["version"] = "0.1.0"
    data["sessionAttributes"] = {}
    data["response"] = {}
    data["response"]["outputSpeech"] = {}
    #data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
    #data["response"]["outputSpeech"]["values"] = {}
    #data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
    #data["response"]["outputSpeech"]["values"]["lang"] = "ko"
    #data["response"]["outputSpeech"]["values"]["value"] = "안녕하세요, 마이펫입니다. 무엇을 도와드릴까요?"
    data["card"] = {}
    data["directives"] = []
    data["shouldEndSession"] = False

    return data

def http_error_response(error_msg, status_code):
    data = {
        'status_code': status_code,
        'msg': error_msg
    }

    js = json.dumps(data)

    res = Response(js, status=status_code, mimetype='application/json')
    return res


def http_success_response(message):
    js = json.dumps(message)

    res = Response(js, status=200, mimetype='application/json')
    return res

def verify(message, signature, public_key_path):
   public_key = open(public_key_path,'r').read()

   rsakey = RSA.import_key(public_key)
   signer = PKCS1_v1_5.new(rsakey)
   digest = SHA256.new()
   digest.update(message.encode('utf8'))
   
   result = True
   try:
      signer.verify(digest, b64decode(signature))
      print("Signature is valid.")
   except (ValueError, TypeError):
      result = False
      print("Signature is not valid.")

   return result
        
class ClovaInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def LaunchRequest(cls):
        raise NotImplementedError()

    @abc.abstractmethod
    def IntentRequest(cls):
        raise NotImplementedError()

    @abc.abstractmethod
    def SessionEndedRequest(cls):
        raise NotImplementedError()

    @abc.abstractmethod
    def Run(cls):
        raise NotImplementedError()

class ClovaMyPet(ClovaInterface):

    def __init__(self, requestBody):
        self.requestBody = requestBody

    def LaunchRequest(self):
        data = responseTemplate()

        data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
        data["response"]["outputSpeech"]["values"] = {}
        data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
        data["response"]["outputSpeech"]["values"]["lang"] = "ko"
        data["response"]["outputSpeech"]["values"]["value"] = "안녕하세요, 마이펫입니다. 무엇을 도와드릴까요?"

        return http_success_response(data)

    def IntentRequest(self):
        data = responseTemplate()

        data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
        data["response"]["outputSpeech"]["values"] = {}
        data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
        data["response"]["outputSpeech"]["values"]["lang"] = "ko"
        #data["response"]["outputSpeech"]["values"]["value"] = "안녕하세요, 마이펫입니다. 무엇을 도와드릴까요?"

        date = self.requestBody["request"]["intent"]["slots"]["date"]["value"]
        eatType = self.requestBody["request"]["intent"]["slots"]["eatType"]["value"]
        print("date: "+date+", eatType: "+eatType)

        # key             value
        # 2021-06-06      {"water":0, "food":0}
        #try:
        rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

        redisData = rdb.get(date)
        #print(type(redisData))
        print(redisData)
        redisDataJSON = json.loads(redisData)
            
        speech_result = "오늘 물 {}번, 밥 {}번 먹었어요.".format(redisDataJSON["water"], redisDataJSON["food"])
        print(speech_result)
            
        data["response"]["outputSpeech"]["values"]["value"] = speech_result
        #except:
        #    return http_error_response("redis connection error!", 500)

        return http_success_response(data)        

    def SessionEndedRequest(self):
        data = responseTemplate()

        data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
        data["response"]["outputSpeech"]["values"] = {}
        data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
        data["response"]["outputSpeech"]["values"]["lang"] = "ko"
        data["response"]["outputSpeech"]["values"]["value"] = "감사합니다, 마이펫을 종료합니다."

        return http_success_response(data)

    def Run(self):
        if self.requestBody is not None:
           requestType = self.requestBody["request"]["type"]
           print("request type: " + requestType)

           result = None

           if requestType == "LaunchRequest":
               result = self.LaunchRequest()
           elif requestType == "IntentRequest":
               result = self.IntentRequest()
           elif requestType == "SessionEndedRequest":
               result = self.SessionEndedRequest()
           
           return result

    def verifySignature(self, message, signature):
        verified = verify(message, signature, 'signature-public-key.pem')
        
        return verified

