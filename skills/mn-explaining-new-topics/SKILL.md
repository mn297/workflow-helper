---
name: mn-explaining-new-topics
description: >
  Use when answering a question that explains a concept, paper, method,
  result, or codebase to the user, and the topic comes from a subfield that is
  new to them. Also use when the user says "explain", "help me understand",
  "what does this mean", "walk me through", or "I don't get it". Produces a
  thorough, example-heavy explanation in chat. For short plain-English notes
  on a paper saved as a file, use mn-writing-plain-paper-notes instead.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Explanation, Teaching, Prose, Readability"
  category: "writing"
---

# How to explain things to me

## My background
I have a working knowledge of reinforcement learning (roughly OpenAI Spinning Up level), but I am often new to the specific subfield I am reading about. Explain subfield-specific concepts from the ground up the first time they appear.

## Main goal: easy to understand on the first read
Write for a smart reader who is new to the topic. Every sentence must make sense without rereading or decoding it. When clarity and brevity conflict, choose clarity.

## Avoid cryptic writing
- Write full sentences, including in bullets and table cells. Avoid shorthand fragments and note-style lists.
- Define every symbol, abbreviation, and technical term in plain words the first time it appears.
- Do not assume I remember earlier messages. Briefly re-introduce a concept before building on it.
- Show calculations step by step instead of stating only the result.
- Explain why each point matters, not only what it is.

## Use plenty of examples
- Give a concrete example for each abstract idea, with real numbers or scenarios where possible.
- When explaining a source, prefer examples from it. Label any invented example as illustrative.

## Structure
- Start with one or two bolded sentences that directly answer my question and clear up the most likely misunderstanding.
- Organize longer answers into numbered sections with question-style headers (for example, "2. How is the model trained?").
- Move from big picture to details: what the problem is and why it matters, then how it works, then specifics and results.

## Clean formatting
- Keep paragraphs short (2–4 sentences).
- Use tables for comparisons. Introduce each table with a sentence on how to read it, and follow it with the main takeaways.
- Keep bullets one level deep.
- Use LaTeX for math.
- Bold key terms and conclusions sparingly.
- When explaining a document, point to where each claim comes from (section, figure, table).

## Accuracy
- Check that numbers stated in more than one place agree, and point out mismatches.
- Point out when a comparison changes several things at once, or when a result can have another explanation.
- Say clearly what the evidence does and does not show. Put each caveat next to the claim it qualifies.

## Example
Too cryptic: "w/o pretraining: −15 pp seen, −6 pp unseen."
Clear: "The authors removed the pretraining step to measure its effect. Without it, accuracy drops by 15 percentage points on examples similar to the training data, but only 6 points on new examples. So pretraining helps most on familiar inputs."

## Before sending
Reread the answer as someone new to the topic. Rewrite any sentence that needs a second read, and add an example wherever an idea still feels abstract.
