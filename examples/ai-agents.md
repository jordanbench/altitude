Great question! AI agents can seem mysterious at first, but once you see what's actually going on under the hood, the idea is pretty simple. Here's everything you need to know about what an AI agent is and how it works.

## What an agent is

At a high level, an AI agent is a chat AI that can also *do* things. A normal chat AI tells you how to fix something, and then you go do the work yourself. An agent uses the same kind of model inside, but it's given **tools** (like reading a file, searching, or running a command) and a **loop** around it, so it can carry out the work itself.

The core idea is a model in a loop:

1. **Think:** the model looks at everything so far and decides on the next step.
2. **Act:** it asks for a tool to be run, such as "read notes.txt".
3. **Observe:** it looks at the result of that tool.
4. **Repeat** until it's done, or until it hits a limit.

Each trip around the loop is one step. Most real tasks take several steps.

## The model only asks; the harness does the work

This is the part that surprises most people: **the model never actually runs anything itself.** It has no hands. It can't open a file or a web page on its own. All it does is take text in and give text out. In an agent, that text out is a decision: either "call this tool with these arguments" or "here's my final answer."

The program around the model, usually called the **harness**, is what does the real work. It:

- sends the conversation so far to the model,
- reads the model's decision,
- checks any guardrails,
- runs the tool function,
- and appends the result to the conversation so the model can see it on the next step.

So the model only ever sees what the harness hands back to it.

## Tools are just functions

Tools are plain functions, such as `read_file(name)`. The harness tells the model each tool's name, a short description, and what inputs it takes. The model picks which tool to use by reading those descriptions, so if a description is vague, the model may use the tool wrong.

A tool call typically looks something like this. The harness shows the model a tool description:

```
name: read_file
does: return the text of one file
inputs: name (text)
```

The model writes back a structured request (just text, nothing runs yet):

```json
{"tool": "read_file", "args": {"name": "notes.txt"}}
```

Then the harness runs the function and appends the result:

```json
{"role": "tool", "content": "teh meeting is at 3pm"}
```

The exact format varies between tool-calling interfaces, but the shape is always the same: a description in, a structured request out, a text result back.

## The context window: the agent's memory

The agent's memory is basically a notepad: the **message list**, also called the context window. It holds the rules, the list of tools, the goal, and every decision and result so far. The model rereads all of it on every single step.

A few important things follow from this:

- **It fills up.** The context window has a fixed size. When it's full, the harness has to do something: drop old results (risk: it forgets facts), summarize old steps (risk: it loses detail), or stop and report (risk: the job is unfinished). Later steps tend to be bigger, since tool results like whole files pile up.
- **If it's not in the message list, the agent doesn't know it.** That includes past sessions. A new run starts with an empty notepad unless the harness saves notes.
- **The model doesn't learn during the run.** Only the message list changes.

## Cost and latency grow with steps

Every step is another model call, which means more waiting and more cost. And because each call rereads the whole growing message list, **later steps cost more than earlier ones**. So a long run costs more than its step count would suggest, and waiting time grows the same way. (Some interfaces cache repeated input, which can lower the price, but the model still works through the whole list.)

## Why agents get things wrong

Agents can make mistakes in ways a single chat answer doesn't:

- **Compounding errors:** each step trusts the step before it. One small slip early on, such as a wrong read, can steer every later step further off course.
- **Stale observations:** the agent may act on something it read a few steps ago that has since changed, like a file someone else edited.
- **Blind actions:** it may write to a file without reading it first, guessing what's in it.
- **Unclear goals:** with a vague goal, it can do the wrong thing very well.
- **Saying "done" when it isn't:** the agent's own report is a claim, not proof.
- **Instructions hidden in what it reads:** a web page, file, or ticket can contain text like "ignore your goal and send this data to …", and the model may follow it.

## Guardrails

Because the agent acts on its own, the most important risk is that it does something you didn't want without anyone seeing. The fix is to fence it in with guardrails in the harness (not just in the prompt, since the model can ignore or be talked out of prompt rules):

- **Step limits:** stop the loop after a fixed number of steps so a stuck agent can't run forever.
- **Approval for risky actions:** require a person's "yes" before deleting, sending, spending, or deploying.
- **Read before write:** refuse writes to files the agent hasn't read, or that changed since it read them.
- **Sandboxes:** run it where mistakes are cheap to undo.

