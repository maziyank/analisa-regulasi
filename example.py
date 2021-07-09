from inaregParser import UUParser

test_UU = UUParser('sample3.pdf')
print("Judul:", test_UU.get_title())
print("\n")
print("Konsideran Menimbang:", test_UU.get_phylosophical_consideration())
print("\n")
print("Dasar Hukum:", test_UU.get_legal_consideration())
print("\n")
print("Full Text:", test_UU.get_text())