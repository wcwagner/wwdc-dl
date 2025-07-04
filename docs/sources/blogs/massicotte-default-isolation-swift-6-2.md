# Default isolation with Swift 6.2
May 12, 2025

As we started getting closer to the release of Swift 6.0, I had this bright idea. I decided to write about every evolution proposal related to concurrency that would ship with that release. This resulted in [12 posts](/concurrency-swift-6-se-401) and let me tell you, it was a lot of work. I even cheated! I skipped [one](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0433-mutex.md), the introduction of the [Mutex](https://developer.apple.com/documentation/synchronization/mutex) type. I guess it just didn’t feel like enough of a “language change”.

I did a mini version of this again for [6.1](/concurrency-6_1), but as a single post. That wasn’t too bad, because there were only ~~three~~ two changes and they were quite manageable. But now, Swift 6.2 is right around the corner and it is bringing with it 11 concurrency-related proposals.

I don’t think I can pull off a post for each proposal this year. But, I’m not sure that’s even necessary anyways. Many of them are minor things. But not all.

Let’s talk about one of the most interesting of the changes coming: control over default isolation.

## Visibility

Here’s a mistake that I make all the time. I’m working on some bit of code and things are going well. I’ve gotten far enough now that I want to start writing some tests. But, I immediately realize that I’ve forgotten to include `public` on a whole bunch of stuff. Catching this kind of mistake can be even harder if you leave the default `@testable` attribute on your imports. I usually remove it, but sometimes I forget that too.

I know, I know. You’re thinking: “What does visibility have to do with anything?”

Well, visibility is interesting because it has a default. If you don’t specify anything, visibility will implicitly be `internal`. And that default is quite reasonable. You may want more fine-grained control. You might need to make stuff public, like I do here. But the `internal` default can get you quite far.

The second reason I’m bringing this up is because visibility is defined entirely by the source. It’s all about communicating some information to the compiler. It doesn’t change anything at runtime. It has no dynamic component. Visibility is a **static** construct.

Further, and perhaps most importantly, you can write real programs without even thinking about visibility. That’s **progressive disclosure**! In fact, with a single-module application, quite a common form of Swift project, you might never even encounter it.

All this visibility stuff is an analogy for **isolation**!

## Static Isolation

I wanted to go on this little side-quest because people don’t find understanding [isolation](/isolation-intuition) easy. Adding the distinction between static vs dynamic just makes it that much harder. And I really wanted to find a way to help explain this, because this is the Big Idea you need to get to understand what’s changing.

Very similar to visibility, every declaration has a well-defined static isolation. What we’re most interested in here the default. What is the static isolation when you don’t specify anything?

```swift
func howIsThisIsolated() {
}
```

Without annotations or anything else involved, the default static isolation is `nonisolated`.

## What does `nonisolated` mean?

I frequently talk about how Swift concurrency makes heavy use of the type system. One way I really like to emphasize that is by showing that “isolation” the concept can be modelled entirely using a type.

```swift
typelias Isolation = (any Actor)?
```

Actors, types that conform to the [Actor](https://developer.apple.com/documentation/swift/actor) protocol, are what implement the isolation mechanism at runtime. But, note that this type is optional. There could be no actor at all. A `nil` here corresponds to `nonisolated`.

This does not mean unsafe! There’s lots of stuff that doesn’t require any form of thread-safety. Many things are just inherently thread-safe.

```swift
let global = 42
```

This is just an immutable integer. There’s no way to introduce any data races with this value. So, the default of `nonisolated` works fine. No protection needed.

The core problem is it’s very easy to write code that is **not** fine.

```swift
var global = 42
```

A **mutable** global value could be read and written anywhere. This is not safe and the compiler will tell you so. In this case (and many others), a default of `nonisolated` doesn’t work so well.

## The Problem

When we looked at visibility, we noted three properties. It’s defined statically, it has a default, and that default suits many situations well.

Isolation is also statically defined. But, it’s default is **not well suited** to many kinds of problems. In fact, you can think about a default of `nonisolated` as a kind of presumption of concurrency. The compiler is assuming that all code has no isolation. Because Swift 6 will not permit data races all non-isolated code therefore **must** be thread-safe via other means.

That has big implications for progressive disclosure. The compiler will force you think about concurrency, even for toy programs that have no concurrency in them. It could force you think about concurrency before you’ve even learned what concurrency is.

Another major issue is many Swift projects are primarily, sometimes exclusively composed of main thread state. I spend a surprising amount of time trying to convince people that types that contain main thread-only state should be marked `@MainActor`.

For many Swift projects, `nonisolated` just isn’t a great default.

## Controlling the default

[SE-0466](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md) introduces a way to control the default isolation. I’m not yet sure how it will be surfaced in Xcode, but here’s how it will work for packages:

```swift
let package = Package(
	name: "Test",
	products: [
		.library(name: "Test", targets: ["Test"]),
	],
	targets: [
		.target(
			name: "Test",
			swiftSettings: [
				.defaultIsolation(MainActor.self) // <- !!
			]
		),
	]
)
```

The mechanism uses a new `SwiftSetting` called `defaultIsolation`. By supplying the argument `MainActor.self`, the compiler will assume a default of `@MainActor`.

This is a **big** change!

Note that you can also use an argument of `nil`. Or you can just omit the setting altogether. Both of these will preserve the current behavior of a `nonisolated` default. That’s very important: this is **opt-in**.

## Whoa whoa whoa

Many people have been worried about this. “Everything on the main thread? Performance is going to be terrible!”

The concern makes sense. This has the potential to shift a lot of work onto the main thread.

However!

I am firmly of the opinion that moving work off the main thread should be done with both care and intention. It is **far** easier to introduce some targeted concurrency into a `MainActor` type than it is to work with a non-isolated type. There’s a tremendous amount of code out there that **should** be marked `@MainActor` but isn’t.

Understanding and managing [slow synchronous work](/synchronous-work) remains very important. But I find myself much more preoccupied with code that has a fundamentally-problematic concurrency design. Give me UI hangs over that any day.

## A new dialect

Ok, so let’s now return to an example we looked at earlier:

```swift
var global = 42
```

Pop quiz, hotshot! Does this compile with Swift 6.2 in the 6 language mode?

This question is **unanswerable**.

It is not possible to fully understand how or even if Swift code works without knowing this setting. If this code has omitted this new setting, or explicitly opted to use a `nonisolated` default, it does not compile. But if the code has opted into the `@MainActor` default, it does.

This is known as a “language dialect”. The meaning of the code depends on an external setting not present in the source.

It is absolutely true that a huge amount of Swift code could make sense to be `MainActor` by default. But, does all? As soon as you go below the UI, the answer starts to become less clear. And that’s just in the context of apps. What about server side work? Or embedded projects?

Choosing a universal default isn’t easy or even obvious. That’s why the trade-off was made here to allow for per-module control.

## Another option

While not yet actually accepted, [SE-0478](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0478-default-isolation-typealias.md) introduces another option to control this behavior that is visible in the source.

It is done via a top-level `typealias` declaration.

```swift
private typealias DefaultIsolation = MainActor

// or

private typealias DefaultIsolation = nonisolated
```

This would apply just to the current file, overriding any module-level settings.

And, speaking of related proposals, it’s also worth noting that [SE-0449](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0449-nonisolated-for-global-actor-cutoff.md), included with Swift 6.1, makes it possible to use the `nonisolated` keyword in many more contexts. This is an important capability for a world where the default is not longer guaranteed.

## Choosing a default

Today, there are a lot of APIs marked `@MainActor`. I’m not sure exactly how many occurrences there are of this attribute within UIKit but I’m going to estimate it at roughly 1 bazillion. Yet there are also a lot of uses of `nonisolated`, either explicitly or implicitly. Even for a huge UI-heavy system, I’m not sure it’s 100% clear exactly what a reasonable default could be.

And this brings us to a tough choice. Swift 6.2 gives us the ability to set the default to `@MainActor`.

But should we?

Setting the default has the potential to completely remove the need to think about concurrency. This could be an **enormous** win in many situations. For example, it would make the Swift 6 language mode a more friendly choice for true beginner programmers.

But I find myself hesitating for all other situations. It certainly **could** work. And by no means am I implying it would only be for beginners. Is it better to save yourself from typing `@MainActor` or `nonisolated`? You might even decide to preemptively mark things as explicitly `nonisolated`, in case you want to experiment.

For now, I just don’t know how to make this call. I don’t love the idea of a language dialect. But just because that could be a problem doesn’t mean it actually will. And, there another significant [change](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md) coming in 6.2 that I think complicates this even further. Right now, though, I see myself sticking with a `nonisolated` default. I need more experience trying this out with real systems before I make up my mind. But as always, if you have thoughts on this, I’d be very interested to hear them.

Oh and also, if you enjoyed this, it was all inspired by preparation I’m doing for [One More Thing](https://omt-conf.com). I’d love to see you there.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
