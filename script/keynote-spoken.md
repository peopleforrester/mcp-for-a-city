<!--
ABOUTME: The words spoken on stage at MCP Dev Summit Toronto, 2026-10-06, taken from the deck's speaker notes.
ABOUTME: Build slides that share one spoken passage are merged; slide numbers follow the deck.
-->

# Governing MCP for a Workforce the Size of a City: the spoken script

Michael Forrester, MCP Dev Summit Toronto, Tuesday 2026-10-06. Speaker notes exported from the deck on 2026-10-03.

## 1. Governing MCP for a Workforce the Size of a City

Governing MCP for a workforce the size of a city. So what do we mean by a city? Let me put it in ships.

## 2.

Star Trek called the Enterprise a whole city in space. Kirk counted the crew: four hundred and twenty-eight.

## 3.

The Enterprise-D, about a thousand.

## 4.

Galactica, about twenty-eight hundred.

## 5.

The Infinity, from Halo, seventeen thousand.

## 6.

A Star Destroyer, thirty-seven thousand.

## 7.

Vader's flagship, the Executor, two hundred and eighty thousand.

## 8.

And the Death Star, one point two million.

## 9.

Now, I work for Accenture, which is great for scale. I also work for Accenture, which means there are a lot of things I cannot talk about, and the exact number is one of them. So let us call it two-thirds of a Death Star.

## 10. Remember these?

That is the city. Now, the tooling they are all about to use. You hear this a lot: MCP is the USB of AI tooling. I do not disagree. But does anyone remember the early days of USB? How many of you remember a PS/2 cable? A serial cable? Proprietary, non-standard cables? Is that A? Is that Mini? Is that Micro? Which way up does it go?

## 11. "MCP is the USB of AI tooling"

USB 1.0 shipped in January 1996. The USB-C specification arrived in August 2014. It took us eighteen years to get to one plug. I think MCP will get there a lot quicker, and you could argue it is already happening. But we are not at USB-C yet.

## 12. What you expect me to talk about

Now, I lied to you. The title says governance at scale, so you probably expected me to talk about the architecture. The number. The process we followed. The security incidents. And wrapping MCP servers in MCP servers. Other people here have talked about all of these, and I can answer every one. So let me do that quickly.

## 13. The architecture, the simple version

The architecture, the simple version. A person. An agent. One gate that every call goes through. The tools. Everything else on the next slide is that gate, done properly.

## 14. The architecture

The architecture, done properly. Start on the device, because that is where the user and the agent live, and that is where two policies have to sit: which MCP servers the client may load, and the operating-system and application policies that close the side doors, like Outlook's automation guard and the browser's remote debugging. Tool traffic goes through a proxy, which answers how the request reaches the server, and then the gateway, which answers whether this caller should be allowed: identity, authorization, policy and rate limits, enforced once. Behind it, the service boundary, the MCP server, wrapped where it needs to be and holding an exchanged token rather than the user's, and the tool itself. Third-party hosted MCP sits off the gateway, and the vendor's own agent behind it acts under the user's own grant, which your gateway never issued. Model traffic goes through its own gateway to the providers. The control plane feeds all of this: the identity provider, the MCP registry, the model registry, workload identity so the gateway knows which agent is calling, and GitOps with admission control so an unsanctioned server cannot land. Everything that goes through a gateway is audited and joined by trace context. And the two red dashed lines are the point of this talk: the shell and the browser never touch any of it.

## 15. Total number of adopters?

Total number of adopters? That is worth talking about. Unfortunately, I cannot tell you the number.

## 16. Total number of adopters?

Two-thirds of a Death Star.

## 17. The process: six gates before yes

The process. Six gates, and a request passes through them in order. Do we know the vendor? Is there a real need? How well is it built, and does it need wrapping? Does it speak the current spec? Does it carry authorization? And is the vendor itself compliant? Let me take them one at a time.

## 18. Gate 1: Do we know the vendor?

Gate one: do we know the vendor? Is this their own server or a fork somebody made? Do we have a contract and a support path? Who maintains it, and how fast do they fix a security issue? You verify that by checking that the registry namespace matches the vendor's domain, that the server calls the vendor's own API, and that a contract and a security contact are on file.

