---
name: threading
description: >
  Language-neutral design principles for in-process concurrency -- threads,
  event loops, workers, cancellation, locks -- for code bases that are robust
  to future requirements changes. Applies to any language.
license: MIT
compatibility: Any language with threads or an event loop
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Thread and concurrency design -- portable guidance

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

**Scope.** In-process concurrency in any language: threads, event loops, and the
boundaries between them. The rules state design claims; the library, primitive,
or language feature that expresses them is a parameter.

## How to apply this

- **Precedence.** A project's own stated convention wins. Where the project is
  silent, these rules are the default.
- **Scope of application.** These rules govern the code you are writing or
  editing. In a codebase that predates them they forbid *new* violations and
  authorize no repairs: never fix an existing violation as a side effect of
  unrelated work, and never read this document as a mandate to refactor.
- **Principles travel; parameters do not.** Each rule states a general claim.
  Its concrete expression -- which primitive, which library, which runtime --
  is the project's, and the language's, to choose.
- **Rules are locally checkable.** Each rule must be checkable by reading the
  code in front of you, not by reasoning about all the ways it could interleave.
  Ownership is visible where state is declared; message-passing is visible at
  the send and the receive. A rule that can only be verified by enumerating
  interleavings is not a rule this document imposes.
- **Rule ids are stable names.** Reference these rules as C1--C5 (C for
  concurrency); they do not renumber.

Each rule ends with a test -- the question to ask of the code in front of you.

## The rules

**C1. State has exactly one owning thread.** Every piece of mutable state is
owned by one thread. A thread that does not own it may not read or write it
directly.
- Cross-thread communication happens only through the owning thread's channel: a
  queue it drains, or a message it reads -- never by calling into the owner's
  objects.
- Messages are values, or immutable, or ownership transferred -- never a
  reference into live mutable state.
- The owner of a view -- a user interface, a display, anything the program
  presents -- is a single thread, and all view mutation happens there.
- *Test:* point to the places where this state crosses threads -- the channel
  each one goes through. If you can't, two threads reach it.

**C2. Threads are bounded, and they end.** Create a thread for one long
operation the owning thread must not block on -- not one per item.
- A worker has a defined end: it stops when its work ends, when it is
  cancelled, or when the process exits. Nothing waits forever -- a shutdown
  path signals cancellation and waits within a bound.
- Whether a thread is a daemon -- one that does not keep the process alive -- is
  the project's choice. A worker with cleanup obligations is not a daemon; its
  owner drains it at shutdown.
- *Test:* how does this thread end, and what happens if it never does?

**C3. Cancellation is an event, not a flag someone else sets.** A thread that can
be cancelled observes a cancellation event, or an equivalent predicate, and
checks it at loop boundaries.
- Do not poll a shared mutable flag from outside, and do not stop a thread by
  mutating its state.
- Cancellation must be observable while a blocking wait is in progress: use a
  bounded timeout, or a wait that the cancellation interrupts.
- *Test:* can this thread be asked to stop while it is blocked?

**C4. Locks are used only on queues.** Application code holds no locks. The only
locking in a program is inside the queue that carries messages between threads --
the queue's own internal synchronization, which you do not extend.
- If state appears to need a lock, two threads can reach it: fix that under C1,
  or make the value immutable after construction. Do not add a lock to an
  object, a cache, a counter, or a callback.
- *Test:* name the object this lock guards. If it isn't a queue, delete the lock.

**C5. The owning thread never blocks.** The thread that owns the user interface,
or any latency-sensitive loop, does no sleeping, no joining, no network I/O, and
no long computation. That is what the worker exists for.
- A blocking put is a blocking wait: the owning thread never performs one.
- *Test:* what is the longest this loop can take before it can respond again?

## What this document is not

- It is not a style guide for any particular threading library or runtime.
- It describes no tooling and ships no checker.
- It authorizes no refactor, and no cleanup of code that predates it.
- It is not any project's policy, and it does not override a project's own
  conventions.
