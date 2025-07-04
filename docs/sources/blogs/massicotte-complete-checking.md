# Should You Enable Swift's Complete Concurrency Checking?

Feb 14, 2024

Recently, I’ve seen a lot of talk around enabling Swift’s complete concurrency checking. I think this is a really good discussion to have. I have opinions! But, I’d prefer to try to give you enough information to understand the trade-offs, because they are significant.

## How

By default, all checking is set to `minimal`. If you want the compiler to do more checking, you have to opt-in. There are [in-depth instructions](https://www.swift.org/documentation/concurrency/) over on swift.org, but I’ll summarize.

For Xcode, the `SWIFT_STRICT_CONCURRENCY` setting must be `complete`. For Swift packages, you’ve got to set a `swiftSettings` value.

```swift
.target(
	swiftSettings: [
		.enableExperimentalFeature("StrictConcurrency")
	]
)
```

This isn’t hard to do, but I’d recommend checking out [this article](https://useyourloaf.com/blog/strict-concurrency-checking-in-swift-packages/), as there are a few ways and you can get quite clever with it.

I do want to note that there is also an intermediate form of concurrency checking called `targeted`. I have not used this much, so I don’t fully understand what it will and will not catch. I’m only going to talk about `complete` because it’s all I know.

## Why

I think many people believe you turn on complete checking to get prepared for Swift 6. And, yes, that is true! But, I do not think this is the most compelling reason today.

You turn on complete checking to **learn** how Swift concurrency **actually** works.

When you write code the compiler complains if your syntax is wrong. So you look at the errors and they help you fix things. That’s **feedback**! Finally you get things sorted and can run the program. But of course it doesn’t work right yet, so you debug. That process is **also** driven by feedback.

The problem is today you can use Swift’s concurrency system with **almost** no feedback. And it is amazingly forgiving! Because you are most likely following patterns you already know that work well. Threading issues are also notoriously tricky. You might only hit a problem 1 in 10,000 times. Or never!

The point is you need **feedback** to help you form a mental model of how things work. No feedback, incorrect mental model. I am speaking from experience.

With that, let’s look at some considerations.

## Apple Frameworks

Probably the single biggest issue right now is Apple’s own frameworks aren’t all fully updated for concurrency. This means there are cases where you can hit warnings that are **impossible** to resolve without resorting to tricks. Lots of cases can be fixed with the now-familiar `nonisolated/MainActor.assumeIsolated` [dance](https://github.com/mattmassicotte/ConcurrencyRecipes/blob/main/Recipes/Protocols.md#solution-1-non-isolated-conformance). But, in general there’s no forumla you can follow.

Thankfully there is a major new feature coming called [Region-Based Isolation](https://github.com/apple/swift-evolution/blob/main/proposals/0414-region-based-isolation.md) that I think will help tremendously here. But, it has not shipped yet.

*   Con: lots of tricky-to-resolve warnings that will probably just go away one day
*   Pro: learn how to deal with libraires not built for concurrency

## Non-Swift Code

Thankfully, Apple themselves has **lots** of C, C++, and Objective-C code. There are many ways to help express concurrency concepts here, both within the non-Swift code using clang annotations, and from Swift using `nonisolated(unsafe)` or `@unchecked Sendable`. Also, all non-Swift libraries are automatically imported with `@preconcurrency` to try to help mitigate the problems.

*   Con: complex and frustrating new interoperability problems
*   Pro: learn how to express safety to the compiler that is otherwise invisible

## Swift Packages

Whether you are using packages to define local modules, or via 3rd party libraries, the situation is roughly the same as with Apple’s libraries. The public interfaces will have an impact on concurrency usage. If they are under your control, you have maximum flexibility to do what’s required. I suspect that 3rd party libraries will begin to see a lot of bug reports as more apps run into issues.

*   Con: lots of warnings that could require a 3rd-party to resolve
*   Pro: open source opportunities, finding problematic APIs now

## So What Do You Do?

I tried to keep the above reasonably opinion-free. But, here’s where I tell you what *I* think.

If you are using concurrency without complete checking, you do not understand it. And, if you are building APIs with concurrency features, it is possible those APIs will **have to change**. It will be possible to use Swift 6 without these specific warnings/errors enabled. So, you can potentially kick this can down the road for quite a while. But that is not what I would recommend.

I also want to take a moment to empathize with you if this process brings up negative emotions. You didn’t ask for these features and your code works fine. I have no doubt there are many people, both outside and inside Apple that feel similarly. But, I do not think it is productive to dwell. Feel your feelings. And, then tackle this like all the other technical challenges you have overcome before. Refusing to learn or adopt Swift concurrency will not serve you well.

Here is what I recommend:

If you are **using** concurrency features today, I think it is **important** you turn complete checking on.

If you are using concurrency features in any of your module’s **API**, I think it is **essential** you turn complete checking on.

If you are building a library, regardless of whether it uses concurrency features or not, you **should** update your public API so it is warning-free.

This is a massive shift in how Swift code is written. I think some code bases will just not be able to make this transition. Some libraries will be deprecated, or even abandoned. We’ll see half-finished branches with names like “concurrency” in open source projects years to come. I don’t want to sound pessimistic, but I do want to prepare you in case you haven’t been thinking about this. The Swift team is doing a truly fantastic job here. But I don’t think sugar-coating the situation is helpful to anyone.

Ok, so now that you are sufficiently scared, take a breath. You have actual features you need to work on and bugs you have to address. You do not need to drop everything. But, I think you have to make **some** room in your schedule for this.

## Resources

*   Now-dated talk I did about concurrency: [The Bleeding Edge of Swift Concurrency](https://www.youtube.com/watch?v=HqjqwW12wpw)
*   Repo with some common problems/solutions: [ConcurrencyRecipes](https://github.com/mattmassicotte/ConcurrencyRecipes)

Let me know if you have other resources you think are helpful! I’d like to include them.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
