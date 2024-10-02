import os
import pandas as pd
os.environ["OPENAI_API_KEY"] = ""
os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
os.environ["NEO4J_USERNAME"] = ""
os.environ["NEO4J_PASSWORD"] = ""


from langchain_community.graphs import Neo4jGraph


graph = Neo4jGraph()

file_path_root = "file:///"
cypherquery_type_legal = ["Information", "Right to Data Portability", "Right to Object", "Right to Restrict Processing", "Right to Compensation", "Automated Decision Making and Profiling", "Rectification"]
cypherquery_type_practical = ["Affects content uploaded on products", "AI Training", "Cookies policy", "Opt out", "Usage by Third Parties"]

dict_of_node_file_names = {
                "RightOfInformationAndAccess": "Information",
                "RectificationAndErasure": "Automated Decision Making and Profiling",
                "RightToObject": "Right to Object",
                "RightToCompensation": "Right to Compensation",
                "RightToRestrictProcessing": "Right to Restrict Processing",
                "RightOfDataPortability": "Right to Data Portability",
                "AutomatedDecisionMakingAndProfiling": "Automated Decision Making and Profiling",
                "AITraining": "AI Training",
                "ContentUploadedOnProducts": "Affects content uploaded on products",
                "Cookies": "Cookies policy",
                "OptOut": "Opt out",
                "UsageByThirdParties": "Usage by Third Parties"
            }

dict_of_node_classes = {
                "RightOfInformationAndAccess": "Legal Rights",
                "RectificationAndErasure": "Legal Rights",
                "RightToObject": "Legal Rights",
                "RightToCompensation": "Legal Rights",
                "RightToRestrictProcessing": "Legal Rights",
                "RightOfDataPortability": "Legal Rights",
                "AutomatedDecisionMakingAndProfiling": "Legal Rights",
                "AITraining": "Practical Rights",
                "ContentUploadedOnProducts": "Practical Rights",
                "Cookies": "Practical Rights",
                "OptOut": "Practical Rights",
                "UsageByThirdParties": "Practical Rights"
}

list_of_node_names = list(dict_of_node_file_names.keys())

dict_of_class_names = {"PracticalRights" : "Practical Rights", "LegalRights": "Legal Rights", "PrivacyPolicy": "Privacy Policy"}

list_of_class_names = list(dict_of_class_names.values())



def add_from_csv():
    def lower_node_loader(filenumber, node_lower_name):

        cypher = f"""LOAD CSV WITH HEADERS FROM '{file_path_root}{filenumber}' AS row
    WITH row
    WHERE NOT toInteger(trim(row.`ID`)) IS NULL
    CALL""" + """ { 
      WITH row
      MERGE""" + f"(n: `{node_lower_name}`" + """{ `id`: toInteger(trim(row.`ID`)) })
      SET n.`id` = toInteger(trim(row.`ID`))
      SET n.`text` = row.`Text`
      SET n.`rationale` = row.`Rationale`
    } IN TRANSACTIONS OF 10000 ROWS;
    """

        return cypher

    def class_loader(filenumber):

        cypher_list = ["", "", ""]
        cypher_list[0] = f"""LOAD CSV WITH HEADERS FROM '{file_path_root}{filenumber}' AS row
WITH row
WHERE NOT row.`Main-combined` IS NULL """ + """
  MERGE (n: `Privacy Policy` { `combined-ID`: row.`Main-combined` })
  SET n.`combined-ID` = row.`Main-combined`
  SET n.`jurisdiction` = row.`Main-jurisdiction`
  SET n.`organisation` = row.`Main-organisation`
  SET n.`policyname` = row.`Main-policyname`"""
        cypher_list[1] =  "LOAD CSV WITH HEADERS FROM " + f"""'{file_path_root}{filenumber}' AS row
WITH row
WHERE NOT toInteger(trim(row.`Legal Right`)) IS NULL""" + """
  MERGE (n: `Legal Rights` { `commonLRid`: toInteger(trim(row.`Legal Right`)) })
  SET n.`commonLRid` = toInteger(trim(row.`Legal Right`))"""

        cypher_list[2] = "LOAD CSV WITH HEADERS FROM" + f"""'{file_path_root}{filenumber}' AS row
WITH row
WHERE NOT toInteger(trim(row.`Practical Right`)) IS NULL""" + """
  MERGE (n: `Practical Rights` { `commonPRiD`: toInteger(trim(row.`Practical Right`)) })
  SET n.`commonPRiD` = toInteger(trim(row.`Practical Right`))
"""
        #print(cypher_list)
        return cypher_list

    def relationship_nodes_loader(filenumber, node_lower_name, class_name):
        if class_name == "Practical Rights":
            target_name = "commonPRiD"
        else:
            target_name = "commonLRid"

        cypher = f"""LOAD CSV WITH HEADERS FROM '{file_path_root}{filenumber}' AS row
""" + """WITH row
MATCH (source: """ + f"`{node_lower_name}`" + """ { `id`: toInteger(trim(row.`ID`)) })
MATCH (target: """ + f"`{class_name}`" +  "{" + f"""`{target_name}`: toInteger(trim(row.`Relationship`))""" + """ })
MERGE (source)-[r: `IS_A`]->(target)"""
        #print(cypher)
        return cypher

    def relationship_class_loader(filenumber):

        cypher_list = ["", ""]

        cypher_list[0] = f"""LOAD CSV WITH HEADERS FROM '{file_path_root}{filenumber}' AS row
WITH row""" + """ MATCH (source: `Legal Rights`{ `commonLRid`: toInteger(trim(row.`Legal Right`)) })
  MATCH (target: `Privacy Policy` { `combined-ID`: row.`Main-combined` })
  MERGE (source)-[r: `OF`]->(target)"""

        cypher_list[1] =  "LOAD CSV WITH HEADERS FROM" + f"""'{file_path_root}{filenumber}' AS row
WITH row""" + """
  MATCH (source: `Practical Rights` { `commonPRiD`: toInteger(trim(row.`Practical Right`)) })
  MATCH (target: `Privacy Policy` { `combined-ID`: row.`Main-combined` })
  MERGE (source)-[r: `OF`]->(target)
"""
        return cypher_list

    #csv_folder_path = input("Give the absolute path of the directory which has all the CSV files to be imported.")

    file_names = os.listdir("")

    print (file_names)
    for file in file_names:
        name = file.split(".csv")[0]
        if name in list_of_node_names:

            filenumber = file
            node_lower_name = dict_of_node_file_names[name]
            cypher = lower_node_loader(filenumber, node_lower_name)
            graph.query(cypher)
        elif name == "MainClass":

            filenumber = file
            cypher_list = class_loader(filenumber)
            for cypher in cypher_list:
                graph.query(cypher)



    ## First need to create nodes then the relationships, hence two separate for loops
    for file in file_names:

        name = file.split(".csv")[0]
        if name in list_of_node_names:

            filenumber = file
            node_lower_name = dict_of_node_file_names[name]
            if node_lower_name in cypherquery_type_legal:
                class_name = "Legal Rights"
            else:
                class_name = "Practical Rights"
            cypher = relationship_nodes_loader(filenumber, node_lower_name, class_name)
            graph.query(cypher)

        elif name == "MainClass":

            filenumber = file
            cypher_list = relationship_class_loader(filenumber)

            for cypher in cypher_list:
                graph.query(cypher)



