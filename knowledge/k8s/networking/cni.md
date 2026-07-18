### What is CNI?

CNI stands for Container Network Interface. It isn't a piece of software you
install; it is a specification (a standardized set of rules) created by the
Cloud Native Computing Foundation (CNCF).

Think of Kubernetes as a television and CNI as the HDMI standard. Kubernetes
knows how to send out "video and audio signals" (networking requests), but it
doesn't care if you plug in a Sony, Samsung, or LG TV—as long as the plug
matches the HDMI standard, it just works.

In the same way, CNI allows Kubernetes to interact with dozens of different
networking providers interchangeably.

---

### Why does Kubernetes need it?

When the Kubernetes agent (`kubelet`) is told to spin up a new Pod on a server,
it follows a strict sequence:

1. It creates the isolated network environment (namespace) for the container.
2. It looks at the configured CNI plugin and says: "Hey, I have a new container
   here. Give it an IP address and hook it up to the rest of the cluster."
3. The CNI plugin does the heavy lifting, assigns the IP, connects the virtual
   cables, and hands control back to Kubernetes.
4. When the Pod dies, the `kubelet` calls the CNI plugin again to clean up and
   release the IP address.

---

### The Common CNI Plugins

Because CNI is just a standard, different engineering teams have built different
plugins to solve the problem, depending on what features you care about most.

Flannel: Best known for simplicity. It is lightweight and just gives you a basic
"overlay" network so Pods can talk. No bells and whistles, but very easy to set
up. Think of it like a simple two-lane highway.

Calico: Best known for performance & security. It handles massive clusters
beautifully and supports Network Policies, which let you write firewall rules to
block traffic between specific Pods. Think of it like a smart highway with
security checkpoints.

Cilium: Best known for next-gen tech. It uses a powerful Linux kernel technology
called eBPF to bypass traditional routing tables, making it incredibly fast and
giving deep visibility into network traffic. Think of it like a hyper-loop
system.

---
