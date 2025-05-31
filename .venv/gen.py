from Crypto.PublicKey import ECC

private_key = ECC.generate(curve='P-256')

with open("ecc_private.pem", "wt") as f:
    f.write(private_key.export_key(format='PEM'))

with open("ecc_public.pem", "wt") as f:
    f.write(private_key.public_key().export_key(format='PEM'))
