#Padding oracle attack in python version 2.7.10

from Crypto.Cipher import AES
import binascii
import sys

#Simple example of how to encrypt in python
tkey = 'sixteen byte key'
ivd = '1234567812345678'
obj1 = AES.new(tkey, AES.MODE_CBC, ivd)
message = '01020304050607080102030405060708010203040506070801020304050607080102030405060708010203040506070801020304050607080102030405060701'.decode('hex')
ciphertext = obj1.encrypt(message)
print "ciphertext is:"
print " ".join(hex(ord(n)) for n in ciphertext)

#check the padding of plaintext
def check_enc(text):
    nl = len(text)
    val = int(binascii.hexlify(text[-1]), 16) 
    if val == 0 or val > 16: 
        return False
        
    for i in range(1, val+1):
        if (int(binascii.hexlify(text[nl-i]), 16) != val):
            return False
    return True

#Padding Oracle
def PadOracle(ciphertext):
    if len(ciphertext) % 16 != 0:
        return False
    
    tkey2 = 'sixteen byte key'
    ivd2 = ciphertext[:AES.block_size]
    obj2 = AES.new(tkey2, AES.MODE_CBC, ivd2)
    ptext = obj2.decrypt(ciphertext[AES.block_size:])
    return check_enc(ptext)


# Isaac Pena
# CPSC 467
# Homework 01

# Programming questions 
# 1. Describe a method to decrypt the last byte of C2. 
# The last byte of C2 is equivalent to the encrypted value of 
# the last byte of C1 XOR'd with the last byte of P2. We can
# retrieve it without having to know the encryption algorithm used,
# however, because we can use our oracle to tell when a particular
# block is padded correctly. If an adversary removes the only block
# that actually needs padding (i.e. the last block), the server on the
# far end doing decryption will not be able to find proper padding 
# unless the /plaintext/ message in the second-last block is padded correctly.
# 
# Thus, if the last block is cut off, only a single value - the one that arises
# from a final plaintext byte in the second-last plaintext block as 0x01 (or
# from the last two as 0x02, or the last three as 0x03 so on and so forth)
# will allow the server to decrypt with proper padding. XORing the final
# byte of C1 with value equivalent to the final byte of M2 and 0x01 will
# return the correct plaintext value for the final byte of M2. This is because
# the usual formula for this byte is the last byte of C2, decrypted, XOR'd with
# the last byte of C1. Changing the value of C1 by passing lastbyteofC1 XOR lastbyteofM2 XOR 0x01
# to the server will raise a padding error for 255/256 of the possible bytes - the only
# one that won't raise an error has the correct last byte of M2 value (which will only
# cancel out the decryption of the last byte of C2 if they're the same), because 
# if this is the last block, the server needs it to be 0x01 on the far side.

# My solution for 2. is below.

# 3. This could be extended to the entire block just by repeating the same formula as below:
# once you have the last three bytes of the plaintext, check all possible combinations of the
# fourth-to-last XOR'd with 0x04, as well as the known correct values of the plaintext XOR'd with 0x04.
# (i.e. bytesarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, l^4, thirdlastbyte^4, secondlastbyte^4, lastbyte^4])
# so on and so forth until XORing by 16 with the last 15 values in the block known. After this is solved,
# the block becomes a padding block and can be cut off in further requests to the server (i.e. in 
# attempting to decrypt C1 instead of C2.)

def xorstrings(s1, s2):
    return ''.join(chr(ord(a) ^ ord(b)) for a,b in zip(s1, s2))

ivector = ciphertext[:AES.block_size]
cblockone = ciphertext[AES.block_size:(AES.block_size * 2)]
cblocktwo = ciphertext[(AES.block_size * 2):(AES.block_size * 3)]
lastbyte = 0;
secondlastbyte = 0;
thirdlastbyte = 0;

# get last byte
for i in range(0, 255):    
    bytesarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, i^1]
    hackstring = "".join(map(chr, bytesarray))
    newctext = ivector + xorstrings(hackstring, cblockone) + cblocktwo
    if(PadOracle(newctext) == True): 
        lastbyte = i

# get second to last byte
for j in range(0, 255):
    bytesarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, j^2, lastbyte^2]
    hackstring = "".join(map(chr, bytesarray))
    newctext = ivector + xorstrings(hackstring, cblockone) + cblocktwo
    if(PadOracle(newctext) == True):
        secondlastbyte = j


# get third to last byte
for k in range(0, 255):
    bytesarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, k^3, secondlastbyte^3, lastbyte^3]
    hackstring = "".join(map(chr, bytesarray))
    newctext = ivector + xorstrings(hackstring, cblockone) + cblocktwo
    if(PadOracle(newctext) == True):
        thirdlastbyte = k
       
print('The last three bytes of C2 are {0}, {1}, and {2}, in that order.\n'.format(thirdlastbyte, secondlastbyte, lastbyte))
 