def execute_cypher(cypherquery):
    df = pd.DataFrame()
    try:
        response = (graph.query(cypherquery))
        # print (response)
        extracted_data = []
        for match in response:
            entry = match['n']
            extracted_data.append(entry)

        # Converting to DataFrame
        df = pd.DataFrame(extracted_data)

        # Displaying the DataFrame
        # print(df)
        error_code = False

        return df, error_code
    except Exception as e:
        response = str(e)
        error_code = True
        print (response)
        return df, error_code

def add_embeddings(path_to_csv_http, name_of_organisation):


    '''type_of_embedding = input("Enter '1' if it is a text embedding that you have provided or '2' if it is a rationale embedding\n")

    if type_of_embedding == "1":
        name_of_property = "textEmbedding"
        name_of_row = "text-embedding"
    else:
        name_of_property = "rationaleEmbedding"
        name_of_row = "rationale-embedding"
    '''

    names_of_properties = ["textEmbedding", "rationaleEmbedding"]
    names_of_rows = ["text-embedding", "rationale-embedding"]

    for i in range (0,2):

        cypherquery = f"""LOAD CSV WITH HEADERS
    FROM '{path_to_csv_http}'
    AS row
    MATCH (pp:`Privacy Policy` """ + "{organisation: " + f"'{name_of_organisation}'" + """})<-[:OF]-(r)<-[:IS_A]-(m {id: toInteger(row.ID)})
    WHERE (r:`Practical Rights` OR r:`Legal Rights`)
    CALL db.create.setNodeVectorProperty(m, """ + f"""'{names_of_properties[i]}', apoc.convert.fromJsonList(row.`{names_of_rows[i]}`))
    RETURN count(*)"""

        graph.query(cypherquery)

def add_vector_indexes():
    names_of_nodes = ["Affects content uploaded on products", "AI Training", "Cookies policy", "Opt out", "Usage by Third Parties"] + ["Information", "Right to Data Portability", "Right to Object", "Right to Restrict Processing", "Right to Compensation", "Automated Decision Making and Profiling", "Rectification", "Automated Decision Making and Profiling"]
    names_of_embedding_properties = ["textEmbedding"]

    for node_name in names_of_nodes:

        for embedding_property in names_of_embedding_properties:

            cypherquery = f"""CREATE VECTOR INDEX textExtracts IF NOT EXISTS
        FOR (n: `{node_name}`) 
        ON n.{embedding_property}""" + """
        OPTIONS { indexConfig : {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}"""

            graph.query(cypherquery)


if __name__ == "__main__":
    path_to_csv_http = input("Enter the URL containing the path to the csv hosted online (HTTP or HTTPS address)")

    name_of_organisation = input(
        "Enter the name of the organisation as is under the Privacy Policy node's property in the Graph\n")

    add_embeddings(path_to_csv_http, name_of_organisation)

    add_vector_indexes()
