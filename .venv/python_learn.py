name = "ola"
from math import *
# print(name+" "+name)
# print(floor(4.5))

# name = input("Please input your name:")
# age = input("Please enter number 1: ")
# age2 = input("Please enter number 2: ")
# sum = float(age) + float(age2)
# str(sum)
# print("Welcome to python " + name +" you are "+ age + " Years old" + " sum of age is ")
# print(sum)

#list

# friends = ['ewe', 'qwewewe', 'ewewe']
# import numpy as np
# _array = np.array([2,21,21,21,212,21])
# _array2 = [2,21,21,21,212,21]
# friends.append("_array2")
# # friends.extend(_array2)
# print(friends)
# print(_array)

#couples
# coordinate = (1,2)
# print(coordinate[0])

#functions

# def sayhi(name, age):
#     print("hi " + name + " you are "+ age+ " Years old")


# sayhi("ola", "32")

#Return statement

# def cube(num):
#     cube = num*num*num
#     return cube

# print(cube(4))


# is_male = True
# is_tall = True

# if is_male and is_tall:
#     print("i am male and tall")
# elif is_male and not(is_tall):
#     print("i am a short male")
# elif not(is_male) and is_tall:
#     print("you are not a male but you are tall")

# # if is_male or is_tall:
# #     print("i am male and tall")
# else:
#     print("i am neither male nor tall")


#if with comparison

# def max(num1,num2,num3):
#     if num1>num2 and num1>num3:
#         return num1
#     elif num2>num1 and num2>num3:
#         return num2
#     else:
#         return num3
    
# print(max(20,70,100))

# num1 = float(input("Please input number 1: "))
# opp = input("Enter a operator")
# num2 = float(input("Please input second number: "))

# if opp == '+':
#     print(num1 + num2)
# elif opp == '-':
#     print(num1-num2)
# elif opp =='*':
#     print(num1*num2)
# elif opp == '/':
#     print(num1/num2)
# else:
#     print("Invalid a operator")


#dictionary

# monthConversion = {
#     "jan":"January",
#     "feb":"Febuary",
#     "mar":"march",
#     "apr":"April",
#     "may":"May",
#     "jun":"June",
#     "Jly":"July",
#     "aug":"August",
#     "sept":"September",
#     "oct":"October",
#     "nov":"November",
#     "dec":"December"
# }

# print(monthConversion.get("nov"))

#while Loop

# i= 1
# while i<=10:
#     print(i)

# print("done with loop")

#raise to power

# def num_raise_to_power(num1, power):
#     result =1
#     for i in range(power):
#         result = result*num1
#     return result

# print(num_raise_to_power(2,32))

#object
class Student:
    def __init__(self,name, age):
        self.name = name
        self.age = age
        