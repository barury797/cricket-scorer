math = input("MATH! ")

x,y,z = math.split()

x = float(x)
z = float(z)
if y == "+": print(x + z)
if y == "-": print(x - z)
if y == "*": print(x * z)
if y == "/": print(x / z)
