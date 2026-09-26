# Voice and command design principles

This is the design guide for **Spenser Two-Point-Oh**. It records the reasons behind the voice and command work so the project is understandable beyond the checklist in [TODO.md](../TODO.md). The [voice workflow proposal](../voice-workflow-proposal.md) contains the broader interaction vision and the detailed audio effect. This guide distinguishes **working prototype**, **chosen direction**, and **idea to test**.

## The experience we are building

Spenser should eventually live independently in the house and feel like a member of the family: attentive, useful, playful and capable of looking after itself. The first milestone is a **stationary, desk-bound social robot**, before drive motors or autonomous navigation. A person should be able to speak naturally while the robot looks towards them, listens, thinks, answers and uses small eye, head and arm movements to show attention.

The robot is physically present, so conversation and action must agree. It should not say that it turned on a light, moved an arm or exited AI mode unless the application actually did so. Spoken replies should be brief enough to sound natural.

## Three layers of intelligence and control

| Layer | Purpose | Boundary |
| --- | --- | --- |
| Speech recognition | ReSpeaker audio into words or a wake event; Vosk is the current prototype, while Sherpa/other neural recognition is to be evaluated | Recognition does not itself authorize an action |
| Deterministic command parser | Match known subjects, actions and bounded values using explicit rules | Execute only one unambiguous, validated intent |
| Local language model | Interpret flexible wording, short personality replies, intent and parameters | Produces constrained requests; cannot directly operate hardware |
| OpenAI voice conversation | Richer conversation, reasoning and current-information tools when needed | Requests the same robot capabilities through application code |

Python/ROS validates and executes capabilities; subsystem controllers own their state; the Arduino handles low-level hardware. The local and cloud models should share the robot's purpose, personality and *available capabilities* so changing modes does not change what the robot claims it can do.

A local command should remain possible if the internet or API is unavailable. Opening and closing cloud conversation are application actions, not something a model can merely announce. A future web search should be offered when current information is needed, with permission and tool access enforced in code.

## Deterministic parsing and neural speech: keep the distinction

**The central principle:** speech recognition and command parsing answer different questions. A recogniser estimates *what words were said*. A deterministic parser decides whether those words match a defined command. A neural recogniser such as **sherpa-onnx** could improve or replace the speech-to-text/wake stage without changing the rules that grant an action. Conversely, a local language model may interpret natural phrasing, but its output must pass the same capability validation before anything happens.

```text
Microphone
  → speech/wake recognition (Vosk today; Sherpa or other neural option to test)
  → deterministic command match first
      → one valid match: request the named capability
      → no match or ambiguous: clarify or try local language interpretation
  → validate any proposed action against the same capability schema
  → ROS controller / hardware
```

The deterministic path is useful for routine, well-defined commands because its vocabulary, parameter ranges and failure conditions are inspectable and testable. It should remain available offline. Neural speech recognition is a candidate way to improve recognition in real household conditions; it is **not** a replacement for explicit command permissions, range checks or control ownership. The neural *language* model is a separate optional route for indirect requests such as “It's a bit dark in here,” multi-intent phrases and short conversation. Do not confuse the speech model's transcript with a validated intent, or a language model's confident wording with proof of user intent.

