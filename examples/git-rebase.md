Great question! Rebasing for the first time can feel scary, but once you understand what's actually happening under the hood, it's very manageable. Here's everything you need to know about what happens when you run `git rebase`.

## What rebase does

At a high level, `git rebase` moves your work to the end of the line. Say you have a branch called `feature/login` that split off from `main` a while ago, and since then other people have kept working and added commits to `main`. When you run `git rebase main` from `feature/login`, git takes your commits and puts them on top of the newest version of `main`, so instead of a fork in the history you end up with one straight line: main's commits, then yours. Your changes are the same; they just start from the newest version of main now.

The key thing to understand is that **your commits are copied, not moved**. Git replays each of your commits, one at a time, oldest first, onto main's tip. Each replayed commit is a brand-new commit with a **new hash** (commit ID). The old commits aren't deleted — they're just hidden (no branch points at them any more). This one fact explains basically every rule about rebasing.

## Why rebase at all?

The main benefit is a clean, linear history. If you merge main into your branch instead, you get a merge commit (a "knot" in the history) every time you sync, and the history keeps every fork. With rebase you get one straight line, which is easier to read, easier to `git bisect`, and easier to review commit by commit. Merging also works fine, though — it keeps the true shape of history, while rebasing keeps a tidy one.

## How it works, step by step

Here are the moving parts:

- **Branch name:** `feature/login` is just a label (a pointer) to one commit. Rebase builds new commits and then moves this label to the last one. Nothing else moves — `main` stays exactly where it was. Labels are pointers, not containers, so moving a label doesn't move or delete commits.
- **Merge base:** the last commit your branch and `main` share, i.e. where you split off. Everything after it on your side is "your work"; everything after it on main's side is what you're catching up to.
- **Replay list:** the commits on your branch that aren't on main — `main..feature/login` — oldest first. Merge commits on your branch are dropped and their changes flattened by default, unless you pass `--rebase-merges`. Commits whose change is already on main get skipped.
- **The replay:** git checks out main's tip with a **detached HEAD** and applies each commit's change one at a time, much like a cherry-pick. Each result is a new commit with a new hash. Your author name, author date, and commit message carry over; the committer date becomes the time of the rebase.
- **The stop:** if a change doesn't apply cleanly, git pauses on that one commit, marks the conflicting files, and hands control to you.
- **The finish:** git moves `feature/login` to the last new commit and checks it out. It also writes `ORIG_HEAD` and a **reflog** entry, both pointing at your old tip.
- **The server copy:** `origin/feature/login` still points at the old commits. Since your new commits don't descend from them, a normal push will be refused as "non-fast-forward", and you'll need a force-push.

So the flow is:

1. Find the merge base.
2. List the commits to replay.
3. Detach HEAD at main's tip.
4. Apply the next commit. If there's a conflict, stop and wait for you (fix + `git add` then `--continue`, or `--skip`, or `--abort` to undo everything). If more commits remain, loop back.
5. Move `feature/login` to the last copy and write `ORIG_HEAD` and the reflog entry pointing to the old tip.

The loop runs once per commit, and a conflict pauses inside the loop — so a branch with several clashing commits can stop several times.

### Side effects

- Every replayed commit gets a new hash and a new committer date. Your file changes, commit messages, author, and author date don't change.
- `feature/login` points at the new last commit. `main` and every other branch are untouched.
- `ORIG_HEAD` and the reflog record your old tip. The old commits still exist, unlabeled, until garbage collection (the reflog keeps them about 30 days by default).
- Your branch and `origin/feature/login` have diverged. Nothing leaves your machine until you push, so the server is unaffected.
- Merge commits on your branch are flattened away by default.
- If you have unstaged changes, git refuses to start the rebase, unless you pass `--autostash`.

## Conflicts

If two edits clash (for example both main and your branch changed the same line), git stops on that commit and waits for you. It won't guess. It stops on one commit at a time, so you might stop more than once. You have three options:

