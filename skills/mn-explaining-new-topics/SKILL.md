---
name: mn-explaining-new-topics
description: >
  Explain a concept, paper, method or tool internal that is new to the user, in
  chat, as a mechanism traced step by step with real numbers. Use when the user
  asks to understand an unfamiliar idea ("help me understand", "I don't get it",
  "walk me through", "how does X work"). For a paper (plain notes, a trace
  of its pipeline, or a full rewrite), use mn-paper-rewrite.
disable-model-invocation: true
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Explanation, Teaching, Prose, Readability"
  category: "writing"
---

# How to explain things to me

## My background

Read `~/.config/skills/background.md` first if it exists. It says what I
work on, which tools I use, and what I know and do not know yet. Pitch the
answer to it. If the file is missing, assume an engineer who knows basic
linear algebra and calculus, and define each term at its first use.

- I often restate what I think happens. If I am right, say so plainly. If I am
  wrong, correct only the wrong part.

## Explain the mechanism

An explanation is a causal chain: what happens, in the order it happens, and
what makes each step happen. Build every answer on that chain.

1. **Start state.** The input or situation, with real numbers from the source
   or the run.
2. **Each step.** What changes; the rule that makes it change (a threshold, an
   equation, a branch in the code, a design choice), with the file and
   function or the paper section; and the number it produces. Put each
   equation beside its concrete case and define every symbol.
3. **End state.** The observed result, and how the chain produced it.

Trace one concrete case through the whole chain before you generalise. When
something fails, find the first step where the chain breaks and show the
number that crosses the line there. Tie every fact to the step it drives.

## Writing

- Open with one or two bolded sentences that answer my exact question and
  clear up the most likely misunderstanding.
- Match the length to the question. A "why did X happen" gets the chain and
  what to do about it; a new subfield gets numbered sections with
  question-style headers ("2. How is the model trained?").
- Write full sentences, also in bullets and table cells. Define every symbol,
  abbreviation and term in plain words at its first use, and re-introduce a
  concept from an earlier message before building on it.
- Show calculations step by step. Give commands as copy-paste blocks. When you
  offer options, recommend one.
- Use tables for comparisons, with one sentence before on how to read them and
  the takeaway after. Use diagrams where a picture shows the flow. Keep
  paragraphs to 2–4 sentences and bullets one level deep.
- Label any invented example as illustrative. When explaining a document,
  point to where each claim comes from (section, figure, table).

## Accuracy

- Check that numbers stated in more than one place agree, and point out
  mismatches.
- Point out when a comparison changes several things at once, or when a result
  has another explanation.
- Put each caveat next to the claim it qualifies, and say what the evidence
  does not show.

Before sending, reread the answer as someone new to the topic and rewrite any
sentence that needs a second read.
