import socket
import ssl
import numpy
import threading
import time
import hashlib
import random 
import string

def client(port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	ssl_socket = ssl.wrap_socket(s, ca_certs="server.crt", cert_reqs=ssl.CERT_OPTIONAL)

	ssl_socket.connect(('localhost', port))

	# Actual operations go here

	alpha = ssl_socket.read()
	falpha = ssl_socket.read()
	puzzlehash = ssl_socket.read()
	n = ssl_socket.read()
	
	return ((int(alpha), int(falpha)), int(puzzlehash), int(n))	

	if False:
		ssl_socket.write("dksdjaskfsdf")
		data = ssl_socket.read()
		ssl_socket.close()


def server(port, share, puzzlehash, n, parties):
	bindsocket = socket.socket()
	bindsocket.bind(('', port))
	bindsocket.listen(5)

	i = 0
	
	# Service n clients and then shut down!

	while True:
		if i == parties:
			break
		newsocket, addr = bindsocket.accept()
		connstream = ssl.wrap_socket(newsocket, server_side=True, certfile="server.crt", keyfile="server.key")
		try:
			connstream.write(str(share[0]))	
			time.sleep(0.1)
			connstream.write(str(share[1]))
			time.sleep(0.1)
			connstream.write(str(puzzlehash))
			time.sleep(0.1)
			connstream.write(str(n))
		finally:
			connstream.shutdown(socket.SHUT_RDWR)
			connstream.close()
		i = i + 1

def SolvePuzzle(b1, b2, hardness):
	hasher = hashlib.sha256()
	hasher.update(b1)
	hasher.update(b2)
	
	power = pow(2, (256 - hardness))

	hashcopy = hasher.copy()
	n = 0
	hasher.update(str(n))
	while int(hasher.hexdigest(), base=16) >= power:
		n = n + 1
		hasher = hashcopy.copy()
		hasher.update(str(n))
	print "The solution of the puzzle is {0}, and the hash of the solution is {1}.".format(n, hasher.hexdigest())
	return (n, int(hasher.hexdigest(), base=16)) 

def Share(b2, alpha):
	hasher = hashlib.sha256()
	hasher.update(b2)
	
	
	
	coeff = int(hasher.hexdigest(), base=16)
	

	vec = ""
	for i in range(0, len(b2)):
		vec = vec + hex(ord(b2[i]))[2:]

	yintercept = int(vec, base=16)
	
	fvalue = coeff * alpha + yintercept
	return(alpha, fvalue)	

def Broadcast(partyone, partytwo, shareone, sharetwo, puzzlehash, n, parties):
	portone = 10023
	porttwo = 10024


	print "Party {3} sharing (alpha, f(alpha)) share = {0}, solved puzzle hash = {1}, and n value for the solution = {2}.".format(shareone, hex(puzzlehash), n, partyone)	
	serverone = threading.Thread(target=server, args=(portone, shareone, puzzlehash, n, parties))
	serverone.start()

	print "Party {3} sharing (alpha, f(alpha)) share = {0}, slved puzzle hash = {1}, and n value for the solution = {2}.\n".format(sharetwo, hex(puzzlehash), n, partytwo)
	servertwo = threading.Thread(target=server, args=(porttwo, sharetwo, puzzlehash, n, parties))
	servertwo.start()
	
	vec = []
	i = 0
	for i in range(parties):		
		cshareone, cpuzzlehash, cn = client(portone)
		csharetwo, cpuzzlehashtwo, cntwo = client(porttwo)
		vec.append((cshareone, csharetwo, cpuzzlehash, cn))
		print "Party {4} now has the following: party one's share = {0}, party two's share = {1}, the puzzle's hash = {2}, and the solution = {3}.".format(cshareone, csharetwo, cpuzzlehash, cn, i+1)
		

def Verify(pno, b1, n, puzzlehash, shareone, sharetwo, hardness):
	slope = (sharetwo[1] - shareone[1])/(sharetwo[0] - shareone[0])
	yintercept = shareone[1] - (shareone[0] * slope)
	
	b2hex = str(hex(yintercept))
	if b2hex[-1:] == "L":
		b2hex = b2hex[:len(b2hex)-1]
	if b2hex[:2] == "0x" or b2hex[:2] == "0X":
		b2hex = b2hex[2:]
	
	i = 0
	vec = []
	while i < len(b2hex):
		vec.append(int(b2hex[i:(i+2)], base=16))
		i = i + 2

	chars = []
	for i in range(len(vec)):
		chars.append(chr(vec[i]))
	
	b2 = ''.join(chars)
		
	print "Party {0} has calculated the new block's string value to be \"{1}\".".format(pno, b2)
	
	hasher = hashlib.sha256()
	hasher.update(b1)
	hasher.update(b2)
	hasher.update(str(n))

	
	if int(hasher.hexdigest(), base=16) != puzzlehash:
		print "b2 shares do not hash to the hash of the solved puzzle."
		return b2
	
	print "Party {0} has correctly reconstructed the new block's string value; concatenation with the blockchain and solution, when hashed = {1}.".format(pno, hex(puzzlehash))
	
	
	power = pow(2, (256 - hardness))
	if int(hasher.hexdigest(), base=16) >= power:
		print "hash of the solved puzzle is not a correct solution."
		return b2	

	print "Puzzle correctly verified by party {0}; {1} < 2^{2}.\n".format(pno, hasher.hexdigest(), 256-hardness)

	return b2

def main():
	b1 = "old block"
	b2 = "new block"
	hardness = 8
	
	partyno = 4

	alphas = [12, 17, 25, 36]
	
	partyone = random.randint(1, 4)
	partytwo = random.randint(1, 4)
	while partyone == partytwo:
		partytwo = random.randint(1, 4)
	
	parties = [partyone, partytwo]

	# The two solving parties solve the puzzle with the same data, their values here would be the same.

	print "\n---1. SolvePuzzle---\n"		
	n, puzzlehash = SolvePuzzle(b1, b2, hardness)
	
	# The two solving parties create their shares with different data (different alpha values) and their values are thus different. 
	print "\n---2. Share with two randomly chosen parties: Party {0} and Party {1} ---\n".format(partyone, partytwo)
	shareone = Share(b2, alphas[parties[0] - 1])
	print "Party {1}'s share: {0}.".format(shareone, partyone)
	sharetwo = Share(b2, alphas[parties[1] - 1])
	print "Party {1}'s share: {0}.\n".format(sharetwo, partytwo)
	
	print "---3. Broadcast to all {0} parties---\n".format(partyno)
	Broadcast(partyone, partytwo, shareone, sharetwo, puzzlehash, n, partyno)		
	
	print "\n---4. Verify solutions with all parties--- \n".format(partyno)
	i = 0
	for i in range(partyno):
		Verify(i+1, b1, n, puzzlehash, shareone, sharetwo, hardness)	

	print "All {0} parties have correctly verified the addition to the blockchain.".format(partyno)

	
if __name__ == "__main__":
	main()
	
	
