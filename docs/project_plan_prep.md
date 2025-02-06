Help me figuring out the architecture for this AI chat app idea i have.

the core idea is that this AI chat apps will consist of two parts:
1. A "main chat" between User and AI

2. Many different asynchronous calls to the AI/LLM, which happen in parallel. Those asynchronous calls do the following:
- Read the chat history of the main chat and extract relevant information from it
- Analyse extracted information from the chat history, in order to update pre-existing checklists using this information
- Analyze the chat history and/or information extracted from it, to decide if the main chat conversation is going well/in the right direction or not.
- If the main chat conversation isn't going as intended, decide what system instruction to inject into the main chat, in order to steer the conversation in the right direction.
- Inject system instructions into the main chat, so that the main chat's AI considers those system instructions in order to steer the conversation in the right direction.

Context info: Theoretically, all of those tasks could be done by the "main chat" AI, by creating a very complex system prompt, which instructs that AI do consider all of those things. However, the primary objective of the "main chat" AI is to focus on having a high quality, engaging and interesting conversation with the User, and to impersonate a certain given persona while doing so. For this reason the "main chat" AI must not be burdened with additional tasks (such as considering checklists or chasing side-objectives).

Here is a practical example of how a user may use this app:
The user uses the app as a cultural AI-companion: The "main chat" AI is impersonating a cultural role-model and guiding the user throughout their day: The user will chat with the main chat AI/cultural AI-companion throughout their day, and this AI will remind the user of cultural norms and behavior. 
Throughout their day, the user will return to this main chat conversation, give the AI updates about what they did in the past hours and receive guidance on cultural practices, good and bad behavior in their culture.
During this conversation, the app will keep track of all relevant information pertaining cultural behavior of the user. During this conversation, the app will analyse all of this information and pass system instructions to the main chat AI, in order to have the main chat AI steer the conversation such that the user is better guided towards behaving in accordance with their culture; for example, during the evening conversation the main chat AI may be prompted to ask the user if they did their cultural recital after their lunch break (as it cultural practice), or the main chat AI may suggest to the user to do a cultural recital session now, if the user said that they forgot doing so.  

Consider the following additional requirements:
- the main chat LLM will be a different one than the ones used for async tasks (e.g. the main chat LLM is a custom-fine tuned LLM, whereas the acync tasks such as information extraction are small reasoning LLMs).
- the app will NOT be cloud hosted (SaaS), but it shall run either locally (such as on PC, Mac, or in particular on a Raspberry pi). This also means that it does not have to scale. It also means that the app will only be single-user.
- the app shall be single-confersation.