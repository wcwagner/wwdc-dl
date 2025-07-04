# What on earth is going on with awakeFromNib?
Sep 6, 2024

When I first got into Cocoa development, Interface Builder was a **big deal**. I used it pretty extensively until sometime around the macOS 10.7 era, when I began experimenting with programmatically-defined UIs. I was an instant convert, and never looked back. This was roughly 14 years ago!

I got most of my Swift concurrency experience working on a very AppKit-heavy application. So, my ears always perk up when someone has an AppKit-related concurrency issue. Yet, here was an interesting [problem](https://forums.swift.org/t/swift-concurrency-in-real-apps/73790/34) that I wasn’t at all familiar with!

I really like this one because it is both technical and also, in my opinion, quite philosophical.

## `awakeFromNib`

Interface builder works with the file extension “NIB”. I’m pretty sure the “n” stands for “Next”, to give you an idea of the age of this stuff.

The Nib system, if you aren’t familiar with it, allows you to serialize arbitrary objects into user interface description files. But, these objects often need to reference each other. That’s tricky, because as they are being deserialized, the full graph might not yet be ready. The `awakeFromNib` method is there to allow you to finish setting up your Nib-based objects at a point where they are guaranteed to all be created.

```swift
func awakeFromNib() {
	// work with other components that might live in the nib too
}
```

The `NS/UINib` class itself lives in AppKit/UIKit. So, you would be forgiven for thinking that this whole `awakeFromNib` stuff is a method on `NS/UIResponder` or something like that. But that’s not the case!

[`awakeFromNib`](https://developer.apple.com/documentation/objectivec/nsobject/1402907-awakefromnib) is defined in the Objective-C runtime on `NSObject`. 🫨

## The Problem

I have a feeling this is uncommon, but it turns out that you totally **can** load Nibs in the background. I don’t know if this is a **good** idea, but the APIs support it. This means `awakeFromNib` is not `MainActor`-isolated.

(As it turns out, `UINib` actually **is** `MainActor`-isolated, while `NSNib` is not. There’s one person out there somewhere maintaining a cross-platform app that uses nibs and this is going to make their life hell.)

The *whole point* of Nibs is to serialize **UI** components. That’s literally the only reason it exists. And that doesn’t work in Swift 6:

```swift
@MainActor
class MyViewController : NSViewController {
	@IBOutlet var nibView: NSView!
	
	override func awakeFromNib() {
		// ahh finally I'm certain nibView has been deserialized
		// and I can finish with my set up

		// ERROR: Main actor-isolated property `nibView` can not be
		// referenced from a nonisolated context 
		self.nibView.color = .blue
	}
}
```

This just feels *wrong* doesn’t it?

## The Solution?

The compiler must honor the API contract of `awakeFromNib`. The framework maintainers have decided to not apply any isolation. The types and APIs aren’t able to fully describe the concurrent behavior, but the developer knows what’s actually going to happen at runtime.

This is a special-case of a very common issue and is **exactly** why dynamic isolation exists.

```swift
@MainActor
class MyViewController : NSViewController {
	@IBOutlet var nibView: NSView!
	
	override func awakeFromNib() {
		// *I* know this will happen on the main thread
		MainActor.assumeIsolated {
			self.nibView.color = .blue
		}
	}
}
```

What you are doing here is expressing the isolation, which is invisible to the compiler, as a runtime invariant. The compiler will trust you, but it will also verify. This code will crash if it is ever run off the MainActor.

This is “the right solution”. But, if you look through that forum thread, people immediately started getting worried. Is this safe? What if *sometimes* this actually does run in the background? Do the frameworks make any guarantees here?

This is **why** the Swift 6 concurrency system was created.

## Is the API wrong?

I’m not going to hide my opinion here. I think extending the root class to solve a UI framework initialization problem was a bad idea. But, the API is what is it. And, it is definitely not wrong, *assuming* AppKit actually does support background loading. The documentation isn’t super-clear on this topic, but the API contract definitely is.

You **can** load Nibs in the background, so this API **cannot** be `MainActor`-isolated.

AppKit could have changed things such that regardless of how you load your nib, `awakeFromNib` is guaranteed to always be called on the main thread. This would have compatibility implications. So even if they wanted to do this, and I bet they did not, it could have been technically impossible anyways.

## Is the language wrong?

I think this is a much more interesting question. You might be tempted to think the compiler is being stupid here. My type is `MainActor`, just stop complaining!

The thing is, there are examples of `NSObject` subclasses that mix `MainActor` and non-`MainActor` methods. If the compiler were to treat all overrides as matching the isolation of its enclosing type, it would **completely** break `NSDocument`. Now, I want to be fair: `NSDocument` is probably as close to pathological as you can get. It uses a **custom** concurrency system that is not based on GCD or `OperationQueue`. And, it regularly mixes in main thread and background work, which is pretty much all configurable at runtime.

(The automatic ObjC-> async bridging, which is documented as being an option, is also unsafe to use with `NSDocument`: FB13394787)

Bottom line: I don’t think the language **can** solve this problem. It **must** respect APIs as written.

## Everything is wrong!

Some APIs, even really important ones that you use every day, just won’t ever work well with Swift concurrency. I’m certain some language changes could make things a little easier here and there. But, largely, these problematic APIs are going to be deprecated and replaced. It’s happening with [Notifications](https://forums.swift.org/t/pitch-concurrency-safe-notifications/73713) right now.

You might find yourself wondering if this stuff is even ready yet, given how many problems there still are. And that, my dear reader, is exactly how you should feel when you are encountering a major technology transition. There’s a reason Swift 6 is opt-in for both existing **and** new projects.

Like all major transitions, this one will take **years**.

But if you want to opt-in and use Swift 6, go for it! You just have to be clear-eyed about exactly what you are opting into. There are some APIs that will **never** work well. You have to be ready to understand why **and** find solutions. This `awakeFromNib` thing honestly isn’t particularly bad, as far as problems I’ve encountered. Count yourself lucky runloops aren’t involved.

In another year, I expect things will be in better shape. Just don’t make the same mistake I did and opt into concurrency before you are ready to deal with the implications. I started using it very early on, and the results were painful. Sure, I learned a lot. But I also built a bunch of things that were totally wrong and had to be replaced. I’m still dealing with some of those mistakes.

Think carefully about your timing and goals. If you want everything to just work, now is definitely not the right time.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