- **`git rebase --continue`**: use this after you've fixed the conflicting files and run `git add` on them. Git will open your editor for the commit message — save and close it.
- **`git rebase --skip`**: use this when the commit isn't needed any more, e.g. main already has the same fix. Be careful: this **drops that commit's changes**. It's not a "fix it later" button.
- **`git rebase --abort`**: use this if you're unsure, tired, or the conflict is bigger than you expected. It puts you back in the exact pre-rebase state. Nothing is lost.

If you keep hitting the same conflict on every commit (each commit that touches the clash stops again), you can squash your commits first, or turn on `git config rerere.enabled true` so git replays your earlier resolutions. For example, six commits that all edit the same function could stop the rebase up to six times, while one squashed commit can stop at most once. To squash without conflicts first, run `git rebase -i $(git merge-base HEAD main)` (no new base, so no conflicts), then rebase onto main. The trade-off is that you lose the step-by-step commits, so keep them if your reviewers read commit by commit.

## The safety net: reflog

You really can't lose your work by accident. After a rebase, the old versions of your commits are still around. `git reflog` remembers where your branch used to point. For example `git reflog show feature/login` will show an entry like `rebase (finish): refs/heads/feature/login onto <hash>` followed by the earlier entries for your original commits. To get back the old version, you can run `git reset --hard feature/login@{1}`, or `git reset --hard ORIG_HEAD` right after the rebase (before another command overwrites `ORIG_HEAD`).

How long does the safety net last? After a rebase, the old commits are "unreachable" (no branch points at them), so their reflog entries expire according to `gc.reflogExpireUnreachable`, which defaults to 30 days. Reachable entries expire after `gc.reflogExpire`, which defaults to 90 days. Garbage collection can delete the commits only after their reflog entries expire. You can check `git config --get gc.reflogExpire` and `git config --get gc.reflogExpireUnreachable` — empty output means the defaults apply — and read `git help config` for details.

## The one big risk: shared branches

**Don't rebase a branch other people are using or building on.** Because rebase creates new copies with new hashes, anyone who built on the old commits is now standing on commits that no longer exist upstream. For example, if alice rebases `feature/login` and force-pushes it while bob has his own work on top of the old commits, when bob pulls he gets both the old copies and the new copies of every commit — the same changes, twice. If he then pushes, everyone gets the duplicates. Rule of thumb: only rebase branches that only you work on.

## Pushing after a rebase

If you'd already pushed the branch, a regular `git push` will be refused, because the server still has the old hashes and your branch no longer descends from them. That's expected — it doesn't mean you did anything wrong. Git's hint will suggest running `git pull`, but **don't** do that after a rebase, since it would merge the old copies back in.

Your options:

- `git push` — refused (non-fast-forward). Won't work.
- `git push --force` — overwrites the server branch no matter what's there. It will silently delete any commits someone else pushed since you last fetched. Avoid this.
- `git push --force-with-lease` — overwrites only if the server branch still matches your last-fetched `origin/feature/login`. If someone else pushed in the meantime, it's refused with "stale info". This should be your default.

One gotcha with `--force-with-lease`: the lease checks against your last fetch. If you run `git fetch` right before pushing, you effectively "accept" whatever is on the server, and the lease will pass even if you never looked at the new commits. If you do fetch, check `git log feature/login..origin/feature/login` first. Git 2.30 and later also offer `--force-if-includes` to close this gap.

## Rebase vs. merge

Here's a quick comparison:

| | Rebase | Merge main in |
|---|---|---|
| History shape | One straight line; easy to read, bisect, review commit by commit | True shape, with a merge commit each time you sync |
| Commit hashes | All of yours change | None change |
| Push after | Needs a force-push if already pushed | Normal push |
| Conflicts | Resolved per commit; can stop several times | Resolved once, in the merge commit |
| Safe on shared branches | No — others end up with duplicate commits | Yes |
| Undo | `--abort` mid-way, reflog after | `git merge --abort` mid-way, `git reset` after |

A simple way to decide: has anyone else pulled or built on this branch? If yes, merge main in (or agree on a time with them). If no, have you pushed it yet? If not, rebase and push normally. If you have, rebase and push with `--force-with-lease`.

Some other alternatives worth knowing about:

