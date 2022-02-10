k_box = (
    (0xC, 0x4, 0x6, 0x2, 0xA, 0x5, 0xB, 0x9, 0xE, 0x8, 0xD, 0x7, 0x0, 0x3, 0xF, 0x1),
    (0x6, 0x8, 0x2, 0x3, 0x9, 0xA, 0x5, 0xC, 0x1, 0xE, 0x4, 0x7, 0xB, 0xD, 0x0, 0xF),
    (0xB, 0x3, 0x5, 0x8, 0x2, 0xF, 0xA, 0xD, 0xE, 0x1, 0x7, 0x4, 0xC, 0x9, 0x6, 0x0),
    (0xC, 0x8, 0x2, 0x1, 0xD, 0x4, 0xF, 0x6, 0x7, 0x0, 0xA, 0x5, 0x3, 0xE, 0x9, 0xB),
    (0x7, 0xF, 0x5, 0xA, 0x8, 0x1, 0x6, 0xD, 0x0, 0x9, 0x3, 0xE, 0xB, 0x4, 0x2, 0xC),
    (0x5, 0xD, 0xF, 0x6, 0x9, 0x2, 0xC, 0xA, 0xB, 0x7, 0x8, 0x1, 0x4, 0x3, 0xE, 0x0),
    (0x8, 0xE, 0x2, 0x5, 0x6, 0x9, 0x1, 0xC, 0xF, 0x4, 0xB, 0x0, 0xD, 0xA, 0x3, 0x7),
    (0x1, 0x7, 0xE, 0xD, 0x0, 0x5, 0x8, 0x3, 0x4, 0xF, 0xA, 0x6, 0x9, 0xC, 0xB, 0x2)
)

input_hex = 0x0011AA33445566FF
key_hex = 0x0000111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF

# Разбиение 64-бит блока на 2 блока по 32-бит, записанных в обратном порядке бит
def input_split(input):
    n1 = int(format(input >> 32, '032b')[::-1], 2)
    n2 = int(format(input & 0xFFFFFFFF, '032b')[::-1], 2)
    return n1, n2

# Разбиение 256-бит ключа на 8 блоков 32-бит, записанных в обратном порядке бит
def key_split(key):
    key_list = []
    for i in range(7,-1,-1):
        key_list.append(int(format(((key_hex >> (32 * i)) & 0xFFFFFFFF), '032b')[::-1], 2))
    return key_list

# Суммирование блока N1 и ключа Xround по модулю 2**32 
def cm1_calc(x, n1):
    cm1 = n1 + x
    if cm1 >= 2**32:
        cm1 = cm1 - 2**32 + 1
    cm1 = format(cm1, '032b')
    return cm1

# Замена блоков 4-бит соотстветствущими из таблицы kbox
def kbox_change(cm1):
    k = ''
    for block in range(8):
        k += format(k_box[block][int(cm1[block*4:block*4+4], 2) - 1], '04b')
    return k

# Циклический сдвиг на 11 бит влево
def r_shift(k):
    r = k[11:] + k[:11]
    return r

# Суммирование блока N2 и состояния r поразрядно по модулю 2
def cm2_calc(r, n2):
    cm2 = n2 ^ int(r, 2)
    return cm2

# Функция шифрования 64-битного блока 256-битным ключом
def encryption(input_hex, key_hex):
    n1, n2 = input_split(input_hex)
    x_list = key_split(key_hex)
    for round in range(1, 25):
        cm1 = cm1_calc(x_list[(round-1) % 8], n1)
        k = kbox_change(cm1)
        r = r_shift(k)
        cm2 = cm2_calc(r, n2)
        n2 = n1
        n1 = cm2
    for round in range(25, 33):
        cm1 = cm1_calc(x_list[(32-round) % 8], n1)
        k = kbox_change(cm1)
        r = r_shift(k)
        cm2 = cm2_calc(r, n2)
        if round == 32:
            n2 = cm2
        else:
            n2 = n1
            n1 = cm2
    cipher = format(n1, '032b')[::-1] + format(n2, '032b')[::-1]
    return cipher

# Функция шифрования 64-битного шифротекста 256-битным ключом
def decryption(cipher, key_hex):
    n1, n2 = input_split(int(cipher, 2))
    x_list = key_split(key_hex)
    for round in range(1, 9):
        cm1 = cm1_calc(x_list[(round-1) % 8], n1)
        k = kbox_change(cm1)
        r = r_shift(k)
        cm2 = cm2_calc(r, n2)
        n2 = n1
        n1 = cm2
    for round in range(9, 33):
        cm1 = cm1_calc(x_list[(32-round) % 8], n1)
        k = kbox_change(cm1)
        r = r_shift(k)
        cm2 = cm2_calc(r, n2)
        if round == 32:
            n2 = cm2
        else:
            n2 = n1
            n1 = cm2
    plain = format(n1, '032b')[::-1] + format(n2, '032b')[::-1]
    return plain

def main():
    # ENCRYPTION
    print('Plain:       ', format(input_hex, '016x'))
    print('Key:         ', format(key_hex, '016x'))
    cipher = encryption(input_hex, key_hex)
    print('Encrypted:   ', format(int(cipher, 2), '016x'))
    # DECRYPTION
    plain = decryption(cipher, key_hex)
    print('Decrypted:   ', format(int(plain, 2), '016x'))
    
if __name__ == "__main__":
    main()