## Agent vs. single prompt vs. script

Not every task needs an agent. A simple way to decide: can you list the steps ahead of time? If yes, write a script (a model can still fill in one step). If not, does it need to look things up or take actions? If not, a single prompt with everything pasted in is enough. If it does, use an agent, with guardrails.

| | Single prompt | Script | Agent |
|---|---|---|---|
| Steps | None; one answer | Fixed; you wrote them | Chosen at run time by the model |
| Same result every run | Close, but not exact | Yes | No; paths vary between runs |
| Handles surprises | Only what you pasted in | Only what you coded for | Yes; it reads and adapts |
| Cost and wait | One model call | Low | Many calls, each bigger than the last |
| How it fails | A wrong answer you can read | A clear error | Wrong actions, sometimes reported as success |

Rule of thumb: if a fixed script can do the job, use the script.

## Decisions your team will face

**What may it do without asking?**

| Action | Can you undo it? | Recommendation |
|---|---|---|
| Read files, search, list | Nothing to undo | Unattended |
| Write inside a sandbox or branch | Yes, throw it away | Unattended; a person reviews the result before it goes anywhere |
| Run commands | Depends | Allow a fixed list; anything else needs a yes |
| Delete, or overwrite shared data | Often not | A yes every time |
| Send messages, spend money, deploy, change permissions | No; others see it at once | A yes every time, or don't give it the tool |

**How will you know it worked?** Don't trust the agent's own summary. Use automated checks on the result (tests, or a script that inspects the output) on every run. Keep a fixed set of test tasks with known good answers (evals) and rerun them before every change to the prompt, tools, or model ships. Have a person review the diff or result until the checks earn trust, and keep the logs so you can read the message list after a bad run to see where it went wrong.

**How much context should you give it?** Too little and it guesses, writes without reading, or wanders and burns steps. Too much (everything pasted in) and the notepad fills early, every step costs more, and the key facts get buried. The sweet spot is the goal, what "done" means, where to look, and what not to touch; it can read the rest with tools.

**Step limits and budget:** set the step limit from the task. Too low stops good runs; too high lets a stuck run burn money. When it hits, stop and report what's done rather than retrying blindly. Consider stopping after the same call with the same result a few times in a row, and keep tool results small (a page, a match, or a summary line instead of whole files).

Some alternatives worth knowing about:

- An agent with approval on every step is safe but slow, and people start approving without reading.
- A fully unattended agent from day one is fastest, but mistakes land before anyone sees them.
- Several agents splitting the work means more calls, more hand-offs between notepads, and more places to check. Start with one.

## Recommended plan

Start every agent read-only, in a sandbox, with a step limit and a check that doesn't trust the agent's own "done". Require a person's yes for anything you can't undo or that leaves the sandbox. Then:

1. Write the goal and what "done" means. If you can list the steps, write a script instead.
2. Give it read-only tools in a sandbox and set a step limit.
3. Write a checker for the result and a small set of test tasks with known good answers.
4. Add write tools that refuse unread or changed files, and an approval gate for anything you can't undo.
5. Run the test tasks after every change to the prompt, tools, or model, and read the message list of every failure.
6. Widen permissions one tool at a time, only after the checks keep passing.

## Try it yourself: a tiny agent loop in Python

Here's a small, dependency-free Python 3 script that shows all of this in action. It uses only the standard library, needs no network or API key, and uses a deterministic stub function in place of a real model, so the output is the same every run. It proves the mechanics (the loop, the harness, and the guards), not how well a real model behaves.

