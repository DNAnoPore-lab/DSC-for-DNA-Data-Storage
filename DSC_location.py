# The code is used to process DNA sequence data, with functions including: randomly generating sequences without specific repeated patterns (such as "CCC", "AAAA", "TTTT"); 
# filtering sequences with specific base ratios; selecting and comparing sequences using the longest common substring method, removing sequences that contain specific substrings or have too high a similarity with other sequences.
# Finally, output the DNA sequences that meet the criteria for further analysis.

import random
import pandas as pd
import openpyxl


input= []
input2=[]
input3=[]
# long is the length per strand.
long=21
# 'numbers' is how many strands per group
numbers=200000
wb = openpyxl.load_workbook('0.xlsx')
sheet = wb.active
# If 'long' and 'numbers' increase, appropriately scale up the loop parameters.
for i in range(9999999):
    string = ""
    for j in range(21):
        char = random.choice(["A", "C", "T"])
        string += char
        # Ensure that there are no occurrences of "CCC", "AAAA", or "TTTT"
        if string.find("CC"):
            char1 = random.choice(["A", "T"])
            string += char1
        if string.find("AAA"):
            char2 = random.choice(["C", "T"])
            string += char2
        if string.find("TTT"):
            char3 = random.choice(["A", "C"])
            string += char3
    input.append(string[0:long])

# Control the amount
for k in range (8000000):
    if input[k].count("A") <= 6 and input[k].count("C") <= 9 and input[k].count("T") <= 6 and input[k].count("A") >= 4 and input[k].count("C") >= 7 and input[k].count("T") >= 4:
        input2.append(input[k])
for q in range(numbers):
    sheet.cell(row=i + 1, column=1).value = input2[q]

import pandas as pd
df = pd.read_excel('1.xlsx')
# Get data from a specific column
column_name = 'Sequence'
data= df[column_name].values
input=[]
for i in range(47660):
    if data[i].find("CCC")==-1 and data[i].find("AAAA")==-1 and data[i].find("TTTT")==-1:
        input.append(data[i])
l=len(input)
for i in range(l):
    print(input[i])

import pandas as pd
def getNumofCommonSubstr(str1, str2):
    lstr1 = len(str1)
    lstr2 = len(str2)
    record = [[0 for i in range(lstr2 + 1)] for j in range(lstr1 + 1)]
    # The extra position avoids out-of-bounds issues
    maxNum = 0  # The maximum match length
    p = 0  # The starting position of the match
    for i in range(lstr1):
        for j in range(lstr2):
            if str1[i] == str2[j]:
                # Accumulate if they are the same
                record[i + 1][j + 1] = record[i][j] + 1
                if record[i + 1][j + 1] > maxNum:
                    # Get the maximum match length
                    maxNum = record[i + 1][j + 1]
                    # Record the end position of the maximum match length
                    p = i + 1
    return str1[p - maxNum:p]
df = pd.read_excel('2.xlsx')
# Get data from a specific column
column_name = 'Sequence'
data= df[column_name].values
inputs=[]
for i in range(12477):
        str1 = data[i]
        str2=str1[::-1]
        res  = getNumofCommonSubstr(str1, str2)
        if len(res) >5 and len(res)<21 and res.find("C")==-1:
            data[i]=""
for i in range(12477):
    print(data[i])

import pandas as pd
def getNumofCommonSubstr(str1, str2):
    lstr1 = len(str1)
    lstr2 = len(str2)
    record = [[0 for i in range(lstr2 + 1)] for j in range(lstr1 + 1)]
    maxNum = 0  # The maximum match length
    p = 0  # The starting position of the match
    for i in range(lstr1):
        for j in range(lstr2):
            if str1[i] == str2[j]:
                # Accumulate if they are the same
                record[i + 1][j + 1] = record[i][j] + 1
                if record[i + 1][j + 1] > maxNum:
                    # Get the maximum match length
                    maxNum = record[i + 1][j + 1]
                    # Record the end position of the maximum match length
                    p = i + 1
    return str1[p - maxNum:p]
df = pd.read_excel('3.xlsx')

# Get data from a specific column
column_name = 'Sequence'
data= df[column_name].values
inputs=[]
for i in range 41302:
    j=i+1
    for j in range(41302):
        str1=str(data[i])
        str2=str(data[j])
        res = getNumofCommonSubstr(str1, str2)
        if  len(res) >6 and len(res)<18:
            data[j]=""
for i in range 41302:
    print(data[i])

import pandas as pd
def getNumofCommonSubstr(str1, str2):
    lstr1 = len(str1)
    lstr2 = len(str2)
    record = [[0 for i in range(lstr2 + 1)] for j in range(lstr1 + 1)]
    maxNum = 0  # The maximum match length
    p = 0  # The starting position of the match
    for i in range(lstr1):
        for j in range(lstr2):
            if str1[i] == str2[j]:
                # Accumulate if they are the same
                record[i + 1][j + 1] = record[i][j] + 1
                if record[i + 1][j + 1] > maxNum:
                    # Get the maximum match length
                    maxNum = record[i + 1][j + 1]
                    # Record the end position of the maximum match length
                    p = i + 1
    return str1[p - maxNum:p]

# Comparison and selection
df = pd.read_excel('3.xlsx')
df2= pd.read_excel('4.xlsx')
column_name = 'Sequence'
data= df[column_name].values
data2=df2[column_name].values
inputs=[]
for i in range(12477):
    for j in range(30):
        str1=str(data[i])
        str2=str(data2[j])
        res = getNumofCommonSubstr(str1, str2)
        if  len(res) >5 and len(res)<18:
            data[i]=""
for i in range 12477:
    print(data[i])
