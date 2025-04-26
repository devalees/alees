
**Remember:**

*   Replace placeholders like `<branch-name>`, `<file>`, `<commit-hash>`, and `"Message"` with your actual values.
*   `origin` is the conventional name for your primary remote repository (like GitHub).
*   **WARNING:** Commands marked with `!!! DANGER !!!` are destructive and can lead to data loss if used incorrectly. Understand them before using.

---

**1. Checking Status & History**

*   **See what's changed and staged:**
    ```bash
    git status
    ```
*   **View commit history (briefly):**
    ```bash
    git log --oneline --graph --decorate
    ```
*   **See changes not yet staged:**
    ```bash
    git diff
    ```
*   **See changes staged but not committed:**
    ```bash
    git diff --staged
    ```

**2. Branching**

*   **List all local branches (current one marked with `*`):**
    ```bash
    git branch
    ```
*   **Create a new branch:**
    ```bash
    git branch <branch-name>
    ```
*   **Switch to an existing branch:**
    ```bash
    git switch <branch-name>
    # Older alternative: git checkout <branch-name>
    ```
*   **Create AND switch to a new branch:**
    ```bash
    git switch -c <branch-name>
    # Older alternative: git checkout -b <branch-name>
    ```
*   **Delete a local branch (only if fully merged):**
    ```bash
    git branch -d <branch-name>
    ```
*   **!!! DANGER !!! Force delete a local branch (even if not merged):**
    ```bash
    git branch -D <branch-name>
    ```
*   **Delete a remote branch:**
    ```bash
    git push origin --delete <branch-name>
    ```

**3. Saving Changes (Committing)**

*   **Stage a specific file for commit:**
    ```bash
    git add <file>
    ```
*   **Stage all changed files in the current directory and subdirectories:**
    ```bash
    git add .
    ```
*   **Commit staged changes with a message:**
    ```bash
    git commit -m "Your descriptive message"
    ```
*   **Stage AND commit all tracked, modified files in one step:**
    ```bash
    git commit -am "Your descriptive message"
    # Note: This does NOT add *new* (untracked) files
    ```

**4. Undoing Changes**

*   **Unstage a file (remove from staging area, keep changes in working dir):**
    ```bash
    git restore --staged <file>
    # Older alternative: git reset HEAD <file>
    ```
*   **Discard changes in a specific file in the working directory (since last commit):**
    ```bash
    git restore <file>
    # Older alternative: git checkout -- <file>
    ```
*   **!!! DANGER !!! Discard ALL uncommitted changes (staged and unstaged) in working directory:**
    ```bash
    git restore .
    git clean -fd # Also removes untracked files/directories
    # OR the more powerful reset (also moves HEAD, careful!)
    git reset --hard HEAD
    ```
*   **Undo the last commit, keep changes staged:**
    ```bash
    git reset --soft HEAD~1
    # Now you can fix the changes and commit again
    ```
*   **!!! DANGER !!! Undo the last commit AND discard its changes:**
    ```bash
    git reset --hard HEAD~1
    ```
*   **!!! DANGER !!! Reset local branch to match remote (discard local commits & changes):**
    ```bash
    git fetch origin
    git reset --hard origin/main # Example for main branch
    ```
*   **!!! DANGER !!! Reset local branch to a specific past commit (discard later commits & changes):**
    ```bash
    git reset --hard <commit-hash>
    ```

**5. Merging Branches**

*   **Switch to the branch you want to merge INTO (e.g., `main`):**
    ```bash
    git switch main
    ```
*   **Merge another branch (e.g., `feature-branch`) INTO the current branch:**
    ```bash
    git merge <feature-branch>
    # Resolve any conflicts if they occur, then git add . and git commit
    ```

**6. Working with Remotes**

*   **Download changes from remote, but don't merge yet:**
    ```bash
    git fetch origin
    ```
*   **Download changes from remote AND merge them into current local branch:**
    ```bash
    git pull origin <branch-name> # e.g., git pull origin main
    # Often just `git pull` works if tracking is set up
    ```
*   **Upload your local commits to the remote branch:**
    ```bash
    git push origin <branch-name> # e.g., git push origin main
    # Often just `git push` works if tracking is set up
    ```

