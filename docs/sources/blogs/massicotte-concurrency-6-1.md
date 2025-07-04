# New Concurrency Stuff with 6.1
Feb 23, 2025

At long last, there is now a beta release of Swift 6.1! There are a few interesting things in here for those concurrency enthusiasts out there, and I wanted to go over them quickly.

## Isolated synchronous deinit

(Update: While trying to test this feature, I was unable to get it to work. I, incorrectly, assumed that was just a beta thing. Turns out this has been pulled from 6.1 and will be delayed to a future release. Very sorry to get your hopes up like that.)

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0371-isolated-synchronous-deinit.md) has been a long-time coming. Just look at that review process! There were **eight** steps! This, I’m sure, also gives you an idea of the complexity of the problem.

Many people have been surprised that `deinit` **wasn’t** isolated. It doesn’t always cause issues, but it definitely does come up. There are some workarounds suggested in the concurrency [migration guide](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/commonproblems#Non-Isolated-Deinitialization), but it can occasionally be a real problem.

Well ~~as of 6.1~~ in a future release, you’ll be able to do this!

```swift
@MainActor
class SomeMainClass {
	isolated deinit() {
		// this is now MainActor!
	}
}
```

You do have to explicitly opt into this functionality with that `isolated` keyword. First, because applying it automatically would be source-breaking. But second, this behavior has a performance cost. I don’t think you have to be **afraid** of that cost, but you should definitely be aware of it.

## Allow nonisolated to prevent global actor inference

I really like [proposals](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0449-nonisolated-for-global-actor-cutoff.md) that make things work more intuitively. What this one does is expand the use of `nonisolated` so you can better control global isolation inference.

Suppose you’ve got some non-isolated protocol with a bunch of requirements. But, you want to apply it to a `MainActor` type.

```swift
protocol NotIsolated {
	func doStuff()
	func doThings()
}

@MainActor
class MainActorType {
}
```

Before, you had to do something like this.

```swift
extension MainActorType : NotIsolated {
	nonisolated func doStuff() {
	}
	
	nonisolated func doThings() {
	}
}
```

But with this 6.1, you can shift that `nonisolated` to the extension!

```swift
nonisolated extension MainActorType : NotIsolated {
	func doStuff() {
	}
	
	func doThings() {
	}
}
```

I like this. And that’s just one example. You can now use `nonisolated` in inheritance clauses and other spots too. This is very convenient, and could play a more important role, given [other changes](https://forums.swift.org/t/pitch-control-default-actor-isolation-inference/77482) that may be coming.

## Allow TaskGroup’s ChildTaskResult Type To Be Inferred

I completely missed [this one](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0442-allow-taskgroup-childtaskresult-type-to-be-inferred.md) when it was pitched! It’s just a great little quality-of-life improvement for the `with*TaskGroup` family of APIs.

I’m going to steal and simplify the examples from the proposal, because they make the change really clear. When you are working with `TaskGroup`, you always need to provide some kind of clue on the types involved. Like this:

```swift
let messages = await withTaskGroup(of: Message.self) { group in
	// ...
}
```

That `(of: Message.self)` argument part is required. Or at least, it was! With Swift 6.1 it is no longer necessary.

```swift
let messages = await withTaskGroup { group in
	// the result type can now be inferred!
}
```

The type inference happening here is not magic, and there are some patterns that will defeat it. But they are rare, and I think this is super cool. Well done [Richard](https://github.com/rlziii)!

## Other improvements

I’ve been looking very forward to Swift 6.1 for a while now. This release contains a bunch of great diagnostic improvements. There’s nothing life-changing, but efforts here are very welcome.

Another area that has seen attention is around the `sending` keyword. There were a number of situations where the compiler was too conservative with `sending` and 6.1 has gotten a lot better! If you have run into issues here, take a look. Quite a few problems I have encountered have been addressed.

(Upon further reflection, these fixes I’ve noticed are probably technically all improvements to the [region-based isolation](concurrency-swift-6-se-0414) system and not really `sending` specifically.)

## What’s Next?

There was an incredible amount of activity recently in the Swift world, all centered around the now-approved [vision document](https://github.com/swiftlang/swift-evolution/blob/main/visions/approachable-concurrency.md) to improve the approachability of data-race safety. I’m excited, because there is good stuff coming!

And speaking of good stuff, have you noticed that Swift is now on both [Bluesky](https://bsky.app/profile/swift.org) and [Mastodon](https://mastodon.social/@swiftlang)?

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
