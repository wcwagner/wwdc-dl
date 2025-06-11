# Code-along: Cook up a rich text experience in SwiftUI with AttributedString

**Session 280** - WWDC 2025

## Description
Learn how to build a rich text experience with SwiftUI's TextEditor API and AttributedString. Discover how you can enable rich text...

## Transcript

[00:07] Hi, I'm Max, an Engineer on the SwiftUI team,
[00:10] and I’m Jeremy, an engineer on the Swift standard libraries team!
[00:14] We’re both delighted to share
[00:16] how you can build rich text-editing experiences
[00:19] using the power of SwiftUI
[00:21] and AttributedString.
[00:23] Together with Jeremy’s help,
[00:24] I’ll cover all the important aspects of rich text experiences in SwiftUI:
[00:29] first, I’ll discuss upgrading TextEditor
[00:32] to support rich text using AttributedString.
[00:36] Then, I’ll build custom controls, enhancing my editor with unique features.
[00:41] And finally, I’ll create my own text formatting definition
[00:44] so my editor - and its contents - always look great!
[00:49] Now, while I may be an engineer by day, I am also…
[00:55] a home cook on a mission to make the perfect croissant!
[00:59] So recently, I’ve been cooking up a little recipe editor
[01:02] to keep track of all my attempts!
[01:06] It has a list of recipes to the left,
[01:09] a TextEditor for editing the recipe text in the middle,
[01:12] and a list of ingredients in the inspector to the right.

### Code Sample: TextEditor and String - [1:15]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: String

    var body: some View {
        TextEditor(text: $text)
    }
}
```

[01:15] I’d love to make the most important parts of my recipe text stand out
[01:19] so I can easily catch them at a glance while cooking.
[01:22] Today I’ll make that possible by upgrading this editor to support rich text!
[01:28] Here is the editor view, implemented using SwiftUI’s TextEditor API.
[01:34] As indicated by the type of my text state,
[01:37] String, it currently only supports plaintext.
[01:41] I can just change String into AttributedString,

### Code Sample: TextEditor and AttributedString - [1:45]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: AttributedString

    var body: some View {
        TextEditor(text: $text)
    }
}
```

[01:47] dramatically increasing the view’s capabilities.
[01:51] Now that I have support for rich text,
[01:54] I can use the system UI for toggling boldness
[01:58] and applying all kinds of other formatting,
[02:01] such as increasing the font size.
[02:05] I can now also insert Genmoji from the keyboard,
[02:14] and thanks to the semantic nature of SwiftUI’s Font and Color attributes,
[02:19] the new TextEditor can support Dark Mode and Dynamic Type as well!
[02:26] In fact, TextEditor supports boldness, italics,
[02:29] underline, strikethrough, custom fonts
[02:31] point size, foreground and background colors,
[02:33] kerning, tracking, baseline offset, Genmoji, and…
[02:36] important aspects of paragraph styling!
[02:39] Line height, text alignment, and base writing direction are available
[02:43] as separate independent AttributedString attributes for SwiftUI as well.
[02:49] All these attributes are consistent with SwiftUI’s non-editable Text,
[02:54] so you can just take the content of a TextEditor,
[02:57] and display it with Text later!
[03:00] Just like with Text, TextEditor substitutes the default value
[03:04] calculated from the environment
[03:06] for any AttributedStringKeys with a value of nil.
[03:10] Jeremy, I got to be honest here…
[03:12] I've managed my way through working with AttributedStrings so far,
[03:15] but I could really use a refresher
[03:17] to make sure all my knowledge is super solid
[03:20] before I get into building controls.
[03:22] Also, I really gotta make that croissant dough for later,
[03:26] so would you mind sharing a refresher while I do that?
[03:29] Sure thing Max!
[03:30] While you get started on preparing the croissant dough,
[03:32] I’ll take a moment to discuss some AttributedString basics
[03:35] that will come in handy when working with rich text editors.
[03:39] In short, AttributedStrings contain a sequence of characters
[03:42] and a sequence of attribute runs.
[03:45] For example, this AttributedString stores the text, “Hello!
[03:48] Who’s ready to get cooking?”
[03:50] It also has three attribute runs:
[03:53] a starting run with just a font,
[03:56] a run with an additional foreground color applied,
[03:59] and a final run with just the font attribute.
[04:03] The AttributedString type fits right in
[04:05] alongside other Swift types you use throughout your apps.
[04:08] It’s a value type, and just like String from the standard library,
[04:12] it stores its contents using the UTF-8 encoding.
[04:16] AttributedString also provides conformances to many common Swift protocols
[04:21] such as Equatable, Hashable, Codable, and Sendable.
[04:26] The Apple SDKs ship with a variety of pre-defined attributes -
[04:31] like those Max shared earlier - grouped into attribute scopes.
[04:35] AttributedString also supports custom attributes that you define in your app
[04:40] for styling personalized to your UI.

