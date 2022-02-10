from codecs import getdecoder
from codecs import getencoder
from os import urandom

_hexdecoder = getdecoder("hex")
_hexencoder = getencoder("hex")

def modinvert(a, n): 
    # Функция по нахождению мультипликативного обратного через расширенный алгоритм Эвклида
    if a < 0:
        return n - modinvert(-a, n)
    t, newt = 0, 1
    r, newr = n, a
    while newr != 0:
        quotinent = r // newr
        t, newt = newt, t - quotinent * newt
        r, newr = newr, r - quotinent * newr
    if r > 1:
        return -1
    if t < 0:
        t = t + n
    return t

def point_size(point):
    # Функция определения разрядности точки
    return (512 // 8) if point.bit_length() > 256 else (256 // 8)

def hexenc(data):
    #Функция перевода в шестнадцатеричную систему исчисления
    return _hexencoder(data)[0].decode("ascii")

def hexdec(data):
    #Функция перевода из шестнадцатеричной системы исчисления
    return _hexdecoder(data)[0]

def bytes2long(raw):
    # Перевод бинарной строки в число
    return int(hexenc(raw), 16)

def long2bytes(n, size=32):
    # Перевод числа в бинарную строку
    res = hex(int(n))[2:].rstrip("L")
    if len(res) % 2 != 0:
        res = "0" + res
    s = hexdec(res)
    if len(s) != size:
        s = (size - len(s)) * b"\x00" + s
    return s

# Стартовые параметры эллиптической кривой согласно ГОСТ 34.10-2012
p=bytes2long(hexdec("8000000000000000000000000000000000000000000000000000000000000431"))    #Простое число
q=bytes2long(hexdec("8000000000000000000000000000000150FE8A1892976154C59CFC193ACCF5B3"))    #Порядок подгруппы группы точек эллиптической кривой
a=bytes2long(hexdec("0000000000000000000000000000000000000000000000000000000000000007"))    #Коэффициент эллиптической кривой
b=bytes2long(hexdec("5FBFF498AA938CE739B8E022FBAFEF40563F6E6A3472FC2A514C0CE9DAE23B7E"))    #Коэффициент эллиптической кривой
x=bytes2long(hexdec("0000000000000000000000000000000000000000000000000000000000000002"))    #Координата х точки P
y=bytes2long(hexdec("08E2A8A0E65147D4BD6316030E16D19C85C97F0A9CA267122B96ABBCEA7E8FC8"))    #Координата y точки P
prv = bytes2long(hexdec("7A929ADE789BB9BE10ED359DD39A72C11B60961F49397EEE1D19CE9891EC3B28"))    #Ключ подписи  

def pos(v):
    # Перевод отрицательного числа в положительное
    if v < 0:
        return v + p
    return v

def _add(p1x, p1y, p2x, p2y):
    # Функция сложения точек
    if p1x == p2x and p1y == p2y:
        t = ((3 * p1x * p1x + a) * modinvert(2 * p1y, p)) % p
    else:
        tx = pos(p2x - p1x) % p
        ty = pos(p2y - p1y) % p
        t = (ty * modinvert(tx, p)) % p
    tx = pos(t * t - p1x - p2x) % p
    ty = pos(t * (p1x - tx) - p1y) % p
    return tx, ty

def exp(degree, xx=None, yy=None):
    # Функция вычисления координат кратной точки
    xx = xx or x
    yy = yy or y
    tx = xx
    ty = yy
    if degree == 0:
        raise ValueError("Bad degree value")
    degree -= 1
    while degree != 0:
        if degree & 1 == 1:
            tx, ty = _add(tx, ty, xx, yy)
        degree = degree >> 1
        xx, yy = _add(xx, yy, xx, yy)
    return tx, ty

# Генерация публичного ключа из приватного
pub=exp(prv)
size = point_size(pub[0])
final_pub=(long2bytes(pub[1], size) + long2bytes(pub[0], size))[::-1]

size = point_size(p)
# Информация, которая будет подписываться
digest=b"Default Message"
print("Исходное сообщение:")
print(digest)

# Процедура подписи информации
e = bytes2long(digest) % q #Вычисление числа e, являющееся двоичным представлением исходного сообщения и числа альфа
if e == 0:
    e = 1
rand=None    

while True:
    rand = urandom(size) 
    k = bytes2long(rand) % q #Генерация случайного числа k
    if k == 0:
        continue

    r, _ = exp(k)  #Вычисление координаты х точки эллиптической кривой C=kP
    r %= q
    if r == 0:
        continue

    s = (prv*r + k*e) % q #Вычисление значения s
    if s == 0:
        continue
    break
signed_data = long2bytes(s, size) + long2bytes(r, size) #Получение подписи через конкатенацию значений r и s

print("Итоговая цифровая подпись:")
print((hexenc(signed_data)))


# Процедура проверки подписи
size = point_size(p)
if len(signed_data) != size * 2:
    raise ValueError("Invalid signed_data length")
s = bytes2long(signed_data[:size]) #Вычисление значений s и r по значению подписи и проверка их верности
r = bytes2long(signed_data[size:])
if r <= 0 or r >= q or s <= 0 or s >= q:
    print("Подпись не верна")

e = bytes2long(digest) % q #Вычисление числа e, являющееся двоичным представлением исходного сообщения и числа альфа
if e == 0:
    e = 1

v = modinvert(e, q) #Вычисление числа v

z1 = s * v % q      #Вычисление чисел z1 и z2
z2 = q - r * v % q

p1x, p1y = exp(z1) 					#Вычисление координаты точки C1=z1P
q1x, q1y = exp(z2, pub[0], pub[1])  #Вычисление координаты точки C2=z2Q

# Вычисление координаты С=С1+С2
lm = q1x - p1x 
if lm < 0:
    lm += p
lm = modinvert(lm, p)
z1 = q1y - p1y
lm = lm * z1 % p
lm = lm * lm % p
lm = lm - p1x - q1x
lm = lm % p
if lm < 0:
    lm += p
lm %= q

# Проверка подписи
if lm==r:
 	print("Подпись верна")
else:
	print("Подпись не верна")