from inaregParser import UUParser

test_UU = UUParser('sample/sample5.pdf')
print("Judul:", test_UU.get_title())
print("\n")
print("Konsideran Menimbang:", test_UU.get_philosophical_consideration())
print("\n")
print("Dasar Hukum:", test_UU.get_legal_consideration())
print("\n")
print("Token:", test_UU.get_words(40))
print("\n")
print("Definitions:", test_UU.get_definitions())
print("\n")
print("Phrases:", test_UU.get_phrashes(4))