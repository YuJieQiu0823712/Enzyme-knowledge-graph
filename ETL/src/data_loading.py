# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 15:52:14 2023

-> see import_data_clean.py - this is a modification with a speed test (and some other minor changes)

@author: jenny
@modified by: Jaldert François - jaldert.francois@kuleuven.be
"""
# always add imports at the top of the file
import logging
import time
import pandas as pd
from tqdm import tqdm
from neo4j import GraphDatabase


# configure logging file, default location is the running directory
def configure_logging(log_file_path: str = "progress.log"):
    """
    Setup logging file to track progress and errors
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )


# CHECK FUNCTION
def check_cluster_uniqueness(cluster_file):
    """
    Check if entries in cluster file only belong to one cluster.
    """
    # Load the cluster data
    cluster_data = pd.read_table(cluster_file, sep='\t', header=None)

    # Perform the checks
    total_entries = len(cluster_data.iloc[:, 1])
    unique_entries = len(cluster_data.iloc[:, 1].drop_duplicates())

    # If the numbers are not equal, log a warning
    if unique_entries != total_entries:
        logging.warning(f"Inconsistency found in {cluster_file}: Expected unique entries to match the total number of entries, but got {unique_entries} unique entries and {total_entries} total entries.")
    else:
        logging.info(f"All entries in {cluster_file} are unique.")


# fasta file parser
def parse_fasta_to_df(fasta_path: str) -> pd.DataFrame:
    """
    Parses a FASTA file and converts it into a pandas DataFrame with two columns: 'ID' and 'Sequence'.
    """
    # Define empty lists to store IDs and sequences
    ids = []
    sequences = []

    # Open the FASTA file and read its contents
    with open(fasta_path, 'r') as fasta_file:
        current_id = None
        current_sequence = []
        for line in fasta_file:
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
    return df


def load_cluster_data(cluster_file):
    cluster = pd.read_table(cluster_file, sep='\t', header=None)
    cluster.columns = ['representatives', 'members']
    representatives = pd.DataFrame(cluster['representatives'].unique(), columns=['representatives'])
    return cluster, representatives


def split_ec_numbers(df):
    split_data = {'Entry': [], 'EC number': []}
    for Entry, EC in zip(df['Entry'], df['EC number']):
        if pd.notna(EC):
            EC_list = EC.split('; ')
            split_data['Entry'].extend([Entry] * len(EC_list))
            split_data['EC number'].extend(EC_list)
    return pd.DataFrame(split_data)


def add_property_to_nodes(tx, label, identifier, property_name, property_value):
    query = (
        f"MATCH (n:{label} {{{identifier}: $identifier}}) "
        f"SET n.{property_name} = $property_value"
    )
    tx.run(query, identifier=identifier, property_value=property_value)


# Function to add a property to enzyme nodes
def add_property_to_enzyme_nodes(session, df, property_name):
    start_time = time()
    for _, row in tqdm(df.iterrows(), total=df.shape[0]):
        Entry = row['ID']
        property_value = row[property_name]
        if Entry in df['Entry'].values:
            session.write_transaction(add_property_to_nodes, 'Enzyme', Entry, property_name, property_value)
    end_time = time()
    logging.info(f"Property {property_name} added to Enzyme nodes. Time taken: {end_time - start_time:.2f} seconds")


# Function to add a property to organism nodes
def add_property_to_organism_nodes(session, subswiss_uni, property_name):
    start_time = time()
    for _, row in tqdm(subswiss_uni.iterrows(), total=subswiss_uni.shape[0]):
        Organism = row['Organism']
        property_value = row[property_name]
        session.write_transaction(add_property_to_nodes, 'Organism', Organism, property_name, property_value)
    end_time = time()
    logging.info(f"Property {property_name} added to Organism nodes. Time taken: {end_time - start_time:.2f} seconds")



def create_enzyme_nodes(tx, enzyme):
    tx.run(
        "CREATE (e:Enzyme {Entry: $Entry, `Entry Name`: $Name, `UniParc`: $UniParc, `AlphaFoldDB`: $AlphaFoldDB, `PDB`: $PDB})",
        Entry=enzyme['Entry'],
        Name=enzyme['Entry Name'],
        UniParc=enzyme['UniParc'],
        AlphaFoldDB=enzyme['AlphaFoldDB'],
        PDB=enzyme['PDB']
    )


def create_organism_nodes(tx, organism):
    tx.run("CREATE (o:Organism {`Organism`: $organism})", organism=organism)


def create_ec_nodes(tx, ec):
    tx.run("CREATE (ecn:ECnumber {`EC number`: $ec})", ec=ec)


def create_enzyme_ec_relationship(tx, Entry, ec):
    tx.run(
        "MATCH (s:Enzyme {Entry: $Entry}), (ecn:ECnumber {`EC number`: $ec}) "
        "CREATE (s)-[:HAS_A]->(ecn)",
        Entry=Entry, ec=ec
    )


def create_enzyme_organism_relationship(tx, Entry, Organism):
    tx.run(
        "MATCH (s:Enzyme {Entry: $Entry}), (t:Organism {Organism: $Organism}) "
        "CREATE (s)-[:BELONGS_TO]->(t)",
        Entry=Entry, Organism=Organism
    )


