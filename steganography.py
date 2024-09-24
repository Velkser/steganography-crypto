# -*- coding: utf-8 -*-
"""steganography.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1D8Cs5VNO51RdyBz2aVv4t2siQWwYtm1K
"""


from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

# from google.colab import userdata

import os
import sys

BMP_HEADER_SIZE = 54

def encode_image(input_img_name, output_img_name, txt_file, degree):
    """
    This function reads text from the txt_file file and encodes it
    by bits from input_img to output_img.
    Because every byte of image can contain maximum 8 bits of information,
    text size should be less than (image_size * degree / 8 - BMP_HEADER_SIZE)

    :param input_img_name: name of 24-bit BMP original image
    :param output_img_name: name of 24-bit BMP encoded image (will create or overwrite)
    :param txt_file: name of file containing text to be encoded in output_img
    :param degree: number of bits from byte (1/2/4/8) that are taken to encode text data in image.
    :return: True if function succeeds else False
    """

    if degree not in [1, 2, 4, 8]:
        print("Degree value can be only 1/2/4/8")
        return False

    text_len = os.stat(txt_file).st_size
    img_len = os.stat(input_img_name).st_size

    if text_len >= img_len * degree / 8 - BMP_HEADER_SIZE:
        print("Too long text")
        return False

    text = open(txt_file, 'r')
    text_txt = encrypt_message(text.read())


    input_image = open(input_img_name, 'rb')
    output_image = open(output_img_name, 'wb')

    bmp_header = input_image.read(BMP_HEADER_SIZE)
    output_image.write(bmp_header)

    text_mask, img_mask = create_masks(degree)

    # while True:
    #     symbol = text.read(1)
    #     if not symbol:
    for symbol in text_txt:
            # break
        symbol = ord(symbol)

        for byte_amount in range(0, 8, degree):
            img_byte = int.from_bytes(input_image.read(1), sys.byteorder) & img_mask
            bits = symbol & text_mask
            bits >>= (8 - degree)
            img_byte |= bits

            output_image.write(img_byte.to_bytes(1, sys.byteorder))
            symbol <<= degree

    output_image.write(input_image.read())

    text.close()
    input_image.close()
    output_image.close()

    return True

def decode_image(encoded_img, output_txt, symbols_to_read, degree, symb_conunt):
    """
    This function takes symbols_to_read bytes from encoded image and retrieves hidden
    information from them with a given degree.
    Because every byte of image can contain maximum 8 bits of information,
    text size should be less than (image_size * degree / 8 - BMP_HEADER_SIZE)

    :param encoded_img: name of 24-bit BMP encoded image
    :param output_txt: name of txt file where result should be written
    :param symbols_to_read: amount of encoded symbols in image
    :param degree: number of bits from byte (1/2/4/8) that are taken to encode text data in image
    :return: True if function succeeds else False
    """
    if degree not in [1, 2, 4, 8]:
        print("Degree value can be only 1/2/4/8")
        return False

    img_len = os.stat(encoded_img).st_size

    if symbols_to_read >= img_len * degree / 8 - BMP_HEADER_SIZE:
        print("Too much symbols to read")
        return False

    text = open(output_txt, 'w', encoding='utf-8')
    text_txt = ""
    encoded_bmp = open(encoded_img, 'rb')

    encoded_bmp.seek(BMP_HEADER_SIZE)

    _, img_mask = create_masks(degree)
    img_mask = ~img_mask

    read = 0
    while read < symb_conunt:
        symbol = 0

        for bits_read in range(0, 8, degree):
            img_byte = int.from_bytes(encoded_bmp.read(1), sys.byteorder) & img_mask
            symbol <<= degree
            symbol |= img_byte

        if chr(symbol) == '\n' and len(os.linesep) == 2:
            read += 1

        read += 1
        # text.write(chr(symbol))
        text_txt += chr(symbol)
    text_txt = decrypt_message(text_txt)
    text.write(text_txt)
    text.close()
    encoded_bmp.close()
    return True

def create_masks(degree):
    """
    Create masks for taking bits from text bytes and
    putting them to image bytes.

    :param degree: number of bits from byte that are taken to encode text data in image
    :return: a mask for a text and a mask for an image
    """
    text_mask = 0b11111111
    img_mask = 0b11111111

    text_mask <<= (8 - degree)
    text_mask %= 256
    img_mask >>= degree
    img_mask <<= degree

    return text_mask, img_mask

def encrypt_message(message ):
    password = userdata.get('password')
    salt = get_random_bytes(16)  # Generating a random salt
    key = PBKDF2(password, salt, 16, count=1000000)  # Generating a key from the password
    cipher = AES.new(key, AES.MODE_CBC)  # Creating a cipher object
    cipher_text = cipher.encrypt(pad(message.encode(), AES.block_size))  # Encrypting the message
    return base64.b64encode(salt + cipher.iv + cipher_text).decode()  # Encoding to base64 and concatenating the data

def decrypt_message(encrypted_message):
    password = userdata.get('password')
    encrypted_data = base64.b64decode(encrypted_message.encode())  # Decoding from base64
    salt = encrypted_data[:16]  # Extracting the salt
    iv = encrypted_data[16:32]  # Extracting the initialization vector
    cipher_text = encrypted_data[32:]  # Extracting the encrypted text
    key = PBKDF2(password, salt, 16, count=1000000)  # Generating the key from the password and salt
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)  # Creating the cipher object with the initialization vector
    decrypted_message = unpad(cipher.decrypt(cipher_text), AES.block_size).decode()  # Decrypting and removing padding
    return decrypted_message

def main():
    text_file = "/content/stegapy/examples/bmp_example/sample.txt"
    degree = 4
    encode_image("/content/stegapy/examples/bmp_example/start.bmp", "/content/stegapy/examples/bmp_example/encoded.bmp", text_file, degree)
    print("Encoded image with degree 4")

    to_read = os.stat(text_file).st_size
    decode_image("/content/stegapy/examples/bmp_example/encoded.bmp", "/content/stegapy/examples/bmp_example/result.txt", to_read, degree, 26284)
    print("Decoded image with degree 4")

if __name__ == "__main__":
    main()

