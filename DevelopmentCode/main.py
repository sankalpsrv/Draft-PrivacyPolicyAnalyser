
import pandas as pd
from langchain_community.graphs import Neo4jGraph

from exampleprompts import example_questions_dict
from cypherprompts import cypherpromptgeneration
from DBMSops import execute_cypher
import ast
import os
import numpy as np
os.environ["OPENAI_API_KEY"] = ""

from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings

from sklearn.metrics.pairwise import cosine_similarity

graph = Neo4jGraph()
def convert_to_array(embedding_str):
    try:
        # Strip the string of unnecessary whitespace or newlines
        embedding_str = embedding_str.strip()

        # Safely evaluate the string to a Python list
        embedding_list = ast.literal_eval(embedding_str)

        # Convert the list to a NumPy array of floats
        return np.array(embedding_list, dtype=float)
    except (ValueError, SyntaxError) as e:
        print(f"Error converting {embedding_str}: {e}")
        return None

def find_similar_embeddings(query_embedding, embeddings, top_n=3):
    # Compute cosine similarities
    similarities = cosine_similarity([query_embedding], embeddings)
    # Get indices of top_n most similar embeddings
    top_indices = np.argsort(similarities[0])[::-1][:top_n]
    return top_indices, similarities[0][top_indices]


def get_embedding(text):
    # Initialize the embedding model
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    # Get the embedding
    embedding = embedding_model.embed_query(text)

    # Convert to numpy array
    return np.array(embedding)

def example_selector(question:str):

    examples = example_questions_dict
    cypherquery_list = []
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        # This is the list of examples available to select from.
        examples,
        # This is the embedding class used to produce embeddings which are used to measure semantic similarity.
        OpenAIEmbeddings(),
        # This is the VectorStore class that is used to store the embeddings and do a similarity search over.
        Chroma,
        # This is the number of examples to produce.
        k=3,
    )

    # Select the most similar example to the input.
    #question = ("What kind of obligations does Apple which can say they are porting their data??")
    selected_examples = example_selector.select_examples({"question": question})

    #print(f"Examples most similar to the input: {question}")
    for example in selected_examples:
        #print("\n")
        for k, v in example.items():
            print(f"{k}: {v}")
            if k == "cypherquery_variable":
                cypherquery_list.append(v)


    print ("cypherquery_list is,", cypherquery_list)
    return cypherquery_list

def query_similar_nodes(node_id, column_name):

    if column_name == "Text":
        vector_index_name = "textExtracts"

    else:
        vector_index_name = "rationaleExtracts"

    cypher = "MATCH (m{id:"+ f"{node_id}" +"""})
    
CALL db.index.vector.queryNodes(""" + f"""'{vector_index_name}', 6, m.textEmbedding)
YIELD node, score
    
RETURN node.{column_name.lower()} AS text, score"""

    print(cypher)

    response = (graph.query(cypher))

    return response

def comparison_selector():
    pass

def select_organisation():

    dict_of_organisations = {"OpenAI": ["EU"], "Microsoft": ["US"], "Adobe": ["India"]}

    # Create a list with serialized numbering
    serialized_list = [f"{i + 1}. {key}: {value}" for i, (key, value) in enumerate(dict_of_organisations.items())]

    # Print each item in the list
    for item in serialized_list:
        print(item)

    organisation_choice = input("Select the serial number you want to view\n")

    organisation = list(dict_of_organisations.keys())[int(organisation_choice)-1]

    return organisation

def main():

    organisation = select_organisation()

    choice = input("Press 1 if you have a specific right you want to know about. \n"
                   "Press 2 if you want to compare with the annotated text or its rationale\n")

    if choice == "1":
        queryforrights = input(
            "What do you want to know about a specific privacy right for the organisation you have selected\n")
        cypherquery_list = example_selector(queryforrights)
        query_counter = 0
        for query in cypherquery_list:
            query_counter += 1
            cypherquery = cypherpromptgeneration(query, organisation)
            result_df, error_code = execute_cypher(cypherquery)
            print (f"error_code for {query} is {error_code}")
            if not error_code:
                print("Matching result found:\n\n", result_df)
                result_df.to_csv(f"Matching_result{query_counter}.csv")
                if query != cypherquery_list[len(cypherquery_list)-1]:
                    choice_for_more=input ('DO YOU WANT MORE RESULTS? TYPE "Y" IF SO')
                    if choice_for_more != "Y":
                        break
        else:
            # This block executes if the for loop completes without a break (i.e., no successful query)
            print("No more matching results found. Please try again with a new prompt.")

    elif choice == "2":

        df_results = pd.DataFrame()

        #choice_for_comparison = input(
        #    "Press 1 if you want to compare a specific clause or 2 if you want to compare a rationale\n")

        choice_mode_for_comparison = input("Press 1 if you want to compare using node ID or 2 if you want to compare using extract of the text\n")

        choice_for_comparison = "1"

        if choice_for_comparison == "1":
            choice_string = "clauses in the privacy police"
            embedding_name = "text-embedding"
            column_name = "Text"
        else:
            choice_string = "rationales for classification"
            embedding_name = "rationale-embedding"
            column_name = "Rationale"

        if choice_mode_for_comparison == "1":
            node_id = input("Enter the node ID below (this is the value of the property 'ID' for a specific text extract")
            response = query_similar_nodes(node_id, column_name)
            df_new_results = pd.DataFrame(response)
            df_results = pd.concat([df_results, df_new_results], ignore_index=True)
            df_results.to_csv("SimilarNodes.csv")

        elif choice_mode_for_comparison == "2":



            text_for_comparison = input(f"Now give the text you want to view similar {choice_string} to.\n")
            organisation_file_name = input (f"Now give the name of the organisation file name you want to search for similar nodes for {choice_string} for\n")
            df_for_comparison = pd.read_csv(f"./embeddings/{organisation_file_name}")
            query_embedding = get_embedding(text_for_comparison)
            # Apply the function to the Embedding column
            df_for_comparison[embedding_name] = df_for_comparison[embedding_name].apply(convert_to_array)
            top_indices, similarities = find_similar_embeddings(query_embedding, df_for_comparison[embedding_name].tolist())

            list_of_node_IDs = []
            list_of_results = []
            # Display the results
            for idx, similarity in zip(top_indices, similarities):
                list_of_results.append(f"{column_name}: {df_for_comparison.loc[idx, column_name]}, Similarity: {similarity}")
                node_id = df_for_comparison.loc[idx, "ID"]
                list_of_node_IDs.append(node_id)

            print("List of node ids", list_of_node_IDs)

            for node_id in list_of_node_IDs:
                response = query_similar_nodes(str(node_id), column_name)
                df_new_results = pd.DataFrame(response)
                df_results = pd.concat([df_results, df_new_results], ignore_index=True)

            df_results.to_csv("SimilarNodes.csv")


if __name__ == "__main__":
    main()