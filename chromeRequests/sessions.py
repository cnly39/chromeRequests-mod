import ctypes
import json
from urllib import request
import json as toJson
from .response import Response
from .headers import Headers
from .cookies import Cookies
from .utils import *

library = None
request = None

def loadLibrary(pathToLibrary):
    library = ctypes.cdll.LoadLibrary(pathToLibrary)
    return library

class Session:
    def __init__(self, proxy="",oneTime = False,library = None):
        if library == None:
            raise Exception("Library is not loaded")
        self.__session = library.createSession
        self.__session.restype = ctypes.c_void_p
        self.__request = library.request
        self.__request.restype = ctypes.c_void_p
        self.__changeProxy = library.changeProxy
        self.__changeProxy.restype = ctypes.c_void_p
        self.__uuid = pullFromMem(self.__session(proxy.encode('utf-8'))) if not oneTime else ""
        self.__closeSession = library.closeSession
        self.__closeSession.restype = ctypes.c_void_p
        self.cookies = Cookies()
        self.headers = Headers()

    def setProxy(self, proxy: str):
        payload = {
            "session": self.__uuid,
            "proxy": proxy,
        }
        load = json.dumps(payload).encode('utf-8')
        self.__changeProxy(load)

    def request(self,load):
        resposne = self.__request(load)
        toReturn = Response(pullFromMem(resposne))
        cookies = toReturn.cookies
        self.cookies.update(cookies)
        return resposne

    def createPayload(self, requestType: str, url: str, **kwargs) -> dict:
        payload = {
            "session": self.__uuid,
            "requestType": requestType,
            "url": url,
            "paramters": {
                "url": url,
            }
        }
        allowedGetParams = ['proxy', 'headers', "cookies","allow_redirects"]
        allowedPostParams = ['json', 'proxy', 'headers', 'data', "cookies","allow_redirects"]
        params = allowedGetParams if requestType == "GET" else allowedPostParams
        for item in kwargs:
            if not item in params:
                raise Exception(f"{item} is not an accepted PARAM")
        payload['paramters']['headers'] = kwargs.get("headers", {})
        payload['paramters']['headers'].update(self.headers.get_dict())
        payload['paramters']['proxy'] = kwargs.get("proxy", "")
        payload['paramters']['Cookies'] = kwargs.get("cookies", {})
        payload['paramters']['Redirects'] = kwargs.get("allow_redirects", True)
        payload['paramters']['Cookies'].update(self.cookies.get_dict())
        if requestType == "POST" or requestType == "PUT":
            payload['paramters']['FORM'] = kwargs.get("data", [])
            payload['paramters']['Json'] = json.dumps(kwargs.get("json", {}))
        return payload
        
    def get(self, url: str, **kwargs) -> Response:
        payload = self.createPayload("GET", url, **kwargs)
        response = self.request(json.dumps(payload).encode('utf-8'))
        return Response(pullFromMem(response))

    def post(self, url: str, **kwargs) -> Response:
        payload = self.createPayload("POST", url, **kwargs)
        response = self.request(json.dumps(payload).encode('utf-8'))
        return Response(pullFromMem(response))
    
    def put(self, url:str , **kwargs) -> Response:
        payload = self.createPayload("PUT", url, **kwargs)
        response = self.request(json.dumps(payload).encode('utf-8'))
        return Response(pullFromMem(response))
    
    def close(self):
        self.__closeSession(self.__uuid.encode('utf-8'))

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False