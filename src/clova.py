import abc
from base64 import b64encode, b64decode, urlsafe_b64decode
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

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

class ClovaMyPet(ClovaInterface):
    def __init__(self):
        pass

    def LaunchRequest(self):
        pass

    def IntentRequest(self):
        pass

    def SessionEndedRequest(self):
        pass

    def verifySignature(self, message, signature):
        verified = verify(message, signature, 'signature-public-key.pem')
        
        return verified

