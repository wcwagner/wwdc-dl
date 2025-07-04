# Isolated Parameters
Jan 19, 2024

I’ve been using Swift concurrency a lot over the past year or so. And I’m a bit embarrassed to say that I haven’t used isolated parameters at all. I knew they existed, and I read about them a little. But I never understood why you might use them or what problems they solve. That is, until I read this [post](https://jackmorris.xyz/posts/2024/01/12/swift-sqlite-part-3/) by [Jack Morris](https://mastodon.social/@jackmorris). It’s part of a series he’s been doing on a SQLite interface. There’s lots of interesting stuff in there.

But what stopped me in my tracks was his use of **isolated parameters**.

## Isolation?

In order for the compiler to make concurrency work, it needs to understand how it should isolate values. Often, it will have access to enough static metadata for this purpose. Things with global actor annotations like `@MainActor`. I would imagine that static annotations alone account for the vast majority of concurrency usage. You’re either on the `@MainActor` or you waiting for something external that will ultimately affect the `@MainActor`.

```swift
@MainActor
func mainOnly() { ... }
```

Next you have custom actor types. In this case, static metadata is not enough. The compiler knows that you’ve got an actor, but the specific actor reference matters at runtime. When you are interacting with an actor, this is all taken care of for you. If needed, the compile will enforce an `await` to ensure that it can hop (this is the term of art it seems) to the right isolation domain to ensure safety.

```swift
actor MyActor {
	func otherStuff() { ... }

	func doThing() {
		// no awaits needed in here
		otherStuff()
	}
}

let actor = MyActor()

// await is required to isolate to `actor`
await actor.doThing()
```

Another kind of isolation you might not think about too much is none at all. It may seem weird, but it’s common! Any async function that isn’t tied to an actor has no isolation.

```swift
func noIsolation() async { ... }
```

## Isolated Parameters

So far, I would imagine there’s not much new here. But there’s one more way to tell the compiler what actor a function should use.

```swift
func run(on actor: isolated MyActor) { ... }
```

What does this even mean?

It took me a while to wrap my head around this. `@MainActor` means a function always runs on that one actor. An isolated parameter means the function runs on whatever actor is passed in. Because of this, there must be only one isolated parameter, and it must be an actor type. This is useful because it gives you a way to dynamically pass around the isolation that an actor provides.

While not equivalent, it may be helpful, at first, to think of it like an extension on the actor:

```swift
extension MyActor {
	func run() { ... }
}
```

Note that functions that use isolated parameters do not have to be async. The need for an `await` will determined at the call site, just like all other forms of isolation.

## Isolated Closure Parameters

Ok, so now we can finally get to the thing that Jack did which blew my mind. He didn’t just use isolated parameters, which would have been cool enough. He used them **in a closure**.

```swift
public actor MyActor {

	func run<Value>(
		_ action: @Sendable (_ actor: isolated MyActor) -> Void
	) {
		// we are isolated to the actor here

		action(self) // no await!

		// still isolated
	}

}
```

This is amazing. It gives you the ability to inject bits of code into an actor that uses that actor’s isolation **without** any suspension. I think Jack’s example of a transaction is fantastic. But I can imagine there are many other uses. I don’t think this is the kind of thing you’ll need to use every day. But I have encountered situations where this would have helped.

Definitely going to keep this one in mind.

---

Sponsorship helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
