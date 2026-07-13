# Bridge CNI Plugin - Conceptual Overview

## What is a Bridge?

Think of a network bridge like a **network switch** (that physical box with multiple ethernet ports). It's a virtual version of that, living inside your server.

## How Does it Work?

```
┌──────────────────── Node ────────────────────┐
│                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │  Pod A   │  │  Pod B   │  │  Pod C   │    │
│  │ 10.0.0.2 │  │ 10.0.0.3 │  │ 10.0.0.4 │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │          │
│       └─────────────┼─────────────┘          │
│                     │                        │
│              ┌──────┴──────┐                 │
│              │   Bridge    │                 │
│              │   (cni0)    │                 │
│              │  10.0.0.1   │                 │
│              └──────┬──────┘                 │
│                     │                        │
└─────────────────────┼────────────────────────┘
                      │
                  Internet
```

## Simple Analogy

- **Bridge** = A hub/switch that connects all the pods on a node
- **Pods** = Computers plugged into that switch
- **Each pod** gets its own IP address from the same subnet

## The Three Things It Does

1. **Creates a virtual switch** (bridge) on the node
2. **Connects pods to it** using virtual cables (veth pairs)
3. **Gives pods IP addresses** so they can talk to each other

## The Bottom Line

The bridge plugin is the **"Hello World"** of Kubernetes networking. It's simple, easy to understand, but not feature-rich enough for production use.
