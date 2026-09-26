# Voice and Command Architecture Notes

These notes capture design decisions from the current Python speech prototype so they are not lost when the robot moves to ROS.

## Core principle

Robot capabilities belong to the subsystem that implements them. Speech recognition is only one consumer of those capabilities.

For example, the lights subsystem should ultimately own its command definitions, the volume/audio subsystem should own volume commands, and the Big Brain subsystem should own the command that hands conversation to the online OpenAI path.

The current root `commands/` directory is a prototype registry. When the project is reorganised into ROS packages, move each command definition into the package/node responsible for that capability rather than making the voice node the authority on what the robot can do.

## Intended flow

Current prototype:

```
Moonshine speech recognition
        |
        v
CommandEngine
        |
        +--> deterministic local command --> subsystem
        |
        +--> obvious question/request not handled locally
                 |
                 v
          ask to open Big Brain
                 |
              yes/no
                 |
                 v
          Big Brain / OpenAI
```

Likely ROS version:

```
speech/ASR node
      |
      | transcript / speech observations
      v
command/interaction node
      |
      +--> subsystem command/action
      |
      +--> request robot speech
      |
      +--> Big Brain handoff
```

Do not make the ASR node responsible for command semantics.

## Separate interaction states

Keep these concepts separate:

1. **Attention** — is the user currently talking to Spencer? Wake words establish this and attention can decay over time.
2. **Subject context** — what subsystem/topic is the current command about? This should normally decay faster than attention.
3. **Pending confirmation** — Spencer has asked a specific question and is temporarily expecting an answer such as yes/no.

Pending confirmation is explicit state, not another form of wake-word or subject context.

## Confirmation and robot speech

A confirmation becomes active as soon as Spencer decides to ask it. The user must therefore be able to answer while the robot is still speaking.

Desired behaviour:

```
pending confirmation created
        |
robot starts speaking
        |
        |---- user may say YES/NO here (interrupt/barge-in)
        |
robot finishes speaking
        |
        |---- confirmation remains valid for ~5 seconds
        |
confirmation expires
```

Do **not** make CommandEngine understand WAV files or audio duration.

The voice/output component owns playback. It should report speech lifecycle events/state to the interaction/command component.

Conceptually:

```
SPEECH_STARTED   utterance_id=42
SPEECH_FINISHED  utterance_id=42
```

The command engine can start the post-question grace timeout when it receives the matching `SPEECH_FINISHED` event.

Use an `utterance_id` (or equivalent correlation ID) so an unrelated acknowledgement finishing cannot accidentally affect a pending confirmation.

This abstraction should work regardless of whether speech comes from:
- prerecorded WAV files
- Piper/local TTS
- another local voice system
- online/OpenAI speech

## Barge-in / interruption

Keep recognition active while Spencer speaks where practical. A valid response to a pending question should be accepted during playback.

Later, if the user gives a valid answer while Spencer is still speaking, the voice component should be able to stop/cancel the current utterance and the command should proceed immediately.

The interaction logic should not depend on whether cancellation is implemented yet.

## Execution acknowledgements

Eventually, spoken acknowledgement such as "Certainly" should happen after the target subsystem confirms that the command was executed, not merely because CommandEngine successfully parsed the sentence.

The current Moonshine playground acknowledges parser matches only as a prototype/test convenience.

## Big Brain fallback

`big_brain` specifically means handing the interaction to the more capable online conversational AI. Avoid using a generic `system` subject for this because `system` may later have broader robot-management responsibilities.

Clear local commands should win before fallback logic.

An obvious question/request that cannot be handled deterministically can trigger a subsystem-defined confirmation such as "Shall I open the Big Brain?"

Generic pending-confirmation machinery belongs in the interaction/CommandEngine layer. The meaning of the fallback, prompt, target action and parameters belong to the Big Brain subsystem's command definition.

Do not define `yes` as a permanent Big Brain command. Yes/no only have their special meaning while a confirmation is pending.

## ROS migration rule of thumb

When converting the prototype to ROS, preserve ownership and replace direct Python calls across component boundaries with ROS messages/actions/services where appropriate.

Do not redesign working semantics simply because ROS is being introduced. The Python prototype should deliberately model the eventual boundaries now.
