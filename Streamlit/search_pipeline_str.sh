#!/bin/bash

# Check if an argument (file name) is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_name2>"
    exit 1
fi

# Extract the file name from the command-line argument
file_name2="$1"

if [ ! -e "foldseek_search" ]; then
    "mkdir foldseek_search"
fi


if [ ! -e "foldseek_DB" ]; then
    echo "Creating target database..."
    foldseek databases Alphafold/Swiss-Prot foldseek_DB tmpDir
    result=$?
    if [ $result -eq 0 ]; then
        echo "Finish creating target database!"
    else
        echo "Creating target database failed with error:"
    fi
fi

entry_name=$(basename "$file_name2" .pdb | awk -F. '{print $1}')
foldseek easy-search $file_name2 foldseek_DB foldseek_search/"$entry_name" tmp

# Add header to the result file
echo -e 'Query\tTarget\tIdentity%\tAlignment_Length\t#Mismatches\t#Gaps\tStart_position(query)\tEnd_position(query)\tStart_position(target)\tEnd_position(target)\tE-value\tBit_score' > header.txt

# Concatenate header and result files
cat header.txt foldseek_search/"$entry_name" > foldseek_search/"$entry_name"_header

# Use awk to format the output with tabs
awk -v OFS='\t' '{$1=$1; print}' foldseek_search/"$entry_name"_header > foldseek_search/"$entry_name"_header_tab

