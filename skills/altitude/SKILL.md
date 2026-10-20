---
name: altitude
description: Deliver an answer at four reading altitudes - one HTML artifact with a 10k, 5k, 1k, and 100 view of the same topic as tabs, opening on the 10k view. Use when the altitude hook says altitude views are on, when the user asks for altitude, views, or a 10k view, or when the user types '/altitude'. Changes how the answer is delivered, not how the work is done.
---

# Altitude

## Overview

Reading is the slowest step when you work with an agent all day. The agent writes in minutes, and the person still has to read it, understand it, and decide. Altitude gives every answer at four depths so the reader picks the one that fits the moment and goes deeper only when they need to.

You do the work exactly as you would without this skill: investigate, query, write code, open PRs. Altitude only changes how you deliver the result.

## Quick Reference

- One HTML artifact, four tabs, each answering one question: 10k "What is it?", 5k "How does it work?", 1k "What should we decide?", 100 "Prove it."
- Keep the tab labels short: 10k view, 5k view, 1k view, 100 view.
- Start each tab with one line that states its question and when to read it. Build on the tab above. Don't start the story over.
- Always open on the 10k view.
- The 10k view is a stack of panels: a plain-sentence headline, one big picture, one line. Write it for someone who knows nothing about the topic.
- Every view covers the whole topic, including decisions and risks, at its own depth.
- Every view uses visuals.
- The 100 view is the full version.
- In the session: three to five bullets, the link, and one next action.

## When this applies

- The altitude hook added context saying altitude views are on for this prompt.
- The user asks for altitude, views, or a specific view, such as "give me the 10k view."
- The user types `/altitude`. With a topic, build views of that topic. Without one, build views of the most recent answer in the session.

If the user says "no views", answer normally for that prompt.

## What you deliver

1. **One HTML artifact with four tabs:** 10k view, 5k view, 1k view, and 100 view, in that order. It always opens on the 10k view. Follow [the tab template](reference/tab-template.md).
   - If you have an Artifact tool, publish the page with it.
   - If you don't, write the page to the session's scratchpad directory, or the working directory if there's no scratchpad, and give the path.
2. **A short summary in the session:** three to five bullets that say what the 10k view says, the link or path to the page, and one next action.

Don't paste the views into the session as text. The page is the answer.

## The four views

Each view answers one question. The question is the view's job, and it's the first thing the reader sees when they open the tab.