### Code Sample: AttributedString Basics - [4:43]

```swift
var text = AttributedString(
  "Hello 👋🏻! Who's ready to get "
)

var cooking = AttributedString("cooking")
cooking.foregroundColor = .orange
text += cooking

text += AttributedString("?")

text.font = .largeTitle
```

[04:44] I’ll create my AttributedString from earlier using a few lines of code.
[04:48] First, I create an AttributedString with the start of my text.
[04:53] Next, I create the string “cooking,” set its foreground color to orange,
[04:57] and append it to the text.
[04:59] Then, I complete the sentence with the ending question mark.
[05:03] Lastly I set the entire text’s font to the largeTitle font.
[05:07] Now, I’m ready to display it in my UI on my device!
[05:12] For more on the basics of creating AttributedStrings,
[05:15] as well as creating and using your own custom attributes and attribute scopes,
[05:19] check out the What’s new in Foundation session from WWDC 2021.
[05:26] Max, it looks like you’re done making the dough!
[05:28] Are you ready to dive into the details of using AttributedString in your recipe app?
[05:32] For sure, Jeremy, that sounds like just what I…
[05:35] kneaded.

### Code Sample: Build custom controls: Basics (initial attempt) - [5:36]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: AttributedString
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .preference(key: NewIngredientPreferenceKey.self, value: newIngredientSuggestion)
    }

    private var newIngredientSuggestion: IngredientSuggestion {
        let name = text[selection.indices(in: text)] // build error

        return IngredientSuggestion(
            suggestedName: AttributedString())
    }
}
```

[05:36] I’ve really been wanting to offer better controls
[05:39] connecting my text editor to the rest of my app.
[05:43] I want to build a button that allows me
[05:45] to add ingredients to the list in the inspector to the right,
[05:48] but without having to type out the name of the ingredient manually again.
[05:53] For example, I just want to be able to select the word “butter”
[05:56] that is already in my recipe,
[05:59] and mark it as an ingredient with a single press of a button.
[06:03] My inspector already defines a preference key
[06:06] that I can use in my editor to suggest a new ingredient for the list.
[06:14] The value I pass to the preference view modifier
[06:17] will bubble up the view hierarchy
[06:19] and can be read via the name “NewIngredientPreferenceKey”
[06:22] by any view that uses my recipe editor.
[06:26] Let me define a computed property for this value below my view body.
[06:34] All I need to provide for the suggestion is the name,
[06:37] as an AttributedString.
[06:40] Of course, I don’t just want to suggest the entire text that is in my editor.
[06:45] Instead, I want to suggest the text that is currently selected,
[06:49] like I showed with "butter."
[06:51] TextEditor communicates what is selected via the optional selection argument.
[07:02] Let me bind that to a local state of type AttributedTextSelection.
[07:09] Ok, now that I have all the context I need available in my view,
[07:13] let me head back to the property computing the ingredient suggestion.
[07:26] Now, I need to get the text that is selected.
[07:33] Let me try subscripting text with the result
[07:36] of this indices function on selection.
[07:43] Hmm, that doesn’t seem to be the right type.
[07:48] It returns AttributedTextSelection.Indices.
[07:53] Let me look that up.
[07:59] Oh, that’s interesting,
[08:01] I just have one selection, but the Indices type’s second case,
[08:05] is represented by a set of ranges.
[08:10] Jeremy can you explain why that is
[08:12] while while I get to folding my croissant dough?
[08:14] Ha, that’s funny.
[08:15] I’m also folding - under the anticipation of these tasty croissants.
[08:20] But no worries Max,
[08:21] I’ll explain why this API doesn’t use the Range type you expected.
[08:26] To explain why this API uses a RangeSet
[08:29] and not a single Range, I’ll dive into AttributedString selections.
[08:34] I’ll discuss how multiple ranges can form selections
[08:37] and demonstrate how to use RangeSets in your code.
[08:41] You’ve likely used a single range in AttributedString APIs
[08:44] or other collection APIs before.
[08:46] A single range allows you to slice a portion of an AttributedString
[08:50] and perform an action over that single chunk.

### Code Sample: Slicing AttributedString with a Range - [8:53]

```swift
var text = AttributedString(
  "Hello 👋🏻! Who's ready to get cooking?"
)

guard let cookingRange = text.range(of: "cooking") else {
  fatalError("Unable to find range of cooking")
}

