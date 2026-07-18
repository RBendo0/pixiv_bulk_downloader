# UI Message Conventions

This document defines the meaning and intended usage of message prefixes and colors used throughout the application console interface.

The goal is to provide a consistent and immediately recognizable visual language for the user.

---

# Message Prefixes

## `[+]` Success / Produced Result

Indicates that something has been successfully produced, obtained, completed, or added.

Examples:

```text
[+]: Download completed.
[+]: Artwork indexed.
[+]: Bookmark added.
```

---

## `[-]` Skipped / Not Necessary

Indicates that an operation was intentionally skipped or was not necessary.

Examples:

```text
[-]: Already downloaded.
[-]: Last chrono page reached.
[-]: Artwork already present locally.
```

---

## `[i]` Information / Status

Indicates informational messages, progress updates, and operational status.

Examples:

```text
[i]: Fetching information of bookmarked works...
[i]: Waiting for the service to become available...
[i]: Operation resumed.
[i]: Operation interrupted by user.
```

---

## `[!]` Important Event

Indicates an event that deserves the user's attention.

This prefix does **not** necessarily represent an error.

Examples:

```text
[!]: API call failed.
[!]: Invalid selection.
[!]: Access limited by the service.
[!]: Operation interrupted by user.
```

---

## `[?]` User Input Request

Indicates that the application is waiting for a decision or input from the user.

Examples:

```text
[?]: Choose an option.
[?]: Continue?
[?]: Select bookmark visibility.
```

---

# Color Semantics

Colors represent the technical severity of the message and are independent from the message prefix.

## `COLOR_ERROR` (Red)

Used for:

* Exceptions
* Operation failures
* Fatal errors
* Unrecoverable conditions

Examples:

```text
[!]: API call failed.
[!]: Artwork processing failed.
```

---

## `COLOR_WARNING` (Yellow)

Used for:

* Recoverable situations
* Temporary service limitations
* Invalid user input
* Warnings

Examples:

```text
[!]: Invalid selection.
[!]: Pixiv API rate limit reached.
[i]: Access limited by the service. Retrying in 60 seconds.
```

---

## `COLOR_DEFAULT` (White)

Used for:

* Normal information
* Progress messages
* User-driven operations
* Neutral events

Examples:

```text
[i]: Fetching information...
[i]: Operation resumed.
[i]: Operation interrupted by user.
```

---

# Design Principles

* Prefixes describe the **logical meaning** of the message.
* Colors describe the **technical severity** of the message.
* Prefix and color are intentionally independent and may be combined freely when appropriate.
