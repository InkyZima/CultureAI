# CultureAI

CultureAI is a purpose-build LLM chat application for cultural AI-companions. Your cultural AI-companion is going to accompany you through your day, ensuring you follow cultural principles and exercise cultural practices. Some features:
- Overseer: As you chat with your cultural AI-companion, it will collect informaton about what you did and didn't do today, and compare this to cultural practices/tasks which you should do today ("overseeing"). It will then prompt you to give it information about the completion of those tasks and/or suggest you to do them. Those tasks will vary based on time of day. All of this happens asynchonously, that is, computing overseeing answers by the LLM does not block computing chat answers.
- NotificationServer: If enabled by the user, an LLM will check every x minutes (30 minutes by default) if now is a good time to proactively notify the user, for example if they were to complete a task recently, but it is unclear if they did so or not. The user's browser will then send a notification that there is a new chat message by the cultural AI-assistant. All of this happens asynchonously, that is, computing notification answers by the LLM does not block computing chat answers.
- MainChat / cultural AI-companion: There is a system prompt, where the cultural information can be set.
- TaskUpdater: There is a list of tasks (cultural day-to-day practices), which the user should do every day. Those are updated/checked automatically using the information the user provides in the chat. All of this happens asynchonously, that is, computing task updates by the LLM does not block computing chat answers.


## v0.1 prototype: Installation and usage
- Clone the repo
- Rename .env.example and put your real GOOGLE_API_KEY into it. Get your (free) GOOGLE_API_KEY from https://aistudio.google.com/
- python main.py
- The frontend should now run at http://localhost:8000/



# Project info and TODOs dump (20250204 - state of Prototype v0.1)
This project is going to be the main Orchestrator and personal server for the cultural AI-companion ("CultureAI").
The CultureAI is an LLM with which the user is going to interact with throughout their day, in order to acculturate with their desired culture. The CultureAI is going to serve as a cultural social environment for the user and as a cultural role-model/ideal. Through conversation with the CultureAI, the user is going to learn the thinking patterns, lifestyle, behavior, beliefs, values etc. of the desired culture, until they become embodiment of that culture. The user is going to interact with the CultureAI multiple times during the day (typically in the morning right after waking up, during lunch break, in the evening and before going to bed).
The CultureAI is tasked not just to chat with the user; the CultureAI is also tasked to ensure that the user meets a (check)list of cultural objectives, such as: Meditating three times a day, exercising two times a day, planning out their day in the morning, reflecting on the day before going to sleep.
The CultureAI consists of several parts:
- Main chat: This is where the user chats with the CultureAI every day.
- Extractor: An LLM which extracts relevant information about the user from the main chat.
- Overseer: An LLM which steers the main chat in certain directions in order to achieve certain objectives, for example: Have the main chat LLM ask the user if they exercised today, in order to collect that information from the user, in order to understand if the user is meeting their cultural objectives.
- Notifier: A program which nudges the user to continue the main chat after a longer break, in the form of a notification sent to the user's smartphone.
- (further parts/features to be defined)

The goal of this "Orchestrator" project is to orchestrate all those parts, as well as to implement some central elements such as central database which will be used by all those parts. 
Each part has been already implemented in the form of a python project. Each part exposes a REST endpoint, which can be called (by the Orchestrator) to do whatever this part is supposed to do.

The Orchestrator is going to informt the Extractor about user prompts to the LLM via Main Chat. This must happen AFTER sending the user prompt to the Main Chat, because the Extractor is going to utilize the Main Chat as well, and thus should run after the Main Chat generates the response to the user that.

user_objectives (/tasks) are objectives which the user should achieve.
ai_objectives are objectives which the LLM should achieve.

TODOs:
migrate GOOGLE_API_KEY= from all services to the main .env
fix day breaks across the board. everything should have only current day active by default.
MD instead of pure html chat window
ONE database.
remove all secrets. text field (and instructions) in the front-end for google ai api key.
update this README to reflect reality (e.g. the orchestration being the frontend). Note that the backend services are not independent; their only dependence is the db / tables.
abstract the provider away and implement and test ollama.
Fix negative objectives.
TTS, STT

the entire server-side should run on Mobile, so that users have to only install one app.
central config for all params in all services
migrate to tailwind and check if Sonnet is better with that than plain css...
Overseer or Meta-overseer should be able to dynamically alter the system prompt of any other component.
tasks and objectives need to be formatted as an array within json. taskupdater LLM system prompt instruction must return that format. etcetc.
