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
    data["response"]["outputSpeech"]["brief"] = {}
    data["reprompt"] = {}
    data["reprompt"]["outputSpeech"] = {}
    data["response"]["card"] = {}
    data["response"]["directives"] = []
    data["response"]["shouldEndSession"] = False

    return data

def http_error_response(error_msg, status_code):
    data = {
        'status_code': status_code,
        'msg': error_msg
    }

    js = json.dumps(data)

    res = Response(js, status=status_code, mimetype='application/json;charset-UTF-8')
    return res


def http_success_response(message):
    js = json.dumps(message)

    print("response: " + js)

    res = Response(js, status=200, mimetype='application/json;charset-UTF-8')
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
        print("requestBody: ")
        print(requestBody)
    
    def LaunchRequest(self):
        data = responseTemplate()

        data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
        data["response"]["outputSpeech"]["values"] = {}
        data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
        data["response"]["outputSpeech"]["values"]["lang"] = "ko"
        data["response"]["outputSpeech"]["values"]["value"] = "안녕하세요, 마이펫입니다. 무엇을 도와드릴까요? 집에 있는 반려동물의 상태를 알 수 있어요. 반려동물이 밥 먹었는지 물어보세요."
   
        #data["response"]["outputSpeech"]["brief"]["type"] = "PlainText"
        #data["response"]["outputSpeech"]["brief"]["lang"] = "ko"
        #data["response"]["outputSpeech"]["brief"]["value"] = "예) ""오늘 강아지가 밥 먹었어?"", ""오늘 강아지가 물 마셨어?"""
        
        return http_success_response(data)

    def IntentRequest(self):
        data = responseTemplate()

        data["response"]["outputSpeech"]["type"] = "SimpleSpeech"
        data["response"]["outputSpeech"]["values"] = {}
        data["response"]["outputSpeech"]["values"]["type"] = "PlainText"
        data["response"]["outputSpeech"]["values"]["lang"] = "ko"
       
        failedDate = False
        failedEatType = False
        
        date=''
        eatType=''

        if not 'date' in self.requestBody["request"]["intent"]["slots"] or len(self.requestBody["request"]["intent"]["slots"]["date"]) == 0:
            print("no date field")
            failedDate = True
        else:
            date = self.requestBody["request"]["intent"]["slots"]["date"]["value"]
            print("date:"+date)

        if not 'eatType' in self.requestBody["request"]["intent"]["slots"] or len(self.requestBody["request"]["intent"]["slots"]["eatType"]) == 0:
            print("no eatType field")
            failedEatType = True
        else:
            eatType = self.requestBody["request"]["intent"]["slots"]["eatType"]["value"]
            print("eatType:"+eatType)
       
        speech_result = "잘 이해하지 못했어요. 다시 말씀해 주세요."

        if failedDate == False and failedEatType == False:
           rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

           if rdb.exists(date):
              redisData = rdb.get(date)
              print(redisData)

              redisDataJSON = json.loads(redisData)

              if eatType == '밥':
                 speech_result = "오늘 밥 {} 번 먹었어요.".format(redisDataJSON["food"])
              elif eatType == '물':
                 speech_result = "오늘 물 {} 번 마셨어요.".format(redisDataJSON["water"])
           else:
               speech_result = '오늘 아직 아무것도 먹지 않았어요.'

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

