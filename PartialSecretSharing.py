# Largely copied from Wikipedia
from __future__ import division
from __future__ import print_function

import random
import functools

# 12th Mersenne Prime
_PRIME = 2 ** 127 - 1

_RINT = functools.partial(random.SystemRandom().randint, 0)

def _eval_at(poly, x, prime):
    """Evaluates polynomial (coefficient tuple) at x, used to generate a
    shamir pool in make_random_shares below.
    """
    accum = 0
    for coeff in reversed(poly):
        accum *= x
        accum += coeff
        accum %= prime
    return accum

def make_random_shares(secret, minimum, shares, prime=_PRIME):
    """
    Generates a random shamir pool for a given secret, returns share points.
    """
    if minimum > shares:
        raise ValueError("Pool secret would be irrecoverable.")
    poly = [secret] + [_RINT(prime - 1) for i in range(minimum - 1)]
    points = [(i, _eval_at(poly, i, prime))
              for i in range(1, shares + 1)]
    return points

def _extended_gcd(a, b):
    """
    Division in integers modulus p means finding the inverse of the
    denominator modulo p and then multiplying the numerator by this
    inverse (Note: inverse of A is B such that A*B % p == 1). This can
    be computed via the extended Euclidean algorithm
    http://en.wikipedia.org/wiki/Modular_multiplicative_inverse#Computation
    """
    x = 0
    last_x = 1
    y = 1
    last_y = 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y

def _divmod(num, den, p):
    """Compute num / den modulo prime p

    To explain this, the result will be such that:
    den * _divmod(num, den, p) % p == num
    """
    inv, _ = _extended_gcd(den, p)
    return num * inv

def _lagrange_interpolate(x, x_s, y_s, p):
    """
    Find the y-value for the given x, given n (x, y) points;
    k points will define a polynomial of up to kth order.
    """
    k = len(x_s)
    assert k == len(set(x_s)), "points must be distinct"
    def PI(vals):  # upper-case PI -- product of inputs
        accum = 1
        for v in vals:
            accum *= v
        return accum
    nums = []  # avoid inexact division
    dens = []
    for i in range(k):
        others = list(x_s)
        cur = others.pop(i)
        nums.append(PI(x - o for o in others))
        dens.append(PI(cur - o for o in others))
    den = PI(dens)
    num = sum([_divmod(nums[i] * den * y_s[i] % p, dens[i], p)
               for i in range(k)])
    return (_divmod(num, den, p) + p) % p

def recover_secret(shares, prime=_PRIME):
    """
    Recover the secret from share points
    (points (x,y) on the polynomial).
    """
    x_s, y_s = zip(*shares)
    return _lagrange_interpolate(0, x_s, y_s, prime)

def inputNaturalNumber(prompt): 
	while True: 
		try: 
			value = int(input(prompt))
		except: 
			print('Please enter a natural number. ')
			continue
		if value <= 0: 
			print('Please enter a natural number. (Natural numbers are greater than zero.)')
		else: 
			return value

def inputWholeNumber(prompt): 
	while True: 
		try: 
			value = int(input(prompt), 16)
		except: 
			print('Please enter a whole number. ')
			continue
		if value < 0: 
			print('Please enter a whole number. (Whole numbers cannot be less than zero.)')
		else: 
			return value

def toHex(value, minLength = 0): 
	valueHex = f'{value:X}'
	while len(valueHex) < minLength: 
		valueHex = '0' + valueHex
	return valueHex

def encodeShares(total, shares): 
	totalStr = toHex(total)
	totalLen = len(totalStr)
	totalPrefix = ('F' * totalLen) + '0' + totalStr
	encodedShares = []
	for share in shares: 
		encodedShares.append((share[0], int(totalPrefix + toHex(share[0], totalLen) + toHex(share[1]), 16)))
	return encodedShares

def decodeShares(share): 
	shareStr = toHex(share)
	encodedTotalLen = ''
	index = 0
	while shareStr[index] != '0': 
		encodedTotalLen += shareStr[index]
		index += 1
	totalLen = len(encodedTotalLen)
	total = int(shareStr[(totalLen + 1):((2 * totalLen) + 1)], 16)
	shareNum = int(shareStr[((2 * totalLen) + 1):((3 * totalLen) + 1)], 16)
	shareValue = int(shareStr[((3 * totalLen) + 1):], 16)
	return ((total, shareNum, shareValue))

def main():
	"""Main function"""
	print('Partial Secret Sharing')
	print()
	print(' 1. Break Secret into Parts')
	print(' 2. Recover Secret from Parts')
	print(' 3. Quit')
	print()
	while True: 
		action = input('Action: ')
		if action == '1': 
			secret = input('Secret: ').encode()
			secretNum = 0
			power = 1
			for char in secret:
			    secretNum += char * power
			    power *= 256
			while True: 
				required = inputNaturalNumber('Required Parts: ')
				total = inputNaturalNumber('Total Parts: ')
				if total >= 256: 
					print('Software does not current support splitting secret into more than 255 parts. ') # TODO
				elif total < required: 
					print('Cannot require more parts than exist. ')
				else: 
					break
			shares = make_random_shares(secretNum, minimum=required, shares=total)
			shares = encodeShares(total, shares)

			print('Partial Secrets:')
			if shares:
			    for share in shares:
			        print('  ', toHex(share[1]))
		elif action == '2': 
			required = inputNaturalNumber('Required Parts: ')
			parts = []
			for i in range(required): 
				part = inputWholeNumber('Part: ')
				(total, num, share) = decodeShares(part)
				parts.append((num, share))
			secretNum = recover_secret(parts)
			secretList = []
			while secretNum > 0: 
			    secretList.append(secretNum % 256)
			    secretNum //= 256
			print('Secret:', bytearray(secretList).decode())
		elif action != '3': 
		    print('Please enter 1, 2, or 3. ')
		    continue
		break

if __name__ == '__main__':
    main()