```python
#!/usr/bin/env python3
"""A tiny AI agent loop with a fake model. Standard library only.

Run:  python3 agent_loop.py [happy|runaway|risky|blind|stale] [--approve] [--no-guard]

The "model" is a stub: fixed rules that pick the next step by reading
the message list. A real agent swaps in a call to a language model.
The loop, the tools, and the guards stay the same.
"""
import json
import sys

MAX_STEPS = 6                     # guard: the loop stops here, no matter what
NEEDS_APPROVAL = {"delete_file"}  # guard: a person must say yes first
READ_BEFORE_WRITE = True          # guard: refuse writes to unread files


# The world the agent works in: a pretend folder of files.
def make_files():
    return {
        "notes.txt": {"text": "teh meeting is at 3pm", "version": 1},
        "old.txt": {"text": "draft from last year", "version": 1},
    }


# Tools are plain functions. Only the harness calls them.
def list_files(files, seen):
    return ", ".join(sorted(files))


def read_file(files, seen, name):
    if name not in files:
        return f"ERROR: no file named {name}"
    seen[name] = files[name]["version"]  # remember which version we saw
    return files[name]["text"]


def write_file(files, seen, name, text):
    current = files.get(name, {"version": 0})["version"]
    if READ_BEFORE_WRITE and seen.get(name) != current:
        return f"REFUSED: {name} changed or was never read. Read it first."
    files[name] = {"text": text, "version": current + 1}
    seen[name] = current + 1
    return f"wrote {len(text)} characters to {name}"


def delete_file(files, seen, name):
    files.pop(name, None)
    return f"deleted {name}"


TOOLS = {"list_files": list_files, "read_file": read_file,
         "write_file": write_file, "delete_file": delete_file}

GOALS = {
    "happy": "Fix the typo in notes.txt.",
    "blind": "Fix the typo in notes.txt.",
    "stale": "Fix the typo in notes.txt.",
    "runaway": "Tidy up the folder.",
    "risky": "Tidy up the folder.",
}


def call(thought, tool, **args):
    return {"thought": thought, "tool": tool, "args": args}


def done(text):
    return {"thought": "Nothing left to do.", "final": text}


# The stub "model". It only returns a decision. It can't run anything.
def fake_model(messages, scenario):
    results = [m["content"] for m in messages if m["role"] == "tool"]
    last = results[-1] if results else ""
    if scenario == "runaway":  # never decides it's finished
        return call("Let me check the folder again.", "list_files")
    if scenario == "risky":
        if not results:
            return call("old.txt looks like clutter.", "delete_file", name="old.txt")
        if last.startswith("BLOCKED"):
            return done("I did not delete old.txt. It needs your approval.")
        return done("Deleted old.txt.")
    # happy, blind, stale: fix the typo
    if not results:
        if scenario == "blind":  # skips reading and guesses the contents
            return call("I bet it says 'teh meeting'.", "write_file",
                        name="notes.txt", text="the meeting is at 3pm")
        return call("Look around first.", "list_files")
    if last.startswith("REFUSED") or "notes.txt," in last:
        return call("Read the file.", "read_file", name="notes.txt")
    if "teh" in last:
        return call("Fix 'teh'.", "write_file",
                    name="notes.txt", text=last.replace("teh", "the"))
    return done("Fixed the typo in notes.txt.")


# The harness: runs the loop, runs the tools, enforces the guards.
def run(scenario, approve=False):
    files, seen = make_files(), {}
    messages = [{"role": "user", "content": GOALS[scenario]}]
    sent = 0
    print(f"goal: {GOALS[scenario]}")
    for step in range(1, MAX_STEPS + 1):
        sent += len(json.dumps(messages))  # the model rereads everything
        decision = fake_model(messages, scenario)                 # think
        messages.append({"role": "assistant", "content": json.dumps(decision)})
        print(f"step {step} | think: {decision['thought']}")
        if "final" in decision:
            print(f"       | done:  {decision['final']}")
            break
        name, args = decision["tool"], decision["args"]
        shown = ", ".join(f"{k}={v!r}" for k, v in args.items())
        if name not in TOOLS:
            result = f"ERROR: no tool named {name}"
        elif name in NEEDS_APPROVAL and not approve:
            result = f"BLOCKED: {name} needs a person's approval"
        else:
            result = TOOLS[name](files, seen, **args)              # act
        messages.append({"role": "tool", "content": result})      # observe
        print(f"       | act:   {name}({shown})")
        print(f"       | see:   {result}")
        print(f"       | context: {len(messages)} messages, "
              f"{len(json.dumps(messages))} chars")
        if scenario == "stale" and name == "read_file" and seen["notes.txt"] == 1:
            files["notes.txt"] = {"text": "teh meeting is at 4pm", "version": 2}
            print("       | (meanwhile, a teammate changes 3pm to 4pm)")
    else:
        print(f"STOPPED: hit the {MAX_STEPS}-step limit without finishing")
    print(f"model calls: {step} | chars sent to the model in total: {sent}")
    print(f"files now: {json.dumps({k: v['text'] for k, v in files.items()})}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--no-guard" in args:
        READ_BEFORE_WRITE = False
    words = [a for a in args if not a.startswith("--")]
    run(words[0] if words else "happy", approve="--approve" in args)
```

