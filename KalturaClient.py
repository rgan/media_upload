# ===================================================================================================
#                           _  __     _ _
#                          | |/ /__ _| | |_ _  _ _ _ __ _
#                          | ' </ _` | |  _| || | '_/ _` |
#                          |_|\_\__,_|_|\__|\_,_|_| \__,_|
#
# This file is part of the Kaltura Collaborative Media Suite which allows users
# to do with audio, video, and animation what Wiki platfroms allow them to do with
# text.
#
# Copyright (C) 2006-2011  Kaltura Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.
#
# @ignore
# ===================================================================================================
from KalturaCoreClient import *
from KalturaClientBase import *
from xml.parsers.expat import ExpatError
from xml.dom import minidom
from threading import Timer
import hashlib
import random
import base64
import socket
import urllib
import time
import sys
import os

from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
import urllib2

# Register the streaming http handlers with urllib2
register_openers()

pluginsFolder = os.path.normpath(os.path.join(os.path.dirname(__file__), 'KalturaPlugins'))
if not pluginsFolder in sys.path:
    sys.path.append(pluginsFolder)

class MultiRequestSubResult:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return '{%s}' % self.value
    def __repr__(self):
        return '{%s}' % self.value
    def __getattr__(self, name):
        if name.startswith('__') or name.endswith('__'):
            raise AttributeError
        return MultiRequestSubResult('%s:%s' % (self.value, name))
    def __getitem__(self, key):
        return MultiRequestSubResult('%s:%s' % (self.value, key))

class PluginServicesProxy:
    def addService(self, serviceName, serviceClass):
        setattr(self, serviceName, serviceClass)

