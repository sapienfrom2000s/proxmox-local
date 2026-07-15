# containerd — Learnings

## What problem do containers solve?

Before containers, if you had an app that worked on your
machine, deploying it to a server was painful. Different OS,
different libraries, different versions — "it works on my
machine" became a meme for a reason.

Containers solve this by packaging an app with everything it
needs to run (libraries, dependencies, runtime) into an
isolated unit. The app sees its own filesystem and processes,
even though it shares the host OS kernel. Unlike VMs, there's
no full guest OS overhead — containers are lightweight
because they share the host kernel.

But "running a container" isn't one thing. It's a chain of
responsibilities, and understanding that chain is the key
to understanding containerd.

---

## Container runtime — what does "running a container"
## actually mean?

Running a container involves two very different jobs:

**Job 1: Orchestration**
Pulling images from a registry, managing storage, handling
networking, keeping track of which containers exist, talking
to Kubernetes — this is the "management" side.

**Job 2: Execution**
Creating Linux namespaces, setting up cgroups, starting the
actual process in isolation — this is the "make it run" side.

These two jobs are handled by two different types of software:

| Tier           | What it does                           | Examples                |
|----------------|----------------------------------------|-------------------------|
| **High-level** | Image mgmt, lifecycle, orchestration   | containerd, CRI-O       |
| **Low-level**  | Creates isolated process via kernel    | runc, crun, gVisor      |

**Why the split?** Separation of concerns. The orchestration
layer shouldn't need to know how cgroups work. The execution
layer shouldn't need to know how to pull images from a
registry. They talk through a well-defined interface (more
on that below).

---

## OCI — the standard that makes runtimes interchangeable

In the early days, Docker had its own image format and its
own way of running containers. If you built an image with
Docker, you could only run it with Docker. That's a lock-in
problem.

The **Open Container Initiative (OCI)** was created to fix
this. It defines two specifications:

**Image Spec** — How a container image is packaged: a
manifest, layered tarballs (the filesystem), and a config
JSON. If your tool produces OCI images, any OCI-compatible
runtime can run them.

**Runtime Spec** — How to start a container given a bundle
(a directory with `config.json` and the root filesystem).
It defines lifecycle commands: `create`, `start`, `kill`,
`delete`. Any runtime that implements these commands is
OCI-compliant.

**Why this matters:** You can build an image with any builder
and run it with any OCI runtime. containerd can use runc
today, switch to gVisor tomorrow, or use Kata for a different
workload — all because they all speak the same OCI language.

---

## containerd — the high-level runtime

containerd (pronounced "container-dee") is the
industry-standard high-level container runtime. It was
originally part of Docker, then extracted into its own
project and graduated from CNCF in 2017.

Today, containerd is the default container runtime for
Kubernetes. EKS, GKE, AKS, and OpenShift all use it. Docker
Desktop also uses containerd under the hood.

**What containerd is responsible for:**

- **Image management** — pulling, pushing, storing
  container images
- **Container lifecycle** — creating, starting, stopping,
  deleting container records
- **Storage** — managing snapshots (how container filesystems
  are laid out on disk)
- **Networking** — coordinating with CNI plugins for
  container network setup
- **CRI plugin** — speaking Kubernetes' Container Runtime
  Interface so kubelet can talk to it
- **Event handling** — tracking what happened (container
  started, exited, OOM killed, etc.)

**What containerd does NOT do:**

- It does not directly create containers or talk to the
  kernel for isolation
- It delegates that to something else (the shim and runc)

**Architecture:** Everything in containerd is a plugin. Image
handling is a plugin. Storage is a plugin. Runtime management
is a plugin. This makes it extensible — you can swap out
components without rewriting the whole system.

---

## The shim — why containerd doesn't do it alone

Here's a problem: containerd is one daemon process. If it
crashes, what happens to all the running containers?

Before shims, the answer was: they all die. Docker worked
this way for years — one Docker daemon, crash it and every
container on the node goes down. That's a huge blast radius.

**The solution:** For each container (or pod), spawn a small
helper process called a **shim**. The shim becomes the
container's parent process. containerd talks to the shim,
the shim watches the container. If containerd crashes, the
shims keep running and the containers survive. When
containerd restarts, it reconnects to the existing shims and
resumes management.

**What the shim actually does:**

1. Listens for commands from containerd (start, stop, kill)
2. Calls runc to create/manage the container
3. Watches the container process (is it alive? did it exit?)
4. Reports back to containerd (exit codes, OOM events)

**Why the shim is reliable:** It's tiny. It does almost
nothing on its own. Simple things crash less. A bug in image
pulling or garbage collection (containerd's job) can't take
out a running container because they're in separate
processes.

**Blast radius after shims:**

| What crashes   | What dies                                        |
|----------------|--------------------------------------------------|
| containerd     | Nothing (containers keep running via shims)      |
| One shim       | Only that one container/pod                      |
| runc           | Nothing (runc exits after starting the container)|

---

## The full picture — how a container starts

Here's the complete flow, step by step:

```
1. Kubelet says "run this pod"
        |
        v
2. containerd receives the request (via CRI)
        |
        v
3. containerd prepares the image and filesystem
        |
        v
4. containerd spawns a shim for this pod
        |
        v
5. The shim calls runc: "create and start a container"
        |
        v
6. runc talks to the Linux kernel:
   create namespaces, cgroups, start the process
        |
        v
7. runc exits — it's done its job
        |
        v
8. The shim stays behind as the container's parent,
   watching over it
        |
        v
9. containerd monitors through the shim (not directly)
```

**Key insight:** Notice that runc exits at step 7. It's a
tool that sets up the container and walks away. The shim is
the one that sticks around as the container's parent. This
is why a runc crash doesn't kill containers — runc isn't
running during the container's lifetime.

---

## Where runc fits

runc is the most common low-level (OCI) runtime. It's the
reference implementation of the OCI runtime spec.

**What runc does:** Given an OCI bundle (a directory with
`config.json` describing the container's settings and a
`rootfs` with the filesystem), runc uses Linux kernel
features to create the isolated container process:

- **Namespaces** — gives the container its own view of
  processes, network, filesystem, etc.
- **Cgroups** — limits how much CPU, memory, and I/O the
  container can use
- **Seccomp** — filters which system calls the container is
  allowed to make
- **Capabilities** — controls what root-level operations the
  container can perform

**runc is interchangeable.** Because OCI defines the
interface, you can swap runc for:

| Runtime           | What it does differently                        |
|-------------------|------------------------------------------------|
| **gVisor (runsc)** | Runs in a user-space kernel. Slower, but     |
|                   | much stronger isolation. Good for untrusted code.|
| **Kata Containers** | Runs in a lightweight VM. Strongest         |
|                   | isolation, but higher overhead.                 |
| **crun**          | Same as runc but written in C. Faster startup, |
|                   | lower memory.                                   |

You don't change anything in containerd or Kubernetes to
switch — you just point the configuration at a different
runtime.

---

## Putting it all together

The container ecosystem has four layers, each with its own
job:

| Layer         | Speaks to            | Job                                     |
|---------------|----------------------|-----------------------------------------|
| **Kubelet**   | containerd (CRI)     | "I need a pod running"                  |
| **containerd**| shim (ttrpc)         | "Manage this container's lifecycle"     |
| **Shim**      | runc (CLI)           | "Create and watch this process"         |
| **runc**      | Linux kernel         | "Set up namespaces, cgroups, start"     |

Each layer talks a different language. Each can be swapped or
upgraded independently. And if one layer crashes, the damage
is limited to what's directly below it — not the entire
system.