- `git pull --rebase` rebases your local commits onto the server copy of the *same* branch. It's useful for syncing with teammates, not for moving onto main.
- Squash-merging in the pull request gives main one clean commit without a local rebase, but you still need to sync with main if there are conflicts.
- Never updating your branch just pushes the conflicts onto the reviewer or the merge button.

## Interactive rebase

`git rebase -i` lets you edit the list of commits before the replay starts. Git opens your editor with a "todo list", one line per commit, oldest at the top (the top runs first), for example:

```
pick  3c1d2e4 Add login form
fixup 7a9b0c5 Validate password
pick  0e1f2a3 Style login page
```

You change the first word on each line:

- `pick` — keep the commit
- `reword` — keep it but change the message
- `squash` — fold it into the commit above and combine the messages (git opens an editor)
- `fixup` — fold it into the commit above and discard its message
- `edit` — pause at that commit so you can amend it
- `drop` — remove the commit

Reordering lines reorders commits, and deleting a line drops that commit. Save and close the editor to start the replay.

## Edge cases and what could go wrong

- **Uncommitted changes:** rebase refuses to start. Commit, `git stash`, or pass `--autostash`.
- **Stale local main:** if you rebase onto an old local `main`, you'll still hit conflicts at review time. Run `git fetch` and rebase onto `origin/main`.
- **Someone else built on the branch:** they'll get both old and new copies of every commit on their next pull. Don't rebase — merge, or coordinate a reset with them.
- **Merge commits on your branch:** they're flattened away by default. Use `--rebase-merges` to keep them.
- **Same conflict over and over:** squash first, or enable `rerere`.
- **Result looks wrong after finishing:** run `git reset --hard ORIG_HEAD` right away, or find the old tip in `git reflog`.
- **You panic mid-conflict:** `git rebase --abort`. Nothing is lost.
- **A clean rebase can still produce code that doesn't work together**, so always build and run your tests afterwards.

## Recommended plan for your first rebase

If `feature/login` is yours alone, here's what I'd do: fetch, rebase onto `origin/main`, run your tests, and push with `--force-with-lease`. If anyone else has pulled or built on the branch, merge main in instead.

1. Commit or stash everything and make sure `git status` is clean.
2. `git fetch origin`
3. Optionally, note your current tip with `git rev-parse --short HEAD` (the reflog has it too).
4. `git rebase origin/main`. On each stop: fix the files, `git add` them, `git rebase --continue`. If things go sideways, `git rebase --abort`.
5. Build and run your tests.
6. `git push --force-with-lease`

## Try it yourself: a safe repro

If you want to see all of this for yourself before touching your real branch, paste this setup function into a terminal (needs git 2.28 or later). Each experiment calls `demo`, which builds a fresh throwaway repo in a temp directory. Your hashes will differ from the ones shown below.

```sh
demo() {
  cd "$(mktemp -d)" || return
  git init -q -b main
  git config user.name alice
  git config user.email alice@example.com
  echo v1 > app.txt; git add app.txt; git commit -qm "Initial app"
  git switch -qc feature/login
  echo "login form" > login.txt; git add login.txt; git commit -qm "Add login form"
  echo "check password" >> login.txt; git commit -qam "Validate password"
  git switch -q main
  echo footer > footer.txt; git add footer.txt; git commit -qm "Add footer"
  git switch -q feature/login
}
```

This gives you a `main` with "Initial app" then "Add footer", and a `feature/login` that split off after "Initial app" with two commits.

**1. Your work moves to the end, and main stays put:**

```sh
demo
git log --oneline --graph --all
git rev-parse --short main
git rebase main
git log --oneline --graph --all
git rev-parse --short main
```

Expected output:

```
* 9e8f7d6 (main) Add footer
| * 7a9b0c5 (HEAD -> feature/login) Validate password
| * 3c1d2e4 Add login form
|/
* a1b2c3d Initial app
9e8f7d6
Successfully rebased and updated refs/heads/feature/login.
* d4e3f2a (HEAD -> feature/login) Validate password
* 5b6c7d8 Add login form
* 9e8f7d6 (main) Add footer
* a1b2c3d Initial app
9e8f7d6
```

The fork is gone, your commits come after "Add footer", and `main` has the same hash before and after.

**2. Copies with new hashes, but identical changes:**

