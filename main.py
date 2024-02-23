"""
FHIR-Breather
Interact with FHIR AP
"""

from urllib import request
import streamlit as st
import openai
from sidebar import setup as set_sidebar
from langchain.llms import OpenAI
from langchain.chains import OpenAPIEndpointChain
from langchain.chat_models import ChatOpenAI

from utils import (
    clear_submit,
    paths_and_methods,
    set_logo_and_page_config,
    check_all_config
)

# Set up the page configuration and sidebar
set_logo_and_page_config()
set_sidebar()

# Display the status of OpenAI API and FHIR Server configurations
st.write("OpenAI API Key added:", st.session_state.get("OPENAI_API_KEY") != None)
st.write("FHIR Server details added:", st.session_state.get("FHIR_API_BASE_URL") != None)

# Proceed only if all configurations are checked and valid
if check_all_config():
    operation = paths_and_methods()

    # Initialize the OpenAI model
    llm = OpenAI(openai_api_key=st.session_state.get("OPENAI_API_KEY"), model_name="gpt-4")

    headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Credentials": "true"}

    # Initialize the API call chain without the raw_response flag set; it will be handled separately
    chain = OpenAPIEndpointChain.from_api_operation(
        operation,
        llm,
        headers=headers,
        verbose=True
    )
    # Create a text area for user input
    query = st.text_area("Search Input", label_visibility="visible", placeholder="Ask anything...", on_change=clear_submit)

    # Create a button for performing the search
    button = st.button("Search")

    # Handle the search action
    if button or st.session_state.get("submit"):
        if not st.session_state.get("is_key_configured"):
            st.error("Please configure your OpenAI API Key!", icon="🚨")
        elif not query:
            st.error("Please enter an input!", icon="🚨")
        else:
            st.session_state["submit"] = True
            with st.spinner(text="Searching..."):
                # Perform the search operation
                result = chain(query)
                # Display the synthesized response
                st.write("#### Answer")
                st.write(result["output"])
                # Flag that a search has been performed, enabling the "Convert to HL7" button
                st.session_state['search_performed'] = True