text[cookingRange].foregroundColor = .orange
```

[08:53] For example, AttributedString provides APIs
[08:57] that allow you to quickly apply an attribute
[08:59] to a portion of text all at once.
[09:01] I’ve used the .range(of:) API to find the range of the text “cooking”
[09:05] in my AttributedString.
[09:07] Next I use the subscript operator to slice the AttributedString
[09:11] with that range to make the entire word “cooking” orange.
[09:16] However, an AttributedString sliced with just one range
[09:19] isn’t enough to represent selections in a text editor
[09:22] that works for all languages.
[09:24] For example, I might use this recipe app to store my recipe for Sufganiyot
[09:29] that I plan to cook during the holidays which includes some Hebrew text.
[09:34] My recipe says to, “Put the Sufganiyot in the pan,”
[09:37] which uses English text for the instructions
[09:39] and Hebrew text for the traditional name of the food.
[09:43] In the text editor, I’ll select a portion of the word “Sufganiyot”
[09:47] and the word “in” with just one selection.
[09:50] However, this is actually multiple ranges in the AttributedString!
[09:55] Since English is a left-to-right language, the editor lays out the sentence visually
[09:59] from the left side to the right side.
[10:02] However, the Hebrew portion, Sufganiyot, is laid out in the opposite direction
[10:06] since Hebrew is a right-to-left language.
[10:10] While the bidirectional nature of this text
[10:12] affects the visual layout on the screen,
[10:14] the AttributedString still stores all text in a consistent ordering.
[10:19] This ordering breaks apart my selection into two ranges:
[10:23] the start of the word “Sufganiyot”
[10:25] and the word “in,” excluding the end of the Hebrew text.
[10:29] This is why the SwiftUI text selection type uses multiple ranges
[10:33] rather than a single range.
[10:36] To learn more about localizing your app for bidirectional text,
[10:40] check out the Get it right (to left) session from WWDC 2022
[10:45] and this year’s Enhance your app’s multilingual experience session.

### Code Sample: Slicing AttributedString with a RangeSet - [10:50]

```swift
var text = AttributedString(
  "Hello 👋🏻! Who's ready to get cooking?"
)

let uppercaseRanges = text.characters
  .indices(where: \.isUppercase)

text[uppercaseRanges].foregroundColor = .blue
```

[10:50] To support these types of selections,
[10:53] AttributedString supports slicing with a RangeSet,
[10:55] the type Max noticed earlier in the selection API.
[10:59] Just like you can slice an AttributedString with a singular range,
[11:02] you can also slice it with a RangeSet to produce a discontiguous substring.
[11:07] In this case I’ve created a RangeSet using the .indices(where:) function
[11:11] on the character view to find all uppercase characters in my text.
[11:15] Setting the foreground color to blue on this slice
[11:18] will make all uppercase characters blue,
[11:20] leaving the other characters unmodified.
[11:23] SwiftUI also provides an equivalent subscript that slices an AttributedString
[11:27] with a selection directly.
[11:30] Hey Max, if you finished folding that beautiful croissant dough,
[11:33] I think using the subscript API
[11:35] that accepts a selection might resolve the build error in your code!
[11:38] Let me give that a try!

### Code Sample: Build custom controls: Basics (fixed) - [11:40]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: AttributedString
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .preference(key: NewIngredientPreferenceKey.self, value: newIngredientSuggestion)
    }

    private var newIngredientSuggestion: IngredientSuggestion {
        let name = text[selection]

        return IngredientSuggestion(
            suggestedName: AttributedString(name))
    }
}
```

[11:40] I can just subscript text with the selection directly,
[11:46] and then transform the discontiguous AttributedSubstring
[11:49] into a new AttributedString.
[11:52] That’s awesome!
[11:54] Now, when I run this on device, and select the word “butter,"
[11:58] SwiftUI automatically calls my property
[12:01] newIngredientSuggestion to compute the new value,
[12:04] which bubbles up to the rest of my app.
[12:07] My inspector then automatically adds the suggestion
[12:10] at the bottom of the ingredient list.
[12:13] From there, I can commit it to the ingredient list with a single tap!
[12:18] Features like that can elevate an editor, to a beautiful experience!
[12:24] I’m really happy with this addition,
[12:26] but with everything Jeremy has shown me so far, I think I can go even further!

### Code Sample: Build custom controls: Recipe attribute - [12:32]

```swift
import SwiftUI

struct IngredientAttribute: CodableAttributedStringKey {
    typealias Value = Ingredient.ID

    static let name = "SampleRecipeEditor.IngredientAttribute"
}

extension AttributeScopes {
    /// An attribute scope for custom attributes defined by this app.
    struct CustomAttributes: AttributeScope {
        /// An attribute for marking text as a reference to an recipe's ingredient.
        let ingredient: IngredientAttribute
    }
}

extension AttributeDynamicLookup {
    /// The subscript for pulling custom attributes into the dynamic attribute lookup.
    ///
    /// This makes them available throughout the code using the name they have in the
    /// `AttributeScopes.CustomAttributes` scope.
    subscript<T: AttributedStringKey>(
        dynamicMember keyPath: KeyPath<AttributeScopes.CustomAttributes, T>
    ) -> T {
        self[T.self]
    }
}
```

