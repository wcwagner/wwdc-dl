# Concurrency Step-by-Step: Stateful Systems

Dec 30, 2024

You know what? Coming up with example material is hard. This might sound silly or like it doesn’t matter that much, but it really does! Of course, a great example helps keep things understandable. It makes writing a lot more enjoyable too. But, writing is still a lot of work.

That’s why I was so annoyed when [James Dempsey](https://mastodon.social/@jamesdempsey) messaged me with a fantastic idea.

He noted that both the [first](/step-by-step-network-request) and [second](/step-by-step-reading-from-storage) of these posts used an exclusively read-only system. That’s completely unrealistic! Real applications write to local storage, remote services, and generally are up to their eyeballs in mutable state.

In this post, we’re going to build a SwiftUI app that works with state hosted on a (pretend) remote network service.

## Quick notes

Following all previous posts in this series, I’m going to ignore errors and require Xcode 16. I also remain a SwiftUI beginner, and there’s more SwiftUI here than in other posts.

Another important note is that I tried, and failed, to find a suitable free remote service to use. At first I thought this was a deal-breaker. But, then I realized that this might be a happy accident. Read on to find out why!

## A “remote” system

To start, we need some kind of remote service to interact with. The whole point of this exercise is to deal with state, so it is important that this system be **stateful**. But I couldn’t find one, so we’re just going to pretend.

```swift
final class RemoteSystem: @unchecked Sendable {
	private var state = false
	private let queue = DispatchQueue(label: "RemoteSystemQueue")

	func toggleState(completionHandler: @escaping @Sendable () -> Void) {
		queue.async {
			self.state.toggle()
			completionHandler()
		}
	}
	
	func readState(completionHandler: @escaping @Sendable (Bool) -> Void) {
		queue.async {
			completionHandler(self.state)
		}
	}
}
```

This is a simulation of a remote system that manages exactly one boolean. The outside world can toggle or read the current state, but it must do so asynchronously.

I’m sure you’ve also noticed that I also chose to implement this with dispatch. To make this work with Swift 6, we have to inform the compiler that we assumed responsibility for thread-safety by marking the type `@unchecked Sendable`. We also need a few `@Sendable` closures.

## A view

Now, we need a view that actually does something with this system.

```swift
struct ContentView: View {
	@State private var system = RemoteSystem()
	@State private var state = false

	private var imageName: String {
		state ? "star.fill" : "star"
	}

	private func press() {
		system.toggleState {
			system.readState { value in
				DispatchQueue.main.async {
					self.state = value
				}
			}
		}
	}

	var body: some View {
		Image(systemName: imageName)
			.imageScale(.large)
			.foregroundStyle(.tint)
			.onTapGesture {
				press()
			}
			.padding()
	}
}
```

The `body` of this view isn’t particularly interesting, but that `press` function is where all the action is. When you touch the star image, we toggle the remote state, then read it, and finally update our UI to reflect the result. Again, all with dispatch in Swift 6 mode.

## Reentrancy

This code compiles, but it has serious problems. That `press` function runs a series of asynchronous operations, each with a dependency on what came before. The problem is there’s nothing stopping the user from tapping again **while** the first tap is being processed. And the timing of a remote system is both unpredictable and variable. It is possible for that second tap to actually finish **before** the first, resulting in the two flows interleaving in unfortunate ways.

The following sequence of events can actually happen:

*   User taps
*   `toggleState` begins, but is slow for some reason
*   User taps again
*   another `toggleState` begins, but this time is fast!
*   then its read completes and the UI is updated
*   now first `toggleState` finally completes
*   UI is updated again, reversing what user intended

There are many possible variations of this. But, we have this problem because this code isn’t **atomic**. It’s possible for `press` to start executing again before a previous invocation completed. The function can be “entered”, and then it can be “re-rentered” again, potentially many times.

This is **reentrancy**!

## The term “reentrancy”

I don’t really like the term “reentrant”. First, I just find it awkward to say/read. Second, historically, saying that “a function is reentrant” has often meant that it is **safe** to use simultaneously from multiple threads. And, third, I don’t feel like it expresses the problem particularly well.

This is just a plain old race condition. But, it isn’t a **data** race. We do not have multiple threads reading/writing the same spots in memory. I prefer to call these kinds of things “logical” races. (If there is a more correct term, however, please do let me know!)

Interestingly, you do not even need to have multiple threads to have logical races. You just need some way for multiple things to happen at the same time. A single threaded-program with a runloop is enough. As soon as you can have non-synchronous execution, you can have logical races.

## Actors

I chose to use dispatch exclusively to illustrate that you don’t need actors or Swift concurrency anywhere to run into these kinds of problems. Yet, people talk a lot about “actor reentrancy” specifically when working with concurrency - and for good reason! We just have to do some work before we can look at that more closely.

The first thing we’ll do is make an actor to model our remote system.

```swift
actor RemoteSystem {
	private(set) var state = false

	init() {
	}

	func toggleState() {
		self.state.toggle()
	}
}
```

If you go back and compare the two implementations, it’s kind of dramatic how much less code this is. Actors provide an extremely convenient way to protect state via an async interface.

However, I think what’s even more interesting is what we are using an actor to model.

## Actor vs service

Remember, I wanted to find a simple **remote** service. Being remote, the only way to interact with it would be via network requests. Actors are a lot like a remote service, in that the only way you can possibly interact with their internal state is asynchronously.

But there’s more! To use a network service, you also must package up and send any parameters over the wire. And, in turn, that service has to do the same to return any results back. This is a great way to think about actors from a design perspective. All the inputs and outputs need to be sent back and forth too.

Of course a remote service needs the data to actually be serialized for transport. With an actor, we don’t need the serialization. We just need to ensure that it’s safe for these types to leave whatever thread/queue they are currently in to “send” them over to the actor. We need these inputs and outputs to be `Sendable`.

Actors and remote network services are not interchangeable. But they can be really close! And I think it can be useful to think about them in a similar way.

(This similarity to remote services is exactly where [distributed actors](https://developer.apple.com/documentation/distributed) comes from!)

## Using the actor

Ok, now back to the problem at hand. We also have to modify the view to actually make use of this actor-ified system. But, we can keep the changes localized to just that `press` method.

```swift
private func press() {
	Task {
		await system.toggleState()
		self.state = await system.state
	}
}
```

The reduction of code, again, is quite substantial. But, this small amount of code packs in a lot! There’s all kinds of stuff going on here, and we’re going to step through it all.

To start, we have to actually run async methods, and that means we need a `Task`. Recall that isolation inference has made this `press` method `@MainActor`. This, in turn, means that the `Task` body will inherit `@MainActor` too. This is why it is ok to assign to `self.state` here.

(If you don’t understand this yet, there are details in the [first post](/step-by-step-network-request). You can also go [deeper](/isolation-intuition) on both isolation inference and inheritance if you want.)

I like to call this out because it isn’t up the the programmer to remember, or even **understand** how or why `self.state` must be accessed on the main thread. This requirement is encoded into the type system, allowing the compiler to ensure it is happening. All this is in **stark** contrast to the dispatch version, which requires the developer to know they need the `DispatchQueue.main.async` for thread safety.

But there’s yet more subtly here. If you go back and check out the dispatch-based version, you can see that `press` makes a call into `system.toggleState` **synchronously**. The execution goes all the way from the UI directly into the `RemoteSystem` method all without leaving the main thread.

That’s no longer the case here! We have now introduced a **new** asynchronous step. That `Task`, which establishes the async context we need, will not run immediately. It has to be scheduled on the main queue.

(There is a lot of subtly around `Task` creation and exeuction ordering. In the general case, though, you should not think about Task having FIFO sematics. Ths is a major difference between concurrency and dispatch.)

Those don’t really matter in this **specific** example, but can be a major change to the ordering of events. It is something you should keep in mind every time you introduce a `Task`. And doubly so if you do it as part of a migration from completion handlers to async/await. This was one of the first [major problems](/ordering-and-concurrency) I encountered when starting to use Swift concurrency.

We’ll return to this idea, but migrating a system from completions handlers to async functions is not purely a change in syntax.

## Adding delays

Because we’re now starting this work asynchronously, we’ve actually **increased** the window of opportunity for our logical race. In that sense, it has definitely been made worse! But, I don’t think that’s really so bad. In fact, when faced with logical races (known or suspected), I sometimes do this kind of thing intentionally. Slowing down code can often expose latent bugs like this. Many races are just unlikely, possibly virtually impossible, given normal code execution.

Doing that here can also really help us develop some better intuition around how this stuff all works. Because async code, by design, looks really similar to synchronous code. And, in my opinion, **that’s** why it is more susceptible to logical races. They don’t (yet) stand out to us because it all looks so similar to synchronous code.

To add delays, first I’m just going to define a little helper function which will produce a random delay up to 1s.

```swift
func randomDelay() {
	let delayRange: Range<UInt32> = 0..<1_000_000

	usleep(delayRange.randomElement()!)
}
```

You don’t have to be so fancy. Most of the time a simple `sleep(1)` can work. But, delaying for a second every time can really add up if you do it a lot. And, using completely uniform delays can sometimes fail to expose races, even when you know they are there.

(Details on [sleep](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/sleep.3.html) and [usleep](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/usleep.3.html) via manpages.)

Here’s the code with the delays inserted:

```swift
private func press() {
	Task {
		randomDelay() // start

		randomDelay() // enter
		await system.toggleState()
		randomDelay() // complete

		randomDelay() // enter
		let value = await system.state
		randomDelay() // complete

		self.state = value
	}
}
```

There are a lot!

The first is the latency that a `Task` can experience before even beginning. This is inherit to pretty much all APIs like this, and something like a queue’s `async` method would experience as well. It’s really good to always keep this in mind.

Next, we have two pairs of delays, around our async calls. An async call **may** need some time to begin. It then will run, and require some time before completing.

Remember, these delays are not artificial. What we are doing here is really just **magnifying** all of the real delays in the execution to help us think about them and observe their effects.

(Understanding the details about when/why/how an `await` can actually suspend is complex. Thankfully, you rarely need to care. But I’d love to write more on this one day anyways.)

## Focusing on the race

I hope I have now convinced you that there’s a lot of opportunity for this code to interleave. This is a very common problem for UIs in particular. Let’s look at some ways to fix it.

The core problem is it is possible for the user to invoke `press` more than once. If we add a little state to our UI, we can prevent that.

```swift
struct ContentView: View {
	@State private var inProgress = false

	// ...

	private func press() {
		if inProgress { return }
		self.inProgress = true
		
		Task {
			await system.toggleState()
			self.state = await system.state
			
			self.inProgress = false
		}
	}
}
```

All we’ve done here is add a simple guard. If the work has already started, do nothing. If not, mark it started, actually do the work, and then mark it complete.

Simple!

## Critical sections

I bet you have run into problems just like this before. Maybe you’ve disabled buttons or added spinners, but solutions usually look about the same. However I really want to highlight an important element here.

The check must be **synchronous**.

Here’s an alternative, with the checks all inside the `Task`. I want you to really think for a second, though. Is there still a race here?

```swift
private func press() {
	Task {
		if inProgress { return }
		self.inProgress = true
		
		await system.toggleState()
		self.state = await system.state
		
		self.inProgress = false
	}
}
```

This `Task` body will always run on the main thread. This means that while more than one of these could potentially be **started**, only one can ever be executing the synchronous code within this closure.

We can argue over which approach is better, but this version is also race-free.

Now, let’s change our code slightly to illustrate what can go wrong when we **don’t** do this check synchronously.

```swift
private func press() {
	Task {
		if inProgress { return }
		
		await system.prepare()
		
		self.inProgress = true
		
		await system.toggleState()
		self.state = await system.state
		
		self.inProgress = false
	}
}
```

I’ve just inserted a new async call here. But, you can now more clearly see the problem. We consult our state. We then **incorrectly** assume that state cannot change when we call `prepare()`, but it totally could!

One way to think about `await` is like a marker ending a [critical section](https://en.wikipedia.org/wiki/Critical_section). We have to do any state accesses **synchronously**, before the task has any opportunity to suspend. This is **vital** for the correctness of many kinds of operations.

## What about actors?

Let’s look again at a part of our original, dispatch-based `RemoteSystem`.

```swift
func toggleState(completionHandler: @escaping @Sendable () -> Void) {
	queue.async {
		self.state.toggle()
		completionHandler()
	}
}
```

We discussed this above. This method takes a completion handler, but it actually is **synchronous**. When called, this work will be added to the internal queue in a way that preserves calling order. That’s not the case with our actor! Despite being synchronous function, from the outside world, it can only ever be called asynchronously.

```swift
func toggleState() {
	self.state.toggle()
}

await system.toggleState()
```

As written, this implementation is **incapable** of capturing and retaining order in the same way. Whether this matters or not is hard to say, but I want to call it out. Async functions are **not** just syntactic sugar for completion handlers. They are close, but they have critical semantic differences - this is just [one of them](/ordering-and-concurrency).

Further, just like our UI issue above, actors can totally have similar problems internally. Let’s imagine a slightly more complex version of `toggleState`.

```swift
func toggleState() async {
	await initializeStateIfNeeded()
	
	self.state.toggle()
}
```

We’ve now got another logical race, because it could be possible for more than one caller to invoke `toggleState` simultaneously. Actors are not atomic, which could lead to `initializeStateIfNeeded` being called more than once.

Now, the “ifNeeded” naming here kind of suggests a solution. We totally can introduce a state variable, just like we did in our UI above, to help. But that only really works for very simple situations. This problem can easily get much more complex. Solutions can be quite involved without something like an async [lock](https://github.com/mattmassicotte/Lock).

## Wrapping up

At this point, I now find it easier to spot logical races with async/await than I did with completion handlers. The nesting and non-linear code flow of callbacks has begun to feel quite confusing to me. That doesn’t mean callbacks don’t have uses! They can be quite powerful. But now that I have practice doing this with async code, it’s definitely my preference.

Of course, that practice took real time. It takes a while to really develop the sense of watching for and thinking carefully when you encounter an `await`.

Oh, and if you find yourself struggling to manage logical races within an actor, you aren’t alone. Many people, myself included, have had problems here. There are async versions of a [lock](https://github.com/mattmassicotte/Lock) and [semaphore](https://github.com/groue/Semaphore) that I’ve all found useful. But, if you can keep things even simpler, that might be best. Step one when having problems with actors is to make sure you actually need an actor in the first place. Just remember though, that even single-threaded (`MainActor`-only) code can still run into logical races.

And you cannot un-async real network services, so a [queue](https://github.com/mattmassicotte/Queue) isn’t something we’ll ever be able to avoid. Thankfully, often an [AsyncStream](https://developer.apple.com/documentation/swift/asyncstream) can get the job done.

I suspect that many people want more depth on working with asynchronous state mutation. This really just scratched the surface. I get so many questions about SwiftData in particular, and I’ve never used it! But, I think we still covered a lot of important stuff! Being able to recognize logical races and think about managing state synchronously are both incredibly important, even if you aren’t using Swift concurrency.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
