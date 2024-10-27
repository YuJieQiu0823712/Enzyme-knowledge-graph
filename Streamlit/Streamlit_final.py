# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 15:52:48 2023

@author: jenny
"""
import streamlit as st
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
import pandas as pd
import json
import subprocess
import os
import re


@st.cache_data
def runWSL(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result, result.stdout, result.stderr


# Function to connect to the Neo4j database
@st.cache_resource
def connect_to_neo4j(uri, username, password):
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        return driver
    except Exception as e:
        st.error(f"Error connecting to Neo4j: {e}")
        return None

# Function to retrieve graph data from Neo4j
@st.cache_data
def get_graph_data(_driver,database):
    query = "MATCH (n)-[r:HAS_A]->(m) RETURN n, r, m "
    with _driver.session(database=database) as session:
        result = session.run(query)
        records = result.data()
        df = pd.DataFrame.from_records(records)
        mgmt_data = df.to_json(orient='values')
        dict_convert = json.loads(mgmt_data)
        return dict_convert
@st.cache_data
def retrieveNodes(_driver,Entry,database):
    query = """
    MATCH (sourceNode {Entry: $entry})-[r]-(relatedNode)
    RETURN sourceNode, r, PROPERTIES(r), relatedNode
    """
    with _driver.session(database=database) as session:
        result = session.run(query,entry=Entry)
        records = result.data()
        df = pd.DataFrame.from_records(records)
        
        for i in range(0,len(df)):
            relationship = df['r'][i][-2]
            df['r'][i] = relationship 

        return df
    
@st.cache_data
def retrieveECnumberDataframe(_driver,Entry,database):
    query_check_selfEC = """
    MATCH (sourceNode {Entry: $entry})-[r:`:HAS_A`]->(self_e:ECNumber)
    RETURN sourceNode,self_e
    """    
    percentages = ['99%', '95%', '90%', '85%', '80%']    
    df_final = pd.DataFrame()
       
    with _driver.session(database=database) as session:
        result = session.run(query_check_selfEC,entry=Entry)
        records = result.data()
        df = pd.DataFrame.from_records(records)
        if not df.empty:
            df_final['Similar sequence']=[df['sourceNode'].apply(extract_entry,key='Entry')[0]]
            df_final['EC number']=[df['self_e'].apply(extract_entry,key='ECNumber')[0]]
        else:
            df_final['Similar sequence']=[Entry]
            df_final['EC number']=None
            
            
        for percentage in percentages:            
            #Cypher doesn't support passing node labels as parameters.
            
            #SequenceCluster
            #Entry has SequenceClusters 
            query = """
            MATCH (sourceNode {Entry: $entry})-[r1:IS_IN {`Identity percentage`: $percentage}]->(c:SequenceCluster)
            MATCH (s:Sequence) -[r2:IS_IN {`Identity percentage`: $percentage}]-> (c)
            RETURN sourceNode, c, s, r2
            """          
            result = session.run(query,entry=Entry,percentage=percentage)
            records = result.data()
            df = pd.DataFrame.from_records(records)
            
            column_name = f'SequenceCluster ({percentage})'
            if not df.empty: #Entry has SequenceCluster.
                query = """
                MATCH (sourceNode {Entry: $entry})-[r1:IS_IN {`Identity percentage`: $percentage}]->(c:SequenceCluster)
                MATCH (s:Sequence) -[r2:IS_IN {`Identity percentage`: $percentage}]-> (c)
                MATCH (s)-[r3:`:HAS_A`]->(e:ECNumber)
                RETURN sourceNode, c, s, r2, e, r3
                """   
                result = session.run(query,entry=Entry,percentage=percentage)
                records = result.data()
                df2 = pd.DataFrame.from_records(records)
                
                if not df2.empty: # and cluster members have EC numbers
                    df_final[column_name]=[sorted(list(extract_entry(df2['s'][i], key='Entry') + ' (' + extract_entry(df2['e'][i], key='ECNumber') + ')' for i in range(len(df2))))]
                else: # cluster members don't EC numbers
                    df_final[column_name]=[sorted(list(extract_entry(df['s'][i], key='Entry')+ ' (None)' for i in range(len(df))))]
                    
            else: # If Entry isn't in any SequenceCluster.
                df_final[column_name]=[['']]
                
  
                
            
            #StructureCluster
            #Entry has StructureCluster
            query = """
            MATCH (sourceNode {Entry: $entry})-[r1:IS_IN {`Identity percentage`: $percentage}]->(c:StructureCluster)
            MATCH (s:Sequence) -[r2:IS_IN {`Identity percentage`: $percentage}]-> (c)
            RETURN sourceNode, c, s, r2
            """          
            result = session.run(query,entry=Entry,percentage=percentage)
            records = result.data()
            df = pd.DataFrame.from_records(records)
            
            column_name = f'StructureCluster ({percentage})'
            if not df.empty:
                query = """
                MATCH (sourceNode {Entry: $entry})-[r1:IS_IN {`Identity percentage`: $percentage}]->(c:StructureCluster)
                MATCH (s:Sequence) -[r2:IS_IN {`Identity percentage`: $percentage}]-> (c)
                MATCH (s)-[r3:`:HAS_A`]->(e:ECNumber)
                RETURN sourceNode, c, s, r2, e, r3
                
                """   
                result = session.run(query,entry=Entry,percentage=percentage)
                records = result.data()
                df2 = pd.DataFrame.from_records(records)
                
                if not df2.empty: # and cluster members have EC numbers
                    df_final[column_name]=[sorted(list(extract_entry(df2['s'][i], key='Entry') + ' (' + extract_entry(df2['e'][i], key='ECNumber') + ')' for i in range(len(df2))))]
                else: # cluster members don't EC numbers
                    df_final[column_name]=[sorted(list(extract_entry(df['s'][i], key='Entry')+ ' (None)' for i in range(len(df))))]
                    
            else:# If Entry isn't in any StructureCluster.
                    df_final[column_name]=[['']]

    return df_final




def columnsToDisplay(df,key):
       
    selected_columns={}
    
    selected_columns['Similar sequence']=st.checkbox('Sequence ID', value=True,key=key+1)
    selected_columns['EC number']=st.checkbox('EC number', value=True,key=key+2)
    
    st.subheader('Which clusters to show:')
    all_clu_columns=st.checkbox(':blue[**Select all clusters**]',key=key+3)
    selected_columns['SequenceCluster']=st.checkbox('Sequence clusters', value=all_clu_columns,key=key+4)
    selected_columns['StructureCluster']=st.checkbox('Structure clusters', value=all_clu_columns,key=key+5)
    
    st.subheader('In which similarity percentage:')
    all_per_columns=st.checkbox(':blue[**Select all percentage**]',key=key+11)
    selected_columns['(99%)']=st.checkbox('99% similarity', value=all_per_columns,key=key+6)
    selected_columns['(95%)']=st.checkbox('95% similarity', value=all_per_columns,key=key+7)
    selected_columns['(90%)']=st.checkbox('90% similarity', value=all_per_columns,key=key+8)
    selected_columns['(85%)']=st.checkbox('85% similarity', value=all_per_columns,key=key+9)
    selected_columns['(80%)']=st.checkbox('80% similarity', value=all_per_columns,key=key+10)   
    
    selected_columns_names = [col_name for col_name, selected in selected_columns.items() if selected]
    
    filtered_df = df.copy()
    combinationlist=[item for item in selected_columns_names if "Cluster" not in item and "%" not in item]
    for item in selected_columns_names:
        if "Cluster" in item:
            for item2 in selected_columns_names:
                if "%" in item2:  # cluster and %
                    combination = f"{item} {item2}"
                    combinationlist=combinationlist+[combination]
    
        
    
    if all_per_columns:
        for item in [item for item in selected_columns.keys() if "%" in item]:
            selected_columns[item]=True
    if all_clu_columns:
        for item in [item for item in selected_columns.keys() if "Cluster" in item]:
            selected_columns[item]=True
    
    filtered_df = filtered_df[combinationlist]
    return filtered_df





    
@st.cache_data    
def extract_entry(dictionary,key):
    return dictionary.get(key, None)

@st.cache_data 
def get_edge_width(identity_percentage):
    if identity_percentage == '99%':
        return 10
    elif identity_percentage == '95%':
        return 8
    elif identity_percentage == '90%':
        return 6
    elif identity_percentage == '85%':
        return 4
    elif identity_percentage == '80%':
        return 2
    else:
        # Default width if not explicitly specified
        return 1
@st.cache_data 
def get_expacy_uri(ec_number):
    return f"https://enzyme.expasy.org/EC/{ec_number}"
@st.cache_data 
def get_brenda_uri(ec_number):
    return f"https://www.brenda-enzymes.org/enzyme.php?ecno={ec_number}"
@st.cache_data 
def get_kegg_uri(ec_number):
    return f"https://www.genome.jp/dbget-bin/www_bget?ec:{ec_number}"

@st.cache_data
def make_graph(df,geneName_show=False):
    nodes=[]
    edges=[]
    
    subject=df['sourceNode'].apply(extract_entry,key='Entry')[0]
    structureClustersNodes=list(df['relatedNode'].apply(extract_entry,key='StructureCluster').dropna().drop_duplicates())
    sequenceClusterNodes = list(df['relatedNode'].apply(extract_entry,key='SequenceCluster').dropna().drop_duplicates())
    organismNodes=list(df['relatedNode'].apply(extract_entry,key='Organism').dropna())    
    ECNumberNodes=list(df['relatedNode'].apply(extract_entry,key='ECNumber').dropna())

    nodes.append(Node(id=subject,label=subject,color='#FDD00F'))
    for i in range(0,len(structureClustersNodes)):
        cluster_name=structureClustersNodes[i]
        label=f'{cluster_name} cluster'
        nodes.append(Node(id=label,label=label,color="#07C1F5"))
    for i in range(0,len(sequenceClusterNodes)):
        cluster_name=sequenceClusterNodes[i]
        label=f'{cluster_name} cluster'
        nodes.append(Node(id=label,label=label,color="#E019AB"))
    nodes.append(Node(id=organismNodes[0],label=organismNodes[0],symbolType='diamond',color='#2DBA42'))
    for i in range(0,len(ECNumberNodes)):
        nodes.append(Node(id=ECNumberNodes[i],label=ECNumberNodes[i],color="#7A2DBA"))
        
        expacy_uri = get_expacy_uri(ECNumberNodes[i])
        brenda_uri = get_brenda_uri(ECNumberNodes[i])
        kegg_uri = get_kegg_uri(ECNumberNodes[i])


        with st.expander(f"The information of EC Number of {subject}."):
            # st.write(
            #     '''
            #     The information of EC Number.
            #     '''  
            #     )
            expasy_logo_url = "https://upload.wikimedia.org/wikipedia/commons/f/fc/Expasy_logo_Homepage.png"                      
            brenda_logo_url = "https://www.brenda-enzymes.org/images/brenda_logo.svg"
            kegg_logo_url = "https://www.genome.jp/Fig/kegg128.gif"

            
             # Use st.columns to display logos in a single row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<a href="{expacy_uri}" target="_blank"><img src="{expasy_logo_url}" alt="Expasy Logo" width="200"></a>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<a href="{brenda_uri}" target="_blank"><img src="{brenda_logo_url}" alt="Brenda Logo" width="200"></a>', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'<a href="{kegg_uri}" target="_blank"><img src="{kegg_logo_url}" alt="Kegg Logo" width="200"></a>', unsafe_allow_html=True)

    
       
    for i in range(0,len(df)):       
        related_node = df.iloc[i]['relatedNode']
        source_entry = df.iloc[i]['sourceNode']['Entry']
      
        if list(related_node)[0]=='StructureCluster':
            r_type = df.iloc[i]['r']
            IP = df.iloc[i]['PROPERTIES(r)']['Identity percentage']
            label= f'{r_type} ({IP})'
            cluster_name=related_node['StructureCluster']
            target=f'{cluster_name} cluster'
            edges.append(Edge(source=source_entry,target=target,label=label, width=get_edge_width(IP)))
        elif list(related_node)[0]=='SequenceCluster':
            r_type = df.iloc[i]['r']
            IP = df.iloc[i]['PROPERTIES(r)']['Identity percentage']
            label= f'{r_type} ({IP})'
            cluster_name=related_node['SequenceCluster']
            target=f'{cluster_name} cluster'
            edges.append(Edge(source=source_entry,target=target,label=label, width=get_edge_width(IP)))
        elif list(related_node)[0]=='Organism':   
            edges.append(Edge(source=source_entry,target=related_node['Organism'],label=df.iloc[i]['r']))
        elif list(related_node)[0]=='ECNumber':   
            edges.append(Edge(source=source_entry,target=related_node['ECNumber'],label=df.iloc[i]['r']))

    return nodes, edges

    
def run_str(uri, username, password,database,key):
    first_container2 = st.container()
    second_container2 = st.container()
    third_container2 = st.container()
    container2 = st.container()
    
    uploaded_file2 = container2.file_uploader(label="Upload the PDB file",type=["pdb"])
    if uploaded_file2 is not None:
        
        file_name2 = uploaded_file2.name
        bytes_data2 = uploaded_file2.read()
        text_data2 = bytes_data2.decode('utf-8')
        
        entry_name2 = file_name2.split('.')[0]
        
        with st.expander('Preview the file '):
            st.text(text_data2)
        css='''
            <style>
            [data-testid="stExpander"] div:has(>.streamlit-expanderContent) {
                overflow: scroll;
                max-height: 200px;
                }
            </style>
            '''
        st.markdown(css, unsafe_allow_html=True)
        
    
        with open(file_name2, "w") as temp_file2:
            temp_file2.write(text_data2)
        
            
    button3 = st.button('Run structure similarity search')
    
    with third_container2:
        if st.session_state.get('Run structure similarity search') != True:
            st.session_state['Run structure similarity search'] = button3
        if st.session_state['Run structure similarity search'] == True: 
            try:
                pipeline_command = f"wsl ./search_pipeline_str.sh {file_name2} "
                column=f"wsl column -t -s $'\t' foldseek_search/{entry_name2}_header_tab | head -n 11"
                count=f"wsl wc -l foldseek_search/{entry_name2}"
                try:
                    with second_container2:
                        st.write("Searching by structure similarity...")

                        runWSL("wsl chmod +x search_pipeline2.sh")
                        runWSL("wsl sed -i 's/\r$//' search_pipeline2.sh")
                        
                        runWSL(pipeline_command) 
                        result4, stdout4, stderr4 = runWSL(column)        
                          #Check if the command was successful
                        if result4.returncode == 0 :
                            # Display the output if successful
                            st.success("Search completed successfully!")                      
                            result,max_value,stderr=runWSL(count)
                            max_value= int(max_value.split(" ")[0])
                            st.write(f"Preview the top 10 similar sequences (total: {max_value}) :")
                            st.code(stdout4, language="text")
                            st.download_button(
                                label="Download data as TSV",
                                data=stdout4,
                                file_name=f'{entry_name2}_foldseek_search_result.tsv',
                                mime='text/tsv',
                                key='download structure similarity tsv'
                            )
                            with first_container2:
                                number = st.number_input('How many target sequences to display',min_value=1,max_value=max_value,step=1 )
                        else:
                        # Display the error message if the command failed
                            st.error(f"Command failed with error:\n{stderr4}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                except UnboundLocalError:
                        pass
            except UnboundLocalError:
                pass
                

            with first_container2:
                button4=st.button('Find/Predict EC number',key=2)
            st.markdown("""---""")    
                
            if st.session_state.get('Find/Predict EC number') != True:
                st.session_state['Find/Predict EC number'] = button4
            if st.session_state['Find/Predict EC number'] == True: 
                try:        
                    with first_container2:
                        st.write('You have selected', number, 'target sequences to display, which are:')
                        subjects = f"wsl awk -v OFS='\t' '{{print $2}}' foldseek_search/{entry_name2} | head -n {number}"
                        result7, stdout7, stderr7 = runWSL(subjects)        
                        if result7.returncode == 0 :
                            # Display the output if successful
                            st.code(stdout7, language="text")
                            st.markdown("""---""")
                            entries = [entry for entry in stdout7.split('\n') if entry.strip()]
                        else:
                        # Display the error message if the command failed
                            st.error(f"Command failed with error:\n{stderr7}")
                except Exception as e:
                    st.error(f"{str(e)}")
                except UnboundLocalError:
                        pass
                
                
                Nodes_list=[]
                Edges_list=[]
                try: 
                    driver = connect_to_neo4j(uri, username, password)
                    pattern = r'AF-(.*?)-F1-model_v4'
                    df=pd.DataFrame()
                    if driver is not None:
                        with first_container2:                                                                                  
                            for entry in entries:
                                entry=re.findall(pattern, entry)[0] 
                                entryNodes = retrieveNodes(driver,entry,database)
                                df_entry = retrieveECnumberDataframe(driver,entry,database)
                                df = pd.concat([df, df_entry], axis=0, ignore_index=True)
        
                                if entry is None:
                                    st.code("No data found for the given sequence.")
                                    driver.close()
                                else:
                                    
                                    Nodes, Edges = make_graph(entryNodes)
                                    for item in Nodes:
                                        if item.id not in [node.id for node in Nodes_list]:
                                            Nodes_list.append(item)
                                    for item in Edges:
                                        if item not in Edges_list:
                                            Edges_list.append(item)
                                            
                            config = Config(width=750,
                                        height=550,
                                        directed=True,
                                        physics=True,
                                        hierarchical=False,
                                        highlightColor='#FF00FF',
                                        nodeHighlightBehavior=True,
                                        node={'labelProperty':'label','renderLabel':False},
                                        edge={'labelProperty': 'label', 'renderLabel': False})

                            driver.close()
                except Exception as e:
                    st.error(f"Can't create graph: {str(e)}")
                except UnboundLocalError:
                    pass
                
                with first_container2:
                    graph_container=st.container()
                    with graph_container:
                        try:
                            agraph(nodes = Nodes_list,edges = Edges_list,config = config)
                        except UnboundLocalError:
                                pass
                    st.markdown("""---""")
        
                    st.header('Select:')                
                    filtered_df=columnsToDisplay(df,key)   
                    st.dataframe(filtered_df)
                    
                    
                    st.download_button(
                        label="Download data as CSV",
                        data=filtered_df.to_csv(index=False).encode('utf-8'),
                        file_name='result_dataframe.csv',
                        mime='text/csv',
                        key='download structure similarity'
                    )
                    st.markdown("""---""")                        
                

    
        
        
    # Cleanup: Delete the temporary file
                
    try:
        os.remove(file_name2)
    except FileNotFoundError:
        pass
    except UnboundLocalError:
        pass




def run_seq(uri, username, password,database,key):
    first_container = st.container()
    second_container = st.container()
    third_container = st.container()
    container = st.container()
        
    uploaded_file = container.file_uploader(label="Upload the fasta file",type=["fasta"])        
    if uploaded_file is not None:
            
        file_name = uploaded_file.name
        bytes_data = uploaded_file.read()
        text_data = bytes_data.decode('utf-8')
            
        entry_name = file_name.split('.')[0]
            
        with st.expander('Preview the file '):
            st.text(text_data)
        css='''
            <style>
            [data-testid="stExpander"] div:has(>.streamlit-expanderContent) {
                overflow: scroll;
                max-height: 200px;
                }
            </style>
            '''
        st.markdown(css, unsafe_allow_html=True)
        
        # Save the uploaded file temporarily
        with open(file_name, "w") as temp_file:
            temp_file.write(text_data)
    else:
        st.cache_data.clear()
    button1 = st.button('Run sequence similarity search')

    with third_container:
        df=pd.DataFrame()        
        if st.session_state.get('Run sequence similarity search') != True:
            st.session_state['Run sequence similarity search'] = button1
        if st.session_state['Run sequence similarity search'] == True: 
            try:
                pipeline_command = f"wsl ./search_pipeline.sh {file_name} "
                column=f"wsl column -t -s $'\t' ResultDB/{entry_name}_header_tab.m8 | head -n 10"
                count=f"wsl wc -l ResultDB/{entry_name}.m8"
                try:
                    st.write("Searching by sequence similarity...")
                    runWSL("wsl chmod +x search_pipeline2.sh | sed -i 's/\r$//' search_pipeline2.sh")
                    runWSL(pipeline_command) 
                    result4, stdout4, stderr4 = runWSL(column)
                    result,max_value,stderr=runWSL(count)
                    max_value= int(max_value.split(" ")[0])
                      #Check if the command was successful
                    if result4.returncode == 0 :
                        # Display the output if successful
                        st.success("Search completed successfully!")
                        st.write(f"Preview the similar sequences (total: {max_value}) :")
                        st.code(stdout4, language="text")
                        entry_name = file_name.split('.')[0]
                        st.download_button(
                            label="Download data as TSV",
                            data=stdout4,
                            file_name=f'{entry_name}_search_result.tsv',
                            mime='text/tsv',
                            key='download ssquence similarity tsv'
                        )
                        
                        with first_container:
                            number = st.number_input('How many target sequences to display',min_value=1,max_value=max_value,step=1 )
                    else:
                    # Display the error message if the command failed
                        st.error(f"head Command failed with error:\n{stderr4}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                except UnboundLocalError:
                    pass
            except UnboundLocalError:
                pass
        
                
            with first_container:    
                button2=st.button('Find/Predict EC number')
            st.markdown("""---""")    

                                
            with second_container:
                if st.session_state.get('Find/Predict EC number') != True:
                    st.session_state['Find/Predict EC number'] = button2
                if st.session_state['Find/Predict EC number'] == True: 
                    try:        
                        with first_container:
                            st.write('You have selected', number, 'target sequences to display, which are:')
                            subjects = f"wsl awk -v OFS='\t' '{{print $2}}' ResultDB/{entry_name}.m8 | head -n {number}"
                            result7, stdout7, stderr7 = runWSL(subjects)        
                            if result7.returncode == 0 :
                                # Display the output if successful
                                st.code(stdout7, language="text")
                                st.markdown("""---""")
                                entries = [entry for entry in stdout7.split('\n') if entry.strip()]
                            else:
                            # Display the error message if the command failed
                                st.error(f"Command failed with error:\n{stderr7}")
                    except Exception as e:
                        st.error(f"{str(e)}")
                    except UnboundLocalError:
                        pass
                
                    
                    
                    Nodes_list=[]
                    Edges_list=[]
                    try:
    
                        driver = connect_to_neo4j(uri, username, password)
                        if driver is not None:
                            with first_container:
                                for entry in entries:                       
                                    entryNodes = retrieveNodes(driver,entry,database)
                                    df_entry = retrieveECnumberDataframe(driver,entry,database)
                                    df = pd.concat([df, df_entry], axis=0, ignore_index=True)
            
                                    if entry is None:
                                        st.code("No data found for the given sequence.")
                                        driver.close()
                                    else:
                                        
                    
                                        Nodes, Edges = make_graph(entryNodes)
                                        for item in Nodes:
                                            if item.id not in [node.id for node in Nodes_list]:
                                                Nodes_list.append(item)
                                        for item in Edges:
                                            if item not in Edges_list:
                                                Edges_list.append(item)
                                                
                                                  
                                config = Config(width=750,
                                            height=550,
                                            directed=True,
                                            physics=True,
                                            hierarchical=False,
                                            highlightColor='#FF00FF',
                                            nodeHighlightBehavior=True,
                                            node={'labelProperty':'label','renderLabel':False},
                                            edge={'labelProperty': 'label', 'renderLabel': False})
                                
                                driver.close()
                    except Exception as e:
                        st.error(f"Can't create graph: {str(e)}")
                    except UnboundLocalError:
                        pass

                        
                    with first_container:
                        graph_container=st.container()
                        with graph_container:
                            try:
                                agraph(nodes = Nodes_list,edges = Edges_list,config = config)
                            except UnboundLocalError:
                                    pass
                                
                        st.markdown("""---""")
                          
                        st.header('Select:')                
                        filtered_df=columnsToDisplay(df,key)   
                        st.dataframe(filtered_df)
                            
                            
                        st.download_button(
                            label="Download data as CSV",
                            data=filtered_df.to_csv(index=False).encode('utf-8'),
                            file_name='result_dataframe.csv',
                            mime='text/csv',
                            key='download sequence similarity'
                        )
                        
                        st.markdown("""---""")
                        
                    
                     
            

        
    
    # Cleanup: Delete the temporary file
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass
        except UnboundLocalError:
            pass

#%%%    
# Streamlit UI
def main():    
    st.title("Enzyme similarity search")
    
    
    # Sidebar for database connection details
    st.sidebar.header("Database Connection")
    uri = st.sidebar.text_input("Enter Neo4j URI (e.g., bolt://localhost:7687)")
    username = st.sidebar.text_input("Enter Username")
    password = st.sidebar.text_input("Enter Password", type="password")
    database = st.sidebar.text_input("Enter Database (default: neo4j)")
    
    if st.sidebar.button("Connect"):
        driver = connect_to_neo4j(uri, username, password)
        if driver is not None:
            st.success("Connected to Neo4j!")
            driver.close()
    
    tab1, tab2 = st.tabs(["Sequence similarity search", "Structure similarity search"])
    with tab1:
        run_seq(uri, username, password, database,10)
        

    with tab2:
        run_str(uri, username, password, database,50)


if __name__ == "__main__":
    main()
    