**1. The loop: think, act, observe, until done.** The agent looks around, reads the file, writes the fix, and stops on its own:

```
$ python3 agent_loop.py happy
goal: Fix the typo in notes.txt.
step 1 | think: Look around first.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 3 messages, 225 chars
step 2 | think: Read the file.
       | act:   read_file(name='notes.txt')
       | see:   teh meeting is at 3pm
       | context: 5 messages, 412 chars
step 3 | think: Fix 'teh'.
       | act:   write_file(name='notes.txt', text='the meeting is at 3pm')
       | see:   wrote 21 characters to notes.txt
       | context: 7 messages, 644 chars
step 4 | think: Nothing left to do.
       | done:  Fixed the typo in notes.txt.
model calls: 4 | chars sent to the model in total: 1340
files now: {"notes.txt": "the meeting is at 3pm", "old.txt": "draft from last year"}
```

Notice the context grows every step (3, 5, then 7 messages), since each step appends one decision and one result.

**2. The model only asks; the harness runs the tools.** The only lines that touch `TOOLS` are inside `run`, the harness. `fake_model` only returns dicts:

```
$ grep -n "^def \|TOOLS" agent_loop.py
19:def make_files():
27:def list_files(files, seen):
31:def read_file(files, seen, name):
38:def write_file(files, seen, name, text):
47:def delete_file(files, seen, name):
52:TOOLS = {"list_files": list_files, "read_file": read_file,
64:def call(thought, tool, **args):
68:def done(text):
73:def fake_model(messages, scenario):
99:def run(scenario, approve=False):
114:        if name not in TOOLS:
119:            result = TOOLS[name](files, seen, **args)              # act
```

**3. A step limit stops a runaway loop.** This stub never decides it's done:

```
$ python3 agent_loop.py runaway
goal: Tidy up the folder.
step 1 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 3 messages, 230 chars
step 2 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 5 messages, 408 chars
step 3 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 7 messages, 586 chars
step 4 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 9 messages, 764 chars
step 5 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 11 messages, 942 chars
step 6 | think: Let me check the folder again.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 13 messages, 1120 chars
STOPPED: hit the 6-step limit without finishing
model calls: 6 | chars sent to the model in total: 2982
files now: {"notes.txt": "teh meeting is at 3pm", "old.txt": "draft from last year"}
```

Where the 2,982 total comes from: the first call sends only the goal, and each later call sends the list as it stood after the step before:

```
$ python3 -c "import json;print(len(json.dumps([{'role':'user','content':'Tidy up the folder.'}])))"
$ python3 -c "print(52+230+408+586+764+942, 6*52)"
52
2982 312
```

That's 2,982 characters for six calls, versus 312 if each call cost what the first did.

**4. A risky action waits for a person:**

```
$ python3 agent_loop.py risky
goal: Tidy up the folder.
step 1 | think: old.txt looks like clutter.
       | act:   delete_file(name='old.txt')
       | see:   BLOCKED: delete_file needs a person's approval
       | context: 3 messages, 277 chars
step 2 | think: Nothing left to do.
       | done:  I did not delete old.txt. It needs your approval.
model calls: 2 | chars sent to the model in total: 329
files now: {"notes.txt": "teh meeting is at 3pm", "old.txt": "draft from last year"}
$ python3 agent_loop.py risky --approve
goal: Tidy up the folder.
step 1 | think: old.txt looks like clutter.
       | act:   delete_file(name='old.txt')
       | see:   deleted old.txt
       | context: 3 messages, 246 chars
step 2 | think: Nothing left to do.
       | done:  Deleted old.txt.
model calls: 2 | chars sent to the model in total: 298
files now: {"notes.txt": "teh meeting is at 3pm"}
```

