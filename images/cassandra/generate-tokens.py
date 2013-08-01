number = 4

print [((2**64 / number) * i) - 2**63 for i in range(number)]