```sh
demo
git rebase -q main
git log --oneline -2 ORIG_HEAD    # old tip
git log --oneline -2 HEAD         # new tip
git diff --stat ORIG_HEAD HEAD
git log -1 --format=fuller | grep Date
```

```
7a9b0c5 Validate password
3c1d2e4 Add login form
d4e3f2a Validate password
5b6c7d8 Add login form
 footer.txt | 1 +
 1 file changed, 1 insertion(+)
AuthorDate: Tue Oct 20 10:02:11 2026 -0600
CommitDate: Tue Oct 20 10:02:14 2026 -0600
```

Same messages, different hashes. The only difference between the old and new tips is `footer.txt` (from main), so your `login.txt` changes are byte-for-byte the same. The author date is kept; the commit date is when the rebase happened.

**3. The reflog safety net:**

```sh
demo
git rebase -q main
git reflog show -3 feature/login
git rev-parse --short ORIG_HEAD
git reset --hard feature/login@{1}
git log --oneline --graph --all
```

```
d4e3f2a feature/login@{0}: rebase (finish): refs/heads/feature/login onto 9e8f7d6…
7a9b0c5 feature/login@{1}: commit: Validate password
3c1d2e4 feature/login@{2}: commit: Add login form
7a9b0c5
HEAD is now at 7a9b0c5 Validate password
* 9e8f7d6 (main) Add footer
| * 7a9b0c5 (HEAD -> feature/login) Validate password
| * 3c1d2e4 Add login form
|/
* a1b2c3d Initial app
```

The old tip is still in the reflog (and in `ORIG_HEAD`), and resetting to it restores the original fork exactly.

**4. Conflicts stop one commit at a time.** Here main and the branch both edit line 1 of `app.txt`, in the branch's third commit:

```sh
demo
git switch -q main
echo "v2 from main" > app.txt; git commit -qam "Bump app on main"
git switch -q feature/login
echo "v2 from login" > app.txt; git commit -qam "Bump app for login"
git rebase main
```

```
Auto-merging app.txt
CONFLICT (content): Merge conflict in app.txt
error: could not apply 1f2e3d4... Bump app for login
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
Could not apply 1f2e3d4... Bump app for login
```

The first two commits replayed silently; it stopped on the third, the only one that clashes. The hint lists exactly the three ways out. If you look at the file and the status:

```sh
cat app.txt
git status | grep -E "rebasing|both modified"
```

```
<<<<<<< HEAD
v2 from main
=======
v2 from login
>>>>>>> 1f2e3d4 (Bump app for login)
You are currently rebasing branch 'feature/login' on '6a7b8c9'.
	both modified:   app.txt
```

To abort and put everything back:

```sh
git rebase --abort
git log --oneline -1
# 1f2e3d4 (HEAD -> feature/login) Bump app for login
```

To fix and continue:

```sh
git rebase main                      # stops again
echo "v2 from both" > app.txt
git add app.txt
GIT_EDITOR=true git rebase --continue   # skips the message editor
git log --oneline main..
```

```
Successfully rebased and updated refs/heads/feature/login.
8c7b6a5 Bump app for login
2e3f4a5 Validate password
6d5c4b3 Add login form
```

And to see that `--skip` drops the commit:

```sh
git reset -q --hard ORIG_HEAD        # back to before the previous step
git rebase main                      # stops again
git rebase --skip
git log --oneline main..
```

```
Successfully rebased and updated refs/heads/feature/login.
2e3f4a5 Validate password
6d5c4b3 Add login form
```

"Bump app for login" is gone from the branch.

**5. The merge alternative keeps hashes:**

```sh
demo
git merge -q --no-edit main
git log --oneline --graph
git rev-parse --short HEAD^1
```

```
*   e1f2a3b (HEAD -> feature/login) Merge branch 'main' into feature/login
|\
| * 9e8f7d6 (main) Add footer
* | 7a9b0c5 Validate password
* | 3c1d2e4 Add login form
|/
* a1b2c3d Initial app
7a9b0c5
```

Your original hashes are unchanged, so a normal push works; the cost is the extra merge commit and the forked shape.

