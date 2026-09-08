#!/bin/python3

import math
import os
import random
import re
import sys

#
# Lengkapi fungsi 'bilanganGanjil' di bawah ini.
#
# Fungsi diharapkan mengembalikan sebuah INTEGER_ARRAY.
# Fungsi menerima parameter berikut:
#  1. INTEGER l
#  2. INTEGER r
#

def bilanganGanjil(l, r):
    hasil=[]
    for i in range(l,r+1):
        if i%2!=0:
            hasil.append(i)
    return hasil

if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    l = int(input().strip())
    r = int(input().strip())

    result = bilanganGanjil(l, r)

    fptr.write('\n'.join(map(str, result)))
    fptr.write('\n')

    fptr.close()