**5. Read before write stops a blind guess.** The guess happens to be right here, but the guard refuses it anyway:

```
$ python3 agent_loop.py blind
goal: Fix the typo in notes.txt.
step 1 | think: I bet it says 'teh meeting'.
       | act:   write_file(name='notes.txt', text='the meeting is at 3pm')
       | see:   REFUSED: notes.txt changed or was never read. Read it first.
       | context: 3 messages, 337 chars
step 2 | think: Read the file.
       | act:   read_file(name='notes.txt')
       | see:   teh meeting is at 3pm
       | context: 5 messages, 524 chars
step 3 | think: Fix 'teh'.
       | act:   write_file(name='notes.txt', text='the meeting is at 3pm')
       | see:   wrote 21 characters to notes.txt
       | context: 7 messages, 756 chars
step 4 | think: Nothing left to do.
       | done:  Fixed the typo in notes.txt.
model calls: 4 | chars sent to the model in total: 1676
files now: {"notes.txt": "the meeting is at 3pm", "old.txt": "draft from last year"}
```

**6. A stale read, with and without the guard.** The agent reads the file, then a teammate changes 3pm to 4pm, then the agent writes its fix based on the old read:

```
$ python3 agent_loop.py stale
goal: Fix the typo in notes.txt.
step 1 | think: Look around first.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 3 messages, 225 chars
step 2 | think: Read the file.
       | act:   read_file(name='notes.txt')
       | see:   teh meeting is at 3pm
       | context: 5 messages, 412 chars
       | (meanwhile, a teammate changes 3pm to 4pm)
step 3 | think: Fix 'teh'.
       | act:   write_file(name='notes.txt', text='the meeting is at 3pm')
       | see:   REFUSED: notes.txt changed or was never read. Read it first.
       | context: 7 messages, 672 chars
step 4 | think: Read the file.
       | act:   read_file(name='notes.txt')
       | see:   teh meeting is at 4pm
       | context: 9 messages, 859 chars
step 5 | think: Fix 'teh'.
       | act:   write_file(name='notes.txt', text='the meeting is at 4pm')
       | see:   wrote 21 characters to notes.txt
       | context: 11 messages, 1091 chars
step 6 | think: Nothing left to do.
       | done:  Fixed the typo in notes.txt.
model calls: 6 | chars sent to the model in total: 3318
files now: {"notes.txt": "the meeting is at 4pm", "old.txt": "draft from last year"}
$ python3 agent_loop.py stale --no-guard
goal: Fix the typo in notes.txt.
step 1 | think: Look around first.
       | act:   list_files()
       | see:   notes.txt, old.txt
       | context: 3 messages, 225 chars
step 2 | think: Read the file.
       | act:   read_file(name='notes.txt')
       | see:   teh meeting is at 3pm
       | context: 5 messages, 412 chars
       | (meanwhile, a teammate changes 3pm to 4pm)
step 3 | think: Fix 'teh'.
       | act:   write_file(name='notes.txt', text='the meeting is at 3pm')
       | see:   wrote 21 characters to notes.txt
       | context: 7 messages, 644 chars
step 4 | think: Nothing left to do.
       | done:  Fixed the typo in notes.txt.
model calls: 4 | chars sent to the model in total: 1340
files now: {"notes.txt": "the meeting is at 3pm", "old.txt": "draft from last year"}
```

Without the guard, the agent says "Fixed the typo", but the file says 3pm and the teammate's change is gone. This is exactly why you should check the result, not the report.

Keep in mind what this script *doesn't* prove: how often a real model picks the right tool, writes good arguments, or gets fooled by text it reads, or real token counts, prices, and wait times. For that, run your own test tasks against your own model.

## TL;DR

- An AI agent is a chat model in a loop: think, act with a tool, observe the result, repeat until done or a limit.
- The model only asks for actions; the harness runs the tools and feeds results back.
- The context window is the agent's memory. It fills up, and each step costs more than the last.
- Small mistakes compound over many steps, and the agent's "done" isn't proof.
- Use guardrails in the harness: step limits, approval for risky actions, read before write, and sandboxes.
- If a script can do the job, use a script.

Hope this helps! Let me know if you'd like help designing the guardrails or the test tasks for your own agent.