[12:32] I want to better visualize the ingredients in the text itself!
[12:37] The first thing I need for that is a custom attribute
[12:40] that marks a range of text as an ingredient.
[12:43] Let me define this in a new file.
[12:50] This attribute’s Value will be the ID of the ingredient it refers to.

### Code Sample: Build custom controls: Modifying text (initial attempt) - [12:56]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: AttributedString
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .preference(key: NewIngredientPreferenceKey.self, value: newIngredientSuggestion)
    }

    private var newIngredientSuggestion: IngredientSuggestion {
        let name = text[selection]

        return IngredientSuggestion(
            suggestedName: AttributedString(name),
            onApply: { ingredientId in
                let ranges = text.characters.ranges(of: name.characters)

                for range in ranges {
                    // modifying `text` without updating `selection` is invalid and resets the cursor 
                    text[range].ingredient = ingredientId
                }
            })
    }
}
```

[12:56] Now, I’ll head back to the property
[12:58] computing the IngredientSuggestion in the RecipeEditor file.
[13:03] IngredientSuggestion allows me to provide a closure as a second argument.
[13:11] This closure gets called when I press the plus button
[13:14] and the ingredient is added to the list.
[13:17] I will use that closure to mutate the editor text,
[13:20] marking up occurrences of the name with my Ingredient attribute.
[13:25] I get the ID of the newly created ingredient passed into the closure.
[13:36] Next, I need to find all the occurrences
[13:39] of the suggested ingredient name in my text.
[13:45] I can do this by calling ranges(of:) on AttributedString’s characters view.
[13:55] Now that I have the ranges,
[13:57] I can just update the value of my ingredient attribute for each range!
[14:07] Here, I’m using a short name
[14:09] for the IngredientAttribute I had already defined.
[14:17] Let’s give it a try!
[14:19] I don’t expect anything new here, after all,
[14:22] my custom attribute doesn’t have any formatting associated with it.
[14:27] Let me select “yeast” and press the plus button!
[14:33] Wait, what is that?!
[14:35] My cursor was at the top, not at the end!
[14:38] Let me try again!
[14:40] I select "salt,"
[14:44] press the plus button,
[14:46] and my selection jumps to the end!
[14:49] Jeremy, I have to roll out my croissant dough,
[14:51] so I can’t debug this right now…
[14:54] do you know why my selection is getting reset?
[14:56] That’s definitely not an experience we want for the cooks using your app!
[15:00] Why don’t you get started on rolling out the dough,
[15:02] and I’ll dive into this unexpected behavior.
[15:06] In order to demonstrate what’s happening here and how to fix it,
[15:10] I’ll explain the details of AttributedString indices
[15:13] which form the ranges and text selections used by a rich TextEditor.
[15:18] AttributedString.Index represents a single location within your text.
[15:24] To support its powerful and performant design,
[15:26] AttributedString stores its contents in a tree structure,
[15:30] and its indices store paths through that tree.
[15:33] Since these indices form the building blocks of text selections in SwiftUI,
[15:38] the unexpected selection behavior in the app
[15:41] stems from how AttributedString indices behave within these trees.
[15:46] You should keep two key points in mind when working with AttributedString indices.
[15:51] First, any mutation to an AttributedString invalidates all of its indices,
[15:56] even those not within the bounds of the mutation.
[16:00] Recipes never turn out well when you use expired ingredients,
[16:03] and I can assure you
[16:04] that you’ll feel the same way about using old indices with an AttributedString.
[16:09] Second, you should only use indices with the AttributedString
[16:13] from which they were created.
[16:16] Now I’ll explore indices from the example AttributedString I created earlier
[16:20] to explain how they work!
[16:23] Like I mentioned, AttributedString stores its contents in a tree structure,
[16:27] and here I have a simplified example of that tree.
[16:31] Using a tree allows for better performance and avoids copying lots of data
[16:35] when mutating your text.
[16:37] AttributedString.Index references text by storing a path through the tree
[16:42] to the referenced location.
[16:44] This stored path allows AttributedString
[16:47] to quickly locate specific text from an index,
[16:50] but it also means that the index contains information
[16:53] about the layout of the entire AttributedString’s tree.
[16:58] When you mutate an AttributedString, it might adjust the layout of the tree.
[17:03] This invalidates any previously recorded paths,
[17:06] even if the destination of that index still exists within the text.
[17:11] Additionally, even if two AttributedStrings have the same text
[17:16] and attribute content,
[17:17] their trees may have different layouts
[17:19] making their indices incompatible with each other.
[17:23] Using an index to traverse these trees to find information
[17:27] requires using the index within one of AttributedString’s views.
[17:31] While indices are specific to a particular AttributedString,
[17:35] you can use them in any view from that string.
[17:39] Foundation provides views over the characters, or grapheme clusters,

### Code Sample: AttributedString Character View - [17:40]

```swift
text.characters[index] // "👋🏻"
```

[17:43] of the text content,

### Code Sample: AttributedString Unicode Scalar View - [17:44]

```swift
text.unicodeScalars[index] // "👋"
```

[17:45] the individual Unicode scalars that make up each character,

### Code Sample: AttributedString Runs View - [17:49]

```swift
text.runs[index] // "Hello 👋🏻! ..."
```

[17:50] and the attribute runs of the string.
[17:53] To learn more about the differences
[17:55] between the character and Unicode scalar views,
[17:58] check out Apple’s developer documentation for the Swift Character type.
[18:03] You might also want to access lower level contents
[18:06] when interfacing with other string-like types
[18:08] that don’t use Swift’s Character type, such as NSString.

### Code Sample: AttributedString UTF-8 View - [18:13]

```swift
text.utf8[index] // "240"
```

[18:13] AttributedString now also provides views into both the UTF-8 scalars

### Code Sample: AttributedString UTF-16 View - [18:17]

```swift
text.utf16[index] // "55357"
```

[18:17] and the UTF-16 scalars of the text.
[18:21] These two views still share the same indices as all of the existing views.
[18:27] Now that I’ve discussed the details of indices and selections,
[18:31] I’ll revisit the problem that Max encountered with the recipe app.
[18:35] The onApply closure in the IngredientSuggestion
[18:38] mutates the attributed string,
[18:40] but it doesn’t update the indices in the selection!
[18:44] SwiftUI detects that these indices are no longer valid
[18:47] and moves the selection to the end of the text
[18:49] to prevent the app from crashing.
[18:52] To fix this, use AttributedString APIs to update your indices
[18:56] and selections when mutating text.

### Code Sample: Updating Indices during AttributedString Mutations - [18:59]

```swift
var text = AttributedString(
  "Hello 👋🏻! Who's ready to get cooking?"
)