**Current evidence and open decision:** `vosk_commands.py` implements the deterministic parser and Vosk grammar as a prototype. The repository does not contain a Sherpa implementation or a recorded selection of a Sherpa model. Evaluate Sherpa/other neural recognition against Vosk on the Pi 5 for wake accuracy, household noise, latency, RAM/CPU use and command transcription; retain the same parser and command tests when swapping recognisers. Decide separately whether keyword spotting, speech activity detection and transcription should use one engine or multiple components. The [sherpa-onnx project](https://github.com/k2-fsa/sherpa-onnx) documents offline recognition, keyword spotting and voice activity detection, but their suitability for this robot still needs measurement.

## Listening, wake and conversation

**Working prototype:** [`vosk_commands.py`](../vosk_commands.py) constructs a constrained Vosk grammar from [command definitions](../commands), recognises a wake-word vocabulary (`robot`, `spencer`, `spenser`), and remembers a recent subject for 15 seconds after a matched command. That subject context allows a short follow-up such as “lights blue” followed by “red.” This script currently **prints** a matched command or a handoff suggestion; its `-> EXECUTE` line is not proof of hardware execution. The wake words are currently removed from parsed words; this prototype does not yet enforce the planned inactive-to-active wake gate.

**Chosen direction for the next local voice workflow:** After five minutes without an exchange, clear the short conversation history and require the selected local wake recogniser to hear the wake word before sending speech to the local model. During an active conversation, do not require the wake word every turn. Keep at most ten recent exchanges. Supply the permanent instructions, capability definitions and *live* robot state separately from that rolling history; refresh state as devices change.

The 15-second subject context in the exact-command prototype and the planned five-minute conversation window solve different problems. They should not silently become the same timer. When cloud voice is active, route the microphone to that session and avoid competing normal Vosk transcription as appropriate, while keeping the local path ready to resume. Connection startup, readiness, timeout and return to local listening should be visible or audible to the person.


## Potential interaction architecture: attention, evidence and response policy

The following ideas are **design candidates to test**, not yet implemented. They refine the simple wake + deterministic parser + SLM model above.

### Dual Vosk as evidence, not just transcript replacement

Run unrestricted and reduced-vocabulary Vosk recognisers over the same audio. The unrestricted recogniser preserves natural language; the specialist recogniser is biased towards Spencer's known wake words, subjects and command parameters. Align their words by timestamps, as `vosk_dual.py` already demonstrates.

Do not treat timestamp overlap alone as recognition confidence. Preserve each recogniser's Vosk word `conf` value as well as start/end times. A specialist word may confirm the unrestricted recogniser, plausibly correct a low-confidence near-homophone (for example unrestricted `blew` versus specialist `blue`), or conflict with a strong unrestricted result. Strong conflicts should not be silently overwritten.

Useful evidence to retain/log includes full transcript and word confidences, specialist transcript and word confidences, timestamp overlap, agreement/conflict, speaker identity/continuity, wake age, subject age, candidate command and final routing decision. This may later provide a real-world dataset for tuning or learning, without requiring a machine-learning classifier now.

### Separate attention from command context

A wake word is not a command subject. Hearing `Spencer` should be able to open an attention window even when no subject or action occurs in that utterance:

```text
"Hello Spencer"
    → attention opened; no action

"Turn the lights blue"
    → explicit subject + value while attention is active
    → execute
```

Likewise, information may accumulate over several utterances: `Spencer` → `lights` → `blue`, provided the evidence remains sufficiently fresh. A completed command can establish a recent subject so short follow-ups such as `red`, `medium` or `more` can inherit it.

Attention and subject context should remain separate state. A person may still clearly be talking to Spencer after the previous command subject has become too stale to inherit safely.

### Replace the hard 15-second cliff with decaying evidence

The current 15-second subject timeout is a useful prototype. A later implementation could make contextual trust decay continuously instead of changing abruptly from valid to invalid.

A sigmoid/logistic decay is attractive because evidence can remain almost fully trusted for a short grace period and then fall quickly around a configurable midpoint:

```python
strength = 1 / (1 + math.exp(k * (age - midpoint)))
```

Wake/attention and subject context can have different curves. Attention may reasonably decay more slowly than permission to assume that a bare word still refers to the previous device. Meaningful Spencer-related events may refresh appropriate state, but arbitrary background speech should not keep attention alive forever.

### Use multiple evidence dimensions, not one magic confidence

Keep at least these concepts distinct:

- **recognition confidence** — how strongly Vosk supports the recognised word;
- **attention confidence** — how likely it is that this utterance is directed at Spencer;
- **command confidence/relevance** — how strongly the utterance maps to one valid robot command.

A future evidence scorer can combine wake strength, subject strength, specialist confidence, unrestricted confidence, recogniser agreement, speaker continuity and conflict penalties. Weighted/logistic scoring is preferable to blindly multiplying probabilities. Hard gates may still be appropriate for some conditions.

The deterministic parser remains valuable: it extracts candidate subject/action/value from the capability JSON. The evidence layer decides whether that candidate is trustworthy enough to execute. This replaces a simple binary exact-match decision without allowing the scoring layer to invent capabilities.

### Routing: ignore, act, clarify or converse

The most useful routing distinction is whether Spencer is being addressed before deciding whether speech is a command.

```text
speech
  → attention evidence
      → low / outside wake window: ignore (do not send ordinary household speech to SLM)
      → uncertain: ask "Was that for me?"
      → high: analyse command relevance
          → high: execute validated command
          → uncertain: ask a targeted clarification
          → low: pass full utterance to local SLM as conversation
```

Low command relevance is not necessarily low recognition confidence. `Tell me a joke` may be recognised perfectly and clearly directed at Spencer, but require no handwritten joke routine: it should fall through to the local SLM. Likewise questions and ordinary requests can go to the SLM once attention is established.

Question-like language (`what`, `why`, `how`, `can you`, etc.) is useful evidence for conversational routing, but must not be an absolute rule: `Can you turn the lights blue?` is still a clear robot command.

An ambiguous command-like phrase can trigger clarification rather than an SLM guess. Examples include asking `Did you mean make the lights blue?` or, when attention itself is uncertain, `Was that for me?` Once clarified, the utterance can be executed or passed onward with that ambiguity resolved.

### Compatible parameters versus genuine conflict

Do not eventually treat every multi-match utterance as ambiguous. `red blue lights` contains conflicting values for the same property and should not be guessed. `lights blue medium`, however, can naturally mean colour=blue **and** brightness=50 and may eventually become two compatible validated actions.

### Local SLM and cloud AI are engines behind one Spencer

The local SLM should handle ordinary conversation and flexible language after attention/routing. Higher-level cloud/realtime AI is for harder reasoning, current/web information or explicit user requests. Routing words such as question/help/explain/search may provide evidence, but the local model can also decide that a problem exceeds its capability.

When escalating, transfer a compact recent transcript plus authoritative structured robot events/state and instruct the realtime session to continue as the same Spencer rather than introduce a new assistant. Do not necessarily send an unlimited conversation history; use a rolling history plus summary/state.

The user should be made aware when the realtime/WebSocket connection opens so it is not accidentally left running. Spencer might say something like `I'll bring the online AI in for this`, and later `I'll go back to local mode`. A physical LED/display indication of an active online connection is also desirable. Explicit commands such as go local, close the connection or stay online may override automatic routing. Cloud idle timeout is separate from wake/attention and command-context timing.

When cloud mode closes, pass a compact summary of useful conclusions back into local conversational state so Spencer retains continuity.

### Speaker continuity

Speaker recognition is another independent signal. Sherpa can provide speaker embeddings/verification; persistent unknown identities would require Spencer's own speaker manager. The first useful distinction may simply be owner/same-speaker versus unknown/speaker-changed.

A speaker change should weaken or break inherited command context even when only a few seconds have elapsed. Authoritative history is retained, but a new person should not automatically inherit another person's terse `more` or `right` command context.

### Deterministic acknowledgement and personality

Command interpretation and acknowledgement should be separate. After a validated action, a response manager decides whether Spencer should give a rich, short, minimal or silent acknowledgement.

Input length is useful evidence but interaction structure matters more. A new, polite request may deserve a fuller response; a terse continuation or repeated adjustment should usually get less speech.

Example:

```text
"Spencer, turn the lights blue please."
    → execute
    → "Certainly, Jonathan. I love blue."

"Turn them down."
    → execute
    → "Okay."

"More."
    → execute
    → silence
```

Possible response-policy evidence includes: new wake interaction, first command in a sequence, utterance length/politeness, follow-up status, repetition count, time since last spoken acknowledgement and command confidence. Higher uncertainty can justify an acknowledgement that also confirms the interpretation (`A little brighter`) so a mistaken action is easy to correct.

Silent does not mean expressionless: a head movement, eyes/display response or other subtle physical acknowledgement can replace repetitive speech. Small controlled variation among suitable prerecorded/generated acknowledgements can add personality without invoking the SLM. Later a simple mood/personality state can modify wording and gestures while remaining separate from command authority.

### Learning is deliberately deferred

A Bayesian scorer, logistic regression or tiny neural classifier could eventually learn routing/intent weights from real Spencer interactions, but this is not required for the first implementation. Do not treat an SLM guess as ground truth. Explicit user corrections/confirmations and exact deterministic matches are much stronger labels.

For now, collect the evidence needed to evaluate the simpler system. The dual recognisers, their confidences, contextual decay and explicit routing rules may already provide sufficient behaviour. If learning is introduced later, the accumulated logs can train/tune the weights without changing the capability schema or downstream ROS interface.

### Candidate state to keep independent

A future interaction manager may maintain values such as:

```text
attention_state / wake_time
current_speaker / speaker_changed
active_subject / subject_time
last_action / command_context
full + specialist recognition evidence
command candidate + command confidence
conversation depth/history
ai_mode = LOCAL / CLOUD
cloud_idle_time
last_response_time
repetition_count
personality/mood state
```

These are deliberately separate because they answer different questions. Avoid collapsing them into one timeout or one confidence number.


## How commands should work

1. **Recognise words, then interpret intent.** The current Vosk prototype reports speech; a tested replacement could use Sherpa or another neural recogniser. The exact-command parser or local model decides whether the person addressed the robot and what they meant. A phrase can contain multiple intents or parameters.
2. **Prefer exact local matches for routine controls.** Definitions in `commands/*.json` supply subjects, aliases, actions, named values and bounded percentages. In the current parser, a deterministic match means exactly one candidate action.
3. **Treat uncertainty as uncertainty.** No subject or zero/multiple matches go to further interpretation or clarification. A model's plausible guess is not sufficient authority for a physical action.
4. **Constrain model output.** Free-form text is suitable for short casual replies. For robot actions, restrict the output to defined capabilities and device/command/value combinations. Python checks the request against the current capability schema, parameters, state and safety rules before dispatch.
5. **Use one capability layer.** Local and cloud paths should request the same high-level operations, such as `set_light`, `look_at`, `get_robot_state`, `start_game` and, eventually, bounded arm or navigation actions. Unsupported actions should be reported honestly.
6. **Keep hardware authority below language.** A model can request a behaviour; it does not generate servo positions, bypass joint limits, directly open the Arduino serial port or override a subsystem controller. Test new intents with logged/simulated outputs before enabling real movement.

For example, “It's a bit dark in here” may become a `set_light` request with a validated brightness; “go to sleep” should become a robot-level `sleep` behaviour that coordinates eyes, LEDs and arm/head rather than a voice node directly commanding each device. See the [ROS command flow example](ros-command-flow-example.md).

### Command vocabulary is a capability description

The current JSON definitions cover lights (power, brightness, colour and warmer/cooler) and volume (mute, level and relative adjustment). They are a useful seed for the constrained command schema, not a promise that each operation already controls hardware. Keep names, ranges, synonyms and actual implementations in sync. A percentage must remain within 0–100, and relative adjustments should use the authoritative current state rather than a model's recollection.

The current [`system-prompt.txt`](../config/system-prompt.txt) is a prototype: it lists lights and motors and includes illustrative robot state. Its sample state must not be treated as live telemetry. Before execution is wired up, derive the allowed actions and current state from authoritative application data instead of maintaining conflicting handwritten lists.

## The sound and personality

The speaking character is composed, observant, friendly and mildly cheeky, with understated dry humour and concise British English. It knows it is a physical robot. A traditional British butler manner is used in the current OpenAI Live prompt; the local prototype calls for short playful replies. Preserve the same core personality in both paths while tuning how formal each sounds.

**Working cloud voice prototype:** [`robot.py`](../robot.py) uses the OpenAI Live `ballad` voice, then mixes a mild two-carrier robotic effect with the dry signal and applies a SoX pitch shift of +800 cents. The desired result is synthetic but intelligible, with natural timing and expression. The effect's carrier phase continues across audio chunks to avoid clicks. See the [voice workflow proposal](../voice-workflow-proposal.md) for exact settings and tuning notes.

**Planned local speech:** Kokoro text-to-speech, initially with the Fable voice. Compare its perceived character and level with the cloud voice and prerecorded status sounds. Control final loudness at the playback/hardware mixer when possible; pushing the effect's digital gain too far clips the audio. The NeoPixel mouth should follow actual outgoing speech audio.

## Expression is a behaviour, not servo prose

The initial interaction states are **IDLE, LISTENING, THINKING and SPEAKING**. Possible later reactions include CURIOUS, AMUSED, CONFUSED and SURPRISED. A deterministic expression controller should provide blinking, gaze shifts and subtle head/arm gestures with small variations. The AI selects a high-level communicative intent; it does not script individual joint movements. Eye-ring LEDs should primarily provide useful lighting and game feedback rather than generic emotion colours.

The same boundary applies to games and autonomy. The robot may propose or participate in a game, but the application controls the hardware and safety conditions. A laser used for cat play, for instance, needs independent deterministic aiming and activation safeguards.

## ROS ownership and practical sequence

The planned path is: audio/local recogniser → deterministic parser, with local language interpretation when needed → validated capability/behaviour request → ROS subsystem controller → one Arduino bridge → hardware. A behaviour controller coordinates multi-part actions. One bridge owns the Pi–Arduino serial connection. Controllers retain authoritative device state and priority/override rules.

Near-term work is to benchmark a local model's quality, latency and memory on the Pi 5; connect recognition to structured, validated requests; run them first as logs; then introduce ROS messages and simulated behaviours. The later [voice proposal](../voice-workflow-proposal.md#planned-local-slm-voice-workflow) selects **Qwen2.5-1.5B-Instruct via llama.cpp** for the first local test, with **Qwen2.5-3B-Instruct** if needed. Its earlier SmolLM2/Qwen3 list is a set of candidate benchmarks, not the latest first-choice plan. Model selection remains provisional until measured on the Pi.

## Questions to settle through tests

- Which wake phrase is reliable in household noise, and how is false activation handled?
- Does Vosk or a Sherpa/neural recogniser perform better on the actual microphone and Pi while preserving the same deterministic command rules?
- When should local interaction escalate to cloud conversation, and when should it end?
- How should ambiguous or combined commands be clarified without making routine actions slow?
- What are the real output volume, latency and quality of Kokoro/Fable versus processed Live speech on the robot speaker?
- Which proposed capabilities are actually implemented and safe to expose, especially motion, games and the laser?

Record answers here when tested. Keep implementation tasks and completion ticks in [TODO.md](../TODO.md), and update this guide whenever a test changes a principle.
