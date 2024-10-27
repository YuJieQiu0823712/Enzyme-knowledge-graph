"""
Download relevant data for GraphDB

Author:         Jaldert François    
Contact:        jaldert.francois@kuleuven.be
Creation date:  2023-09-18
Organization:   KU Leuven, CSB-ESAT/STADIUS
"""
from pathlib import Path
import json


class GetData:
    def __init__(self) -> None:
        # get data directory from config file
        config_file = Path(__file__).parent.parent / 'config.json'
        with open(config_file, 'r') as f:
            config = json.load(f)
        self._data_dir = Path(config['data_dir'])
        # set urls for data download
        self._url_Struct_AFDBclustTax = 'https://afdb-cluster.steineggerlab.workers.dev/1-AFDBClusters-entryId_repId_taxId.tsv.gz'
        self._url_Struct_AFDBclustMembers = 'https://afdb-cluster.steineggerlab.workers.dev/5-allmembers-repId-entryId-cluFlag-taxId.tsv.gz'
        self._url_Struct_allVSall = 'https://afdb-cluster.steineggerlab.workers.dev/6-all-vs-all-similarity-queryId_targetId_eValue.tsv.gz'
        
    
    

if __name__ == '__main__':
    data_download_obj = GetData()
    print(data_download_obj._data_dir)