class KalturaClient:
    def __init__(self, config):
        self.apiVersion = API_VERSION
        self.config = None
        self.ks = NotImplemented
        self.shouldLog = False
        self.multiRequest = False
        self.callsQueue = []

        self.config = config
        logger = self.config.getLogger()
        if (logger):
            self.shouldLog = True

        self.loadPlugins()            

    def loadPlugins(self):
        print "LOADING >>>>"
        if not os.path.isdir(pluginsFolder):
            return
        print "LOADING >>>>"
        pluginList = ['KalturaCoreClient']
        for fileName in os.listdir(pluginsFolder):
            (pluginClass, fileExt) = os.path.splitext(fileName)
            if fileExt.lower() != '.py':
                continue
            pluginList.append(pluginClass)

        for pluginClass in pluginList:
            self.loadPlugin(pluginClass)

    def loadPlugin(self, pluginClass):
        pluginModule = __import__(pluginClass)
        if not pluginClass in dir(pluginModule):
            return
        pluginClassType = getattr(pluginModule, pluginClass)

        plugin = pluginClassType.get()
        if not isinstance(plugin, IKalturaClientPlugin):
            return
        self.registerPluginServices(plugin)
        self.registerPluginObjects(plugin)

    def registerPluginServices(self, plugin):
        pluginName = plugin.getName()
        if pluginName != '':
            pluginProxy = PluginServicesProxy()
            setattr(self, pluginName, pluginProxy)

        for (serviceName, serviceFactory) in plugin.getServices().items():
            serviceClass = serviceFactory(self)
            if pluginName == '':
                self.addCoreService(serviceName, serviceClass)
            else:
                pluginProxy.addService(serviceName, serviceClass)

    def registerPluginObjects(self, plugin):
        KalturaEnumsFactory.registerEnums(plugin.getEnums())
        print ">>>>REGISTERING"
        KalturaObjectFactory.registerObjects(plugin.getTypes())

    def addCoreService(self, serviceName, serviceClass):
        setattr(self, serviceName, serviceClass)

    def getServeUrl(self):
        if len(self.callsQueue) != 1:
            return None

        (url, params, _) = self.getRequestParams()

        # reset state
        self.callsQueue = []
        self.multiRequest = False

        result = '%s&%s' % (url, urllib.urlencode(params.get()))
        self.log("Returned url [%s]" % result)
        return result        
        
    def queueServiceActionCall(self, service, action, params = KalturaParams(), files = KalturaFiles()):
        # in start session partner id is optional (default -1). if partner id was not set, use the one in the config
        if not params.get().has_key("partnerId") or params.get()["partnerId"] == -1:
            if self.config.partnerId != None:
                params.put("partnerId", self.config.partnerId)
        params.addStringIfDefined("ks", self.ks)
        call = KalturaServiceActionCall(service, action, params, files)
        self.callsQueue.append(call)

    def getRequestParams(self):
        params = KalturaParams()
        files = KalturaFiles()
        params.put("apiVersion", self.apiVersion)
        params.put("format", self.config.format)
        params.put("clientTag", self.config.clientTag)
        url = self.config.serviceUrl + "/api_v3/index.php?service="
        if self.multiRequest:
            url += "multirequest"
            i = 1
            for call in self.callsQueue:
                callParams = call.getParamsForMultiRequest(i)
                callFiles = call.getFilesForMultiRequest(i)
                params.update(callParams)
                files.update(callFiles)
                i += 1
        else:
            call = self.callsQueue[0]
            url += call.service + "&action=" + call.action
            params.update(call.params)
            files.update(call.files)

        signature = params.signature()
        params.put("kalsig", signature)

        self.log("request url: [%s]" % url)

        return (url, params, files)

    @staticmethod
    def closeHandle(fh):
        fh.close()

    @staticmethod
    def openRequestUrl(url, params, files):
        if len(files.get()) == 0:
            try:
                f = urllib.urlopen(url, urllib.urlencode(params.get()))
            except Exception, e:
                raise KalturaClientException(e, KalturaClientException.ERROR_CONNECTION_FAILED)
        else:
            fullParams = params
            fullParams.update(files)
            datagen, headers = multipart_encode(fullParams.get())
            request = urllib2.Request(url, datagen, headers)
            try:
                f = urllib2.urlopen(request)
            except Exception, e:
                raise KalturaClientException(e, KalturaClientException.ERROR_CONNECTION_FAILED)
        return f

    @staticmethod
    def readHttpResponse(f, requestTimeout):
        if requestTimeout != None:
            readTimer = Timer(requestTimeout, KalturaClient.closeHandle, [f])
            readTimer.start()
        try:
            try:
                data = f.read()
            except AttributeError, e:      # socket was closed while reading
                raise KalturaClientException(e, KalturaClientException.ERROR_READ_TIMEOUT)
            except Exception, e:
                raise KalturaClientException(e, KalturaClientException.ERROR_READ_FAILED)
        finally:
            if requestTimeout != None:
                readTimer.cancel()
        return data

    # Send http request
    def doHttpRequest(self, url, params = KalturaParams(), files = KalturaFiles()):
        if len(files.get()) == 0:
            requestTimeout = self.config.requestTimeout
        else:
            requestTimeout = None
            
        if requestTimeout != None:
            origSocketTimeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(requestTimeout)
        try:
            f = self.openRequestUrl(url, params, files)
            data = self.readHttpResponse(f, requestTimeout)
            self.responseHeaders = f.info().headers
        finally:
            if requestTimeout != None:
                socket.setdefaulttimeout(origSocketTimeout)
        return data
        
    def parsePostResult(self, postResult):
        if len(postResult) > 1024:
            self.log("result (xml): %s bytes" % len(postResult))
        else:
            self.log("result (xml): %s" % postResult)

        try:        
            resultXml = minidom.parseString(postResult)
        except ExpatError, e:
            raise KalturaClientException(e, KalturaClientException.ERROR_INVALID_XML)
            
        resultNode = getChildNodeByXPath(resultXml, 'xml/result')
        if resultNode == None:
            raise KalturaClientException('Could not find result node in response xml', KalturaClientException.ERROR_RESULT_NOT_FOUND)

        execTime = getChildNodeByXPath(resultXml, 'xml/executionTime')
        if execTime != None:
            self.executionTime = getXmlNodeFloat(execTime)

        self.throwExceptionIfError(resultNode)

        return resultNode        
        
    # Call all API services that are in queue
    def doQueue(self):
        self.responseHeaders = None
        self.executionTime = None
        if len(self.callsQueue) == 0:
            self.multiRequest = False
            return None

        if self.config.format != KALTURA_SERVICE_FORMAT_XML:
            raise KalturaClientException("unsupported format: %s" % (postResult), KalturaClientException.ERROR_FORMAT_NOT_SUPPORTED)
            
        startTime = time.time()

        # get request params
        (url, params, files) = self.getRequestParams()        
            
        # reset state
        self.callsQueue = []
        self.multiRequest = False

        # issue the request        
        postResult = self.doHttpRequest(url, params, files)

        # parse the result            
        resultNode = self.parsePostResult(postResult)

        endTime = time.time()
        self.log("execution time for [%s]: [%s]" % (url, endTime - startTime))

        return resultNode

    def getKs(self):
        return self.ks
        
    def setKs(self, ks):
        self.ks = ks
        
    def getConfig(self):
        return self.config
        
    def setConfig(self, config):
        self.config = config
        logger = self.config.getLogger()
        if isinstance(logger, IKalturaLogger):
            self.shouldLog = True
        
    def getExceptionIfError(self, resultNode):
        errorNode = getChildNodeByXPath(resultNode, 'error')
        if errorNode == None:
            return None
        messageNode = getChildNodeByXPath(errorNode, 'message')
        codeNode = getChildNodeByXPath(errorNode, 'code')
        if messageNode == None or codeNode == None:
            return None
        return KalturaException(getXmlNodeText(messageNode), getXmlNodeText(codeNode))

    # Validate the result xml node and raise exception if its an error
    def throwExceptionIfError(self, resultNode):
        exceptionObj = self.getExceptionIfError(resultNode)
        if exceptionObj == None:
            return
        raise exceptionObj

    def startMultiRequest(self):
        self.multiRequest = True
        
    def doMultiRequest(self):
        resultXml = self.doQueue()
        if resultXml == None:
            return []
        result = []
        for childNode in resultXml.childNodes:
            exceptionObj = self.getExceptionIfError(childNode)
            if exceptionObj != None:
                result.append(exceptionObj)
            elif getChildNodeByXPath(childNode, 'objectType') != None:
                result.append(KalturaObjectFactory.create(childNode, KalturaObjectBase))
            elif getChildNodeByXPath(childNode, 'item/objectType') != None:
                result.append(KalturaObjectFactory.createArray(childNode, KalturaObjectBase))
            else:
                result.append(getXmlNodeText(childNode))
        return result

    def isMultiRequest(self):
        return self.multiRequest
        
    def getMultiRequestResult(self):
        return MultiRequestSubResult('%s:result' % len(self.callsQueue))
        
    def log(self, msg):
        if self.shouldLog:
            self.config.getLogger().log(msg)

    @staticmethod
    def generateSession(adminSecretForSigning, userId, type, partnerId, expiry = 86400, privileges = ''):
        rand = random.randint(0, 0x10000)
        expiry = int(time.time()) + expiry
        fields = [partnerId, partnerId, expiry, type, rand, userId, privileges]
        fields = map(lambda x: str(x), fields)
        info = ';'.join(fields)
        signature = KalturaClient.hash(adminSecretForSigning, info)
        decodedKS = signature + "|" + info
        KS = base64.b64encode(decodedKS)
        return KS

    @staticmethod
    def hash(salt, msg):
        m = hashlib.sha1()
        m.update(salt)
        m.update(msg)
        return m.digest().encode('hex')

class KalturaServiceActionCall:
    def __init__(self, service, action, params = KalturaParams(), files = KalturaFiles()):
        self.service = service
        self.action = action
        self.params = params
        self.files = files
        
    # Return the parameters for a multi request
    def getParamsForMultiRequest(self, multiRequestIndex):
        multiRequestParams = KalturaParams()
        multiRequestParams.put("%s:service" % multiRequestIndex, self.service)
        multiRequestParams.put("%s:action" % multiRequestIndex, self.action)
        for (key, val) in self.params.get().items():
            multiRequestParams.put("%s:%s" % (multiRequestIndex, key), val)
        return multiRequestParams

    def getFilesForMultiRequest(self, multiRequestIndex):
        multiRequestParams = KalturaFiles()
        for (key, val) in self.files.get().items():
            multiRequestParams.put("%s:%s" % (multiRequestIndex, key), val)
        return multiRequestParams