| View | Question | Must include | Keep out |
| --- | --- | --- | --- |
| 10k | What is it? | Written for someone who knows nothing about the topic. A stack of panels, one idea each: a short headline sentence, one big picture, and one line under it. What it is, why it matters, and the one risk that matters most. See [Building the 10k view](#building-the-10k-view). | Code, file names, jargon, paragraphs |
| 5k | How does it work? | A diagram of the moving parts. One short paragraph per part. A flow showing how data moves. Side effects by name. | Line-level detail |
| 1k | What should we decide? | The edge cases, risks, and trade-offs that matter, each open decision with a recommendation and the numbers behind it, and the plan or PR sequence. Use flows and decision tables. If there's nothing to decide, answer "What could go wrong?" instead and say so in the tab's first line. | Re-explaining how it works, raw code dumps |
| 100 | Prove it. | The evidence behind every claim in the views above, plus everything else that's true and relevant: file paths with line numbers, queries with results, PR links, commands to reproduce, alternatives considered. Charts, timelines, and annotated diagrams wherever they read faster than text. | Claims without evidence |

The pictures also go from fastest to slowest to read as you go down: big pictures at 10k, a parts diagram at 5k, flows and decision tables at 1k, and charts, tables, and code at 100.

## Moving between views

Readers can't tell which view they need until they know what's in it. Each tab has to say what it's for, and it has to pick up where the tab above it left off.

- **Keep the tab labels short.** The tab bar reads `10k view`, `5k view`, `1k view`, and `100 view`.
- **Start each tab with one line that states its question and when to read it.** Put the question in bold. For example:
  - 10k: "**What is it?** Start here. What this is, in pictures."
  - 5k: "**How does it work?** Read this if the 10k view made sense and you want the moving parts."
  - 1k: "**What should we decide?** Read this if you need to make a call. The risks, trade-offs, and what I'd do."
  - 100: "**Prove it.** Read this to check any claim above. The evidence behind each one."
- **Build on the tab above. Don't start the story over.** The 5k view assumes the reader saw the 10k view. Refer back to it, such as "The 10k view showed the order changes. Here's what decides the order." Don't re-introduce the topic with a new framing on every tab.

## Rules for every view

- **Same topic, different depth.** Altitude is about depth, not topic. Each view covers the whole answer, including its decisions, side effects, and risks, at that view's depth. Don't save the risks for the deep views.
- **Visuals at every altitude.** Pictures aren't only for the 10k view. Use a parts diagram at 5k, flows and decision tables at 1k, and charts and annotated diagrams at 100. If a picture reads faster than a paragraph, use the picture.
- **Depth isn't length.** A short 100 view can take the longest to read, because it assumes the reader knows the services, tables, and code. Write each view for the context its reader brings, not to a word count.
- **Every claim is checkable one tab down.** If the 10k view says "this affects 183 members", the 1k or 100 view shows where that number comes from.
- **The 100 view backs up everything.** A reader who doubts any claim in a higher view finds the evidence for it there.
- **Lead each view with its answer.** Right after the tab's intro line, say what the reader needs to know at that depth.
- **Same structure for every role.** Engineering, product, and design readers get the same four views. Adjust the words and examples to the audience, not the structure.

## Building the 10k view

Write the 10k view as if you were told: "Explain this like I'm someone who knows nothing about this topic, using big pictures and few words." It's the view most people read, and often the only one.

Build it as a stack of panels. Each panel holds one idea:

1. **A headline that's a short, plain sentence.** It states the idea, such as "Same slots. New order. That's it." Not a label like "Overview."
2. **One big picture** that shows the idea, drawn as inline SVG and filling the panel's width.
3. **One line under the picture,** or nothing. Never a paragraph.

Rules for the pictures:

- **Draw real things from the topic's world,** like a van on a road, a tech's calendar with a gap, a switch, a receipt, a padlock, or a stack of pages. Avoid generic boxes and arrows when an object would say more.
- **Show the change, not the system.** Before and after, on and off, this one versus that one.
- **Put the words inside the picture** as short labels a non-engineer would use, such as "how far out of the way?" or "only if you need it."
- **Use big type.** Labels around 18 to 26 pixels, headlines around 30 to 44 pixels. Leave room around everything.
- **Use one accent color** for the thing that matters in each picture. Keep the rest neutral.
- **Use made-up names and numbers only when you label them as examples.** Real numbers must come from the work.

Use 5 to 10 panels: what it is, why it matters, how it changes things, the risk that matters most, and what to do next. Panels can split into two side-by-side pictures to compare, like before and after. End with the one thing the reader should do or know. The [tab template](reference/tab-template.md) has the panel styles.

## Fitting the views to the task

The four views always exist, but what fills them depends on the task:

| Task | 10k: What is it? | 1k: What should we decide? | 100: Prove it. |
| --- | --- | --- | --- |
| Customer bug | What's broken and who it hits | Fix now or later, and how big it is across accounts | Trace, queries, and results |
| Initiative or plan | The big picture | Decisions with recommendations, PR sequence | Every alternative and trade-off, with evidence |
| Clear ask, like a fix or PR | What changed and what to check before merge | Edge cases and risks to check before merging | The diff, tests, and PR links |
| Explainer | What it is, in pictures | What could go wrong, and what's tricky | Code paths and data |

## Messages for someone else

If the user asks for a message to send someone, such as a Slack DM, draft it from the 10k or 5k view, whichever matches the recipient. Format it for Slack and send it to the user to review first. Never send it yourself.

## Common Mistakes

- **A 10k view made of paragraphs or bullet lists.** If a panel needs more than one line of text, the picture isn't doing its job.
- **Labels for headlines.** "How it works" says nothing. "Every slot gets asked four questions" says the idea.
- **Pictures only in the 10k view.** The deeper views need visuals too, with more detail in them.
- **Saving the risks for the 1k or 100 view.** A reader who stops at 10k still needs to know the one risk that matters.
- **A 100 view that only holds code.** It proves the claims above, so tie each piece of evidence to the claim it backs.
- **Starting each tab over.** If every tab re-introduces the topic with its own framing, readers get lost moving between them. Each tab builds on the one above.
- **A tab with no question at the top.** "1k view" doesn't tell anyone what's inside. The first line of the tab has to.
- **A 1k view that re-explains how it works.** That's the 5k view's job. The 1k view is about decisions, risks, and trade-offs.
- **Pasting the views into the session.** The page is the answer. The session gets a short summary.
- **Opening on a deeper tab** because the task looks technical. Always open on the 10k view.
- **Inventing numbers to fill a chart.** Only chart data you looked up.