## 19. Gate 2: Do we need it, and is it core?

Gate two: do we need it, and is it core? What job does this do, and who asked for it? Is it core to the business or a convenience? And the question nobody writes down: what will people build themselves if we say no? You verify it with a named business owner, a written use case, and a data classification for everything it touches.

## 20. Gate 3: How well is it built, and does it need wrapping?

Gate three: how well is it built, and does it need wrapping? One risk level per tool: read and write are separate tools. Every tool annotated as read-only or destructive. Descriptions describe; they never instruct. And if we wrap it, the wrapper exchanges tokens and never forwards the user's. You verify it by running every tool with valid input, diffing the descriptions on every new version, and confirming the token that reaches the upstream is not the client's.

## 21. Gate 4: Does it speak the current spec?

Gate four: does it speak the current spec? Does it implement the July revision? Does it answer server discover? Does it send the method and name headers so a gateway can route without reading the body? You can verify all of that yourself, without the vendor's cooperation. Call discover, read the revision back, watch the headers.

## 22. Gate 5: Does it carry authorization?

Gate five: does it carry authorization? OAuth, not static keys, not open access. Tokens bound to this server as the audience. No passthrough to upstreams. Scopes we can restrict. A revocation path. You verify it by probing the authorization server, and by presenting a token for a different audience and expecting a rejection. And remember the base rate: forty percent of live servers measured this year had no authentication at all.

## 23. Gate 6: Is the vendor itself compliant?

Gate six: is the vendor itself compliant? A SOC 2 Type II report, not a badge on a website. An ISO 27001 certificate that is current. Where the data is processed, how long it is kept, how it is encrypted. And an incident response path for a compromised MCP session. You verify it with the report on file, dated, the data-handling answers in writing, and a named incident contact.

## 24. 24

The security incidents. I can talk about the fun ones. Look at this little gem. One line in a log file. This is the public version of the trick, from a CVE this year. It is kind of genius.

## 25. An attacker plants one line in a log

Here is how it works. An attacker who can write to your application's logs plants that line. It is ordinary structured JSON sitting in a log file.

## 26. An operator asks the agent to read the logs

Later, an operator asks an agent to look at the logs. The agent reads the file, and it reads the planted instruction along with everything else.

## 27. The agent runs kubectl against the attacker's server

The agent does what the line says. It runs kubectl against a server the attacker controls, with TLS verification switched off. Those two flags are the whole attack. The verb does not matter, because the token goes out on the very first request.

## 28. kubectl sends the operator's bearer token

kubectl does exactly what it is told. It sends the operator's bearer token along as the authorization header. One planted line, and the agent hands over the token.

## 29. The attacker replays the token. Every call was authorized.

The attacker replays that token with the operator's permissions. No model was jailbroken. No policy was violated. Every call in that chain was authorized. This is CVE-2026-47250, in mcp-server-kubernetes, fixed in version 3.7.0. Of course somebody tried it. Prompt injection is the thing.

## 30. We wrapped MCP servers in MCP servers. So did you.

And wrapping. We wrapped MCP servers in MCP servers. We thought that was new. It is not. We are all doing it, and nobody is talking about it. A wrapper is an MCP server with no tools of its own: when the client asks for the tool list or calls a tool, it forwards the request to the real server behind it, relays the answer back, and does something useful on the way through. USB, wrapped in USB.

## 31. Why we wrapped them

Here is why we did it. One: the server carries no authorization, so the wrapper validates the token and decides, per tool, whether this caller may use it. Of nearly eight thousand live servers measured this year, forty percent expose tools with no authentication at all, so this is the common reason. Two: the server needs a credential the client must never hold, so the wrapper holds it. Three: the server exposes a hundred tools and the model should see nine, so the wrapper filters the list. Four: the server speaks stdio and the clients speak HTTP, or the other way round, so the wrapper bridges the transport. Five: every call logged, rate limited and traced. And six, the one I like most. We follow Anthropic's rule that a tool does not do both reads and writes. When a server shipped a tool that did both, we wrapped that same server twice: one wrapper that exposes only the reads, and one that exposes only the writes, each with its functionality cut down to exactly that. Two risk levels, two wrappers, two approvals. The tools exist. FastMCP does it in one call. ToolHive does it as a Kubernetes resource with OIDC, Cedar policies and token exchange. Agent Router, which used to be the Envoy AI Gateway and is now a foundation project, aggregates and filters. And here is the part most wrappers get wrong. The spec says it in capitals: the MCP server must not pass through the token it received from the client. A wrapper that just copies the authorization header is the confused deputy. Obsidian Security found exactly that shape at Square and Wix last year, one shared client ID and cached consent, one click to account takeover, and both vendors fixed it. The right wrapper validates on the way in, decides per tool, exchanges the token for one scoped to that upstream, and sends only that. One test tells you whether a wrapper is built right: is the credential that reaches the upstream different from the one the client sent? All of that I can talk about for days. Come find me. But it is not what I really want to talk about.

