from os import environ, listdir 
from json import loads
from datetime import datetime, timedelta
from time import sleep

from streamlit_extras.row import row

import streamlit as st 

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

st.set_page_config(
    page_title='CalWiz',
    page_icon='🧙',
    layout="centered",
    initial_sidebar_state="collapsed",
)

SKIN_DIR = './skins/'

# Sidebar Skin Selector

def format_dropdown_label(string):
    # 40_📜_Mighty_Wizard.skin => 📜 Mighty Wizard
    nr,icon,*avatar = string.split(".")[0].split("_")
    return f"{icon} {' '.join(avatar)}"

# Function to execute a skin file directly
def execute_skin_file(skin_file_path):
    with open(SKIN_DIR + skin_file_path, "r") as skin_file:
        exec(skin_file.read(), globals())
    
# Get a list of all .skin files in the SKIN_DIR directory
skin_files = [file for file in listdir(SKIN_DIR) if file.endswith(".skin")]

# Sort by the trailing number
skin_files.sort()

if selected_option := st.sidebar.selectbox('Select a Skin File', skin_files, format_func=format_dropdown_label):
    execute_skin_file(selected_option)

# App framework
st.title(APP_TITLE)

system = """
Identify any event within the user input that can be put into a calender. 

Output a list of all identified events as JSON with the following keys: summary, start, end, location, description, all-day-event. Separate the events with '<NEXTEVENT>'

For time and date use the ISO 8601 Format, i.e. YYYY-MM-DDTHH:MM:SS 
If no starting time is given, set the key "all-day-event" to "True", otherwise to "False"
If a starting time is given, but no end time, assume that the events ends one hour later.

Do not output anything else. Use only information provided by the user. 
"""

if 'result_list' not in st.session_state:
    st.session_state.result_list = None


def simulate_typing(target_object, string, flag):
    full_response = ''
    for chunk in string.split():
        full_response += chunk + " "
        if flag not in st.session_state:
            sleep(0.09)     
        target_object.markdown(full_response + "▌")
    target_object.markdown(full_response)

with st.chat_message(CHAT_AVATAR):
    message_placeholder = st.empty()
    simulate_typing(message_placeholder,WELCOME_MESSAGE_1, 'greeted')
    message_placeholder = st.empty()
    simulate_typing(message_placeholder, WELCOME_MESSAGE_2, 'greeted')
    message_placeholder = st.empty()
    simulate_typing(message_placeholder, WELCOME_MESSAGE_3, 'greeted')
    prompt = st.text_area(' ', value=SAMPLE_INPUT)
    st.session_state.greeted = 'Yes'

result = None

if st.button(LETS_GO_BUTTON_LABEL):
    if prompt != SAMPLE_INPUT:

        environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]
        chat = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')

        messages = [
        SystemMessage(content=system),
        HumanMessage(content=prompt)
        ]

        try: 
            result = chat(messages).content
            print("RESULT")
            print(result)
            print("*** END RESULT ***")

        except Exception as e:
            # Catch other exceptions and print their details
            st.write(f"An exception of type {type(e).__name__} occurred: {e}")

    else: # prompt was not changed by user, run the simulation, without queringy ChatGPT
            result = (
        '{"summary": "Enchanting gathering", "start": "2023-12-23T14:30:00", "end": "2023-12-23T15:30:00", '
        '"location": "Ricks Citadel", "description": "Share a brew of mystical origins", "all-day-event": "False"}'
        '<NEXTEVENT>'
        '{"summary": "Yuletide recess", "start": "2023-12-23", "end": "2024-01-02", '
        '"location": "", "description": "", "all-day-event": "True"}'
    )

if result:
    try:
        st.session_state.result_list =[loads(item) for item in result.split('<NEXTEVENT>')]

        for event in st.session_state.result_list:
            # als erstes prüfe ich, ob es sich um ein string handelt
            # dann konvertiere ich es in eine dateformat-objekte
            if isinstance(event["start"], str):
                event["start"] = datetime.fromisoformat(event["start"])

            if isinstance(event["end"], str):
                event["end"] = datetime.fromisoformat(event["end"])

            if isinstance(event["all-day-event"], str):
                event["all-day-event"] = True if event["all-day-event"] == 'True' else False
                event["end"] = event["end"] + timedelta(days=1)


    except Exception as e:
        # Catch other exceptions and print their details
        st.write(f"An exception of type {type(e).__name__} occurred: {e}")

if st.session_state.result_list: # Wenn nicht None oder leer, also = []

    st.divider()


    with st.chat_message(CHAT_AVATAR):
        message_placeholder = st.empty()
        simulate_typing(message_placeholder, IDENTIFIED_EVENTS_MESSAGE, 'delivered')
        st.session_state.delivered = 'Yes'

        count = 0
        
        ics_file_data = (
                f'BEGIN:VCALENDAR\n'
                f'VERSION:2.0\n'
                f'CALSCALE:GREGORIAN\n'
                )

        for event in st.session_state.result_list:

            title_row = row(4, vertical_align="bottom")
            event["summary"] = title_row.text_input('What?',event["summary"], key="title"+str(count))
            event["location"] = title_row.text_input('Where?',event["location"], key="location-"+str(count))

            delete = title_row.button(':x: delete', key="include-"+str(count))
            if delete:
                st.session_state.result_list.pop(count)
                st.rerun() # weil wir rerun() machen, ist es egal, dass wir aus der aktuellen Liste etwas löschen.
            
            event["all-day-event"] = title_row.toggle('all day', value=event["all-day-event"], key="toggle-"+str(count), help=NEXT_DAY_HELP_MESSAGE)

            second_row = row(4, vertical_align="center")

            event["start"] = datetime.combine(
                second_row.date_input("Starting Time:", event["start"], key="start-date-"+str(count)),
                second_row.time_input(" ", event["start"], disabled=event["all-day-event"], key="start-time-"+str(count))
                )

            event["end"]   = datetime.combine(
                second_row.date_input("End Time:", event["end"], key="end-date-"+str(count)),
                second_row.time_input(" ", event["end"], disabled=event["all-day-event"], key="end-time-"+str(count))
                )

            event["description"] = st.text_input('Notes', value=event["description"])

            ics_file_data += (
                 f'BEGIN:VEVENT\n'
                 f'SUMMARY:{event["summary"]}\n'
                 )

            if event["all-day-event"]:
                ics_file_data += (
                    f'DTSTART;VALUE=DATE:{event["start"].strftime("%Y%m%d")}\n'
                    f'DTEND;VALUE=DATE:{event["end"].strftime("%Y%m%d")}\n'
                    )
            else:
                ics_file_data += (
                    f'DTSTART:{event["start"].strftime("%Y%m%dT%H%M%S")}\n'
                    f'DTEND:{event["end"].strftime("%Y%m%dT%H%M%S")}\n'
                    )

            ics_file_data += (
                f'LOCATION:{event["location"]}\n'
                f'DESCRIPTION:{event["description"]}\n'
                f'END:VEVENT\n'
                )

            st.divider()
            count+=1


        ics_file_data += "END:VCALENDAR"


    if st.download_button(
            label=GENERATE_ICS_FILE,
            data=ics_file_data,
            file_name=f"your_event.ics",
            mime="text/calendar"
            ):


        with st.chat_message(CHAT_AVATAR):
            message_placeholder = st.empty()
            simulate_typing(message_placeholder, DOWNLOAD_STARTED_MESSAGE, 'finished') 
