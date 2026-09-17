# Voice Workflow Proposal

## Goal

Build a responsive Raspberry Pi robot that handles routine voice commands locally and only opens a paid GPT-Live connection when conversation or current information is needed.

## Proposed workflow

### 1. Local listening

- Keep local voice recognition running on the Raspberry Pi.
- Use Vosk with a restricted vocabulary of known commands.
- No audio is sent to the internet in this mode.
- Local recognition has no per-use API cost.

Example commands:

- "Lights on"
- "Lights off"
- "Move forward"
- "Turn left"
- "Stop"
- "Let's talk"
- "Start a conversation"

### 2. Local commands and prerecorded responses

When Vosk recognises a known command, Python runs the corresponding robot function immediately.

Examples:

| Spoken command | Robot action | Prerecorded response |
|---|---|---|
| "Lights on" | Turn on the lights | "Certainly, turning them on." |
| "Move forward" | Start the drive motors | "Moving forward." |
| "Stop" | Stop the motors immediately | "Stopping." |
| "Let's talk" | Open a GPT-Live session | "Okay, let's talk." |

Responses should be generated once with OpenAI text-to-speech, saved as WAV files, and played locally thereafter. Several variations can be stored for common commands to make the robot feel less repetitive.

Use the same voice for prerecorded and live speech where possible. Marin or Cedar should provide better consistency between the two modes. Fable could be used for prerecorded British speech, but it would not match the live GPT-Live voice.

### 3. GPT-Live conversation mode

A specific local command opens the GPT-Live WebSocket.

While connected:

- Stream microphone audio to GPT-Live.
- Play returned audio as it arrives.
- Maintain a natural multi-turn conversation.
- Use instructions to request a clear, natural British English accent.
- Reset an inactivity timer whenever the user or robot speaks.

After approximately 60 seconds with no meaningful activity:

1. The robot says a short closing phrase, such as "I'll go back to sleep."
2. Python closes the WebSocket.
3. The robot returns to local Vosk listening.

This prevents an idle connection from continuing to incur time-based GPT-Live charges.

### 4. Permission-based web search

GPT-Live should not guess when a question requires current information or when it is uncertain.

Expected interaction:

1. The user asks a question requiring current information.
2. The robot says it is unsure and offers to check the internet.
3. The robot waits for explicit agreement.
4. If the user agrees, the robot says it is searching.
5. GPT-Live delegates the task to a Responses model with the web-search tool.
6. The search result is returned to the live conversation.
7. The robot speaks a concise summary and mentions relevant dates.
8. If trustworthy information cannot be found, the robot says so clearly.

Suggested instruction:

> If a question requires current information or you are unsure, do not guess. Explain that you are unsure and ask whether the user wants you to search the internet. Do not search until the user agrees. After agreement, briefly announce that you are searching. Summarise the results clearly, include relevant dates, and say when reliable information cannot be found.

The Python application should also enforce the permission requirement rather than relying only on the model instruction.

## High-level decision flow

```text
Local microphone
    |
    v
Vosk recognises speech
    |
    +-- Known local command --> Run Python function --> Play prerecorded response
    |
    +-- Conversation command --> Open GPT-Live WebSocket
                                      |
                                      +-- General conversation --> Speak answer
                                      |
                                      +-- Current/unknown question
                                              |
                                              v
                                      Ask permission to search
                                              |
                                  +-----------+-----------+
                                  |                       |
                                 No                      Yes
                                  |                       |
                           Continue without       Announce search
                              searching                  |
                                                       v
                                            Responses API + web search
                                                       |
                                                       v
                                              Speak concise result
                                      |
                                      v
                              60 seconds inactive
                                      |
                                      v
                           Close WebSocket and return
                              to local listening
```

## Cost-control principles

- Keep wake-word detection and routine commands local.
- Reuse prerecorded WAV responses.
- Open GPT-Live only for real conversations.
- Close the WebSocket after inactivity.
- Require permission before paid web searches.
- Keep spoken answers concise.
- Log session duration, searches, and approximate cost for later tuning.

## Suggested implementation order

1. Confirm microphone input and speaker output.
2. Add Vosk with one safe command, such as "stop."
3. Map several local phrases to Python functions.
4. Generate and play prerecorded WAV responses.
5. Open GPT-Live from a local conversation command.
6. Add the inactivity timer and clean WebSocket shutdown.
7. Add Responses delegation and web search.
8. Enforce search permission in Python.
9. Add logging and test the full workflow.
