# Ordering and Concurrency

**Author:** Matt Massicotte
**Published:** Feb 24, 2023

It was more than a full year after its introduction before I began trying out Swift’s concurrency system. I’d never used the async/await paradigm in another language, nor did I have any experience with an `actor` concept. Everything was totally new to me. I watched a bunch of WWDC videos, read some blog posts, and began diving in.

**Update**: Swift 6 has strengthened the ordering guarantees of `Task` via the [`@isolated(any)`](/concurrency-swift-6-se-0431) attribute. This makes a big difference, but the general problems here are still applicable.

## Ordering

Migrating from a queue-based system (Dispatch/Operation) with completion handlers, at first, was amazing! I felt like I was removing so much noise from my code. However, I quickly began experiencing something that really surprised me: races. Lots of them. At the core of the issue was a fundamental misunderstanding on my part.

```swift
func asyncWork(_ block: () -> Void)
func work() async
```

These two functions have a **critical** difference. The `asyncWork` form has an opportunity to run **synchronously** before beginning any internal asynchronous work. In fact, it doesn’t even need to be asynchronous at all.

The `async` version **cannot** run code synchronously before starting if isolation changes. The `await` keyword makes that impossible to guarantee.

This difference is subtle - it certainly wasn’t obvious to me. And, there are many cases where it also doesn’t matter. But, if you have a system where the ordering of operations is important, it is **absolutely essential** you understand this:

*You cannot hide ordering requirements from the callers*

## When does it start?

The key to understanding the ordering problem really comes down to thinking about when work starts vs when it completes. First, take a peek at the non-async version:

```swift
asyncWork {
	print("done")
}
```

In this version, the function begins execution synchronously, **right now**, and finishes later. Things are different with the async version:

```swift
Task {
	await work()
	print("done")
}
```

With a `Task`, the function of course finishes later. But, it also **begins** execution later too. The only way to control for the start of a `Task` is to `await` it.

The million dollar question is - does this matter? I think that being unable to synchronously run code in this way makes some kinds of synchronization techniques trickier.

## No Queue

Here’s a pattern that I have found comes up quite a bit. It’s just a class with an internal queue to protect some state.

```swift
class MyClass {
	private let internalQueue = DispatchQueue(label: "myqueue")

	func beginWork(with value: Int, _ block: () -> Void) {
		internalQueue.async {
			// access some mutable state
			print(value)

			doSomeOtherAsyncThings {
				block()
			}
		}
	}

	func work(with value: Int) async {
		withCheckedContinuation {
			beginWork(with: value) {
				$0.resume()
			}
		}
	}
}
```

The problem arises when you look at how this class is used. It’s been accessed synchronously, but those accesses are spread out over a bunch of disconnected systems.

```swift
myclass.beginWork(with: 1) {
	print("done with 1")
}

// across functions, nested within functions, but all done synchronously,
// on the main thread

myclass.beginWork(with: 2) {
	print("done with 2")
}
```

The callers invoke the function with `1` first, and then later on, invoke it with `2`. Translating this to an async call is problematic. Despite the internal synchronization, the correct ordering of events is now up to the callers.

```swift
Task {
	await myclass.work(with: 1)
}

// across functions, nested within functions...

Task {
	await myclass.work(with: 2)
}
```

Even though it looks like 1 happens before 2 **and** the class has an internal queue, it can and will happen that 2 completes before 1. Now that the API offers an `async` version, it’s easier to introduce races. The solution is to `await` on the first task. But, the structure of your existing legacy code can make that really difficult.

## Yes Queue

You might be thinking this is a lot of words to tell me “If you want A to happen before B, you must make sure A happens before B”. And, yeah, you’re right. But, this wasn’t immediately obvious to me while moving towards using async functions. And I imagine it might not be obvious to others. It really took me quite a while to fully appreciate this problem.

If you have no implicit ordering requirements, hooray! If you can make the dependent tasks explicit - great! But if you are unlucky enough to have a system where ordering does matter, and a code base that makes explicit task dependencies difficult to express - you have yourself a problem.

In hindsight, it’s obvious: there’s no such thing as an implicit task dependency. But, when migrating complex systems, I bet this is something others have run into. As a stop-gap solution, I put together a [FIFO task queue](https://github.com/mattmassicotte/Queue). It works almost like an `OperationQueue`, but accepts async closures.

```swift
let queue = AsyncQueue()

queue.addOperation {
	await myclass.work(with: 1)
}

// ... lots of annoying legacy stuff ...

queue.addOperation {
	await myclass.work(with: 2)
}
```

I’ve really just hoisted the internal queue out and made it the callers responsibility. I really don’t like that. Explicit task dependencies are the solution, but can be pretty tricky to weave though in some cases.

## Returning Tasks

An promising alternative is to flip the problem on its head. Instead of creating an async function that you call in a task, you make a synchronous API that returns a `Task`. Something like this:

```swift
class MyClass {
	func workTask(with value: Int) -> Task<(), Never> {
		// chance to do synchronous work here...

		return Task {
			// async work can occur in this block
		}
	}
}
```

This option restores your ability to protect internal state at time of call. It also makes for easy cancellation support. I have not gone deep with this technique yet, so it’s difficult for me to say with confidence that it works well. But right now, I’m really liking it.

If you’ve faced similar problems, I’d love to hear from you.

---

Sponsorship helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
