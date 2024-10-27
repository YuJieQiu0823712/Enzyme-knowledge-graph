import pandas as pd
import streamlit as st
import neo4j
from neo4j import GraphDatabase


def main():
    # Replace with your uri, username and password
    uri = "bolt://localhost:7687/ibp"
    username = "neo4j"
    password = "12345678"
    # Connect to the database
    driver = GraphDatabase.driver(uri, auth=(username, password))
    db = "ibp"
    session = driver.session(database=db)


    # Streamlit app content
    st.title("Enzyme Tool")

    query = st.text_input("Enter a Cypher query:")
    if st.button("Run Query"):
        results = session.run(query).to_df(expand=True)
        st.table(results)


if __name__ == "__main__":
    main()