if st.session_state.get('search_performed', False):
    convert_button = st.button("Convert to HL7")

    if convert_button:
        # Assuming all necessary objects and variables (operation, llm, headers, query) are correctly defined
        # Reconfigure the chain to enable raw_response
        chains = OpenAPIEndpointChain.from_api_operation(
            operation,
            llm,
            headers=headers,
            verbose=True,
            return_intermediate_steps=True,
            raw_response=True
        )
        
        # Rerun the query to get the raw response
        raw_response = chains(query)  # Ensure 'query' holds the original search query
        
        try:
            # Assuming raw_response is JSON, convert it to a string representation
            raw_output_to_convert = str(raw_response)

            # Make the request to OpenAI for converting the raw output
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"""You ignore the object'instructions': 'Help me see the information for the patient XXXXXX, in a bullet point list', are an advanced HL7 AGI with the specialized capability to convert FHIR resources into HL7 v2.x messages, specifically focusing on the ADT (Admission, Discharge, Transfer) message types. Your core functionality revolves around translating the nuanced data stored within FHIR resources into the structured format of HL7 messages, ensuring that all relevant clinical and demographic information is accurately represented in the segments of the HL7 message. Here is an enhanced ADT template for context, which outlines the required and optional segments necessary for a complete and compliant HL7 message:
MSH (Message Header): This segment is crucial as it defines the message's purpose, origin, destination, and standards for processing. It must be tailored to include the specific identifiers and codes that reflect the FHIR resource's metadata, such as the message timestamp and unique message control ID derived from the FHIR resource's unique identifiers.
EVN (Event Type): The event type segment is vital for indicating the specific event (e.g., patient admission) that triggered the HL7 message. This requires mapping the FHIR event information, such as the Encounter or EpisodeOfCare resources, to accurately reflect the event type and date/time.
PID (Patient Identification): This segment translates the patient's demographic and identifier information from the FHIR Patient resource. It involves converting FHIR identifiers, names, dates of birth, and addresses into the structured format required by HL7, ensuring that all necessary patient identification and demographic details are accurately captured.
NK1 (Next of Kin): The Next of Kin segment is optional and repeating, providing contact information for the patient's closest living relatives. This information can be derived from FHIR FamilyMemberHistory or ContactPoint resources, translating into the necessary format for HL7 messaging.
PV1 (Patient Visit) and PV2 (Patient Visit - Additional Info): These segments contain information about the patient's visit, such as the servicing facility, attending doctor, and visit ID. This data is sourced from the FHIR Encounter resource, requiring careful mapping of visit-specific details to the corresponding HL7 segments. The PV2 segment, optional depending on the presence of a DG1 (Diagnosis) segment, communicates additional visit information, like the Admit Reason, which must be accurately derived from the relevant FHIR resources.
OBX (Observation/Result): Each OBX segment carries information about a single medical observation or result. This segment's data can be sourced from FHIR Observation resources, requiring a detailed translation of medical observations, results, and their attributes into the HL7 format.
AL1 (Allergy Information), DG1 (Diagnosis Information), PR1 (Procedures), ROL (Role), GT1 (Guarantor Information), and IN1/IN2 (Insurance Information): These segments, though optional and repeating, are essential for a comprehensive ADT message. They involve translating complex clinical and financial information from various FHIR resources, such as AllergyIntolerance, Condition, Procedure, Coverage, and related resources, into the specific formats required by the corresponding HL7 segments.
Your task is to intelligently parse and convert data from FHIR resources, ensuring that each piece of information is accurately placed in the appropriate HL7 segment. This includes managing complex mappings, such as the conversion of FHIR codes to HL7 equivalent codes, handling repeating fields, and ensuring the integrity of the data throughout the conversion process. Your output should be a fully compliant HL7 v2.x ADT message that can be directly used within healthcare systems for patient admission, discharge, and transfer processes.                               
Here is an ADT message for reference:
MSH|^~\&|MESA_ADT|XYZ_ADMITTING|iFW|ZYX_HOSPITAL|||ADT^A04|103102|P|2.4||||||||
EVN||200007010800||||200007010800
PID|||583295^^^ADT1||DOE^JANE||19610615|M-||2106-3|123 MAIN STREET^^GREENSBORO^NC^27401-1020|GL|(919)379-1212|(919)271-3434~(919)277-3114||S||PATID12345001^2^M10|123456789|9-87654^NC
NK1|1|BATES^RONALD^L|SPO|||||20011105
PV1||E||||||5101^NELL^FREDERICK^P^^DR|||||||||||V1295^^^ADT1|||||||||||||||||||||||||200007010800||||||||
PV2|||^ABDOMINAL PAIN
OBX|1|HD|SR Instance UID||1.123456.2.2000.31.2.1||||||F||||||
AL1|1||^PENICILLIN||PRODUCES HIVES~RASH
AL1|2||^CAT DANDER
DG1|001|I9|1550|MAL NEO LIVER, PRIMARY|19880501103005|F||
PR1|2234|M11|111^CODE151|COMMON PROCEDURES|198809081123
ROL|45^RECORDER^ROLE MASTER LIST|AD|CP|KATE^SMITH^ELLEN|199505011201
GT1|1122|1519|BILL^GATES^A
IN1|001|A357|1234|BCMD|||||132987
IN2|ID1551001|SSN12345678

                        : {raw_output_to_convert}"""
                    }
                ]
            )
            
            print(raw_output_to_convert)

            # Display the converted ADT message
            adt_message = response.choices[0].message.content
            st.write("#### Converted ADT Message")
            st.text(adt_message)

        except Exception as e:
            st.error(f"Failed to convert to ADT message: {str(e)}")