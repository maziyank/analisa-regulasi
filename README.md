## Indonesian Regulation Text Parser.

_(Pengurai Teks Regulasi Indonesia)._

### 1. Bill Parser (Undang-Undang)

For optimal result, we recommend to load a bill published in Official Gazette (peraturan.go.id).

The parser currently support:

- Title
- Philosophical Considerations (Konsideran Menimbang)
- Legal Considerations (Konsideran Mengingat)

```python

from inaregParser import UUParser

test_UU = UUParser('sample3.pdf')
print("Judul:", test_UU.get_title())
print("Konsideran Menimbang:", test_UU.get_philosophical_consideration())
print("Dasar Hukum:", test_UU.get_legal_consideration())
print("Full Text:", test_UU.get_text())


```