guard var cookingRange = text.range(of: "cooking") else {
  fatalError("Unable to find range of cooking")
}

let originalRange = cookingRange
text.transform(updating: &cookingRange) { text in
  text[originalRange].foregroundColor = .orange
  
  let insertionPoint = text
    .index(text.startIndex, offsetByCharacters: 6)
  
  text.characters
    .insert(contentsOf: "chef ", at: insertionPoint)
}

print(text[cookingRange])
```

[19:00] Here, I have a simplified example of code
[19:02] that has the same problem as the recipe app.
[19:05] First, I find the range of the word "cooking" in my text.
[19:10] Then, I set the range of “cooking” to an orange foreground color
[19:14] and I also insert the word “chef” into my string
[19:17] to add some more recipe theming.
[19:20] Mutating my text can change the layout of my AttributedString’s tree.
[19:25] Using the cookingRange variable after I’ve mutated my string is not valid.
[19:30] It might even crash the app.
[19:33] Instead, AttributedString provides a transform function
[19:36] which takes a Range, or an array of Ranges,
[19:39] and a closure which mutates the provided AttributedString in-place.
[19:44] At the end of the closure,
[19:45] the transform function will update your provided range
[19:48] with new indices to ensure you can correctly use the range
[19:51] in the resulting AttributedString.
[19:54] While the text may have shifted in the AttributedString,
[19:57] the range still points
[19:58] to the same semantic location - in this case, the word “cooking.”
[20:03] SwiftUI also provides an equivalent function
[20:06] that updates a selection instead of a range.
[20:10] Wow, Max, those croissants are really shaping up great!
[20:14] If you’re ready to get back to your app,
[20:16] I think using this new transform function will help get your code into shape too!
[20:20] Thank you!
[20:21] That sounds like just what I was looking for!

### Code Sample: Build custom controls: Modifying text (fixed) - [20:22]

```swift
import SwiftUI

struct RecipeEditor: View {
    @Binding var text: AttributedString
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .preference(key: NewIngredientPreferenceKey.self, value: newIngredientSuggestion)
    }

    private var newIngredientSuggestion: IngredientSuggestion {
        let name = text[selection]

        return IngredientSuggestion(
            suggestedName: AttributedString(name),
            onApply: { ingredientId in
                let ranges = RangeSet(text.characters.ranges(of: name.characters))

                text.transform(updating: &selection) { text in
                    text[ranges].ingredient = ingredientId
                }
            })
    }
}
```

[20:23] Let me see if I can apply this in code.
[20:27] First, I shouldn’t loop over the ranges like that.
[20:30] By the time I reach the last range,
[20:32] the text has been mutated many times, and the indices are outdated.
[20:36] I can avoid that problem entirely by first converting my Ranges to a RangeSet.
[20:48] Then I can just slice with that and remove the loop.
[20:58] This way everything is one change,
[21:00] and I don’t need to update the remaining ranges after each mutation.
[21:06] Second, next to the ranges I want to change, there is also the selection
[21:11] representing my cursor position.
[21:13] I need to always make sure it matches the transformed text.
[21:18] I can do that using SwiftUI’s
[21:20] transform(updating:) overload
[21:22] on AttributedString.
[21:37] Nice, now my selection is updated right as the text gets mutated!
[21:43] Let’s see if that worked!
[21:45] I can select “milk,” it appears in the list,
[21:49] and - when I add it - my selection remains intact!
[21:53] To double-check, when I press Command+B on the keyboard now,
[21:57] I can see the word “milk” turning bold - just as expected!

### Code Sample: Define your text format: RecipeFormattingDefinition Scope - [22:03]

```swift
struct RecipeFormattingDefinition: AttributedTextFormattingDefinition {
    struct Scope: AttributeScope {
        let foregroundColor: AttributeScopes.SwiftUIAttributes.ForegroundColorAttribute
        let adaptiveImageGlyph: AttributeScopes.SwiftUIAttributes.AdaptiveImageGlyphAttribute
        let ingredient: IngredientAttribute
    }

