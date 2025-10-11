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

def escapableInput(prompt): 
	try: 
		return input(prompt)
	except KeyboardInterrupt: 
		exit()

def inputNaturalNumber(prompt): 
	while True: 
		try: 
			value = int(input(prompt))
		except KeyboardInterrupt: 
			exit()
		except: 
			print('Please enter a natural number. ')
			continue
		if value <= 0: 
			print('Please enter a natural number. (Natural numbers are greater than zero.)')
		else: 
			return value

def inputPart(prompt): 
	while True: 
		try: 
			return decodeShares(input(prompt))
		except KeyboardInterrupt: 
			exit()
		except: 
			print('Failed to parse part. ')

ALPHABET = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
digitOrder = {}
for index, digit in enumerate(ALPHABET): 
	digitOrder[digit] = index

def toCode(value, minLength = 0): 
	valueHex = ''
	while value > 0 or len(valueHex) < minLength: 
		valueHex = ALPHABET[(value % len(ALPHABET))] + valueHex
		value //= len(ALPHABET)
	return valueHex

def fromCode(value): 
	intValue = 0
	power = 1
	for digit in value: 
		intValue = (intValue * len(ALPHABET)) + digitOrder[digit]
	return intValue

def encodeShares(total, required, shares): 
	totalStr = toCode(total)
	totalLen = len(totalStr)
	totalPrefix = (ALPHABET[-1] * totalLen) + ALPHABET[0] + totalStr
	prefix = totalPrefix + toCode(required, totalLen)
	encodedShares = []
	for share in shares: 
		encodedShares.append((share[0], fromCode(prefix + toCode(share[0], totalLen) + toCode(share[1]))))
	return encodedShares

def decodeShares(share): 
	encodedTotalLen = ''
	index = 0
	while share[index] != ALPHABET[0]: 
		encodedTotalLen += share[index]
		index += 1
	totalLen = len(encodedTotalLen)
	total = fromCode(share[(totalLen + 1):((2 * totalLen) + 1)])
	required = fromCode(share[((2 * totalLen) + 1):((3 * totalLen) + 1)])
	shareNum = fromCode(share[((3 * totalLen) + 1):((4 * totalLen) + 1)])
	shareValue = fromCode(share[((4 * totalLen) + 1):])
	return ((total, required, shareNum, shareValue))

def main():
	"""Main function"""
	print('Partial Secret Sharing')
	print()
	print(' 1. Break Secret into Parts')
	print(' 2. Recover Secret from Parts')
	print(' 3. Quit')
	print()
	while True: 
		action = escapableInput('Action: ')
		if action == '1': 
			secret = escapableInput('Secret: ').encode()
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
			shares = encodeShares(total, required, shares)

			print('Partial Secrets:')
			if shares:
			    for share in shares:
			        print('  ', toCode(share[1]))
		elif action == '2': 
			# temp values until we get the real values from a share
			requiredBySet = None
			totalInSet = None

			parts = []
			i = 1
			while (requiredBySet is None) or (i <= requiredBySet): 
				(total, required, num, share) = inputPart('Part: ')
				if (totalInSet is None) and (requiredBySet is None): 
					totalInSet = total
					requiredBySet = required
				elif (total != totalInSet) or (required != requiredBySet): 
					print('The previously entered part does not belong to the same set as the parts entered before it.')
					continue
				parts.append((num, share))
				i += 1
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