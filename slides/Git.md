# CSE 636 — Version Control with Git

### Qingsong Zhang, Dr.

---

## Problems Working Alone

Ever run into one of these?

- Had code that worked, made a bunch of changes, saved over it — and now you just want the working version back.
- Accidentally deleted a critical file. Hundreds of lines, gone.
- Messed up the structure or contents of your codebase and just want to **undo** the last crazy action.
- Hard drive crash — everything's gone, the day before the deadline.

**The naive option:** *Save As* (`MyClass-v1.java`, `MyClass-v2.java`, …)

Ugh. And now a single one-line change means duplicating the entire file.

---

## Problems Working in Teams

- **Whose computer stores the "official" copy?** Can we keep the project in a neutral, official location?
- **Can we read/write each other's changes?** Do we have the right permissions? (Emailing files back and forth doesn't scale.)
- **What if we both edit the same file?** "Bill just overwrote a file I worked on for 6 hours!"
- **What if we corrupt an important file?** Is there a way to keep backups?
- **How do I know what code each teammate is working on?**

---

## Solution: Version Control

A **version control system** is software that tracks and manages changes to a set of files.

You already use version control all the time:

- **Word processors / spreadsheets / presentation software** — the magical *Undo* button takes you back to "the version before my last action."
- **Wikis** — built around managing updates and rolling back to previous versions.

---

## Software Version Control

Many version control systems are designed especially for software engineering projects.

> Examples: ClearCase, CVS, Subversion (SVN), Git, BitKeeper, Perforce.

A version control system helps teams work together on code by providing:

- A shared copy of all code files that everyone can access.
- Current versions **and** backups of all past versions.
- Visibility into what files others modified, and the ability to view the changes.
- Conflict management when multiple users edit the same file.

> It isn't limited to source code — you can version papers, photos, etc. — but it works best with plain text and code.

---

## Repositories

A **repository** (or "repo") is a location storing a copy of all files.

- You don't edit files directly in the repo.
- You edit a local **working copy** (the "working tree").
- Then you **commit** your edited files into the repo.

There may be:

- **One shared repository** for all users (CVS, Subversion), or
- **A full copy per user** (Git, Mercurial).

> Files in your working directory must be **added** to the repo before they are tracked.

---

## What to Put in a Repo

**Include** everything needed to build your project:

- Source code (`.java`, `.c`, `.h`, `.cpp`)
- Build files (`Makefile`, `build.xml`)
- Other build resources: icons, text, etc.

**Leave out** things that are easily re-created and just take up space:

- Object files (`.o`)
- Executables (`.exe`)

---

## Repository Location

You can create the repository anywhere.

- **Same machine you work on** — fine for a personal project where you just want rollback protection.
- **A robust, always-available machine** — usually preferable:
  - Up and running 24/7, so everyone always has access.
  - On a redundant file system (e.g. RAID), so a disk crash won't wipe out your project.

**Hosted options:** GitLab, GitHub.

---

## Aside: Git vs. GitHub

**Git** is the software that does version control.

> Like Microsoft Word's "Track Changes," but more rigorous, more powerful, and scaled up to many files.

