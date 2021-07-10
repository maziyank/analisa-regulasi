from inaregParser import UUParser

test_UU = UUParser('sample3.pdf')
print("Judul:", test_UU.get_title())
print("\n")
print("Konsideran Menimbang:", test_UU.get_philosophical_consideration())
print("\n")
print("Dasar Hukum:", test_UU.get_legal_consideration())
print("\n")
print("Info:", test_UU.get_words(40))
print("\n")
print("Definitions:", test_UU.get_definitions())