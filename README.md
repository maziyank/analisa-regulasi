## Analisa Regulasi

Indonesian Regulation Text Parser.

_(Pengurai Teks Regulasi Indonesia)._

### 1. Bill Parser (Undang-Undang)

Currently support parsing:
- Title
- Pylosophical Considerations (Konsideran Menimbang)
- Legal Considerations (Konsideran Mengingat)

```python

from inaregParser import UUParser

tes_UU = UUParser('sample3.pdf')
print("Judul:", tes_UU.get_title())
print("Konsideran Menimbang:", tes_UU.get_phylosophical_consideration())
print("Dasar Hukum:", tes_UU.get_legal_consideration())
print("Full Text:", tes_UU.get_text())


```
