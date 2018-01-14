#!/usr/bin/python

import socket 
import threading
import random
import numpy
import time
from scipy import interp
from numpy.polynomial import polynomial as polynomial

def server(PORT, n, x, y):
	HOST = ''

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((HOST, PORT))
	s.listen(5)

	i = 1
	while i <= n:	
		conn, addr = s.accept()
		conn.sendall(str(x))
		time.sleep(0.1)
		conn.sendall(str(y))
		conn.close()
		i = i + 1
	s.close()

def share(PORT, n, t, secret):
	HOST = ''

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((HOST, PORT))

	# Default port to bind the server to is 50000. The host is, of course, localhost.
	
	s.listen(n)

	# Listen for n connections.
	
	i = 1

	prime = 7103

	# A maximum prime number in case the implementation needs to be a finite prime field	

	coeffs = []
	for j in range(t):
		coeffs.append(random.randint(1, prime))	
	coeffs.append(secret)
	
	print "The distributing server computes the polynomial {0}x + {1}.".format(coeffs[0], coeffs[1])

	polynom = numpy.poly1d(coeffs)
	
	# Polynomials loaded in, and secret appended to end

	while i <= n:
		conn, addr = s.accept()
		conn.sendall(str(i))
		conn.sendall(str(polynom(i)))
		conn.close()
		i = i + 1

		# Wait for a ping from a client and send it back a share - an (x, f(x)) pair from the polynomial.

	s.close()

def getshares(PORT, n):
	HOST = ''
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))

	# Set up a connection with the sharing server, and wait to receive a share.

	xval = s.recv(1024)
	time.sleep(0.1)
	yval = s.recv(1024)	

	print "I, client {0}, received the share ({1}, {2}).".format(n, xval, yval)
	s.close()
	return (int(xval), int(yval))

def reconstruct(PORT, n, shares):
	allshares = [[(0, 0) for k in range(n)] for l in range(n)]
	i = 0
	for i in range(n):
		distribthread = threading.Thread(target = server, args = (PORT + i, n, shares[i][0], shares[i][1]))	
		distribthread.start()
	
		time.sleep(0.1)

		j = 1
		while j <= n:
			allshares[j - 1][i] = client(PORT + i, j)
			j = j + 1	

	print "Shares per client are now:"
	print allshares	
			
	xs = [tup[0] for tup in allshares[1]]
	ys = [tup[1] for tup in allshares[1]]

	f = []

	m = 0
	for m in range(n):
		f.append(numpy.poly1d(numpy.polyfit(xs, ys, 1)))
		print "I, client {0}, have recreated the secret {1}".format(m+1, int(f[m](0)))
	return f

def reconstruct2(PORT, n, shares):
	return reconstruct(PORT, n, shares)


def client(PORT, n):
	HOST = ''

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	xval = int(float(s.recv(1024)))
	time.sleep(0.1)
	yval = int(float(s.recv(1024)))
	
	print "I, client {0}, was lent the share ({1}, {2}).".format(n, xval, yval) 
	s.close()
	return (xval, yval)

def reshare(PORT, n, t, secret, polynom):
	HOST =  ''
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((HOST, PORT))
	
	s.listen(n)
	
	i = 1	
	prime = 7103	

	coeffs = []
	for j in range(t):
		coeffs.append(random.randint(1, prime))
	coeffs.append(0)
	
	newpolynom = numpy.poly1d(polynomial.polyadd(polynom.c, coeffs))


	print "Old polynomial is: {0}x + {1}".format(int(polynom.c[0]), int(polynom.c[1]))
	print "New polynomial is: {0}x + {1}".format(int(polynom.c[0]) + coeffs[0], int(polynom.c[1]) + coeffs[1])
	
	while i <= n:
		conn, addr = s.accept()
		conn.sendall(str(i))
		time.sleep(0.1)
		conn.sendall(str(int(newpolynom(i))))
		time.sleep(0.1)
		conn.close()
		i = i + 1
	
	s.close()
				


def main():

	n = 4
	t = 1
	secret = 97

	#1. The Share method shares correctly.
	print "\nSHARE\n"
	sharethread = threading.Thread(target = share, args = (50000, n, t, secret))
	sharethread.start()	

	shares = []
	i = 1
	while i <= n:
		shares.append(getshares(50000, i))
		i = i + 1
		
	print "All shares are:"
	print shares

	#2. The Reconstruct method reconstructs the correct secret.

	print "\nRECONSTRUCT\n"

	polys = reconstruct(50000, n, shares)

	#3. The Re-share method correctly re-shares a secret and your argument is valid.

	print "\nRE-SHARE\n"

	sharer = random.randint(1, 4)
	resharethread = threading.Thread(target = reshare, args= (50000, n, t, secret, polys[sharer - 1]))
	resharethread.start()	

	newshares = []
	i = 1
	while i <= n: 
		x = getshares(50000, i)
		newshares.append(x)
		i = i + 1

	print "New redistributed shares are:"
	print newshares

	print "Informal argument: It's secure to re-share a share by computing a new polynomial - additively or multiplicatively - and attaching it to the former polynomial which held the secret.\nThis is because encryption under the Shamir's secret sharing scheme is homomorphic; another polynomial g of the same degree as f can pass out new shares and when added to the shares\nof f, they will be shares of (f+g)(x). This allows for a sort of re-randomization - giving each party a new stake in a new polynomial with the same secret. This means that despite\npossessing now two shares each (if, of course, they're a party that was around in a previous round), they cannot combine these shares and expect to be able to retrieve the secret.\nInstead, they still have to cooperate with another party - even if they have t+1 shares themselves, they aren't shares from the same party, and thus each party needs shares from \nanother party to reconstruct the secret.\n"

	#4. The Reconstruct2 method constructs a correct secret even if some parties are missing. Feel free to use filter with newshares to prove this.

	print "\nRECONSTRUCT2\n"
		
	reconstruct2(60000, n, newshares)
	
	#5. One party can join the protocol.

	print "\n PARTY JOINS\n" 
	
	n = 5
	sharer = random.randint(1, 4)
	joinedsharethread = threading.Thread(target = reshare, args = (60000, n, t, secret, polys[sharer - 1]))
	joinedsharethread.start()

	newshares = []
	i = 1
	while i <= n:
		x = getshares(60000, i)
		newshares.append(x)
		i = i + 1

	print "New party shares are:"
	print newshares

	print "\n RECONSTRUCT WITH NEW PARTY \n"
	
	#6. New party receives a share without compromised privacy.
	#7. Parties (including the new ones) can correctly reconstruct the secret.
		
	reconstruct2(60005, n, newshares)

	print("Complete")

if __name__ == "__main__":
	main()	
