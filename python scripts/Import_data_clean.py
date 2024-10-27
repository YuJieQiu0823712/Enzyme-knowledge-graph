# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 15:52:14 2023

@author: jenny
"""

import pandas as pd


swiss = pd.read_table('uniprotkb_reviewed_true_2023_10_18.tsv',sep='\t')

#Use sub-dataset to try out the code
subswiss = swiss.iloc[0:25]




#%%%

from neo4j import GraphDatabase

# create the uri for the connection
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

database='tmp'

with GraphDatabase.driver(URI, auth=AUTH) as driver: 
    driver.verify_connectivity()
    



# %%%


def create_Enzymenodes(tx, Entry, Name,UniParc,AlphaFoldDB,PDB):
    query = "CREATE (s:Enzyme {Entry: $Entry, `Entry Name`: $Name, `UniParc`: $UniParc, AlphaFoldDB: $AlphaFoldDB, PDB: $PDB})"
    tx.run(query, Entry=Entry, Name=Name,UniParc=UniParc,AlphaFoldDB=AlphaFoldDB,PDB=PDB)
    
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in subswiss.iterrows():
            session.write_transaction(create_Enzymenodes, row['Entry'], row['Entry Name'],row['UniParc'], row['AlphaFoldDB'], row['PDB'])

# %%%

# Define a function to add a property to nodes of a certain type
def add_property_to_nodes(tx,label,Entry,property_name,property_value):
    # Cypher query to match nodes of a certain type and set a new property
    query = f"MATCH (n:{label} {{Entry: $Entry}}) SET n.{property_name} = $property_value"    
    tx.run(query,label=label,Entry=Entry,property_name=property_name,property_value=property_value)



# %%%
# add node property: Sequence
# Define empty lists to store IDs and sequences
ids = []
sequences = []

# Open the FASTA file and read its contents
with open('SwissProt.fasta', 'r') as fasta_file:
    lines = fasta_file.readlines()
    current_id = None
    current_sequence = []

    for line in lines:
        if line.startswith('>'):
            # If a new sequence starts, append the previous ID and sequence
            if current_id is not None:
                ids.append(current_id)
                sequences.append(''.join(current_sequence))
            
            # Extract the ID from the line
            current_id = line.split('|')[1]
            
            # Initialize a new sequence list for the current ID
            current_sequence = []
        else:
            # Append sequence lines
            current_sequence.append(line.strip())

    # Append the last ID and sequence
    if current_id is not None:
        ids.append(current_id)
        sequences.append(''.join(current_sequence))

# Create a DataFrame
df = pd.DataFrame({'ID': ids, 'Sequence': sequences})

# Print the DataFrame
print(df)


with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in df.iterrows():
            Entry = row['ID']
            property_value = row['Sequence']
            if Entry in subswiss['Entry'].values:
                session.write_transaction(add_property_to_nodes,'Enzyme',Entry,'Sequence',property_value)




# %%%     
def create_Organismnodes(tx,o):
    query = "CREATE (o:Organism {`Organism`: $o})"
    tx.run(query, o=o)

subswiss_uni=subswiss.drop_duplicates(subset=["Organism"]) 
    
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in subswiss_uni.iterrows():
            session.write_transaction(create_Organismnodes, row['Organism'])  
 
  


def add_property_to_nodes(tx,label,Organism,property_name,property_value):
    # Cypher query to match nodes of a certain type and set a new property
    query = f"MATCH (n:{label} {{Organism: $Organism}}) SET n.{property_name} = $property_value"    
    tx.run(query,label=label,Organism=Organism,property_name=property_name,property_value=property_value)
          
# add node property: Organism ID
subswiss_uni=subswiss.drop_duplicates(subset=["Organism (ID)"]) 
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in subswiss_uni.iterrows():
            Organism = row['Organism'] 
            property_value = row['Organism (ID)']
            session.write_transaction(add_property_to_nodes,'Organism',Organism,'`Organism (ID)`',property_value)
    
    

def add_property_to_nodes(tx,label,Species,property_name,property_value):
    # Cypher query to match nodes of a certain type and set a new property
    query = f"MATCH (n:{label} {{Species: $Species}}) SET n.{property_name} = $property_value"    
    tx.run(query,label=label,Species=Species,property_name=property_name,property_value=property_value)
 
    
 

# %%%
# Split the EC number column based on the delimiter ';' and create a new DataFrame
split_data = {'Entry': [], 'EC number': []}

for Entry, EC in zip(subswiss['Entry'], subswiss['EC number']):
    if pd.notna(EC):
        EC_list = EC.split('; ')
        split_data['Entry'].extend([Entry] * len(EC_list))
        split_data['EC number'].extend(EC_list)

split_data = pd.DataFrame(split_data)

split_data_uni=split_data.drop_duplicates(subset=["EC number"]) 

def create_ECnodes(tx,ec):
    query = "CREATE (ecn:ECnumber {`EC number`: $ec})"
    tx.run(query, ec=ec)
    
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in split_data_uni.iterrows():
            session.write_transaction(create_ECnodes, row['EC number'])



          
          
#use split_data
def create_EnzymeECrelationship(tx, Entry, ec):
    query = (
        "MATCH (s:Enzyme {Entry: $Entry}), (ecn:ECnumber {`EC number`: $ec}) "
        "CREATE (s)-[:HAS_A]->(ecn)"
    )
    tx.run(query, Entry=Entry, ec=ec)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in split_data.iterrows():
            session.write_transaction(create_EnzymeECrelationship, row["Entry"], row["EC number"])



# %%%

def create_EnzymeToxarelationship(tx, Entry, Organism):
    query = (
        "MATCH (s:Enzyme {Entry: $Entry}), (t:Organism {Organism: $Organism}) "
        "CREATE (s)-[:BELONGS_TO]->(t)"
    )
    tx.run(query, Entry=Entry, Organism=Organism)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in subswiss.iterrows():
            session.write_transaction(create_EnzymeToxarelationship, row["Entry"], row["Organism"])







# %%% - Cluster

cluster = pd.read_table('clusters/MMseqs2_cluster_0.80.tsv',sep='\t',header=None)
cluster.columns = ['representatives', 'members']
representatives=pd.DataFrame(cluster['representatives'].unique())
representatives.columns = ['representatives']
# don't know why I have to assign column name twice?!

# #toy cluster example
# cluster = pd.read_table('toy_ex.txt',sep='\t',names=['representative', 'members'])
# representatives=pd.DataFrame(cluster['representative'].unique(),columns=['representative'])


def create_Clusternodes(tx,Cluster):
    query = "CREATE (c:Cluster {`Cluster`: $Cluster})"
    tx.run(query, Cluster=Cluster)
    
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in representatives.iterrows():
            session.write_transaction(create_Clusternodes, row["representative"])


def create_EnzymeClusterrelationship(tx, Entry, Cluster):
    query = (
        "MATCH (s:Enzyme {Entry: $Entry}), (c:Cluster {Cluster: $Cluster}) "
        "CREATE (s)-[:IS_IN]->(c)"
    )
    tx.run(query, Entry=Entry, Cluster=Cluster)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=database) as session:
        for _, row in cluster.iterrows():
            session.write_transaction(create_EnzymeClusterrelationship, row["members"], row["representative"])





# %%%
#Can an enzyme belong to multiple clusters? -->No
Cluster = pd.read_table('MMseqs2_Cluster_0.99/MMseqs2_Cluster_0.99.tsv',sep='\t',header=None)
len(Cluster.iloc[:,1])
len(Cluster.iloc[:,1].drop_duplicates())==len(Cluster.iloc[:,1])

Cluster = pd.read_table('MMseqs2_Cluster_0.80.tsv',sep='\t',header=None)
len(Cluster.iloc[:,1])
len(Cluster.iloc[:,1].drop_duplicates())==len(Cluster.iloc[:,1])




