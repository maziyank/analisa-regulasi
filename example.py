from inaregParser import UUParser

tes_UU = UUParser('sample3.pdf')
print("Judul:", tes_UU.get_title())
print("\n")
print("Konsideran Menimbang:", tes_UU.get_phylosophical_consideration())
print("\n")
print("Dasar Hukum:", tes_UU.get_legal_consideration())
print("\n")
print("Full Text:", tes_UU.get_text())