# Notes Enzyme Knowledge Graph

Change **data_dir** in config file to directory path for ETL!

- Macbook Air (JaldertPHD drive): /Volumes/JaldertPHD/projects/D_enzyme_knowledge_graph

1. **TODO**: We'll have to decide which additional properties/nodes we want to add.
Adding additional properties/nodes for IDs with crosslinks to other databases
will be necessary!

---
---

**Notes on the Graph Database structure and properties**

## Knowledge Graph Structure

The knowledge graph is a directed graph with sequence similarity based on
[MMseqs2](https://github.com/soedinglab/MMseqs2) and structure similarity based 
on [Foldseek](https://github.com/steineggerlab/foldseek) (See also the 
[Foldseek server](https://search.foldseek.com/search)). Cluster IDs will either
be [UniRef clusters](https://www.uniprot.org/help/uniref) or MMSeq based clusters.
Structural similarity clusters will be based on [Foldseek clusters]
(https://cluster.foldseek.com/). 

### Nodes

There are 5 types of nodes:

1. Sequence
2. Cluster - Sequence
3. Cluster - Structure
4. EC number
5. Taxonomy (1 types)

**Update**: instead of different types of nodes for different taxonomy levels,
we will use a taxonomy type node with property "taxonomy rank" to store the
taxonomy level. This will make later additions of new taxonomy levels easier.

Properties to consider:

1. Taxonomy - Domain (superkingdom)
2. Taxonomy - Kingdom
3. Taxonomy - Phylum
4. Taxonomy - family
5. Taxonomy - genus
6. Taxonomy - species

### Node Types

| Index | Node Type | Description |
| --------- | --------- | ----------- |
| 1 | Sequence | AA sequence Enzymes and Proteins|
| 2 | Cluster - Sequence | Sequence similarity clusters |
| 3 | Cluster - Structure | Structure similarity clusters |
| 4 | EC number | Enzyme Commission number |
| 5 | Taxonomy | Taxonomy |

**Obsolete** node types (see above):

| 5 | Taxonomy - Domain | Domain (superkingdom) |
| 6 | Taxonomy - Kingdom | Kingdom |
| 7 | Taxonomy - Phylum | Phylum |
| 8 | Taxonomy - Family | Family |
| 9 | Taxonomy - Genus | Genus |
| 10 | Taxonomy - Species | Species |

### Node Properties

**Sequence**: store sequence, UniParc ID, UniProt ID, AlphaFold ID, PDB ID, Sequence. 
For **Cluster - Sequence** store cluster ID and percentage identity. **IMPORTANT**: 
identity similarity have lower bounds but not upper bounds! The 90% similarity nodes will contain
sequences with 90% to 100% similarity. The 95% similarity nodes contain sequences that are also part
of the 90% similarity nodes! 
**Cluster - Structure** will store cluster ID and percentage identity (TM-score of the alignment). 
**EC number** will store EC number and Brenda ID (and link) and KEGG ID (and link) and ExpasyEnzyme ID (and link).
Important: for EC numbers there will also be nodes on level 1, 2 and 3 (1, 1.34, 1.34.5) to store only partly annotated EC numbers.
**Taxonomy** will store taxonomy ID, taxonomy name, taxonomy rank, and taxonomy link. (taxonomy rank = phylum, kingdom, etc.)

| Index | Index Node Property | Node Type | Property | Description |
| --------- | --------- | --------- | --------- | ----------- |
| 1 | 1 | Sequence | UniParc ID | UniParc ID |
| 2 | 2 | Sequence | UniProt ID | UniProt ID |
| 3 | 3 | Sequence | AlphaFold ID | AlphaFold ID |
| 4 | 4 | Sequence | PDB ID | PDB ID |
| 5 | 5 | Sequence | Sequence | AA sequence |
| 6 | 1 | Cluster - Sequence | Cluster ID | Cluster ID |
| 7 | 2 | Cluster - Sequence | Percentage identity | Percentage identity |
| 8 | 1 | Cluster - Structure | Cluster ID | Cluster ID |
| 9 | 2 | Cluster - Structure | Percentage identity | Percentage identity - TM-score of the alignment |
| 10 | 1 | EC number | EC number | EC number |
| 11 | 2 | EC number | Brenda ID | Brenda ID |
| 12 | 3 | EC number | Brenda ID link | link to relevant Brenda ECnumber site |
| 13 | 4 | EC number | KEGG ID | KEGG ID |
| 14 | 5 | EC number | KEGG ID link | link to relevant KEGG ECnumber site |
| 15 | 6 | EC number | ExpasyEnzyme ID | ExpasyEnzyme ID |
| 16 | 7 | EC number | ExpasyEnzyme ID link | link to relevant ExpasyEnzyme ECnumber site |
| 17 | 1 | Taxonomy | Taxonomy ID | Taxonomy ID |
| 18 | 2 | Taxonomy | Taxonomy name | Taxonomy name |
| 19 | 3 | Taxonomy | Taxonomy rank | Taxonomy rank = Phylum, superkingdom, etc. |
| 20 | 4 | Taxonomy | Taxonomy link | Taxonomy link |

### Edges

There will be 2 groups of edges, for a total of 3 types of edges:

1. Sequence - Sequence edges
   1. sequence similarity
   2. structure similarity
2. Sequence - Cluster edges
   1. belongs to
3. Sequence - EC number edges
   1. Experimental - belongs to
   2. Homology (SwissProt) - belongs to
   3. Predicted - belongs to
4. Taxonomy - Sequence edges
   1. belongs to

### Edge Types

| Index | Edge Type | Node1 | Node2 | Description |
| --------- | --------- | --------- | --------- | ----------- |
| 1 | Sequence similarity | Sequence | Sequence | Sequence similarity based on MMseqs2 |
| 2 | Structure similarity | Sequence | Sequence | Structure similarity based on Foldseek |
| 3 | Belongs to | Sequence | Cluster - Sequence | Sequence belongs to cluster |
| 4 | Belongs to | Sequence | Taxonomy | Sequence belongs to taxonomy |
| 5 | Experimental | Sequence | EC number | Sequence has experimental EC number |
| 6 | Homology (SwissProt) | Sequence | EC number | Sequence has homology based EC number |
| 7 | Predicted | Sequence | EC number | Sequence has predicted EC number |
| 8 | Belongs to | Taxonomy | Sequence | Taxonomy belongs to sequence |

### Edge Properties

**Sequence similarity** will store e-val, bit-score, alignemnt length and sequence identity.
**Structure similarity** will store TM-score, Probability, TM-score query length normalized, TM-score target length normalized.
**Belongs to (Sequence - Cluster)** and **Belongs to (Sequence - Taxonomy)** do not contain any properties.
**Experimental** and **Homology (SwissProt)** will not contain any properties. 
**Predicted** will store a property called "method" that will contain the method used to predict the EC number.

| Index | Index Edge Property | Edge Type | Property | Description |
| --------- | --------- | --------- | --------- | ----------- |
| 1 | 1 | Sequence similarity | e-val | e-value of the alignment |
| 2 | 2 | Sequence similarity | bit-score | bit-score of the alignment |
| 3 | 3 | Sequence similarity | alignment length | alignment length |
| 4 | 4 | Sequence similarity | sequence identity | sequence identity |
| 5 | 1 | Structure similarity | TM-score | TM-score of the alignment |
| 6 | 2 | Structure similarity | Probability | RProbability same SCOPe family|
| 7 | 3 | Structure similarity | TM-score query length | TM-score normalised for query length |
| 8 | 4 | Structure similarity | TM-score target length | TM-score normalised for target length |
| 9 | 1 | Belongs to (Sequence - Cluster) | NA | NA |
| 10 | 1 | Belongs to (Sequence - Taxonomy) | NA | NA |
| 11 | 1 | Experimental | NA | NA |
| 12 | 1 | Homology (SwissProt) | NA | NA |   
| 13 | 1 | Predicted | method | method used to predict the EC number |

---
---

