# this is just a random shuffling of [0 .. 9] + [a .. z] + [A .. Z]
ALPHABET = "Ejw9Nf2JIp3Vxzug0Cv5d6mH4ohRQe8yFcOMZqntTbUDSBA1rPXLl7YKakiGWs"


# Implementation taken from http://stackoverflow.com/a/1119769/1470715
def encode(num, alphabet=ALPHABET):
    """
    Encode a number into a string.
    The base is determined from the alphabet.

    @param num: The number to encode
    @param alphabet: The alphabet to use for encoding

    @return: A string encoded with the given alphabet
    """
    assert(num >= 0)
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def decode(string, alphabet=ALPHABET):
    """
    Decode an encoded string into a number.
    The base is determined from the alphabet.

    @param string: The encoded string
    @param alphabet: The alphabet to use for decoding

    @return: A number decoded using the given alphabet
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num
