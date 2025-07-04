# Making Mistakes with Swift Concurrency
Aug 6, 2024

I’m really enjoying how much discussion has been going on in the Swift community lately. It feels like everyone is talking about their experiences with concurrency, both good and bad. Like with most feedback, the good stuff is nice to hear. But it’s the bad stuff that can often be most useful.

I’ve now heard about lots of problems. There’s a great mix of technical and philosophical stuff. I love both! There are trends and I want to focus in on a few them.

## I’m running into problems, but warnings are disabled

It is so hard to address the concurrency problems that come up here. I’m not sure we can even really have a meaningful discussion. Swift 5 mode + no warnings can be **extremely unsafe** dialect of the language. There are basically no rules, and you cannot use a compiler-based concurrency system when the compiler’s checks are disabled.

When you do this, you aren’t just at risk of building systems that work incorrectly, you are also building an incorrect mental model of how the language works. This is **very** bad. It may feel like it is getting you closer to Swift 6, but it could be doing the exact opposite.

## I have to migrate to Swift 6 mode now

I think there is a lot emotional pressure here because it is such a hot topic. But, the timeline for this migration is going to be measured in years. Now if this is a personal project, go for it! If you work on a larger project/team, I think making this case is a lot harder. This is even more true for large projects with low modularity, because language mode is per-module. Come to think of it, this could be a great way to justify modularization efforts! (Quick, go tell your manager!)

I really want you to have a very clear reason for why this is important to do **right now**, especially considering that the Swift 6 compiler is still in beta.

## I want to ignore this stuff and I can’t

This is kind of the inverse of the previous issue. I completely understand this feeling!

The thing is the Swift 6 compiler supports the **Swift 4 language mode**, which was released in 2017. And, this is a **way** bigger change. I wouldn’t be surprised if the Swift 5 language mode outlives many Swift 5-based projects.

The language is going in this direction, there is absolutely no doubt. But, you are not being forced to come along, at least not in the medium-term. There a handful of APIs that are exclusively available using these new language features. And that will only increase with time. But, it should be relatively painless to bridge back to GCD if you need to.

Unless you are making a library, you can largely **ignore** all this stuff if you aren’t into it. Might not be the worst idea, since we’re certain to see further refinements to both the language and APIs in the coming years.

## I read something that says this whole thing is a bad idea

Whatever you read was a real experience and it is **valid**. But, the context is absolutely **essential** here.

How far did they go before turning on warnings? Were they using a Swift 5 compiler? How modularized was their project? How much of a factor was first- and third-party code? How big was the team? How much non-Swift was involved?

Without clear answers to these kinds of questions, it’s difficult to understand how applicable this experience is going to be to yours.

## You have to understand everything

I’ve encountered this sentiment in a number of places. The language has definitely expanded pretty significantly recently.

Maybe there’s some new language tool you can use to solve a problem or build a better API. How can you possibly know unless you understand everything?

I do not think you need to go and read every proposal. I did, and honestly, it was a lot of [work](/concurrency-swift-6-se-401). But, something I learned from doing it is many of these new language features were specifically built to help **hide** details. It’s still pretty early, but I think ultimately this is going to end up largely succeeding. What it all comes down to is how much concurrency you have in your project. (Probably too much)

You cannot progressively disclose the details of features you are **actively** using. Concurrency touches virtually all existing Swift code so tons of stuff gets shoved in your face all at once. If you are mostly a main-thread developer, working on UIs, I think you’ll be able to get lots of work done without going too deep. If you are building APIs for other developers, you may need to understand a lot more.

## Swift 6 is solving a problem that does not exist

I have worked on crash reporting systems as my full-time job for two companies. I admit that I have been out of the game for a while now. But, accidentally running stuff off the main thread is the simplest and most straight-forward concurrency problem you could possibly have it was **absolutely pervasive**. And an understandable and attributable crash is just about the best outcome you can hope for in this scenario.