    var body: some AttributedTextFormattingDefinition<Scope> {

    }
}

// pass the custom formatting definition to the TextEditor in the updated `RecipeEditor.body`:

        TextEditor(text: $text, selection: $selection)
            .preference(key: NewIngredientPreferenceKey.self, value: newIngredientSuggestion)
            .attributedTextFormattingDefinition(RecipeFormattingDefinition())
```

[22:03] Now that I have all the information in my recipe text,
[22:06] I want to emphasize the ingredients with some color!
[22:10] Thankfully, TextEditor provides a tool for that:
[22:14] the attributed text formatting definition protocol.
[22:17] A custom text formatting definition is all structured around
[22:21] which AttributedStringKeys your text editor responds to,
[22:25] and what values they might have.
[22:28] I already declared a type conforming
[22:30] to the AttributedTextFormattingDefinition protocol here.
[22:34] By default, the system uses the SwiftUIAttributes scope,
[22:38] with no constraints on the attributes’ values.
[22:43] In the scope for my recipe editor,
[22:49] I only want to allow foreground color, Genmoji,
[22:54] and my custom ingredient attribute.
[22:57] Back on my recipe editor,
[23:00] I can use the attributedTextFormattingDefinition modifier
[23:04] to pass my custom definition to SwiftUI’s TextEditor.
[23:13] With this change, my TextEditor will allow any ingredient, any Genmoji,
[23:18] and any foreground color.
[23:21] All of the other attributes now will assume their default value.
[23:25] Note that you can still change the default value for the entire editor
[23:29] by modifying the environment.
[23:32] Based on this change,
[23:33] TextEditor has already made some important changes
[23:37] to the system formatting UI.
[23:39] It no longer offers controls for changing the alignment,
[23:43] the line height, or font properties,
[23:45] since the respective AttributedStringKeys are not in my scope.

### Code Sample: Define your text format: AttributedTextValueConstraints - [23:50]

```swift
struct IngredientsAreGreen: AttributedTextValueConstraint {
    typealias Scope = RecipeFormattingDefinition.Scope
    typealias AttributeKey = AttributeScopes.SwiftUIAttributes.ForegroundColorAttribute

    func constrain(_ container: inout Attributes) {
        if container.ingredient != nil {
            container.foregroundColor = .green
        } else {
            container.foregroundColor = nil
        }
    }
}

// list the value constraint in the recipe formatting definition's body:
    var body: some AttributedTextFormattingDefinition<Scope> {
        IngredientsAreGreen()
    }
