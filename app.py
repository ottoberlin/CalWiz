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


APP_NAME = 'Your Friendly Calendar Wizard'
APP_SHORT_NAME = 'CalWiz'
CHAT_AVATAR = "🧙"
APP_TITLE = CHAT_AVATAR + APP_NAME
WELCOME_MESSAGE_1 = "Greetings, Traveler of Time and Events! :sparkles:"
WELCOME_MESSAGE_2 = "Welcome to the Mystical Realm Where We Weave the Threads of Time into iCal Scrolls 📆✨"
WELCOME_MESSAGE_3 = "Gather Your Human-Readable Event Scrolls and Place Them in the Mystical Field Below 📜"
SAMPLE_INPUT = "Greetings, fellow magician! I, Chatty, extend my conjured invitation for an enchanting gathering tonight at 14:30, where we shall share a brew of mystical origins. Don't forget to bring our arcane board game to Rick's Citadel. And mark it well, our Yuletide recess spans from December 23, 2023, to January 2, 2024."
LETS_GO_BUTTON_LABEL = ":magic_wand: Let's go"
LETS_GO_SIMULATION_BUTTON_LABEL = ":magic_wand: Let's go (simulation)"

# SHOW RECOGNIZED EVENTS
IDENTIFIED_EVENTS_MESSAGE = 'Behold the Events that await your enchantment. Check the events to see if I recognized them correctly. Change it if necessary.'
DELETE_EVENT_BUTTON_LABEL = ":x: delete"

# TOGGLE BUTTON TO SWITCH BETWEEN ALL DAY EVENTS AND EVENTS WITH AN BEGINNING AND AN END TIME
TOGGLE_ALL_DAY_LABEL = "All Day Magic"
NEXT_DAY_HELP_MESSAGE = "In the mystical realm, all-day events conclude at the beginning of the date given as the end date. For example, New Year's Day will be displayed as 2023-01-01 to 2023-01-02."

DOWNLOAD_STARTED_MESSAGE = 'The download incantation has begun. Open the file with your favored Calendar spell. Or dispatch this file to yourself via mystical post to import it on iOS-Devices.'
GENERATE_ICS_FILE = ":scroll: As you command, create an iCal/.ics-File"

USING_CHATGPT_WARNING = "Be mindful, for any incantation you inscribe in the field above shall journey to OpenAI's GPT-3.5 API, a realm of magical computation. Reflect on your input, especially if it contains personally identifiable information."

CONTENT_AI_GENERATED_WARNING = "Know this, the events you behold here were conjured by artificial intelligence deciphering your text. When traversing this realm of AI, wield caution, and validate these manifestations before trusting them. Relying solely upon these events might lead you on an unexpected journey through time and space."


SYSTEM_PROMPT = """
Identify any event within the user input that can be put into a calender. 

Output a list of all identified events as JSON with the following keys: summary, start, end, location, description, all-day-event. Separate the events with '<NEXTEVENT>'

For time and date use the ISO 8601 Format, i.e. YYYY-MM-DDTHH:MM:SS 
If no starting time is given, set the key "all-day-event" to "True", otherwise to "False"
If a starting time is given, but no end time, assume that the events ends one hour later.

Do not output anything else. Use only information provided by the user. 
"""




st.set_page_config(
    page_title=APP_SHORT_NAME,
    page_icon=":magic_wand:",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# App framework
st.title(APP_TITLE)

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
    simulate_typing(message_placeholder, WELCOME_MESSAGE_2, 'greeted')
    message_placeholder = st.empty()
    simulate_typing(message_placeholder, WELCOME_MESSAGE_3, 'greeted')
    prompt = st.text_area('paste your text here', value=SAMPLE_INPUT)
    st.session_state.greeted = 'Yes'
    st.info(USING_CHATGPT_WARNING, icon="ℹ️")

result = None


if st.button(LETS_GO_BUTTON_LABEL):
    if prompt != SAMPLE_INPUT:

        environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]
        chat = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')

        messages = [
        SystemMessage(content=SYSTEM_PROMPT),
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
                if event["all-day-event"] == 'True': 
                    event["all-day-event"] = True 
                    event["end"] = event["end"] + timedelta(days=1)
                else:
                    event["all-day-event"] = False


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

            event["description"] = st.text_input('Notes', value=event["description"], key="description-"+str(count))

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

    st.info(CONTENT_AI_GENERATED_WARNING , icon="ℹ️")
