# Crossing the Boundary
Sep 26, 2023

One of the trickier aspects of working with Swift concurrency is dealing with non-sendable types. They are everywhere! And yeah sure, sometimes it’s easy to make a type sendable. But, let’s take a look at what you can do when it **isn’t** easy.

Note: Most of the problems I’m going to discuss come up only when the Swift concurrency-specific warnings are enabled. It is not really possible to use concurrency correctly without them, so you should probably have these on too.

## Actor Boundaries

Because we’re assuming that you cannot make these types sendable, you’ve only got one option. You have to somehow only use the values within a single actor context. We need to avoid crossing those actor isolation boundaries.

I’m going to cover four options, but no doubt there are more! These are just some that I’ve stumbled onto and found useful.

## Stay on the MainActor

Often, non-sendable types originate on the MainActor. So, just never leave it! There are so many advantages to this. You can easily interface with your UI. You can absolutely still use `async` to keep your UI responsive. And, wise people have often [advocated](https://inessential.com/2021/03/20/how_netnewswire_handles_threading) for just sticking with the main thread as much as you can.

I think it is valuable, when you run into a sendable problem, to think hard about **why** this must be done on another actor. For me, sometimes it has just been this dogmatic goal of getting stuff off the main thread. The thing is, async/await now makes it easy to introduce highly asynchronous behavior into your code without ever leaving the main thread. I sometimes cannot decide if this is the smartest solution or the dumbest. But it definitely is **a** solution worth consideration.

## Actor Expansion

It’s pretty instructive to think about the design of the `MainActor`. There are **thousands** of types that are only safe to use from that one actor. It is just gigantic! Sure, it’s a special-case. But, we can still make use of the principles behind it.

Just keep making the scope of the actor bigger until there is no longer a need to pass non-sendable data around. It has expanded to contain all of it. I’m going to call this solution: **actor expansion**.

Yes, the `MainActor` has taken this to an extreme. But, you do not have to go nearly this far. Maybe you can increase the responsibility of your actor just **enough** to address a non-sendable problem. There is one thing to watch out for. This increased responsibility can compromise your design. I’ve found this particularly common when I have switched a type from a class to an actor.

I think actor expansion works best when you can group your concurrency problem into a well-defined chunk of functionality, just like `MainActor` does. But it totally can work well in other situations too. And, also like `MainActor`, this technique pairs really well with custom global actors. Not something you’d reach for every day, but very handy when used appropriately.

## Creation Capture

(The swift 6 compiler has made this technique completely unnecessary.)

Often, I run into this actor initialization problem. I want an actor to own some non-sendable value, but for some reason or other, it is not possible/convenient for the actor to create that value itself. Here’s what this looks like:

```swift
actor MyActor {
	init(_ nonSendable: NonSendable) {
		// ....
	}
}

let nonSendable = NonSendable()

// this isn't allowed!
let myActor = MyActor(nonSendable)
```

However, there’s a super-easy trick you can use to get around this! Check this out:

```swift
actor MyActor {
	init(_ nonSendable: @Sendable () -> NonSendable) {
		// ....
	}
}

// this is fine!
let myActor = MyActor({ NonSendable() })
```

This works because the closure is **sendable**. Remember: sendable closures can **create** non-sendable stuff, they just cannot **capture** any.

This let’s us give the caller control over the non-sendable creation process. I have found this technique really useful!

We can even get a little fancy with an `@autoclosure` if we really want to simplify the API:

```swift
actor MyActor {
	init(_ nonSendable: @autoclosure @Sendable () -> NonSendable) {
		// ....
	}
}

// hot-damn!
let myActor = MyActor(NonSendable())
```

## Cheat

Ok, so you’ve tried all the other options above, but you cannot find a way to get rid of these stupid sendable warnings. This happens to me most often when working with Apple APIs that have not yet been updated for concurrency. You can now do one of two things. You can live with the warnings or you can lie to the compiler. Here’s how you do the latter:

```swift
struct SendableBox<NonSendable>: @unchecked Sendable {
	let value: NonSendable

	init(_ value: NonSendable) {
		self.value = value
	}
}

let scareQuoteSendable = SendableBox(NonSendable())
```

You have to use these kinds of tricks with extreme caution. You should be **very** confident that you are merely transferring ownership in a way that cannot introduce data races. Obviously, this is a absolute last resort.

## Conclusion

My journey using Swift concurrency has been pretty rocky. I have run into a lot of problems along the way. Many were self-inflicted, brought about by having warnings disabled. And then, once I finally turned them on, I was on a mission to address every one. This turned out to be extremely hard. Wrestling with non-sendable types was a big part of the challenge.

I hope these tricks are handy. And, get in touch with me and let me know yours, I’d love to hear about them!

---
<span>
	[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
	I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
</span>
