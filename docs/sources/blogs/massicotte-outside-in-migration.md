# Migrating from the Outside in
Jan 10, 2025

There is a section in the Swift 6 migration guide on Swift.org called "[Migration Strategy](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/migrationstrategy)". Let me quote it here:

> This document outlines a general strategy that could be a good starting point. There is no one single approach that will work for all projects.

These two sentences are quite a hedge!

But, if you continue, you’ll see that the advice is to start at the “outside” of your application and work your way in. Why would you do this? The reasons are simple.

First, the closer you are to your UI, the more main actor stuff you’ll have. That means very clear, unambiguous places where you can establish isolation. Just sprinkle those `@MainActor` annotations around. And, as I have [discussed](https://www.massicotte.org/step-by-step-reading-from-storage) many times before, using concurrency *without* any isolation is [way harder](https://www.massicotte.org/non-sendable). Especially when you are getting started, which you probably are when just beginning a migration.

Second, it can help you find the places where your UI design need synchronous accesses. This can turn out to be really **annoying**, but your synchronous accesses define these core constraints on your system. You might really **want** to make something an actor, but if you need synchronous access to it from the UI, you just **can’t**.

Speaking of which - you do **not** need to be afraid of `@MainActor`! You need only be worried about long-running, synchronous work. You need **both** to have a problem. And even then, look into moving just that work into a [non-isolated method](/step-by-step-network-request). That is so much easier than making a mess of your system just to avoid making your type `@MainActor`.

(Dealing with synchronous work really deserves a whole post on its own, but that’s for another day. Update: that [day has come](/synchronous-work)!)

Now, of course the real world is more complex. You’ll often bounce around into modules to make structs `Sendable` or to deal with static vars. But, I do think this is a great way **to start** for many projects.

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
