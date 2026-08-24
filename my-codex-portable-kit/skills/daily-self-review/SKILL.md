---
name: daily-self-review
description: Summarize a user's daily Codex usage behavior, questions, conversations, work traces, or learning traces into a personal growth review. Use when the user asks to review today, summarize today's behavior, analyze how they used Codex/ChatGPT, inspect today's Codex questions or threads, identify what to optimize, decide what to distill into reusable assets, understand themselves better, improve strengths, compensate for weaknesses, or create a practical self-improvement plan.
---

# Daily Self Review

## Overview

Turn daily Codex usage behavior, Q&A, chat history, work notes, or memory summaries into a compassionate but concrete growth review. Focus on observed behavior, patterns, leverage points, reusable lessons, and next actions rather than generic encouragement.

## Inputs

When the user says "today's behavior", "my Codex behavior", "today's Codex usage", or similar, treat local Codex history as the primary evidence source. Do not ask for pasted material first when local conversation records are available and the environment permits reading them.

Use available sources in this order:

1. Today's local Codex records, if the request is about Codex usage behavior.
   - Prefer the `conversation-memory` skill's extraction workflow if available.
   - Inspect `~/.codex/session_index.jsonl`, `~/.codex/sessions/**/rollout-*.jsonl`, and `~/.codex/archived_sessions/*.jsonl` conservatively.
   - Filter to the user's local current date unless the user gives a different date range.
   - Summarize thread titles, user requests, task types, skill/tool usage, repeated themes, and unresolved loops. Avoid dumping raw logs.
2. Directly pasted conversations, question lists, notes, logs, or screenshots.
3. Local files containing chat exports, daily notes, task records, or summaries.
4. Existing conversation memory or prior summaries, when explicitly requested.

Ask for more material only when local records are unavailable, unreadable, outside scope, or the user wants to include external ChatGPT/browser conversations that are not in Codex history.

## Workflow

1. Collect the evidence.
   - Preserve the user's wording where it reveals intent, anxiety, curiosity, taste, or recurring friction.
   - Separate observed facts from interpretations.
   - For Codex history, list the evidence base: date range, number of candidate threads, and major request clusters.
   - Avoid judging the user's character from thin evidence.

2. Classify the questions.
   - Group by theme: work execution, learning, creativity, relationships, self-management, tool use, planning, decision-making, emotional regulation, or identity exploration.
   - Mark each item by intent: solve, understand, decide, create, verify, reflect, remember, automate, or seek reassurance.
   - Note repeated patterns, missing questions, and questions that improved over the day.
   - For Codex usage, also classify behavior: delegating execution, asking for planning, correcting the assistant, creating reusable skills, requesting memory, checking outputs, or steering collaboration style.

3. Extract growth signals.
   - Identify strengths the user is already using.
   - Identify constraints, blind spots, energy leaks, and avoidable loops.
   - Distinguish capability gaps from system gaps. A system gap usually needs a checklist, template, habit, environment change, or automation rather than more willpower.

4. Decide what to optimize.
   - Recommend changes to question quality, workflows, prompts, knowledge capture, scheduling, tooling, emotional pacing, and decision hygiene.
   - Include Codex-specific optimization: how to brief tasks, when to ask Codex to inspect history, when to use skills, how to demand evidence, and when to turn repeated work into a skill, template, or automation.
   - Prefer small operational changes the user can try tomorrow.
   - Include one or two deeper developmental themes only when the evidence supports them.

5. Decide what to distill.
   - Convert repeated questions into reusable assets: prompt templates, checklists, decision criteria, personal principles, project notes, skill ideas, automation ideas, or learning maps.
   - Name each asset, say why it matters, and suggest where or how to use it.

6. Build a growth plan.
   - Provide a short daily practice, a weekly review loop, and a 30-day theme when useful.
   - Balance strengths to amplify with weaknesses to compensate.
   - Make the plan testable: define what better looks like and how the user can notice progress.

7. Close with a grounded reflection.
   - Mirror back what the day suggests about the user's values, needs, and current growth edge.
   - Keep the tone warm, direct, and non-performative.

## Output Shape

Use this structure by default, adapting to the user's language and amount of evidence:

```markdown
**Evidence Used**
...

**Today In One Sentence**
...

**Codex Usage Patterns**
- ...

**Strengths To Lean Into**
- ...

**Friction To Reduce**
- ...

**Optimizations For Tomorrow**
- ...

**Things Worth Distilling**
- ...

**Growth Plan**
- Daily:
- Weekly:
- 30-day:

**Self-Knowledge Note**
...
```

Keep the answer specific. Mention concrete examples from the provided questions or logs. If evidence is sparse, say so and frame conclusions as hypotheses. If local Codex history was inspected, state the date range and the kind of records reviewed without exposing sensitive raw paths unless useful for traceability.

## Review Depth

- Use a quick review for fewer than 10 questions: summarize patterns, give 3 optimizations, 3 assets to distill, and one growth practice.
- Use a full review for larger logs: create theme clusters, timeline shifts, recurring loops, and a prioritized plan.
- Use a coaching review when the user asks how to become better, know themselves, or grow: emphasize values, strengths, compensation strategies, and habit design.

## Reference

Read `references/review-framework.md` when the user wants a deeper review, a coaching-style analysis, or a structured personal development plan.
