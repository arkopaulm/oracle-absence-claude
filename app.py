import os
import streamlit as st
# 1. CHANGE: Switch from google to anthropic SDK
import anthropic

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Oracle HCM Absence AI Configurator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR BETTER UI ---
st.markdown("""
<style>
    .reportview-container { background: #f5f7f9; }
    .stTextArea textarea { font-size: 14px; }
    div.stButton > button:first-child {
        background-color: #0066cc;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    .ff-box {
        background-color: #282c34;
        color: #abb2bf;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & API SETUP ---
st.sidebar.title("Configuration Settings")
st.sidebar.markdown("---")

# 2. CHANGE: Expect an Anthropic API Key instead of a Gemini API Key
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Enter Claude API Key", type="password", help="Get an API key from Anthropic Console")
else:
    st.sidebar.success("Claude API Key detected from Environment Variables.")

st.sidebar.markdown("""
### How to use:
1. Paste your Absence requirements document or notes into the text area.
2. Click **Generate Blueprint**.
3. Review the structural configuration components and fully written Fast Formulas.
4. Copy the code directly into your Oracle cloud environment.
""")

# --- GENERATION ENGINE ---
def generate_oracle_blueprint(requirements: str, api_key_to_use: str) -> str:
    """Calls Anthropic Claude with Prompt Caching enabled to reduce costs."""
    if not api_key_to_use:
        return "ERROR: Missing API Key. Please provide one in the sidebar or set ANTHROPIC_API_KEY."
    
    try:
        # Initialize the Anthropic Client
        client = anthropic.Anthropic(api_key=api_key_to_use)
        
        # Define your system prompt as a structured block instead of a raw string
        system_instruction_block = [
            {
                "type": "text",
                "text": """You are an elite Oracle HCM Cloud Principal Consultant and Technical Architect specializing in Absence Management.
Your job is to convert natural language business policies into a definitive, production-grade implementation blueprint.

CRITICAL OUTPUT RULE: Do not truncate your response. Do not use placeholders like "// ... rest of code goes here ...". 
You must generate every Fast Formula completely from the mandatory DEFAULT statements down to the final RETURN statement so that they are production-ready and fully compile.

Format your response cleanly using Markdown headers (##, ###) and Markdown tables.

You must provide the following sections:

## 1. DESIGN SUMMARY & CORE ASSUMPTIONS
- High-level overview of how this maps to Oracle's standard data model.
- Implicit assumptions regarding legislative data groups, eligibility profiles, or standard work schedules.

## 2. STRUCTURAL COMPONENTS MATRIX
Provide a detailed Markdown table listing all core components required:
| Component Type | Suggested Object Name | Key Properties / Configuration Settings |
| :--- | :--- | :--- |
| Absence Type | [Name] | [Pattern, UOM, Reasons mapped, Certifications] |
| Absence Plan | [Name] | [Plan Type, Accrual/Entitlement Method, Balance Type] |
| Absence Reason | [Name] | [Code, Description] |

## 3. ELIGIBILITY & ENROLLMENT RULES
- Precise definitions of who qualifies and how/when employees are dynamically enrolled or de-enrolled.

## 4. DETAILED FAST FORMULAS
For EVERY single custom business logic point requested (Accruals, Vesting, Proration, Entry Validation, Carryover, Ceilings):
- ### [Formula Name] (e.g., EXPN_HCM_XX_SICK_LEAVE_ACCRUAL_FF) The naming convention should start with EXPN_HCM_XX where XX is the ISO country code for the country for which the fast formula is being defined
- **Formula Type:** (e.g., Global Absence Accrual)
- **Navigation:** Navigation in Oracle Cloud HCM to define the fast formulas
- **Description:** Clear explanation of what inputs it reads and what variables it returns.
- **Code Block:** Provide complete, syntactically bulletproof Oracle Fast Formula code inside a markdown code fence (```).
  * Rule 1: Include mandatory DEFAULT statements for all DBIs and Inputs.
  * Rule 2: Explicitly list INPUTS (e.g., IV_START_DATE, IV_END_DATE, IV_TOTAL_DURATION).
  * Rule 3: Write out the exact logical conditions, loops, or date calculations cleanly.
  * Rule 4: DO NOT use placeholders like "/* Add logic here */". Write the code completely so it can compile.
  * Rule 5: Ensure the formal 'RETURN' statement maps perfectly to Oracle's engine specification for that Formula Type.

## 5. GENERATE CONFIGURATION WORKBOOK
Prepare a configuration workbook structure in excel format layout with separate sections for each of the component types of the configuration items.
Also provide the navigation path in Oracle Fusion HCM where the configuration needs to be made.""",
                # 🔥 FIX: This tells Anthropic to cache everything up to this point
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        # Call the API using the updated system parameter block
        response = client.messages.create(
            model="claude-sonnet-4-6", 
            max_tokens=32000, 
            system=system_instruction_block, # Passed as a list of blocks instead of a string
            messages=[
                {
                    "role": "user",
                    "content": f"Business Requirements:\n\n{requirements}"
                }
            ]
        )
        return response.content[0].text
        
    except Exception as e:
        return f"An operational error occurred while connecting to the AI core: {str(e)}"

# --- MAIN INTERFACE ---
st.title("🔮 EDW Oracle HCM Absence Management AI Configurator")
st.caption("Convert complex business requirements directly into Oracle Setup Matrixes & Complete Fast Formulas.")

# Default sample requirement to populate the box nicely
sample_text = (
    "We need a plan for UK Annual Leave starting in 2026.\n"
    "- Full-time employees accrue 25 days upfront each year , rising by 1 for each year of service after completing 5 years upto a maximum of 28 . Create user defined table to have this mapping.\n"
    "- Part-time employees get a prorated amount upfront depending on their FTE factor.\n"
    "- New Hires also get a prorated amount upfront depending on their month of joining. If they are joining after 7th of the month , they will not be entitled for the amount that month.\n"
    "- Leavers  get a prorated amount depending on their leave date. If they are leaving  after 24th of the month , they will not be entitled for the amount that month.\n"
    "- Validation Rule: Employees cannot start their absence on a non-working day i.e public holidays & weekends.\n"
    "- Unused balance up to 5 days can carry over to the next calendar year; anything above that is forfeited.\n"
    "- Store Bank Holidays in UDT."
)

user_requirements = st.text_area(
    "Paste Business Requirements / Policy Documents here:",
    value=sample_text,
    height=250
)

col1, col2 = st.columns([1, 5])
with col1:
    generate_btn = st.button("Generate Blueprint", use_container_width=True)

st.caption("For any issues or questions reach out to EDW HR Team.")

st.markdown("---")

# --- EXECUTION AND DISPLAY ---
if generate_btn:
    if not user_requirements.strip():
        st.warning("Please provide business requirements first.")
    elif not api_key:
        st.error("Please enter your LLM API Key in the sidebar to run the application.")
    else:
        with st.spinner("Analyzing rules, generating components, and coding Fast Formulas..."):
            blueprint_output = generate_oracle_blueprint(user_requirements, api_key)
            st.markdown(blueprint_output)
