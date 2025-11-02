# iam (~) TODO
## display-version bug
make as in bash
like command
play with options and ask about it the creator of p10k (play for 20 minutes) (just try to hide old string)

then check this:
function print-date {
    local date_output
    date_output=$(date)
    print -rn -- $date_output
    zle .insert-last-word $date_output
}
zle -N print-date-widget print-date
bindkey '^X^D' print-date-widget



## Iam files problem
We have two groups of people:
- out of box lovers
- nerdy customizers

Both of them need to have ability to change scripts:
- options
- configs
- plug-ins

Nerdy wants to change any files and thus they may handle the git conflict
Out of box don’t want to think, they want that everything should work. They may change something but it need to be in one place 
After change happened create a directory with a golden standard script and additional script which is user defined 

Let’s image plugins
We have core plugins
User add own plugin and dotfile-update split file to directory and include user defined plugin (plugins.local.zsh)

Options should init conflicts

Solution:
* out of box will get ability to use local files
like plugins.local.zsh
* Nerdy will get full access of shell and responsibility to resolve conflicts on updates (git pull --rebase).
* ability to skip some files from upstream updates, you can do it with:
'''
git merge -s recursive -Xpatience -Xignore-space-change
git rebase -Xpatience -Xignore-space-change upstream_branch
'''

################################################################################
################################################################################
## Research for line freeze at load
Not freezing in docker!!!
- Play with docker
- Turn off script to simulate such behaviour
- Fix the issue
https://github.com/romkatv/powerlevel10k/issues/774
https://github.com/romkatv/powerlevel10k/issues/289
################################################################################
################################################################################
                                  ** FETCH **
################################################################################
################################################################################
1. pfetch
  repo: https://github.com/dylanaraps/pfetch
  time: BFETCH_INFO=pfetch bfetch  0.08s user 0.13s system 92% cpu 0.231 total
  cmd: BFETCH_INFO=pfetch bfetch
2. macchina
  repo: https://github.com/Macchina-CLI/macchina
  time: ./macchina-macos-x86_64  0.01s user 0.01s system 20% cpu 0.124 total
  cmd: ~/Dev/@Tools/macchina-macos-x86_64
3. fastfetch
  repo: https://github.com/LinusDierheimer/fastfetch
  time: ./fastfetch  0.02s user 0.01s system 29% cpu 0.099 total
  cmd: ~/Dev/@Tools/fastfetch/build/fastfetch
4. onefetch
  repo: https://github.com/o2sh/onefetch
  time: ./target/release/onefetch  0.15s user 0.04s system 105% cpu 0.184 total
  cmd: ~/Dev/@Tools/onefetch/target/release/onefetch



## Tools
## Upstream
[OMZ core](https://github.com/ohmyzsh/ohmyzsh/commits/master/lib)

### CLI
**GitIgnore**
[Easy access to gitignore boilerplates](https://github.com/simonwhitaker/gibo)

**Unsorted**
[📋 Cut, copy, and paste anything, anywhere, all from the terminal](https://github.com/Slackadays/Clipboard)
[🤖 Just a command runner](https://github.com/casey/just)
[Sloc, Cloc and Code: scc is a very fast accurate code counter with complexity calculations and COCOMO estimates written in pure Go](https://github.com/boyter/scc)
[Count your code, quickly.](https://github.com/XAMPPRocky/tokei?ref=console.dev)
[A hackable, minimal, fast TUI file explorer](https://github.com/sayanarijit/xplr)
[🥧 HTTPie for Terminal — modern, user-friendly command-line HTTP client for the API era. JSON support, colors, sessions, downloads, plugins & more.](https://github.com/httpie/httpie)
[Print the output of a running process](https://github.com/rapiz1/catp)
[Print a list of paths as a tree of paths 🌳](https://github.com/jez/as-tree)
[Your CLI home video recorder 📼](https://github.com/charmbracelet/vhs)
[scriptable, curses-based, digital habit tracker](https://github.com/nerdypepper/dijo)
[Executes commands in response to file modifications](https://github.com/watchexec/watchexec)
[Run a command when files change](https://github.com/cespare/reflex)
[Filesystem watcher. Works anywhere. Simple, efficient and friendly.](https://github.com/e-dant/watcher)
[Open a web search in your terminal.](https://github.com/zquestz/s)
[A minimalist command line knowledge base manager](https://github.com/gnebbia/kb)
[A very fast implementation of tldr in Rust.](https://github.com/dbrgn/tealdeer)

[A cross-platform terminal-based termux-oriented file manager (and component), meant to be used with a Uni-Curses project or as is.](https://github.com/GiorgosXou/TUIFIManager)
[A more intuitive version of du in rust](https://github.com/bootandy/dust)
[Pipe Viewer - monitor the progress of data through a pipe](https://github.com/a-j-wood/pv)


[A post-modern modal text editor.](https://github.com/helix-editor/helix)
[GitHub - ouch-org/ouch: Painless compression and decompression for your terminal](https://github.com/ouch-org/ouch)
[GitHub - lavie/runlike: Given an existing docker container, prints the command line necessary to run a copy of it.](https://github.com/lavie/runlike)
[GitHub - nelhage/reptyr: Reparent a running program to a new terminal](https://github.com/nelhage/reptyr)

[GitHub - jdxcode/rtx: Runtime Executor (asdf rust clone)](https://github.com/jdxcode/rtx/)

**Time trackers**
[GitHub - TailorDev/Watson: A wonderful CLI to track your time!](https://github.com/TailorDev/Watson)
[Activitywatch](https://docs.activitywatch.net/en/latest/introduction.html)
[How To Install Timewarrior - Timewarrior](https://timewarrior.net/docs/install/)
[Toggl API](https://developers.track.toggl.com/docs/tracking/index.html)
[GitHub - AuHau/toggl-cli: A simple command-line interface for toggl.com](https://github.com/AuHau/toggl-cli)
[GitHub - dominikbraun/timetrace: A simple CLI for tracking your working time.](https://github.com/dominikbraun/timetrace)

