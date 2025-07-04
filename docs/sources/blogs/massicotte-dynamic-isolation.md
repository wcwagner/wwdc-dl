# Is Dynamic Isolation Bad?
Apr 18, 2024

I got a little worked up the other day about, shocking I know, Swift concurrency. So I [posted](https://mastodon.social/@mattiem/112285978801305971) this:

> MainActor.run is almost *never* the right solution. You want to define your isolation statically on the type, via a global actor annotation.
>
> Dynamic isolation is an escape hatch, and it should set off alarm bells every time.

But, this take is lacking a lot of nuance. Luckily, [Rob Napier](https://mastodon.social/@cocoaphony/112286687250476162) didn’t let me get away with it. Thanks largely to his feedback, I’ve thought about it more and I feel like this topic is worth a deeper discussion.

## Static isolation

[Isolation](into-to-isolation) in Swift can take two forms. Keywords like `nonisolated`, `isolated`, `actor` and global actor annotations are all static. They are ways of expressing your isolation requirements to the compiler via the type system.

```swift
@MainActor
class SomeMainActorOnlyClass {
}

// allowed only if the compiler can prove this will be on the MainActor
let b = SomeMainActorOnlyClass()
```

Modelling your code’s isolation requirements statically has a lot of benefits. You aren’t one unexpected code path away from a crash. You no longer need to check the documentation to find out if some type is ok to use on a background thread. Or if some callback needs to happen on the main thread. These kinds of issues, which have been a major source of bugs for Apple platform developers for **decades**, are suddenly impossible. That’s quite something.

But.

Going from nothing to compiler-guaranteed thread-safety cannot happen overnight. There’s an **enormous** amount of pre-concurrency code out there. To help deal with this reality gracefully, Swift offers a variety of tools. One is a way to express isolation dynamically.

## Dynamic isolation

Locks, queues - these are all things that require correct coordination at runtime to keep things working right.

```swift
queue.async {
	// this depends on the runtime instance of queue
}
```

Dynamic isolation will feel familiar. It requires the use of runtime constructs, in the form of methods on an actor. Here are some examples:

```swift
MainActor.assumeIsolated {
	// promise the compiler this bit of code is
	// actually already on the MainActor
}

// add a runtime check to guarantee that the actor-ness is
// what you expect
MainActor.preconditionIsolated()

await MainActor.run {
	// run a chunk of synchronous code, hopping over
	// to the actor if needed
}
```

## MainActor.run

I think both `assumeIsolated` and `preconditionIsolated` are great! They are very useful for interfacing with code that either does not or cannot express the isolation you want.

But, my post from above was really aimed at `MainActor.run`. And I singled it out precisely because of its similarity to other synchronization mechanisms. I’ve run across a lot of code that looks like this:

```swift
class SomeClass {
	var state = 1

	func doStuff() async {
		let newValue = await doAsyncWork()

		await MainActor.run {
			self.state = newValue
		}
	}
}
```

This pattern probably **feels** really familiar, because it is so close to what you might do with a `DispatchQueue`. I want to be really clear - that alone is a valid reason for doing this!

The problem is, just like all forms of runtime synchronization, the compiler cannot help you. Contrast it with this:

```swift
@MainActor
class SomeClass {
	var state = 1

	func doStuff() async {
		self.state = await doAsyncWork()
	}
}
```

Not only this this code a lot simpler, it is also almost certainly a better reflection of reality. It is *possible* that the `state` variable is the only thing that needs to be mutated on the main thread. But I think that situation is quite rare. Most likely, you just have a type that only makes sense to interact with on the main thread. You tell the compiler this, and boom, it will enforce that.

That enforcement is a double-edged sword.

## Incremental adoption

Making just one type `@MainActor` can result in cascade of errors at all usage sites where the compiler now cannot provide that `MainActor` guarantee. This virality can make it really hard to incrementally adopt concurrency with targeted changes. Perhaps that’s not too big a deal for smaller code bases/teams, but I bet this is a killer for big projects. So what do you do?

You make use of dynamic isolation to contain the spread!

```swift
@MainActor
class NewlyMainActored() {
}

class ProbablyShouldJustBeMainActorEventually() {
	// this one stops the MainActor spread
	func withoutIsolation() {
		MainActor.assumeIsolated {
			let obj = NewlyMainActored()

			...
		}
	}

	// so does this
	func asyncWithoutIsolation() async {
		await MainActor.run {
			let obj = NewlyMainActored()

			...
		}
	}
	
	// not as bad as the whole type, but still possibly disruptive
	@MainActor
	func withIsolation() {
		let obj = NewlyMainActored()
	}
}
```

This right here is probably the single best reason to use dynamic isolation. It is a very good tool for incremental adoption.

## Atomicity

The `run` method has another really useful trick up its sleeve, which Rob [zeroed in](https://gist.github.com/rnapier/f513a58ec982ff4738b25afa465f6dda) on immediately. It’s a handy way to execute multiple synchronous calls without the risk of suspension. I’m just going to steal his example:

```swift
// atomic
await MainActor.run {
	obj.methodA()
	obj.methodB()
}

// definitely not atomic
await obj.methodA()
await obj.methodB()   // There is a suspension point between A and B

// equivalent to .run
await Task { @MainActor in
	m.methodA()
	m.methodB()
}.value
```

And yeah, sure, it might make more sense to combine these two methods into one call. But, this is a contrived example, and that could be easier said than done. This kind of usage is also totally valid. Further, I think it is preferable over the equivalent `Task` version. I find it much clearer, especially when you have to rely on `.value` for a `Task` that doesn’t return anything.

## All part of the journey

I heard a funny quip that says any time you see a headline ending in question, the answer is always no. I’m quite pleased to follow that pattern. No, dynamic isolation is **not bad**.

But, I think we can also agree that static isolation is *preferable*. If you find yourself using dynamic isolation solely because it is a familiar pattern, that’s something to think about more deeply. Static isolation is a safer, clearer way to express what you need. That doesn’t mean you can always or even should start with it. Adopting concurrency will be a long process. Dynamic isolation is a very handy tool for getting there, I just don’t think it should typically be an end-state.

Everyone say it with me now: “It Depends!”.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