def create_cluster_nodes(tx, Cluster):
    tx.run("CREATE (c:Cluster {`Cluster`: $Cluster})", Cluster=Cluster)


def create_enzyme_cluster_relationship(tx, Entry, Cluster):
    tx.run(
        "MATCH (e:Enzyme {Entry: $Entry}), (c:Cluster {Cluster: $Cluster}) "
        "CREATE (e)-[:IS_IN]->(c)",
        Entry=Entry, Cluster=Cluster
    )


# CHANGE PATHS TO YOUR OWN PATHS
# CHANGE DB CONFIGURATION
# ENTRY/START TO RUN THE CODE!!!
def main():
    # Configure logging file
    configure_logging() 
    
    ##### CHANGE DB CONFIG #####
    # Database connection parameters
    URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "12345678")
    ##### CHANGE DB NAME #####
    DATABASE_NAME = 'tmp'

    ##### CHANGE FILE PATHS #####
    directory_path = "" # leave empty - otherwise ADD '/' at the end
    swiss_path = f'{directory_path}uniprotkb_reviewed_true_2023_10_18.tsv'
    fasta_path = f'{directory_path}SwissProt.fasta'
    cluster_file_path = f'{directory_path}clusters/MMseqs2_cluster_0.80.tsv'
    cluster_file_099 = f'{directory_path}MMseqs2_Cluster_0.99.tsv'
    cluster_file_080 = f'{directory_path}MMseqs2_Cluster_0.80.tsv'

    # Load data
    swiss_df = pd.read_table(swiss_path, sep='\t')
    ##### REMOVE SLICING FOR FULL DATA #####
    subswiss = swiss_df.iloc[0:25]
    # Additional operations to be added to the main function
    split_df = split_ec_numbers(subswiss)
    fasta_df = parse_fasta_to_df(fasta_path)  # Assuming this function is defined
    cluster_data, representatives = load_cluster_data(cluster_file_path)
    
    # Perform checks
    check_cluster_uniqueness(cluster_file_099)
    check_cluster_uniqueness(cluster_file_080)


    # Start the database operations
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        # check connection
        driver.verify_connectivity()
        with driver.session(database=DATABASE_NAME) as session:
            # Create unique Enzyme nodes
            logging.info("Starting to create Enzyme nodes.")
            start_time = time.time()
            for _, row in tqdm(subswiss.iterrows(), total=subswiss.shape[0]):
                session.write_transaction(create_enzyme_nodes, row)
            end_time = time.time()
            logging.info(f"Finished creating Enzyme nodes. Time taken: {end_time - start_time:.2f} seconds")
            
            # Add sequence property to Enzyme nodes
            add_property_to_enzyme_nodes(session, fasta_df, 'Sequence')

            # Create unique Organism nodes
            logging.info("Starting to create Organism nodes.")
            start_time = time.time()
            subswiss_uni = subswiss.drop_duplicates(subset=["Organism"])
            for organism in subswiss_uni['Organism']:
                session.write_transaction(create_organism_nodes, organism)
            end_time = time.time()
            logging.info(f"Finished creating Organism nodes. Time taken: {end_time - start_time:.2f} seconds")

            # Add Organism ID property to Organism nodes
            subswiss_uni_id = subswiss.drop_duplicates(subset=["Organism (ID)"])
            add_property_to_organism_nodes(session, subswiss_uni_id, 'Organism (ID)')
            
            # Create EC nodes
            logging.info("Starting to create EC nodes.")
            start_time = time.time()
            split_df_uni = split_df.drop_duplicates(subset=["EC number"])
            for ec in split_df_uni['EC number']:
                session.write_transaction(create_ec_nodes, ec)
            end_time = time.time()
            logging.info(f"Finished creating EC nodes. Time taken: {end_time - start_time:.2f} seconds")

            # Create Enzyme-EC relationships
            logging.info("Starting to create Enzyme-EC relationships.")
            start_time = time.time()
            for _, row in split_df.iterrows():
                session.write_transaction(create_enzyme_ec_relationship, row["Entry"], row["EC number"])
            end_time = time.time()
            logging.info(f"Finished creating Enzyme-EC relationships. Time taken: {end_time - start_time:.2f} seconds")
            
            # Create Enzyme-Organism relationships
            logging.info("Starting to create Enzyme-Organism relationships.")
            start_time = time.time()
            for _, row in subswiss.iterrows():
                session.write_transaction(create_enzyme_organism_relationship, row["Entry"], row["Organism"])
            end_time = time.time()
            logging.info(f"Finished creating Enzyme-Organism relationships. Time taken: {end_time - start_time:.2f} seconds")

            # Create Cluster nodes and Enzyme-Cluster relationships
            logging.info("Starting to create Cluster nodes and Enzyme-Cluster relationships.")
            start_time = time.time()
            for _, row in cluster_data.iterrows():
                cluster_id = row['Cluster ID']
                enzyme_entry = row['Entry']
                if enzyme_entry in representatives:
                    session.write_transaction(create_cluster_nodes, cluster_id)
                session.write_transaction(create_enzyme_cluster_relationship, enzyme_entry, cluster_id)
            end_time = time.time()
            logging.info(f"Finished creating Cluster nodes and relationships. Time taken: {end_time - start_time:.2f} seconds")
    logging.info("Database operations completed.")


if __name__ == "__main__":
    main()