**[GitHub.com](https://github.com)** is a site for online storage of Git repositories.

- Many open-source projects use it (e.g. the Linux kernel).
- Free for open-source projects; paid plans for private projects.

**Q: Do I have to use GitHub to use Git?**
**A: No!**

- You can use Git completely locally for your own purposes, or
- Share a repo with users on the same file system, as long as everyone has the needed permissions.

---

## Git Resources

At the command line (where `<verb>` = `config`, `add`, `commit`, …):

```bash
$ git help <verb>
$ git <verb> --help
$ man git-<verb>
```

- **Free online book (Pro Git):** https://git-scm.com/book/en/v2
- **Tutorial:** https://git-scm.com/docs/gittutorial
- **Reference:** https://git-scm.com/docs
- **Website:** https://git-scm.com/
- **Git for Computer Scientists:** http://eagain.net/articles/git-for-computer-scientists/

---

## History of Git

- Came out of the Linux development community.
- Created by Linus Torvalds in 2005.

**Initial goals:**

- Speed
- Support for non-linear development (thousands of parallel branches)
- Fully distributed
- Able to handle large projects like Linux efficiently

---

## Git Uses a Distributed Model

| Centralized Model | Distributed Model |
| ----------------- | ----------------- |
| CVS, Subversion, Perforce | Git, Mercurial |
| One central "true" repo | Every clone is a full repo |

**Result:** many operations are local — and therefore fast.

---

## Ways to Use Git

A repo can live locally or on a server (e.g. **GitHub**). Common setups:

- **One user, one computer** — local rollback protection.
- **One user, multiple computers** — sync your own work across machines.
- **Multiple users** — a shared remote everyone pushes to and pulls from.

---

## A Local Git Project Has Three Areas

| Working Directory | Staging Area | Git Directory (Repo) |
| ----------------- | ------------ | -------------------- |
| Files you edit | Snapshots you've staged | Committed snapshots |
| *modified / unmodified* | *staged* | *committed* |

> The working directory is sometimes called the **working tree**; the staging area is sometimes called the **index**.

---

## Basic Workflow

1. **Modify** files in your working directory.
2. **Stage** files, adding snapshots of them to your staging area.
3. **Commit**, which takes the files as they are in the staging area and stores that snapshot permanently in your Git directory (your local copy of the repo).

A file's state at any time:

- **Committed** — that version is safely in the Git directory.
- **Staged** — modified and added to the staging area.
- **Modified** — changed since checkout, but not yet staged.

---

## Get Ready to Use Git!

**1. Set the name and email Git uses for your commits:**

```bash
$ git config --global user.name "Bugs Bunny"
$ git config --global user.email bugs@gmail.com
```

- Run `git config --list` to verify these are set.
- `--global` applies to all your Git projects; omit it to set values per-project.

**Silence the `push.default` warning** (older Git):

```bash
$ git config --global push.default simple
```

**Set the editor for commit messages** (defaults to vim):

```bash
$ git config --global core.editor emacs
```

> vim tips: `a` to start adding, `esc` when done, `:wq` to save and quit.
> vim guide: http://www.gentoo.org/doc/en/vi-guide.xml — ref card: http://tnerual.eriogerg.free.fr/vimqrc.pdf

---

## Create a Local Copy of a Repo

Two common scenarios — **do only one of these.**

**A. Clone an existing repo into your current directory:**

```bash
$ git clone <url> [local-dir-name]
```

This creates a directory containing a working copy of the repo's files plus a `.git` directory (holds the staging area and your local repo — you can ignore it).

```bash
$ git clone https://github.com/sidpalas/devops-directive-docker-course.git
```

**B. Create a new repo in your current directory:**

```bash
$ git init
```

This creates a `.git` directory in place. You can then commit files into the local repo:

```bash
$ git add file1.java
$ git commit -m "initial project version"
```

---

## Git Commands at a Glance

| Command | Description |
| ------- | ----------- |
| `git clone <url> [dir]` | Copy a Git repository so you can add to it |
| `git add <files>` | Add file contents to the staging area |
| `git commit` | Record a snapshot of the staging area |
| `git status` | View the status of files in your working directory and staging area |
| `git diff` | Show the diff of what is staged vs. modified-but-unstaged |
| `git help [command]` | Get help about a particular command |
| `git pull` | Fetch from a remote repo and merge into the current branch |
| `git push` | Push your new branches and data to a remote repository |

> Others worth knowing: `init`, `reset`, `branch`, `checkout`, `merge`, `log`, `tag`.

---

## Adding & Committing Files

**1. Stage files.** The first time a file is tracked — and before every commit — add it to the staging area:

```bash
$ git add README.txt hello.java
```

This snapshots the files at this point in time.

> To **unstage** a change before committing: `git reset HEAD <filename>`

**2. Commit** to move staged changes into your local repo:

```bash
$ git commit -m "Fixing bug #22"
```

> Edit your most recent commit message (if not yet pushed): `git commit --amend`
> These commands act only on your **local** repo.

---

## Use Good Commit Messages

- Write a short, descriptive summary line (the "why," not just the "what").
- Each commit should have a **single logical purpose**.
- Use the imperative mood: *"Fix login redirect"*, not *"Fixed"* or *"Fixes."*
- Add a longer body when the change needs explanation.

---

## Status and Diff

### Status

View the status of files in your working directory and staging area:

```bash
$ git status        # full status
$ git status -s     # short, one line per file
```

### Diff

```bash
$ git diff          # working directory vs. staging area (modified but unstaged)
$ git diff --cached # staging area vs. local repo (staged changes); --staged is synonymous
```

---

## After Editing a File…

```bash
$ emacs rea.txt
$ git status
# On branch master
# Changes not staged for commit:
#   (use "git add <file>..." to update what will be committed)
#   (use "git checkout -- <file>..." to discard changes in working directory)
#
#   modified: rea.txt
#
no changes added to commit (use "git add" and/or "git commit -a")

$ git status -s
 M rea.txt          # M in the second column = working tree

$ git diff          # shows modifications that have NOT been staged
diff --git a/rea.txt b/rea.txt
index 66b293d..90b65fd 100644
--- a/rea.txt
+++ b/rea.txt
@@ -1,2 +1,4 @@
 Here is rea's file.
+
+One new line added.

$ git diff --cached # shows nothing — nothing staged yet
```

---

## After Adding the File to the Staging Area…

```bash
$ git add rea.txt
$ git status
# On branch master
# Changes to be committed:
#   (use "git reset HEAD <file>..." to unstage)
#
#   modified: rea.txt
#

$ git status -s
M  rea.txt          # M in the first column = staging area

$ git diff          # shows nothing — nothing unstaged

$ git diff --cached # shows the staged modifications
diff --git a/rea.txt b/rea.txt
index 66b293d..90b65fd 100644
--- a/rea.txt
+++ b/rea.txt
@@ -1,2 +1,4 @@
 Here is rea's file.
+
+One new line added.
```

---

## Viewing Logs

See a log of all changes in your local repo:

```bash
$ git log              # full log
$ git log --oneline    # one line per commit
1677b2d Edited first line of readme
258efa7 Added line to readme
0e52da7 Initial commit

$ git log -5           # only the 5 most recent commits
```

> Changes are listed by commit ID (a SHA-1 hash).
> Changes pulled/cloned from the remote before your last sync also appear here.

---

## Pulling and Pushing

**Good practice:**

1. **Add and commit** your changes to your local repo.
2. **Pull** from the remote to get the latest changes (resolve conflicts, then add and commit them).
3. **Push** your changes to the remote.

```bash
$ git pull origin master   # fetch + merge remote changes into your working directory
$ git push origin master   # push your local commits to the remote
```

> `origin` = an alias for the URL you cloned from.
> `master` = the remote branch you're pulling from / pushing to. The local branch is your current branch.

---

## Avoiding Common Problems

- **Don't edit the repository (`.git`) manually.** It wasn't designed for hand-editing.
- **Don't make many drastic changes at once.** Make multiple commits, each with a single logical purpose — this minimizes merge conflicts and is good practice anyway.
- **Always `git pull` before editing.** Easy to forget. If you don't, you may edit an outdated version and cause nasty conflicts.
- **Don't forget `git push` after committing.** Your changes aren't on the remote until you push.

---

## Branching

```bash
$ git branch experimental    # create a branch called "experimental"
$ git branch                 # list all branches (* marks the current one)
$ git checkout experimental  # switch to the experimental branch
```

Later, to merge changes from `experimental` into `master`:

```bash
$ git checkout master
$ git merge experimental
```

> `git log --graph` is handy for visualizing branches.
> These branches live in your **local** repo.

---

## SVN vs. Git

**SVN — centralized**

- The main repository is the only "true" source; only it has the complete history.
- Users check out local copies of the current version.

**Git — distributed**

- Every checkout is a full-fledged repository, complete with history.
- Greater redundancy and speed.
- Branching and merging are used much more heavily as a result.

---

## Resources

- Version Control with Git (O'Reilly)
- GitHub Git Cheat Sheet
- Learn Git Branching — visual and interactive
- Pro Git book
- Happy Git and GitHub for the useR
- Git Cheat Sheet
- W3Schools Git Tutorial

---

## Wrap-Up

You **will** use version control on projects — both here and in industry. It's rather foolish not to.

- Set up a repository even for small projects — it will save you time and hassle.
- **HW9 (Git)** walks you through creating a Git repo and adding to a shared repo.
