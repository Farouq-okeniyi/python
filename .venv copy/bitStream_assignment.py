def word_to_bit_stream(word: str) -> str:
    bit_stream = ''
    
    for char in word:
        ascii_code = ord(char)

        binary_code = format(ascii_code, '08b')
        
        bit_stream += binary_code
    
    return bit_stream

word = input("please Input the word you want to convert to bit stream: ")
bit_stream = word_to_bit_stream(word)

print(f"Word: {word}")
print(f"Bit Stream: {bit_stream}")
