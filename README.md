## Indonesian Regulation Text Parser.

_(Pengurai Teks Regulasi Indonesia)._

### 1. Bill Parser (Undang-Undang)

For optimal result, we recommend to load a bill published in Official Gazette (peraturan.go.id).

The parser currently support:

- General Info (Number, Year, Enacment)
- Title
- Philosophical Considerations (Konsideran Menimbang)
- Legal Considerations (Konsideran Mengingat)
- Definitions
- Phrases
- Heading

```python

from inaregParser import UUParser

test_UU = UUParser('sample/sample4.pdf')
print("Judul:", test_UU.title)
print("\n")
print("Konsideran Menimbang:", test_UU.philosophical_consideration)
print("\n")
print("Dasar Hukum:", test_UU.legal_consideration)
print("\n")
print("Token:", test_UU.get_words(40))
print("\n")
print("Definitions:", test_UU.definitions)
print("\n")
print("Info:", test_UU.info)
print("\n")
print("Heading:", test_UU.heading)


```
