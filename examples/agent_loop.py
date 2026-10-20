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