Now there **are** some well-established [patterns](https://inessential.com/2014/03/08/api_design_the_main_thread_and_queues.html) that can help avoid many concurrency issues, that one definitely included. But, these are often employed by advanced users that have been practicing for years. I think it is easy for these habits to make “I don’t have this problem” feel like “this is not a problem”.

## Legacy APIs are easy to use

A particularly pernicious issue is how many APIs remain incorrectly-annotated. This can range from just an annoyance all the way up to a catastrophic interoperability problem. I’m hoping to see further developments to help here, because this one is going to be with us for a while.

But in the meantime I think we have to come to terms with the reality as it is today. All libraries that make use of concurrency across the **entire ecosystem** need to be **updated** or **deprecated**. Unfortunately when it comes to updating APIs, even just the minimum can require a deep understanding.

This is a great time to archive those repos you aren’t going to work on anymore!

## Everything should be Sendable

If it’s a value type, possibly. Maybe even probably! But if it is a reference type, almost certainly not. Needing lots of stuff to be `Sendable` is a usually sign you have too many isolation boundaries. A big cause of this is introducing too many actors into your code. Too many can be one. Actors are deceptively complex, and I think they should considered an advanced tool.

## Actors are FIFO

Nope. Actors are not queues. Let me say it again, `actor` is an advanced tool. Be wary of any material that makes it seem otherwise. You should be sticking to the binary main/not-main until you are very comfortable with isolation before trying them out.

## Non-isolated is unsafe

This one is very understandable. It is tricky to get the idea of isolation, and the word `nonisolated` really does sound like you are turning off some kind of protection. But, the compiler will still prevent you from making mistakes. The two keywords that really could introduce problems are `@unchecked` and `nonisolated(unsafe)`.

A great pattern for most projects is lots of `@MainActor` with some little bits of `nonisolated` here and there to get stuff off the main thread.

## Establishing an async context is easy

This is another one that was made out to be a simple thing in the early days of concurrency. Just use `Task` they said!

The transition from a synchronous to asynchronous context actually is **easy**, but is often also really **tricky**! The problem is controlling order. This is something I have [written about](/ordering-and-concurrency) before, but I really want to revisit it. Here’s a good mental model courtesy of [Rob Napier](https://mastodon.social/@cocoaphony/112893796368067518).

> Every time you write Task, I want you to pretend it’s actually this:

```swift
Task {
	let delay: Int = (0...10).randomElement()!
	try await Task.sleep(for: .seconds(delay))

	// .. Your code
}
```

This is a **little** on the pessimistic side. Swift 6 is bringing some better behavior the to `Task` API. Even so, I still like this way of thinking.

## Beginners will learn about queues and locks

People very commonly ask if they should start by learning UIKit or SwiftUI. Someone just getting started cannot possibly learn everything. So they look for guidance to help them focus. But, the pull towards SwiftUI is very strong, if for no other reason than it is new. People like new stuff, but beginners **love** it. Why should they put time into learning an older technology?

Today, Xcode 16’s default for a new project is Swift 5. Just that is going to go a very long way.

I believe that beginners will still make the transition to Swift 6 relatively quickly. Not with full understanding, mind you. But they didn’t have that with the global-queue-to-main-queue dance either. At least now the compiler will enforce correctness, and can do so with less code.

## Unsafe opt-outs defeat the purpose

This is a really interesting case I think. If you just put `@unchecked Sendable` and `@preconcurrency` all over your code base, did you really achieve something useful? I think the answer is very clear: **absolutely**.

Getting warnings on, or even to full Swift 6 mode, is about setting yourself up for **future** work that fits the model. There are also cases, like with a `@preconcurrency` protocol conformance, that introduce a lot more safety than what you had before.

I think this is a good starting point. I’m not saying it’s **great**. And, it really is a **starting point**. But, I think this approach really can help minimize disruption while also introducing some stronger safety guarantees. You have expressed truth, perhaps with a little optimism mixed in. The pieces are now in place so you can further refactor with more confidence.

## Onward

I’d love for this not to be the case, but for me, making mistakes is a critical part of learning. That can certainly be painful, and sometimes embarrassing. I feel like I’ve been making mistakes at a record pace recently and I choose to believe that’s a good sign!

I’m sure at least some of the stuff here will end up being wrong. I’m ok with that. This is an incredibly interesting time to be working with Swift. We probably still have, at a minimum, another year to wait before we really have a good idea of how this transition is playing out. I’m really appreciative of everyone out there sharing their experiences. I’ve been learning a lot!

***

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.

