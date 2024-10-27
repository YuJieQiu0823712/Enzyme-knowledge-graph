# Some heads-up

* Please save the two bash files in a directory on your Windows (typically located at "C:\Users\user_name"), not in the Linux subsystem. 
  To find the directory path, you can copy and paste the following code below `def main():` in Streamlit_final.py:     

    `command="wsl pwd"`

    `result, stdout, stderr = runWSL(command)`
    
    `st.code(stdout, language="text")`


* Make sure to edit line 37 of the search_pipeline.sh file. 
  Replace "SwissProt.fasta" with the actual file path of your Swiss-Prot database fasta file.


