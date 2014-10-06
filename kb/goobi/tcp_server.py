#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 20/06/2014

@author: jeel
'''
import socketserver
import threading
import time

class StepJobTCPServer(socketserver.TCPServer):
    #http://stackoverflow.com/questions/15889241/send-a-variable-to-a-tcphandler-in-python
    def __init__(self, 
                 server_address, 
                 RequestHandlerClass, 
                 step_job_queue,
                 bind_and_activate=True,
                 logger = None):
        if step_job_queue is None:
            raise ValueError('A step_job_processor thread must be given to server.')
        self.step_job_queue = step_job_queue
        self.logger = logger
        socketserver.TCPServer.__init__(self, 
                                        server_address, 
                                        RequestHandlerClass, 
                                        bind_and_activate=True)

class StepJobTCPHandler(socketserver.BaseRequestHandler):
    """
    Todo: document
    """

    def handle(self):
        step_job_queue = self.server.step_job_queue
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip().decode() # Comes as bytes, convert to string
        if self.server.logger:
            msg = "{0} wrote: {1}"
            msg = msg.format(self.client_address[0],self.data)
            self.server.logger.debug(msg)
        command_arguments = self.data.split()
        command_lenght = len(command_arguments)
        if command_lenght == 1:
            command = command_arguments[0] 
            # TODO: add command to get info about queue
            if command in ['quit','exit','close','die','incinerate']:
                r = ('"{0}" recieved correctly. Shutting down server.')
                r = r.format(self.data).encode() # encode to bytes to send via socket
                self.request.sendall(r)
                def stop_server(server):
                    server.shutdown()
                    time.sleep(0.3)
                # shutdown must be called in a separate thread due to server_forever mechanism - se BaseServer in socketserver
                threading.Thread(target=stop_server, args=(self.server,)).start().run()
            else:
                r = ('"{0}" recieved correctly. Nothing done.')
                r = r.format(self.data).encode() # encode to bytes to send via socket
                self.request.sendall(r)
        elif command_lenght > 1:
            step_job_queue.add(command_arguments)
            r = ('"{0}" recieved correctly and added to queue')
            r = r.format(self.data).encode() # encode to bytes to send via socket
            self.request.sendall(r)