**6. Interactive rebase squashing.** `GIT_SEQUENCE_EDITOR` edits the todo list for you so no editor opens; this turns line 2 from `pick` into `fixup`:

```sh
demo
GIT_SEQUENCE_EDITOR="sed -i.bak '2s/^pick/fixup/'" git rebase -i main
git log --oneline main..
cat login.txt
```

```
Successfully rebased and updated refs/heads/feature/login.
c3d4e5f Add login form
login form
check password
```

One commit is left, with the first commit's message and both commits' changes.

**7. A pushed branch needs a force-push:**

```sh
demo
R="$(mktemp -d)/server.git"; git init -q --bare "$R"
git remote add origin "$R"
git push -q -u origin main feature/login
git rebase -q main
git push
git push --force-with-lease
```

```
 ! [rejected]        feature/login -> feature/login (non-fast-forward)
error: failed to push some refs to '…/server.git'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart. …
To …/server.git
 + 7a9b0c5...d4e3f2a feature/login -> feature/login (forced update)
```

The plain push is refused; the `+` and "forced update" mark the overwrite.

**8. The lease catches someone else's push.** Here bob pushes a commit after alice's last fetch, and then alice rebases and pushes:

```sh
demo
R="$(mktemp -d)/server.git"; git init -q --bare "$R"
git remote add origin "$R"; git push -q -u origin main feature/login
B="$(mktemp -d)/bob"; git clone -q -b feature/login "$R" "$B"
( cd "$B" && git config user.name bob && git config user.email bob@example.com \
  && echo "remember me" > remember.txt && git add remember.txt \
  && git commit -qm "Add remember-me" && git push -q )
git rebase -q main
git push --force-with-lease
git push --force
git fetch -q; git log --oneline origin/feature/login | grep -c remember
```

```
 ! [rejected]        feature/login -> feature/login (stale info)
error: failed to push some refs to '…/server.git'
 + 1a2b3c4...d4e3f2a feature/login -> feature/login (forced update)
0
```

The lease refused because the server moved since alice's last fetch. Plain `--force` went through, and bob's commit is now gone from the server branch.

**9. Rebasing a shared branch duplicates commits.** bob builds on the pushed branch, alice rebases and force-pushes, and bob pulls:

```sh
demo
R="$(mktemp -d)/server.git"; git init -q --bare "$R"
git remote add origin "$R"; git push -q -u origin main feature/login
B="$(mktemp -d)/bob"; git clone -q -b feature/login "$R" "$B"
( cd "$B" && git config user.name bob && git config user.email bob@example.com \
  && echo "remember me" > remember.txt && git add remember.txt \
  && git commit -qm "Add remember-me" )
git rebase -q main; git push -q --force-with-lease
cd "$B"; git pull -q --no-rebase --no-edit
git log --oneline | grep "Add login form"
```

```
5b6c7d8 Add login form
3c1d2e4 Add login form
```

The same commit appears twice, once per hash, because bob's merge stitched the old copies back in.

**10. Unstaged changes block a rebase:**

```sh
demo
echo wip >> login.txt
git rebase main
git rebase --autostash main
```

```
error: cannot rebase: You have unstaged changes.
error: Please commit or stash them.
Created autostash: 4d5e6f7
Applied autostash.
Successfully rebased and updated refs/heads/feature/login.
```

**11. How long the safety net lasts:**

```sh
git config --get gc.reflogExpire               # empty = default 90 days
git config --get gc.reflogExpireUnreachable    # empty = default 30 days
git help config   # search for reflogExpireUnreachable
```

Both print nothing on a stock setup, so the documented defaults apply.

## TL;DR

- Rebase copies your commits onto the tip of main, giving them new hashes; main itself doesn't move.
- Conflicts stop the replay one commit at a time; use `--continue`, `--skip` (drops the commit), or `--abort` (back to the start).
- If something goes wrong, `git reflog` and `ORIG_HEAD` get your old branch back (for about 30 days by default).
- Don't rebase branches other people are building on.
- If you'd already pushed, push with `--force-with-lease`, not `--force`.
- Use `git rebase -i` to squash, reword, reorder, or drop commits.

Hope this helps, and good luck with your first rebase! Let me know if you run into any conflicts and I can help you work through them.