```

[23:50] However, I can still use the color control to apply arbitrary colors to my text,
[23:55] even if those colors don’t necessarily make sense.
[24:02] Oh no, the milk is gone!
[24:06] I really only want ingredients to be highlighted green,
[24:10] and everything else to use the default color.
[24:12] I can use SwiftUI’s AttributedTextValueConstraint protocol
[24:17] to implement this logic.
[24:20] Let me head back to the RecipeFormattingDefinition file
[24:23] and declare the constraint.
[24:34] To conform to the AttributedTextValueConstraint protocol,
[24:37] I first specify the scope of the AttributedTextFormattingDefinition
[24:42] it belongs to,
[24:43] and then the AttributedStringKey I want to constrain,
[24:47] in my case the foreground color attribute.
[24:50] The actual logic for constraining the attribute
[24:53] lives in the constrain function.
[24:56] In that function, I set the value of the AttributeKey - the foreground color -
[25:01] to what I consider valid.
[25:04] In my case, the logic all depends on whether the ingredient attribute is set.
[25:15] If so, the foreground color should be green,
[25:23] otherwise it should be nil
[25:30] This indicates TextEditor should substitute the default color.
[25:35] Now that I have defined the constraint,
[25:38] I just need to add it to the body of the AttributedTextFormattingDefinition.
[25:48] From here, SwiftUI takes care of all the rest.
[25:52] TextEditor automatically applies the definition and its constraints
[25:56] to any part of the text before it appears on screen.
[26:01] All the ingredients are green now!
[26:05] Interestingly, TextEditor has disabled its color control,
[26:10] despite foreground color being in my formatting definition’s scope.
[26:14] This makes sense considering the IngredientsAreGreen constraint I added.
[26:19] The foreground color now solely depends
[26:22] on whether text is marked with the ingredient attribute.
[26:25] TextEditor automatically probes AttributedTextValueConstraints
[26:29] to determine if a potential change is valid for the current selection.
[26:33] For example, I could try to set the foreground color of “milk” to white again.
[26:38] Running my IngredientsAreGreen constraint afterwards
[26:41] would change the foreground color back to green,
[26:43] so TextEditor knows this is not a valid change and disables the control.
[26:49] My value constraint will also be applied to text I paste into my editor.
[26:54] When I copy an ingredient using Command+C and paste it again using Command+V,
[27:01] my custom ingredient attribute is preserved.
[27:03] With CodableAttributedStringKeys, this can even work across TextEditors
[27:08] in different apps
[27:09] as long as both apps list the attribute
[27:12] in their AttributedTextFormattingDefinition.
[27:16] This is pretty great,
[27:17] but there are still some things to improve:
[27:20] with my cursor at the end of the ingredient "milk,"
[27:23] I can delete characters or continue typing and it just behaves like regular text.
[27:29] This makes it feel like it is just green text,
[27:32] and not an ingredient with a certain name.
[27:36] To make this feel right,
[27:37] I want the ingredient attribute not to expand as I type at the end of its run.
[27:43] And I would like the foreground color to reset
[27:46] for the entire word at once if I modify it.
[27:50] Jeremy, if I promise I’ll give you an extra croissant later,
[27:54] will you help me getting that implemented?
[27:56] Hmm… I’m not sure one's gonna be enough,
[27:59] but make it a few and you’ve got a deal, Max!
[28:02] While you go get those croissants in the oven,
[28:03] I’ll explain what APIs might help with this problem.
[28:07] With the formatting definition constraints that Max demonstrated,
[28:11] you can constrain which attributes
[28:13] and which specific values each text editor can display.
[28:16] To help with this new issue with the recipe editor,
[28:19] the AttributedStringKey protocol provides additional APIs
[28:23] to constrain how attribute values are mutated
[28:25] across changes to any AttributedString.
[28:29] When attributes declare constraints,
[28:31] AttributedString always keeps the attributes consistent with each other
[28:35] and the text content to avoid unexpected state
[28:38] with simpler and more performant code.
[28:41] I’ll dive into a few examples to explain
[28:43] when you might use these APIs for your attributes.
[28:47] First, I’ll discuss attributes
[28:48] whose values are coupled with other content in the AttributedString,
[28:52] such as a spell checking attribute.
[28:55] Here, I have a spell checking attribute that indicates the word “ready”
[28:59] is misspelled via a dashed, red underline.
[29:02] After performing spell checking on my text,
[29:05] I need to make sure that the spell checking attribute
[29:07] remains only applied to the text that I have already validated.
[29:12] However, if I continue typing in my text editor,
[29:14] by default all attributes of the existing text
[29:18] are inherited by inserted text.
[29:20] This isn’t what I want for a spell checking attribute,
[29:23] so I’ll add a new property to my AttributedStringKey to correct this.

### Code Sample: AttributedStringKey Constraint: Inherited by Added Text - [29:28]

```swift
static let inheritedByAddedText = false
```

[29:28] By declaring an inheritedByAddedText property on my AttributedStringKey type
[29:33] with a value of "false," any added text will not inherit this attribute value.
[29:39] Now, when adding new text to my string,
[29:42] the new text will not contain the spell checking attribute
[29:45] since I have not yet checked the spelling of those words.
[29:49] Unfortunately, I found another issue with this attribute.
[29:52] Now, when I add text to the middle of a word that was marked as misspelled,
[29:57] the attribute shows an awkward break
[29:59] in the red line underneath the added text.
[30:02] Since my app hasn’t checked if this word is misspelled yet,
[30:05] what I really want is for the attribute to be removed from this word
[30:08] to avoid stale information in my UI.

### Code Sample: AttributedStringKey Constraint: Invalidation Conditions - [30:12]

```swift
static let invalidationConditions:
  Set<AttributedString.AttributeInvalidationCondition>? =
  [.textChanged]
