# Code/Setup Notes for Enzyme Knowledge Graph

### Notes SETUP

See installations/download instructions for [foldseek](https://github.com/steineggerlab/foldseek#databases). 

1. Get foldseek from the [foldseek_ftp](https://mmseqs.com/foldseek/). For Macos, the download link is https://mmseqs.com/foldseek/foldseek-osx-universal.tar.gz.

Foldseek setup MacOS:

```
# go to directory for installation
cd /Users/legallyoverworked/tools
# get foldweek data
wget https://mmseqs.com/foldseek/foldseek-osx-universal.tar.gz
# unzip and set path to foldseek command
tar xvzf foldseek-osx-universal.tar.gz; export PATH=$(pwd)/foldseek/bin/:$PATH
# remove foldseek .gz file
rm foldseek-osx-universal.tar.gz 
```

2. Download foldseek databases

```
# download swissprot foldseek database
cd /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph/foldseek_alphafold_swissprot_db
foldseek databases Alphafold/Swiss-Prot afdb_swissprot tmp
# download uniprot foldseek database
cd /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph/foldseek_alphafold_db
foldseek databases Alphafold/UniProt afdb_uniprot tmp
# download pdb foldseek database
cd /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph/foldseek_pdb_db
foldseek_pdb_db foldseek databases PDB afdb_pdb tmp
# download alphafold u50 database
cd /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph/foldseek_alphafold_u50_db
foldseek databases Alphafold/UniProt50 afdb_u50 tmp
# download esm clustered 30% database
cd /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph/foldseek_esm30_db
foldseek databases ESMAtlas30 afdb_esm30 tmp
```