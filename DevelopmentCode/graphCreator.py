#line numbers 190 and 195 have the filenames to be changed

import json
import re
import csv
from typing import Union, List

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import os

os.environ["OPENAI_API_KEY"] = ""

llm = ChatOpenAI(model="gpt-4o-mini")
def query_response(query:str):

    class ItemWithRationale(BaseModel):
        """Schema to hold an item and its rationale."""
        text: str = Field(..., description="The exact extract from the text which has been classified. It will not be paraphrased or summarised")
        rationale: str = Field(..., description="Explanation or rationale for why this extract was identified.")

    class PrivacyRights(BaseModel):
        """The attributes related to Legal and Practical Rights expected to arise in the text"""

        RightOfInformationAndAccess: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that gives people the right to access their personal data and how this is processed."
        )
        RectificationAndErasure: List[ItemWithRationale] = Field(
            ...,
            description="Anything that enables the deletion or modification of records of user data. Includes any of the measures which allow 'forgetting'."
        )
        RightToObject: List[ItemWithRationale] = Field(
            ...,
            description="A measure that allows the individual to object to processing - through consent checkboxes for instance."
        )
        RightToCompensation: List[ItemWithRationale] = Field(
            ...,
            description="Any consequences that are covered by payment clauses or liability on part of the data processor."
        )
        RightToRestrictProcessing: List[ItemWithRationale] = Field(
            ...,
            description="Consequences that arise from users rights to make requests that limit the scope of data collected on them."
        )
        RightOfDataPortability: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that allows one to port or transfer the data collected about them in a standard format, for example."
        )

        AutomatedDecisionMakingAndProfiling: List[ItemWithRationale] = Field(
            ...,
            description = "automated processing, including profiling of the user which results in a decision made that affects the user"
        )

    class PracticalRights(BaseModel):
        """The attributes related to Practical Rights expected to arise in the text"""

        AITraining: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that indicates that user's data will be used for training an Artificial Intelligence Model or implementing such features."
        )
        ContentUploadedOnProducts: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that indicates that the user's uploaded data and assets created using the product or services will be utilised by the company."
        )
        Cookies: List[ItemWithRationale] = Field(
            ...,
            description="Anything that mentions utilising 'cookies' as a way to collect user data."
        )
        OptOut: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that allows users to opt out of collection of their personal data."
        )
        UsageByThirdParties: List[ItemWithRationale] = Field(
            ...,
            description="Any measure that lets third parties use, process, or analyse the user's data for any purposes."
        )

    class Rights(BaseModel):
        """Identifying the privacy obligations arising in a text."""

        privacy_rights: PrivacyRights
        practical_rights: PracticalRights

        # Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You must classify the text given to you as per the schema provided. Output the matching extracts exactly and do not paraphrase"
                "for each classification in your answer as JSON that matches the given schema: ```json\n{schema}\n```. "
                "Make sure to wrap the answer in ```json and ``` tags and also that each list of classification can contain multiple examples from the text",
            ),
            ("human", "{query}"),
        ]
    ).partial(schema=Rights.schema())


    # Custom parser
    def extract_json(message: AIMessage) -> List[dict]:
        """Extracts JSON content from a string where JSON is embedded between ```json and ``` tags.

        Parameters:
            text (str): The text containing the JSON content.

        Returns:
            list: A list of extracted JSON strings.
        """
        text = message.content
        # Define the regular expression pattern to match JSON blocks
        pattern = r"```json(.*?)```"

        # Find all non-overlapping matches of the pattern in the string
        matches = re.findall(pattern, text, re.DOTALL)

        # Return the list of matched JSON strings, stripping any leading or trailing whitespace
        try:
            return [json.loads(match.strip()) for match in matches]
        except Exception:
            raise ValueError(f"Failed to parse: {message}")

    llm = ChatOpenAI(model="gpt-4o-mini")

    print(prompt.format_prompt(query=query).to_string())
    chain = prompt | llm | extract_json
    response = chain.invoke({"query": query})

    return response

def query_combiner(filename:str):

    with open(filename, "r") as fn:
        csv_reader = csv.reader(fn)
        list_of_strings = list(csv_reader)



    # Assume list_of_strings and query_response are defined elsewhere
    json_list_aggregate = []

    # Collect JSON responses from queries
    for query in list_of_strings:
        response = query_response(query)
        json_list_aggregate.append(response)

    #print("JSON_LIST_AGGREGATE:", json_list_aggregate)

    # Flatten the list of lists to a single list
    flattened_data = [item for sublist in json_list_aggregate for item in sublist]

    # Initialize dictionaries to combine and deduplicate
    combined_privacy_rights = {}
    combined_practical_rights = {}

    # Process each dictionary in the flattened list
    for entry in flattened_data:
        privacy_rights = entry.get('privacy_rights', {})
        practical_rights = entry.get('practical_rights', {})

        # Update combined dictionaries with entries from each item
        for key, value in privacy_rights.items():
            if key not in combined_privacy_rights:
                combined_privacy_rights[key] = value
            else:
                # Deduplicate by extending lists
                existing_values = {json.dumps(v) for v in combined_privacy_rights[key]}
                combined_privacy_rights[key].extend(v for v in value if json.dumps(v) not in existing_values)

        for key, value in practical_rights.items():
            if key not in combined_practical_rights:
                combined_practical_rights[key] = value
            else:
                # Deduplicate by extending lists
                existing_values = {json.dumps(v) for v in combined_practical_rights[key]}
                combined_practical_rights[key].extend(v for v in value if json.dumps(v) not in existing_values)

    # Combine the results into the final output
    final_output = {
        'privacy_rights': combined_privacy_rights,
        'practical_rights': combined_practical_rights
    }

    # Convert to JSON and write to file
    json_str_combined = json.dumps(final_output, indent=2)

    with open('Apple-IndiaOutput.json', 'w') as json_file:
        json_file.write(json_str_combined)


def main():
    query_combiner("")
    


if __name__ == "__main__":
    main()
#hf_global.invoke("Hello")