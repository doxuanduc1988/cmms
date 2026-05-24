import bcrypt
import random
import string


def hash_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_random_password(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))
