from inaregParser import UUParser

test_UU = UUParser('sample/uu10-2020bt.pdf')


print("Judul:", test_UU.title)
print("\n")
print("Info:", test_UU.info)
print("\n")
print("Konsideran Menimbang:", test_UU.philosophical_consideration)
print("\n")
print("Dasar Hukum:", test_UU.legal_consideration)
print("\n")
print("Token:", test_UU.get_words(40))
print("\n")
print("Definitions:", test_UU.definitions)
print("\n")
print("Heading:", test_UU.heading)
print("\n")
print("Futher Provision:", test_UU.further_provision)
print("\n")
print("Currency:", test_UU.extract_currency())
print("\n")
print("Percent:", test_UU.extract_percent())
print("\n")
print("Withdraw:", test_UU.extract_withdraw_provision())


