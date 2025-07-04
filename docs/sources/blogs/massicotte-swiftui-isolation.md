# SwiftUI Got Isolation Wrong

Feb 22, 2024

I was thinking about a [post](https://www.donnywals.com/how-to-determine-where-tasks-and-async-functions-run-in-swift/) by [Donny Wals](https://chaos.social/@donnywals). The discussion is really centered around isolation and how the isolation inheritance rules can be challenging to reason about. But, what I couldn’t get over was that SwiftUI was used as the main source of examples.

I think SwiftUI is doing isolation wrong.

**Update**: SwiftUI has been changed as of the SDKs within Xcode 16!

## Protocol Isolation

Very broadly speaking, there are three isolation patterns you’ll see used with protocols.

*   no isolation
*   whole-conformance isolation
*   per-member isolation

Protocols are used extensively by UIKit and AppKit for delegates. You can find all three patterns. I’m going to use the text system, because I think it has some great examples of the implications of these different patterns.

First up is [`UITableViewDelegate`](https://developer.apple.com/documentation/uikit/uitableviewdelegate). This protocol uses whole-conformance isolation, which roughly looks like this:

```swift
@MainActor
protocol UITableViewDelegate {
	// functions/properties
}
```

What this is saying is any functions that satisfy the conformance to `UITableViewDelegate` **must** be isolated to the `MainActor`. This shouldn’t really be too surprising because you cannot interact with a `UITableView` off the main thread. While totally resonable, it is still a constraint. It is **impossible** to make an actor type conform to this protocol.

(Global actor-isolated protocols are a little complex. An earlier version of this post used the term “whole-type isolation”, but that’s technically inaccurate. Protocols marked with a global actor do not *necessarily* enforce isolation on the entire conforming type.)

Bizarrely, [`NSTableViewDelegate`](https://developer.apple.com/documentation/appkit/nstableviewdelegate) has taken a different approach. It uses per-member isolation, which looks more like this:

```swift
protocol NSTableViewDelegate {
	@MainActor
	optional func tableView(_ tableView: NSTableView, didClick tableColumn: NSTableColumn)

	// lots of other functions all annotated with @MainActor
}
```

The difference is per-member isolation is less restrictive. Compared to whole-conformance isolation, nothing really changes from the perspective of the code using the protocol. But types **conforming** to the protocol have more flexibility with their own isolation. They can, for example, be `actor` types.

The no isolation pattern is used by [`NSTextStorageDelegate`](https://developer.apple.com/documentation/uikit/nstextstoragedelegate). `NSTextStorage` isn’t actually a part of the text systems’s views, and because of that, there’s no need to constrain it to the `MainActor` at all. It’s actually totally possible to use it on another thread.

## Implications

When I started writing this, I was not actually expecting to find a difference between `UITableViewDelegate` and `NSTableViewDelegate`. But, it is kind of a happy accident, because it’s going to help me make my point (which is coming I promise).

Which of these is “better”?

I like the simplicity and explicitness of `UITableViewDelegate`’s whole-conformance isolation. There’s no ambiguity - if a type wants to be the delegate, probably will just be `MainActor`-isolated. But, on the other hand, `NSTableViewDelegate`’s per-member isolation offers flexibility. And, critically, that flexibility comes with **no downsides**. From `NSTableView`’s perspective, it is totally irrelevant if you really wanted to make the delegate an actor. You would have to deal with the isolation headaches that come along with this decision, but that’s up to you.

So, in this case, I think `NSTableViewDelegate`’s approach makes more sense. And, anecdotally, I have found that the per-member isolation pattern is far more commonly-used in Apple’s protocols. Probably for exactly this reason. Why add unnecessary constraints?

And finally, this brings us to SwiftUI.

## View

SwiftUI’s central element is the [`View`](https://developer.apple.com/documentation/swiftui/view) protocol. I’m simplifying things a little, but let’s have a look at it here:

```swift
protocol View {
	@ViewBuilder @MainActor
	var body: Self.Body { get }
}
```

`View` is very explicitly stating that you can make a type **with any form of isolation** conform to `View`. All you have to make sure is that `body` is `MainActor`-isolated.

This makes absolutely **no sense**.

For any non-trivial view, actually constructing that body will require at least some of Swift’s many property wrappers. And, if you want to factor your code in any way that involves adding functions to your view, you’ll immediately have to think about isolation. And just look at Donny’s article for examples of why that is so difficult. It’s incredibly confusing because body inherits different isolation than the rest of the type.

This particular issue was such a common problem that it even motivated a [language change](https://github.com/apple/swift-evolution/blob/main/proposals/0401-remove-property-wrapper-isolation.md)! I think the change was very good, but was only such a wide-spread issue because SwiftUI’s view isolation pattern **doesn’t match** how it is actually used in the common case.

The only reason a SwiftUI View exists is to generate that `MainActor`-isolated `body`.

## The Fix

Now, I will concede that I am not an experienced SwiftUI developer. There may be something I’m missing. And, if you know what that something is, please tell me! But, with the information I have, I’m willing to take a stand here.

I believe the situation where it would make sense for a `View` to **not** be `MainActor`-isolated is so bizarre it should just not be possible. The flexibility you get from per-member isolation is unnecessary. But, the implications of not forcing `MainActor` isolation is enormous, wide-spread **confusion**.

SwiftUI’s `View` should actually be defined like this:

```swift
@MainActor
protocol View {
	@ViewBuilder
	var body: Self.Body { get }
}
```

So, I’ll wrap up by saying two things:

*   All your SwiftUI views should be always be `@MainActor` isolated
*   SwiftUI should just fix `View` to make these problems go away

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