## 32. What I really want to talk about

Let us talk about the problems that arise when you do not give people what they want.

## 33.

What if you gave your end users

## 34.

generative AI,

## 35.

and MCP,

## 36.

and then told them: use AI! Explore! Experiment! MCP! So how do you govern a workforce the size of a city after that? Here is what happened to us.

## 37. You handed everyone a relentless hacker

Here is the problem. You are trying to protect an infrastructure, and you have now handed everyone a relentless hacker with several PhDs and no scruples. It is running on your hardware, inside your security zones, using your tokens and your tools, and it has access to every application the user has.

## 38. We told everyone to use AI

We are telling everyone to use AI, are we not? Is that not the battle cry? I am an AI fan, by the way. I am not knocking AI, and I am certainly not knocking MCP. But if we are all relentlessly chasing the dream, and asking everybody else to chase it, we are handing people superpowers and the tools to make them awesome. So what happens when you tell those people, who now all have superpowers, no? What happens when you do not give them the USB of AI tooling?

## 39. "I want to give the agent access to my email"

A user comes to you and says: I want to give the agent access to my email. I would like it to read my email. Cool. I would like it to draft replies for me. Fine. I want it to send email as me. Whoa. Hold on. These are human tools, meant for human communication.

## 40. These are human tools for human communication

Maybe we give the agent its own email address, one that is identified as your agent. Do we not agree that identity matters, not only for agents but for the sub-agents and the tools they call? We need to be able to audit, fingerprint and attribute. If agents call tools, and those tools have permissions, we need attribution for both the call and the tool. That is accountability, auditability and attribution, in forms of identity we have not solved.

## 41. So we said no

So we said no. We offered alternatives. Another channel. Mail rules. Copilot can help you manage your mail, but it will not send for you. But do you know what happens when you give human beings, and I mean nontechnical human beings who frankly do not know better, superpowers?

## 42. The user asked the agent

The user asked this question. Hey, I do not see an MCP server for Outlook, because my team is not giving me one. Is there some other way we might be able to do this?

## 43. The agent wrote PowerShell against classic Outlook

Classic Outlook exposes a COM automation interface. It has for decades, and you can script it from PowerShell. That is exactly what a user told me they did. They had the agent write the PowerShell. Outlook does have a guard on that interface. By default it only warns when your antivirus is inactive or out of date. On a healthy, managed laptop, the agent goes straight through.

## 44. Then they asked about Teams

And then they said: can we do the same thing for Teams? We want Teams to send messages on our behalf. Hold on. The person on the other end expects you. We can create attributed labels and bots. We can give you a server for that. And they said: I do not want that. I want it to manage my messages. We said: we are not going to do that. What do you think happened then?

## 45. They put the approved browser in debug mode

They took Edge, the approved browser, and turned on remote debugging. And why would we not allow that? It is an approved browser. Endpoint protection is still running. Then the agent walked the browser. The browser walked Teams. The browser walked Outlook. There is a policy for that. It is called RemoteDebuggingAllowed, and debugging is allowed unless you set it. You have to know to set it.

## 46. Psychological acceptance

That is psychological acceptance, and for security it is now more important than ever. Your people did not accept the no. They routed around it, and they did it with the tools you handed them.

## 47. You cannot wait this one out

And you cannot wait it out. Classic Outlook is supported until at least 2029. Search GitHub today and you will find open-source MCP servers that drive classic Outlook over that same COM interface. Block the approved server, and an unapproved one appears anyway.

