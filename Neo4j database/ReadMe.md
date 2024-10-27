### Import Neo4j database

There are two ways to import the neo4j database.

**Way1:**

1.Open Neo4j Desktop on your computer, select/create a project you would like to store the database. Find the "Reveal files in File Explorer" button on the right hand side and click it to open the folder.

2.Download the "ibp.dump" file on the GitLab and move it the the folder.

3.Now the "ibp.dump" file should appear on the Neo4j Desktop. Move your cursor on it, click the three-dots button on the righthand side. Select "Create new DBMS from dump".

4.Set your own Name and Password and create a DBMS. Start it, then the database should be imported in the neo4j(default).


**Way2:**

1.Open Neo4j Desktop on your computer, select/create a project you would like to store the database.

2.Select/add a local DBMS and start it.

3.Click the three-dots button next to the blue "Open" button on the righthand side. Open folder->Import.

4.Download the "neo4j.zip" on the GitLab and unzip it to the "import" folder.

5.Click the little triangle on the blue "Open" button, select "Terminal".

6.Copy & paste the following code and run it on the terminal. The importing process should finish in 30 seconds without error. 

```bin\neo4j-admin database import full --nodes=import\nodes\sequence_nodes.csv --nodes=import\nodes\ECnodes.csv --nodes=import\nodes\unique_organ_nodes.csv --nodes=import\nodes\unique_species_nodes.csv --nodes=import\nodes\unique_genus_nodes_2.csv --nodes=import\nodes\unique_se_cluster.csv --nodes=import\nodes\unique_str_cluster.csv --relationships=import\relationships\Sequence_ECnodes_relationship.csv --relationships=import\relationships\Sequence_Organism_relationship.csv --relationships=import\relationships\Organism_Species_relationships.csv --relationships=import\relationships\Species_Genus_relationships.csv --relationships=import\relationships\Organism_Genus_relationships.csv --relationships=import\relationships\MMseq_cluster_sequence_relationship_99.csv  --relationships=import\relationships\MMseq_cluster_sequence_relationship_95.csv  --relationships=import\relationships\MMseq_cluster_sequence_relationship_90.csv  --relationships=import\relationships\MMseq_cluster_sequence_relationship_85.csv  --relationships=import\relationships\MMseq_cluster_sequence_relationship_80.csv  --relationships=import\relationships\Foldseek_cluster_sequence_relationship_99.csv --relationships=import\relationships\Foldseek_cluster_sequence_relationship_95.csv --relationships=import\relationships\Foldseek_cluster_sequence_relationship_90.csv --relationships=import\relationships\Foldseek_cluster_sequence_relationship_85.csv --relationships=import\relationships\Foldseek_cluster_sequence_relationship_80.csv --skip-bad-relationships ibp```

7.On the same project, click "Create database" at the bottom. Name the database "ibp" (you can use other name but then you have to change the "ibp" at the end of the code provided above).

8.Click the blue "Open" button, select "ibp" (or your choice) in the drop-down on the left. The database should be imported.       
