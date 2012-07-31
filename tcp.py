import threading
import socket

class TCPThread( threading.Thread ):
	def __init__( self , operation , address=None ):
		threading.Thread.__init__( self )

		if operation == 'send':
			self.send(address)
		elif operation =='accept':
			self.accept()

	def send( self , address ):
		print 'Send Operation'
		streamSock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
		streamSock.connect(address)
		streamSock.sendall('Hello TCP World!')
		streamSock.close()

	def accept( self ):
		print 'Accept Operation'
		streamSock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
		streamSock.bind((socket.gethostbyname(socket.gethostname()) , 2501))
		streamSock.listen(1)
		conn, address = streamSock.accept()
		streamSock.setblocking(0)
		data = streamSock.recv(1024)
		print data
		conn.close()

	def run( self ):
		print 'TCP Thread Here'
