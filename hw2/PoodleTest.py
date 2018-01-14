import sys
sys.path.append('../src')

import SocketServer
import ssl
import struct
import random
import string
import threading
import select
import socket

import os
import time


class Simple_Client():

  def trigger(self, msg, ssl_version):
      ssl_host, ssl_port = "0.0.0.0", 30001
      relay_host, relay_port = "0.0.0.0", 30002
      s = socket.create_connection((relay_host, relay_port))
      s = ssl.wrap_socket(s, server_side=False, ssl_version=ssl.PROTOCOL_SSLv3, cert_reqs=ssl.CERT_NONE)
      s.send(msg)
      print s.recv(2)
      return



class SecureTCPHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    self.request = ssl.wrap_socket(self.request, keyfile="cert.pem", certfile="cert.pem", server_side=True, ssl_version=ssl.PROTOCOL_SSLv3, cert_reqs=ssl.CERT_NONE)
    while True:
      try:
        data = self.request.recv(1024)
        if data == '':
          break
        print 'securely received: %s' % repr(data)
        self.request.send('ok')
      except ssl.SSLError as e:
        #print 'ssl error: %s' % str(e)
        break
    return

class MitmTCPHandler(SocketServer.BaseRequestHandler):

  def handle(self):
    destination = socket.create_connection((SSL_HOST, SSL_PORT))

    just_altered = False
    running = True
    sockets = [self.request, destination]
    while running:
      inputready, outputready, exceptready = select.select(sockets,[],[])
      for s in inputready:
        if s == self.request:
          header = self.request.recv(5)
          if len(header) < 1:
            continue
 
          (content_type, version, length) = struct.unpack('>BHH', header)
          data = self.request.recv(length)
          if content_type == 23 and length > 24: # application data
            just_altered = True


          destination.send(header+data)
        elif s == destination:
          data = destination.recv(1024)
          
          if just_altered:
            (content_type, version, length) = struct.unpack('>BHH', data[:5])
            just_altered = False
          self.request.send(data)

    return

if __name__ == "__main__":
  SSL_HOST, SSL_PORT = "0.0.0.0", 30001
  MITM_HOST, MITM_PORT = "0.0.0.0", 30002

  SocketServer.TCPServer.allow_reuse_address = True

  secure_server = SocketServer.TCPServer((SSL_HOST, SSL_PORT), SecureTCPHandler)
  mitm_server = SocketServer.TCPServer((MITM_HOST, MITM_PORT), MitmTCPHandler)

  threads = [
    threading.Thread(target=secure_server.serve_forever),
    threading.Thread(target=mitm_server.serve_forever),
  ]

  for thread in threads:
    thread.start()

  client = Simple_Client()
  client.trigger("EXAMPLEMESSAGE", ssl.PROTOCOL_SSLv3)
  # Added to actually make this program end
  time.sleep(1)
  os._exit(1)

#secure_server.serve_forever()


