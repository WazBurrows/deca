import sys
import mmh3
import numpy as np
from numba import njit

# Need to constrain U32 to only 32 bits using the & 0xffffffff
# since Python has no native notion of integers limited to 32 bit
# http://docs.python.org/library/stdtypes.html#numeric-types-int-float-long-complex

'''
KK FOUND HERE: https://stackoverflow.com/questions/3279615/python-implementation-of-jenkins-hash
'''

'''
Original copyright notice:
    By Bob Jenkins, 1996.  bob_jenkins@burtleburtle.net.  You may use this
    code any way you wish, private, educational, or commercial.  Its free.
'''


@njit(inline='always')
def rot(x, k):
    return (x << k) | (x >> (32 - k))


@njit(inline='always')
def mix(a, b, c):
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    a -= c; a &= 0xffffffff; a ^= rot(c,4);  a &= 0xffffffff; c += b; c &= 0xffffffff
    b -= a; b &= 0xffffffff; b ^= rot(a,6);  b &= 0xffffffff; a += c; a &= 0xffffffff
    c -= b; c &= 0xffffffff; c ^= rot(b,8);  c &= 0xffffffff; b += a; b &= 0xffffffff
    a -= c; a &= 0xffffffff; a ^= rot(c,16); a &= 0xffffffff; c += b; c &= 0xffffffff
    b -= a; b &= 0xffffffff; b ^= rot(a,19); b &= 0xffffffff; a += c; a &= 0xffffffff
    c -= b; c &= 0xffffffff; c ^= rot(b,4);  c &= 0xffffffff; b += a; b &= 0xffffffff
    return a, b, c


@njit(inline='always')
def final(a, b, c):
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,14); c &= 0xffffffff
    a ^= c; a &= 0xffffffff; a -= rot(c,11); a &= 0xffffffff
    b ^= a; b &= 0xffffffff; b -= rot(a,25); b &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,16); c &= 0xffffffff
    a ^= c; a &= 0xffffffff; a -= rot(c,4);  a &= 0xffffffff
    b ^= a; b &= 0xffffffff; b -= rot(a,14); b &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,24); c &= 0xffffffff
    return a, b, c


@njit(inline='always')
def hashlittle2(data, initval=0, initval2=0):
    length = lenpos = len(data)

    a = b = c = (0xdeadbeef + length + initval)

    c += initval2
    c &= 0xffffffff

    p = 0  # string offset
    while lenpos > 12:
        a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24)); a &= 0xffffffff
        b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); b &= 0xffffffff
        c += ((data[p+8]) + ((data[p+9])<<8) + ((data[p+10])<<16) + ((data[p+11])<<24)); c &= 0xffffffff
        a, b, c = mix(a, b, c)
        p += 12
        lenpos -= 12

    if lenpos == 12: c += ((data[p+8]) + ((data[p+9])<<8) + ((data[p+10])<<16) + ((data[p+11])<<24)); b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 11: c += ((data[p+8]) + ((data[p+9])<<8) + ((data[p+10])<<16)); b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 10: c += ((data[p+8]) + ((data[p+9])<<8)); b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 9:  c += ((data[p+8])); b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 8:  b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16) + ((data[p+7])<<24)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 7:  b += ((data[p+4]) + ((data[p+5])<<8) + ((data[p+6])<<16)); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 6:  b += (((data[p+5])<<8) + (data[p+4])); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24))
    if lenpos == 5:  b += ((data[p+4])); a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24));
    if lenpos == 4:  a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16) + ((data[p+3])<<24))
    if lenpos == 3:  a += ((data[p+0]) + ((data[p+1])<<8) + ((data[p+2])<<16))
    if lenpos == 2:  a += ((data[p+0]) + ((data[p+1])<<8))
    if lenpos == 1:  a += (data[p+0])
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    if lenpos == 0: return c, b

    a, b, c = final(a, b, c)

    return c, b


@njit(inline='always')
def hash32_func_bytes(data, init_val=0):
    c, b = hashlittle2(data, init_val, 0)
    return c


def hash32_func(data, init_val=0):
    if isinstance(data, str):
        data = data.encode('ascii')
    return hash32_func_bytes(data, init_val)


def hash48_func(data):
    if isinstance(data, str):
        data = data.encode('ascii')

    v = mmh3.hash128(key=data, x64arch=True)
    return (v >> 16) & 0x0000FFFFFFFFFFFF


def hash64_func(data):
    if isinstance(data, str):
        data = data.encode('ascii')

    v = mmh3.hash128(key=data, x64arch=True)
    return int(np.int64(np.uint64(v & 0xFFFFFFFFFFFFFFFF)))


def hash_all_func(data):
    if isinstance(data, str):
        data = data.encode('ascii')

    c, b = hashlittle2(data, 0, 0)

    v = mmh3.hash128(key=data, x64arch=True)

    return c, (v >> 16) & 0x0000FFFFFFFFFFFF, int(np.int64(np.uint64(v & 0xFFFFFFFFFFFFFFFF)))


def main():
    data = sys.argv[1]

    hv = hash32_func(data)
    print('hash4 "{}" = {:12} , 0x{:08x}'.format(data, hv, hv))

    hv = hash48_func(data)
    print('hash6 "{}" = {:24} , 0x{:012x}'.format(data, hv, hv))

    hv = hash64_func(data)
    print('hash8 "{}" = {:24}, {:24}, 0x{:016x}'.format(data,  hv, np.uint64(hv), np.uint64(hv)))


if __name__ == "__main__":
    main()
