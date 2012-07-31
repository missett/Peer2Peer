import select
import socket
import sys
import struct
import string
from random import choice
import os
import tcp

#Split an ip into 4 bytes
def split_ip( ipString ):
	l = string.split( ipString , '.' )
	x = []
	for i in l:
		x.append( int(i) )
	return x

#Join a received 4 ip byte sequence into string
def join_ip( ipList ):
	r = str(ipList).strip('()')
	s = r.replace(',' , '.')
	t = s.replace(' ' , '')
	return t

#Maintain the neighbours by putting it into the available list first if the list is smaller than
#20. Then convert the list into a set to remove the duplicates, then convert it back to a list. 
#Works because sets cannot contain duplicates, removed automagically. Finally choose a available
#address at random to go into the active list if the list is smaller than 5
def maintain_neighbours( ipAddress , port ):
	if len(available) < 20:
		available.append( (ipAddress , port) )

	list(set(available))

	if len(active) < 5:
		c = choice( available ) 
		active.append( c )
		available.remove( c )

def send_hello( ip , port ):
	ipNums = split_ip( socket.gethostbyname(socket.gethostname()) )
	message = struct.pack( 'cchBBBBh' , '1' , '1' , 6 , ipNums[0] , ipNums[1] , ipNums[2] , ipNums[3] , sock.getsockname()[1] ) 
	sock.sendto(message , (ip , port))

def parse_type( message ):
	result = struct.unpack( 'cc' , message[:2] )
	return result[1]

#Do we really need this method. Nowhere calls it as yet
def receive_hello( message ):
	version , msgType , length = struct.unpack( 'cch' , message[:4] )
	if length is not 6:
		print 'Bad HELLO received'
	else:
		ip = join_ip( struct.unpack( 'BBBB' , message[4:8] ) )
		port = struct.unpack( 'h' , message[8:] )

def send_ack( address ):
	payload = struct.pack( 'cch' , '1' , '2' , len(available)*6 )

	for i in available:
		ipList = split_ip( i[0] )
		payload += struct.pack( 'BBBBh' , ipList[0] , ipList[1] , ipList[2] , ipList[3] , i[1] )

	print 'Sending ACK to ' + address[0] + ':' + str(address[1])
	sock.sendto( payload , address )
	print 'Adding ' + address[0] + ':' + str(address[1]) + ' to neighbours'
	maintain_neighbours( address[0] , address[1] )

def receive_ack( message , address ):
	version , msgType , length = struct.unpack( 'cch' , message[:4] )
	print 'ACK has ' + str(length) + ' addresses'

	for i in range(0,length/6):
		neighbour = struct.unpack( 'BBBBh' , message[(6*i)+4:(6*i)+10] )
		ip = join_ip( list( neighbour[0:4] ) )
		maintain_neighbours( string.strip(str(ip) , '[]') , neighbour[4] )
	
	maintain_neighbours( address[0] , address[1] )

#For this we need to send the address of a TCP socket, not the UDP socket used previously
def send_search( term ):
	ipNums = split_ip( socket.gethostbyname( socket.gethostname() ) )
	#port = sock.getsockname()[1]
	port = 2501

	header = struct.pack( 'cch' , '1' , '3' , len(term)+7 )
	payload = struct.pack( 'cBBBBh' + str(len(term)) + 's' , '0' , ipNums[0] , ipNums[1] , ipNums[2] , ipNums[3] , port , term )
	message = header + payload

	for i in active:
		sock.sendto( message , i )

	tcp.TCPThread('accept').start()

def receive_search( message , address ):
	version , msgType , length = struct.unpack( 'cch' , message[:4] )
	searchIP = join_ip( struct.unpack( 'BBBB' , message[5:9] ) ) 
	searchPort = struct.unpack( 'h' , message[10:12] )[0] 
	searchTerm = struct.unpack( str(length-7) + 's' , message[12:] )[0]
	print 'Got SEARCH from ' + searchIP + ':' + str(searchPort) + ' looking for ' + searchTerm

	if not (repeated_search( (str(searchIP) , int(searchPort) ) , searchTerm )):
		add_search( (str(searchIP) , int(searchPort) ) , searchTerm )

		if look_for_file( searchTerm ):
			print 'SEARCH matched. Sending file.' 
			tcp.TCPThread('receive' , (searchIP,searchPort)).start()
		else:
			print 'SEARCH NOT matched. Forwarding search.'
			for i in active:
				if i != address:
					sock.sendto( message , i )

def repeated_search( address , term ):
	item = ( address , term )
	result = False 
	for i in searches:
		if i == item:
			result = True
	return result

def add_search( address , term ):
	searches.append( (address , term) )

def look_for_file( term ):
	result = False
	for i in os.listdir('.'):
		if i == term:
			result = True
	return result

#List of neighbours to talk to
active = []
available = []

#List of search requests we've seen - form of (address , term) 
searches = []

#We always bind to a socket no matter what, use the try/except for testing purposes
sock = socket.socket( socket.AF_INET , socket.SOCK_DGRAM )
try:
	sock.bind( (socket.gethostbyname(socket.gethostname()) , 2500) )
except:
	sock.bind( ('localhost' , 2500) )
sock.setblocking(0)

print 'New node established on ' + sock.getsockname()[0] + ':' + str(sock.getsockname()[1])

#Check if the user supplied a peer to connect to
try:
	peerIP , peerPort = sys.argv[1] , sys.argv[2]
	print 'Sending HELLO to first peer on ' + peerIP + ':' + peerPort
	send_hello( peerIP , int(peerPort) )
except:
	print 'First node in NEW NETWORK'

while True:
	readable, writable, errors = select.select( [sock , sys.stdin] , [] , [] )

	for s in readable:
		if s is sock:
			data, address = sock.recvfrom(1024)
			if parse_type( data ) is '1':
				print 'Got HELLO from ' + address[0] + ':' + str(address[1])
				send_ack( address )
			elif parse_type( data ) is '2':
				print 'Got ACK from ' + address[0] + ':' + str(address[1]) 
				receive_ack( data , address )
			elif parse_type( data ) is '3':
				receive_search( data , address )

		if s is sys.stdin:
			data = sys.stdin.readline().strip()
			print 'Sending SEARCH for ' + data
			send_search( data )

