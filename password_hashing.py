from cryptography.fernet import Fernet

key = 'fp7vxG1YYQKarV8iRGq5uArKSYvPabXs9UzfR53eIss='


def encrypt(password):
    password = memoryview(password.encode('utf-8')).tobytes()
    return Fernet(key).encrypt(password)


def decrypt(password):
    return Fernet(key).decrypt(password).decode()