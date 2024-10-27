#!/bin/bash

# Check if an argument (file name) is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_name>"
    exit 1
fi

# Extract the file name from the command-line argument
file_name="$1"


# Check and create directories
mkdir -p QueryDB TargetDB ResultDB

# # Check if the directory "swissprot" does not exist
# if [ ! -d "~/swissprot" ]; then
#     echo "Downloading Swiss-Prot database..."
#     mmseqs databases UniProtKB/Swiss-Prot swissprot tmp
#     result=$?
#     if [ $result -eq 0 ]; then
#         echo "Swiss-Prot database downloaded!"
#         # Display the output if successful
#         # Uncomment and modify the next line as needed
#         # st.code(stdout, language="text")
#     else
#         echo "Command failed with error:"
#         # Display the error message if the command failed
#         # Uncomment and modify the next line as needed
#         # st.error("Command failed with error:\n$stderr")
#     fi
# fi

# Check if the directory "TargetDB/targetDB" does not exist
if [ ! -d "TargetDB/targetDB" ]; then
    echo "Creating target database..."
    mmseqs createdb SwissProt.fasta TargetDB/targetDB
    result=$?
    if [ $result -eq 0 ]; then
        echo "Finish creating target database!"
        # st.code(stdout, language="text")
    else
        echo "Command failed with error:"
        # st.error("Command failed with error:\n$stderr")
    fi
fi

# Check if the file "TargetDB/targetDB.idx" does not exist
if [ ! -e "TargetDB/targetDB.idx" ]; then
    echo "Creating index of target database..."
    mmseqs createindex TargetDB/targetDB tmp
    result=$?
    if [ $result -eq 0 ]; then
        echo "Finish creating index of target database!"
        # st.code(stdout, language="text")
    else
        echo "Command failed with error:"
        # st.error("Command failed with error:\n$stderr")
    fi
fi

entry_name=$(basename "$file_name" .fasta | awk -F. '{print $1}')

mmseqs createdb "$file_name" QueryDB/"$entry_name"
mmseqs search QueryDB/"$entry_name" TargetDB/targetDB ResultDB/"$entry_name" tmp -a
mmseqs convertalis QueryDB/"$entry_name" TargetDB/targetDB ResultDB/"$entry_name" ResultDB/"$entry_name".m8



# Add header to the result file
echo -e 'Query\tTarget\tIdentity%\tAlignment_Length\t#Mismatches\t#Gaps\tStart_position(query)\tEnd_position(query)\tStart_position(target)\tEnd_position(target)\tE-value\tBit_score' > header.txt

# Concatenate header and result files
cat header.txt ResultDB/"$entry_name".m8 > ResultDB/"$entry_name"_header.m8

# Use awk to format the output with tabs
awk -v OFS='\t' '{$1=$1; print}' ResultDB/"$entry_name"_header.m8 > ResultDB/"$entry_name"_header_tab.m8