## 48. How do you know what to say yes to?

So how do you know what to say yes to, and what to say no to? Nobody above you is going to decide that for you. Three things. One: say yes fast. The sanctioned path has to arrive before the workaround does. Two: decide on risk, not on function. Read, draft and send are three different yeses. Block took a thirty-tool server down to two tools, one that reads and one that changes things, because each tool should stick to a single risk level. Three: enforce it below the prompt. Across twenty agents, the best refusal rate against poisoned tools was under three percent. A prompt is a request. An authorization check is an answer.

## 49. Three artifacts would make yes faster for everyone

So here is the ask. Three artifacts. One: a published vetting profile, so every enterprise stops deriving the same criteria alone. Two: a machine-readable review attestation attached to server.json, so an approval made once is legible downstream. Three: a revocation feed. Today the path is an upstream takedown, then an aggregator poll, then your own pin update. They have a home. Roadmap priority three, Agent Identity and Enterprise-Ready Security, already exists, and its working group is forming. I am saying it here because the people who would make these stronger are in this room.

## 50. Do you go after the minions, or the summoner?

Let me give you one more way to think about who you are governing. How many of you have played a game, a video game or a board game, where the thing you are fighting can summon other creatures? Goblins. Rainbow spiders. Shout-out to Whitney Lee. Unicorns. Shout-out to Chris Kelly. Do you go after the minions, or do you go after the summoner? The summoner is the heart and mind we need to win.

## 51. Twenty years of no

We tell people to relentlessly pursue productivity and efficiency in their jobs, and then we slow them down with security. Which we should. We have to. But instead of partnering with them on why the security matters, we tell them no. We have done that for twenty years, so now we have twenty years of resentment built up. And at the same moment, these large corporations are saying: we are going to give you Harry Potter magic superpowers, and we want you to stay within the boundaries.

## 52. "Get it done" beats "get it done right", yes?

It is like handing a three-year-old markers. By handing them over, we are sending the message: you can write on the wall now, and you should. Because what is more important than following security? Getting it done. Is that not what we are telling people? It is not get it done right. It is just get it done. We have to be first to market.

## 53. Start talking to your users

The thing I want you to walk away with is not another technology concept. You have plenty of those. Start talking to your users. The thing that mattered at the beginning of the internet revolution, nearly thirty years ago, matters again in this one: the user experience. If you will not win the hearts and minds of your users, you will not win at security. You will not.

## 54. How you govern a workforce the size of a city

That, my friends, is how you govern a workforce the size of a city. You win their hearts and minds, while still doing your duty as the person who must stand at the gate and defend. MCP is going to get to its USB-C faster than anything we have seen. But only if we bring the people with us.

## 55. Listen beyond the technology

There are a lot of great speakers here. They will tell you about the technology and the process, and they will tell you about the people and the psychology of what they ran into. Listen beyond the technology. You can win at the technology by reading the documentation. You can win at the process by experimenting with workflows. You will not win at adoption unless you win the people who are going to use what you build.

## 56. The details are there. Come find me.

I am glad we are talking about identity, authorization, attribution, scope and permissions. I am glad we are talking about registries and gateways and proxies and wrapping. The details are there, and I can go for days. Come find me. The QR code takes you to the repository and the write-up. Remember, I work for Accenture, so you are not going to get numbers. What you will get is value. Technology was always meant to solve human problems, and MCP is meant to give people, using agents in whatever form they take, the tools to solve them.

## 57. Talk to your users.

Think of this as a battle cry that goes beyond MCP but starts right here in Toronto. If you work in security, and especially in an enablement service like MCP, talk to your users. Tell them why you are doing what you are doing. Explain why a no is a no, because the normal guardrails are not working as well as they used to. Do not leave the technology behind. Do not leave the process behind. But if you win the person who uses your technology, you will not only have the USB of AI tooling. You will have the people who use it. My name is Michael Forrester. I will be here after. Thank you.

## 58. Sources

Every figure in this talk has a source on this slide, and the claim-by-claim ledger is in the repository behind the QR code.

## 59. Rainbow spiders

Rainbow spiders. Shout-out to Whitney Lee.
