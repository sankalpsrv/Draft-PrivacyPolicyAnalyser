# Correcting the overwritten list
cypherquery_type_practical = ["Affects content uploaded on products", "AI Training", "Cookies policy", "Opt out", "Usage by Third Parties"]
cypherquery_type_legal = ["Information", "Right to Data Portability", "Right to Object", "Right to Restrict Processing", "Right to Compensation", "Automated Decision Making and Profiling", "Rectification"]
cypherquery_type_group = ["Practical Rights", "Legal Rights"]

def cypherpromptgeneration(cypherquery_variable, organisation_name):

    type_of_variable_right = ""
    cypherquery_type_class = ""

    # Using the global variables correctly
    global cypherquery_type_practical
    global cypherquery_type_legal
    global cypherquery_type_group

    if cypherquery_variable in cypherquery_type_group:
        cypherquery_type_class = "typeofrights"

    elif cypherquery_variable in cypherquery_type_practical:
        cypherquery_type_class = "specificright"
        type_of_variable_right = "Practical Rights"
    elif cypherquery_variable in cypherquery_type_legal:
        cypherquery_type_class = "specificright"
        type_of_variable_right = "Legal Rights"

    cypherquery_dict = {
        "typeofrights": f"MATCH (p:`Privacy Policy` {{organisation: '{organisation_name}'}}), (pr:`{cypherquery_variable}`) WHERE (pr)-[:OF]->(p) MATCH (n)-[:IS_A]->(pr) RETURN n",
        "specificright": f"MATCH path = (n:`{cypherquery_variable}`)-[:`IS_A`]->(m:`{type_of_variable_right}`)-[:`OF`]->(p:`Privacy Policy`) WHERE p.`organisation` CONTAINS '{organisation_name}' RETURN n",
        # "textcompare": f"What are the obligations of {organisation_name} which are similar to {text_for_comparison}?",
        # "rationalecompare": f"What are the obligations of {organisation_name} which are because of {rationale_for_comparison}?"
    }

    cypherquery = cypherquery_dict[cypherquery_type_class]
    print(cypherquery)
    return cypherquery

# Define the variable before calling the function
cypherquery_variable = "AI Training"
organisation_name = "Microsoft"

# Call the function with the defined variables
#cypherpromptgeneration(cypherquery_variable, organisation_name)