```

[30:12] To fix this problem, I’ll add another property to my AttributedStringKey type:
[30:17] the invalidationConditions property.
[30:20] This property declares situations when a run of this attribute
[30:24] should be removed from the text.
[30:26] AttributedString provides conditions for when the text changes
[30:30] and when specific attributes change,
[30:32] and attribute keys can invalidate upon any number of conditions.
[30:36] In this case, I need to remove this attribute
[30:39] whenever the text of the attribute run changes
[30:42] so I’ll use the “textChanged” value.
[30:45] Now, inserting text into the middle of an attribute run
[30:49] will invalidate the attribute across the entire run,
[30:52] ensuring that I avoid this inconsistent state in my UI.
[30:57] I think both of those APIs
[30:59] might help keep the ingredient attribute valid in Max’s app!
[31:02] While Max is finishing up with the oven,
[31:04] I’ll demonstrate one more category of attributes:
[31:07] attributes that require consistent values across sections of text.
[31:11] For example, a paragraph alignment attribute.
[31:15] I can apply different alignments to each paragraph in my text,
[31:19] however just a single word cannot use a different alignment
[31:23] than the rest of the paragraph.

### Code Sample: AttributedStringKey Constraint: Run Boundaries - [31:25]

```swift
static let runBoundaries:
  AttributedString.AttributeRunBoundaries? =
  .paragraph
```

[31:25] To enforce this requirement during AttributedString mutations,
[31:29] I’ll declare a runBoundaries property on my AttributedStringKey type.
[31:33] Foundation supports limiting run boundaries to paragraph edges or the edges
[31:37] of a specified character.
[31:39] In this case, I’ll define this attribute as constrained to paragraph boundaries
[31:44] to require that it has a consistent value from the start to the end of a paragraph.
[31:50] Now, this situation becomes impossible.
[31:53] If I apply a left alignment value to just one word in a paragraph,
[31:57] AttributedString automatically expands the attribute to the entire range
[32:02] of the paragraph.
[32:03] Additionally, when I enumerate the alignment attribute
[32:07] AttributedString enumerates each individual paragraph,
[32:10] even if two consecutive paragraphs contain the same attribute value.
[32:14] Other run boundaries behave the same:
[32:17] AttributedString expands values from one boundary to the next
[32:20] and ensures enumerated runs break on every run boundary.
[32:26] Wow Max, those croissants smell delicious!
[32:29] If the croissasnts are all set in the oven,
[32:31] do you think some of these APIs might complement your formatting definition
[32:35] to achieve the behavior you want for your custom attribute?
[32:37] That sounds like just the secret ingredient I needed!
[32:41] The croissants are all set in the oven, so I can try this out right away!
[32:45] In my custom IngredientAttribute here,

### Code Sample: Define your text format: AttributedStringKey Constraints - [32:46]

```swift
struct IngredientAttribute: CodableAttributedStringKey {
    typealias Value = Ingredient.ID

    static let name = "SampleRecipeEditor.IngredientAttribute"

    static let inheritedByAddedText: Bool = false

    static let invalidationConditions: Set<AttributedString.AttributeInvalidationCondition>? = [.textChanged]
}
```

[32:48] I will implement the optional inheritedByAddedText requirement
[32:52] to have the value false,
[32:54] that way if I type after an ingredient, it won’t expand.
[33:02] Second, let me implement invalidationConditions with textChanged,
[33:08] so when I delete characters in an ingredient
[33:10] it will no longer be recognized!
[33:17] Let’s give it a try!
[33:19] When I add a “y” at the end of “milk,” the “y” is no longer green,
[33:24] and when I delete a character of “milk,”
[33:27] the ingredient attribute gets removed from the entire word at once.
[33:32] Based on my AttributedTextFormattingDefinition,
[33:35] the foreground color attribute continues
[33:37] to follow my custom ingredient attribute’s behavior perfectly!
[33:42] Thank you Jeremy, this app really turned out great!
[33:45] No problem!
[33:46] Now, about those croissants you promised…
[33:49] Don’t worry, they’re almost ready.
[33:51] Why don’t you guard the oven though,
[33:53] since I’m slightly worried Luca might steal them away from us!
[33:56] Ah, THE Luca, I’ve heard of him,
[33:59] lover of all things widgets and croissants.
[34:02] I’m on it chef!
[34:04] Now, before I go join Jeremy,
[34:06] let me give you some final tips:
[34:09] You can download my app as a sample project
[34:11] where you can learn more about using SwiftUI’s
[34:14] Transferable Wrapper for lossless drag and drop or export to RTFD,
[34:18] and persisting AttributedString with Swift Data.
[34:22] AttributedString is part of Swift’s open source Foundation project.
[34:26] Find its implementation on GitHub to contribute to its evolution
[34:30] or get in touch with the community on the Swift forums!
[34:34] With the new TextEditor, it has also never been easier
[34:37] to add support for Genmoji input into your app,
[34:40] so consider doing that now!
[34:42] I just can’t wait to see how you will use this API
[34:46] to upgrade text editing in your apps.
[34:49] Just a little sprinkle can make it pop!
[34:56] Mmm, so delicious!
[34:58] No, so RICH!