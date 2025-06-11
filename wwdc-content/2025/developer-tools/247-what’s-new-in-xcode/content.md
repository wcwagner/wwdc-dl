# What’s new in Xcode

**Session 247** - WWDC 2025

## Description
Discover the latest productivity and performance advancements in Xcode 26. Learn how to leverage large language models in your...

## Transcript

[00:06] 
Hi, I’m Eliza. I work on Swift Previews.

[00:09] 
And I’m Chris.

[00:10] 
I work on Xcode.

[00:12] 
Developing great apps takes a lot of work, whether it’s writing code,

[00:15] 
exploring and prototyping new features,

[00:17] 
debugging, improving performance and more.

[00:19] 
We’re excited to share with you some of the awesome improvements

[00:22] 
in Xcode this year to help support you in your app development.

[00:25] 
We’ll start with some optimizations to Xcode’s download size and performance.

[00:30] 
Then, we’ll explore improvements in the workspace and source editor,

[00:35] 
and try out some exciting new code intelligence features.

[00:39] 
Chris will then talk through some new features in debugging & performance,

[00:44] 
What’s new in builds, and wrap up with some updates in testing.

[00:49] 
Let’s get started with optimizations!

[00:52] 
Over the last few years we’ve been working to make Xcode smaller

[00:56] 
so you can get your tools even faster

[00:58] 
and download only the components that you need.

[01:01] 
This year, Xcode is 24% smaller.

[01:04] 
Simulator runtimes no longer contain Intel support by default,

[01:08] 
and the Metal toolchain will only be downloaded if your project needs it.

[01:13] 
Altogether, this year’s Xcode has a smaller download size

[01:17] 
than Xcode 6 did in 2014!

[01:20] 
We’ve also optimized text input in Xcode this year,

[01:24] 
improving typing latency in some complex expressions by up to 50%.

[01:30] 
We’ve also made some substantial optimizations

[01:33] 
to Xcode’s loading performance.

[01:35] 
It’s now 40% faster to load a workspace.

[01:38] 
For large projects, this makes a big difference.

[01:41] 
Which leads us to updates in the workspace and editing.

[01:45] 
There are tons of enhancements to the source editor in Xcode this year.

[01:50] 
Let’s start with editor tabs.

[01:52] 
This year’s Xcode improves the behavior of editor tabs

[01:55] 
to make them a lot more intuitive.

[01:58] 
Just like in Safari, I can open a tab and decide where to go from there,

[02:03] 
using this new start page.

[02:06] 
And I can pin a tab to fix it on a particular file.

[02:09] 
This puts me in control of exactly how many tabs I have.

[02:13] 
Whether that's just one, one for every file, or a perfectly curated set.

[02:18] 
Now, let’s talk about search.

[02:21] 
When exploring an unfamiliar project, or even navigating a familiar one,

[02:25] 
it’s crucial to be able to search your code effectively.

[02:29] 
This year, Xcode has a really cool new search mode called “Multiple Words search”

[02:34] 
which uses search engine techniques to find clusters of words in your project.

[02:39] 
In this search mode, I can enter a set of words.

[02:43] 
For example, here, I’m trying to find where in my project I’m creating

[02:48] 
clipped resizable images.

[02:51] 
Xcode will now find all the clusters of these words in proximity to each other

[02:56] 
across your documents, sorting the documents by relevance.

[03:01] 
The clusters can span multiple lines and the search terms can appear in any order,

[03:06] 
making this a really powerful feature!

[03:10] 
There’s a big step forward this year for accessibility in Xcode.

[03:14] 
You can now easily use Voice Control to write Swift code, and you can pronounce

[03:19] 
the Swift code just as you’d naturally read it aloud.

[03:22] 
In this mode, Voice Control understands Swift syntax.

[03:26] 
It will figure out where spaces should appear,

[03:28] 
whether expressions correspond to operators

[03:31] 
or should be camel-cased, and so on.

[03:34] 
To fully appreciate how cool this is, it’s best to see it in action.

[03:38] 
With Swift Mode for Voice Control,

[03:40] 
I can navigate and edit my Swift code just by speaking to my Mac.

[03:45] 
Let’s use this to add a field to our landmark inspector

[03:48] 
for the landmark’s continent.

[03:51] 
“Start listening”

[03:54] 
“Swift mode”

[03:57] 
“Select labeled content”

[04:01] 
“Four”

[04:04] 
“Go to the end of the line”

[04:07] 
“New line, new line”

[04:10] 
“If let continent equals landmark dot continent"

[04:15] 
"Open brace"

[04:17] 
“New line”

[04:19] 
“Labeled content paren quote continent quote

[04:24] 
comma value colon continent”

[04:29] 
“Correct quote continent”

[04:33] 
“One”

[04:38] 
“Stop listening”

[04:40] 
Notice that the continent field now appears near the bottom of my preview,

[04:44] 
and I didn’t touch my keyboard once!

[04:47] 
Now, let’s talk about iterating on code.

[04:50] 
Using Previews has always been a great way to quickly iterate on your UI code.

[04:55] 
This year, we’re introducing a new macro called Playground

[04:57] 
which you can use to quickly iterate on any code.

[05:01] 
As with previews, you can add a playground inline in your document,

[05:05] 
and the results of the code execution will appear in their own canvas tab.

[05:10] 
Let me show you a demo.

[05:12] 
I’ve noticed a bug in the Landmarks app where landmarks

[05:15] 
are showing up in the wrong place on the map.

[05:17] 
I’m going to use a playground to poke around at the landmark struct

[05:22] 
and see if I can figure out what’s going on.

[05:28] 
Importing the Playgrounds module gives me access to the playground macro.

[05:34] 
Let’s load a sample landmark so we can examine its data.

[05:41] 
In the canvas, I see an entry for each expression in my playground.

[05:45] 
I just have one, which is the landmark structure for the Grand Canyon,

[05:49] 
and I can see the values for each of its properties.

[05:52] 
Some of the property types have a Quick Look icon.

[05:56] 
Let’s look more closely at the coordinate property.

[06:00] 
Okay, that seems odd...

[06:01] 
the Grand Canyon shouldn’t be inside a city.

[06:04] 
I can add another expression to my playground to get more information

[06:08] 
about the region for this landmark.

[06:11] 
As I modify the playground,

[06:13] 
expressions in it are re-run, and the canvas updates automatically.

[06:18] 
Yeah… the Grand Canyon is definitely not in China.

[06:21] 
Let’s figure out what’s going on here.

[06:24] 
When we load landmarks from a file, we use a regular expression

[06:28] 
to parse the location coordinates from a string.

[06:31] 
This is the regular expression we’re using.

[06:34] 
Maybe there’s a problem with it that’s causing

[06:37] 
our coordinates to be parsed incorrectly?

[06:39] 
Let’s investigate that in another playground.

[06:42] 
When I add a new playground I get a new tab in the canvas.

[06:48] 
Let's add some code to this playground.

[06:52] 
We’re going to call the function where that regular expression is defined.

[06:57] 
I’m using a sample input string, and extracting some computed results

[07:01] 
into local variables so they're easier to examine.

[07:04] 
Some types, such as regular expression match results,

[07:07] 
have custom visualizations in the canvas,

[07:10] 
and in this case, I can see that Xcode

[07:13] 
highlights the match range in the original string.

[07:16] 
The match range makes it clear that there was a problem capturing the minus sign.

[07:22] 
And now the bug makes sense,

[07:23] 
as the negative longitude would have been parsed as a positive number,

[07:27] 
putting the Grand Canyon in the wrong place.

[07:31] 
I’m going to fix the expression, and

[07:33] 
if you watch the playground in the canvas while I do this,

[07:36] 
you’ll see that the results update immediately.

[07:39] 
I can see in the visualization that the minus sign

[07:41] 
is now included in the range matched by the regular expression.

[07:46] 
And if I switch back to the original playground,

[07:49] 
I see that the Grand Canyon is now in the right place!

[07:53] 
And that’s Playgrounds.

[07:54] 
They’re great for understanding existing code as well as for trying out new ideas.

[08:00] 
And the new #Playground macro is also being open-sourced to bring the experience

[08:05] 
to Swift developers writing for other platforms.

[08:08] 
Check out the post on Swift Forums and join in on the conversation!

[08:12] 
Now, let’s talk about icons.

[08:15] 
Icon Composer is a new app bundled with Xcode 26.

[08:20] 
With Icon Composer, you can create beautifully designed, sophisticated,

[08:24] 
multi-layered icons that work across multiple platforms and software versions.

[08:30] 
Over the last few years, we’ve made it easier to create icons for all platforms.

[08:35] 
But this year, icons don’t only differ

[08:37] 
depending on the platform you’re building for.

[08:39] 
They now vary in modes, including dark and tinted modes

[08:43] 
on iOS, iPadOS, and macOS.

[08:46] 
And there’s a new look for watchOS as well.

[08:49] 
Now, all of this can be achieved in one single file using Icon Composer.

[08:55] 
You can take advantage of the full range of our material effects

[08:59] 
and even add dynamic properties to your layers,

[09:02] 
like blur, shadow, specular highlights, and translucency.

[09:07] 
Not only that, the tool is great for creating flat icons

[09:11] 
that are compatible with previous operating systems,

[09:13] 
web pages, or anywhere else you need them.

[09:17] 
To learn more about app icons, and how to use Icon Composer,

[09:21] 
check out “Say hello to the new look of app icons”

[09:24] 
and “Create app icons with Icon Composer.”

[09:28] 
Bringing your app to more users around the globe is incredibly valuable.

[09:32] 
Supporting different languages helps people feel at home in your app.

[09:36] 
And with string catalogs, localization can be a breeze.

[09:40] 
String Catalogs have gotten some big enhancements this year,

[09:43] 
to make life easier for both developers and translators.

[09:48] 
For developers, we’ve added type-safe Swift symbols for localized strings.

[09:54] 
Developers wanting more precise control over strings can define them directly

[09:59] 
in the String Catalog, which now produces Swift symbols

[10:03] 
that can be accessed in code.

[10:05] 
These symbols even appear as auto-complete suggestions!

[10:09] 
And to assist translators, String Catalogs can now automatically generate comments

[10:15] 
that describe string context.

[10:18] 
Xcode accomplishes this by intelligently analyzing where and how

[10:22] 
a localized string is used in your project.

[10:26] 
It then generates comments using the on-device model.

[10:31] 
For more on string catalogs,

[10:33] 
please have a look at the code-along session “Explore localization with Xcode”.

[10:38] 
Which brings us to intelligence.

[10:40] 
Xcode is getting some additional exciting new intelligence features.

[10:44] 
Xcode can now use large language models such as ChatGPT

[10:48] 
to provide coding assistance.

[10:50] 
You can ask general questions about Swift — like

[10:53] 
“tell me about swift concurrency”.

[10:56] 
And because of the integration with Xcode,

[10:58] 
the model can take your code into consideration

[11:01] 
and answer specific questions about your project,

[11:04] 
or even make changes on your behalf.

[11:07] 
In addition, we’re introducing a handy lighter-weight menu

[11:11] 
that you can use to automatically apply changes to selected code.

[11:16] 
When you bring up coding tools, you have quick access to common actions,

[11:20] 
or you can type a custom query into the text field.

[11:23] 
Let’s look at these features in more detail.

[11:26] 
This app has a view that shows my favorite landmark collections,

[11:29] 
but I’m not familiar with the code,

[11:31] 
and I don’t know where that’s implemented.

[11:33] 
So I’m going to ask Xcode.

[11:36] 
Xcode sends the project context to the model,

[11:39] 
and it replies with an explanation

[11:41] 
that describes the relevant source files and what they do.

[11:45] 
The model can also ask for more information from Xcode

[11:48] 
about additional context it needs while it’s coming up with an answer.

[11:53] 
The “info” button in the transcript shows us the context that Xcode sent.

[12:00] 
The response also contains links

[12:02] 
so you can quickly navigate to any mentioned file.

[12:06] 
This looks like the right one.

[12:08] 
This is a great way to explore an unfamiliar code base.

[12:13] 
Now, let’s add a feature!

[12:15] 
Let’s ask Xcode to add ratings to landmark collections.

[12:20] 
Here, I’m using the `@` character

[12:23] 
to directly reference a symbol we want the model to modify.

[12:28] 
Typing the ‘@‘ symbol into my prompt lets me reference symbols, source files,

[12:33] 
or any issues in my project that I want the response to focus on.

[12:37] 
This can be useful when you have specific changes in mind.

[12:40] 
I can even attach files for the query to reference.

[12:44] 
Images are especially useful,

[12:45] 
since many large language models can generate code

[12:48] 
from just a sketch of a user interface.

[12:51] 
The automatic context and code changes do the right thing out of the box,

[12:56] 
but if you can also have more control if you want to.

[13:00] 
This toggle controls whether Xcode includes information

[13:03] 
about your project with the query.

[13:06] 
If you were asking a general question about Swift, for example,

[13:09] 
you might choose to turn off project context.

[13:12] 
But most of the time you’d want to leave it on.

[13:15] 
This toggle lets you control

[13:17] 
whether to automatically apply any code changes in the response.

[13:21] 
If it’s off, you can review each change before deciding whether to apply it.

[13:26] 
Okay, it looks like the response is complete

[13:28] 
and all the changes have been made to my project.

[13:31] 
I can click to see a summary of the changes

[13:33] 
that were made — these look good.

[13:36] 
I can type a new message to continue the conversation.

[13:39] 
Let’s ask the model to add that rating to the user interface.

[13:47] 
The model can figure out what ‘it’ refers to here,

[13:50] 
because new messages preserve the context of earlier queries and replies.

[14:00] 
This change looks pretty good!

[14:03] 
I can continue making changes in the context of the previous ones.

[14:08] 
Let’s have a bit of fun and make it go to eleven.

[14:16] 
Once again, the model knows what I mean by “it” here.

[14:22] 
Ta-da!

[14:23] 
Now we have 11 stars!

[14:25] 
By default, changes are applied automatically to your code.

[14:29] 
But Xcode keeps a snapshot of your code before each change is applied,

[14:33] 
so you can easily view and unwind them using the modification history

[14:37] 
in the conversation view.

[14:39] 
Here I can examine every line of code

[14:42] 
changed during each stage of the conversation.

[14:46] 
I can scrub back and forth through time to apply

[14:49] 
or revert individual sets of changes.

[14:52] 
In this case, I’m happy with all the changes

[14:55] 
so I’ll cancel out of the modification history.

[15:00] 
So far, I’ve been using the code assistant to make changes

[15:03] 
that affect multiple files in my project.

[15:06] 
When I want to focus on a particular section of code,

[15:09] 
I can also use coding tools right from my source editor.

[15:14] 
Let’s use coding tools to add a playground that will exercise our Landmark struct.

[15:19] 
Coding tools has buttons for quick actions to apply to my code,

[15:23] 
or I can enter a custom query.

[15:26] 
In this case, let’s select the action to generate a playground.

[15:30] 
Because the model has access to the context —

[15:32] 
for newly generated code as well as for existing code —

[15:35] 
it can create playgrounds that exercise the code in interesting ways.

[15:40] 
Now we have a playground that lets me inspect a sample landmark!

[15:44] 
In addition to explaining or modifying code,

[15:47] 
Xcode is great at helping me fix issues in my code.

[15:51] 
For example, here I have an error where I’m trying to use a `ForEach` view

[15:55] 
with a type that doesn’t conform to `Identifiable`.

[15:58] 
There’s a new option this year to generate a fix —

[16:02] 
this will bring up the coding assistant.

[16:06] 
Because the model has access to the type declaration

[16:09] 
as well as the place where the error is detected,

[16:12] 
it can figure out which file needs to be modified to fix the error.

[16:16] 
In this case, the fix was to add a protocol conformance in activity.swift.

[16:23] 
And now the error is resolved.

[16:25] 
Xcode is also great at fixing other issues.

[16:29] 
For example, I find I sometimes let deprecation warnings linger in code

[16:33] 
because they’re not causing immediate problems.

[16:35] 
Now I can save time by asking Xcode to fix them for me!

[16:39] 
There are many ways to add a model in Xcode.

[16:42] 
First, you can enable ChatGPT with just a few clicks.

[16:46] 
You’ll get a limited number of requests each day,

[16:49] 
and you can bring your own ChatGPT account for even more requests.

[16:54] 
If you’d like to use another provider, like Anthropic,

[16:57] 
you can simply enter your API key

[16:59] 
and interact with models like Claude 4 Opus and Sonnet.

[17:04] 
You can choose which models to show from each provider,

[17:07] 
and can mark your favorites for quick access.

[17:11] 
And you can also use local models,

[17:13] 
running on your Mac or private network, thanks to tools like Ollama and LM Studio!

[17:20] 
You can add as many providers as you want in Xcode’s preferences.

[17:25] 
Once you’ve configured a set of models,

[17:27] 
you can quickly switch between them

[17:29] 
in the coding assistant when beginning a new conversation.

[17:33] 
So that’s a look through some of the new features

[17:35] 
in Xcode’s workspace and source editor,

[17:38] 
and how you can use code intelligence to get more creative and productive.

[17:42] 
Now, I’ll hand it over to Chris, to tell us about debugging and performance.

[17:46] 
Thanks, Eliza!

[17:48] 
Catching bugs and improving your app's performance are crucial steps

[17:51] 
to providing a great app experience.

[17:53] 
This year, we have a few exciting updates,

[17:56] 
starting with the debugger.

[17:58] 
Debugging Swift concurrency code has gained

[18:00] 
some great livability improvements in this year’s Xcode.

[18:04] 
As you step through code running in a Swift task,

[18:06] 
Xcode now follows execution into asynchronous functions,

[18:09] 
even if that requires switching threads.

[18:12] 
And Xcode’s debugger UI will now show task IDs.

[18:15] 
Here, for example, the current Swift Task

[18:17] 
is displayed in the backtrace view on the left

[18:20] 
and in the Program Counter annotation on the right.

[18:23] 
And in the variables view you’ll see easy-to-read

[18:25] 
representations of concurrency types,

[18:27] 
such as Tasks, TaskGroups, and actors.

[18:31] 
In this example, it’s much easier to see the Task variable’s properties,

[18:34] 
such as its priority and any child tasks.

[18:38] 
Xcode 26 makes debugging Swift concurrency code easier than ever.

[18:43] 
For more information on Swift concurrency see “What’s New in Swift”.

[18:48] 
If you’ve ever added functionality to your app

[18:50] 
that requires accessing a private resource,

[18:53] 
like the user’s location or the camera,

[18:55] 
you may have experienced your app stopping abruptly in the debugger,

[18:59] 
with an error about a missing “usage description”.

[19:02] 
“Usage descriptions” are required when accessing private resources,

[19:05] 
so the system can include them in an authorization prompt,

[19:08] 
to help the user know why the app is requesting access.

[19:12] 
This year’s Xcode now understands

[19:13] 
when an app has stopped due to a missing usage description

[19:16] 
and explains what is missing.

[19:18] 
From the annotation, you can jump directly to documentation to learn more.

[19:23] 
But the quickest way to fix the issue is to use the new “Add” button,

[19:27] 
which will take you directly to the Signing & Capabilities editor.

[19:30] 
The necessary capability will be added for you,

[19:33] 
as the Signing & Capabilities editor in Xcode 26

[19:36] 
now supports editing many capabilities that require usage descriptions,

[19:40] 
so you can edit them all in one place.

[19:42] 
Xcode will take care of updating the underlying Info plist,

[19:46] 
build settings, or entitlements for you.

[19:49] 
So now, all you need to do is enter your usage description.

[19:52] 
Then you can re-run and verify that the capability

[19:55] 
now prompts for permission, as expected.

[19:58] 
Instruments is a powerful tool for analyzing the performance of your apps

[20:01] 
and ships as part of every Xcode install.

[20:04] 
For CPU analysis, Instruments contains some powerful tools,

[20:08] 
providing multiple options for profiling your code’s performance

[20:11] 
on modern Apple silicon hardware.

[20:13] 
Previously,

[20:14] 
Instruments used sampling-based profilers to understand CPU usage,

[20:18] 
which are great choices for analyzing long-running workloads.

[20:22] 
But what does it mean for a profiler to be sampling based?

[20:26] 
It literally means that the tool samples the CPUs periodically,

[20:29] 
expecting that call stacks sampled are responsible

[20:31] 
for the same relative CPU usage overall.

[20:34] 
But sampling by its very nature is only an approximation of the full workload,

[20:39] 
which is why it is more practical for long-running workload analysis.

[20:42] 
In our illustration, the orange sections of execution

[20:45] 
were not captured by sampling, for example.

[20:48] 
Recent Apple silicon devices can capture a processor trace

[20:51] 
where the CPU stores information about the code it runs,

[20:55] 
including the branches it takes, and the instructions it jumps to.

[20:59] 
The CPU streams this information to an area on the file system

[21:02] 
so that it can be analyzed with the Processor Trace instrument.

[21:07] 
Rather than periodic sampling,

[21:09] 
Processor Trace captures information

[21:11] 
about every low-level branching decision the CPU makes,

[21:14] 
on all running threads, with very little runtime overhead.

[21:17] 
This means that the Processor Trace timeline

[21:19] 
can present a high-fidelity visualization of execution flow.

[21:23] 
Unlike traditional sampling profilers that can miss critical code paths

[21:27] 
between sampling intervals,

[21:28] 
this tool reveals every branch taken and function called —

[21:31] 
including compiler-generated code, like ARC memory management in Swift.

[21:36] 
Processor Trace is a fundamental shift in how you can measure software performance,

[21:40] 
with every function call captured, on all threads, with little overhead.

[21:45] 
Processor Trace was introduced with Xcode 16.3

[21:47] 
and is supported by M4 and iPhone 16 devices.

[21:52] 
Processor Trace is great for understanding the execution of your code

[21:55] 
and where CPU time is being spent.

[21:58] 
In contrast, the significantly updated CPU Counters instrument

[22:01] 
will help you understand how your code is interacting with the CPU.

[22:06] 
This tool will help guide you in making microarchitecture optimizations.

[22:11] 
CPU Counters now uses preset modes that group related counters together,

[22:16] 
to provide a guided approach to learning about how your code is handled by the CPU.

[22:21] 
These modes include a general CPU Bottlenecks mode,

[22:24] 
which is a good starting point for this type of analysis.

[22:28] 
CPU Bottlenecks breaks down the CPU's sustainable instruction bandwidth

[22:32] 
into either useful work, or bottlenecked for one of three broad reasons:

[22:37] 
Either the CPU had to wait for execution units or memory to become available;

[22:42] 
Or the CPU couldn’t deliver instructions quickly enough;

[22:45] 
Or the CPU incorrectly predicted future work

[22:48] 
and needed to get back on track.

[22:51] 
In addition to the bottleneck analysis approach,

[22:54] 
the Instruction Characteristics and Metrics modes

[22:56] 
offer a more traditional use of the counters

[22:58] 
to get absolute counts of consumption.

[23:01] 
These let you focus on tuning critical instruction sequences

[23:04] 
by analyzing branches, cache behavior, and numerical operations directly.

[23:10] 
CPU Counters also includes detailed documentation

[23:13] 
to help understand what the modes and counters represent.

[23:17] 
To learn a lot more about Processor Trace and CPU Counters

[23:20] 
see “Optimize CPU performance with Instruments”.

[23:24] 
SwiftUI makes it easier than ever to build highly interactive apps.

[23:28] 
For the best user experience, performance is critical.

[23:31] 
In this year’s OS releases we’ve made a number of improvements

[23:34] 
to SwiftUI performance.

[23:36] 
For example, Lists can update up to 16 times faster

[23:39] 
without any additional changes from your app.

[23:42] 
Even with these improvements,

[23:43] 
your app still might not be performing as well as you’d like it to,

[23:46] 
and you’ll want to find out why your views are updating frequently.

[23:50] 
To help with that, the next-generation SwiftUI instrument included with Xcode 26,

[23:55] 
captures detailed information about the causes and effects

[23:58] 
of SwiftUI updates.

[24:00] 
This makes it easier than ever to understand

[24:02] 
when and why your views update.

[24:04] 
The timeline gives a quick overview

[24:06] 
of when SwiftUI is doing work on the main thread,

[24:09] 
and when individual view updates take a long time

[24:12] 
and put you at risk of a hitch or hang.

[24:15] 
The “View Body Updates” summary tells you

[24:18] 
how many times each view in your app updated.

[24:21] 
If the number of updates to one of your views is much larger than you expect,

[24:25] 
open the cause-and-effect graph to help understand why.

[24:29] 
To learn more about SwiftUI’s performance improvements,

[24:32] 
see “What’s new in SwiftUI”.

[24:35] 
For more information on how to use the SwiftUI instrument,

[24:37] 
check out “Optimize SwiftUI performance with Instruments”.

[24:41] 
People love apps they can rely on throughout their day,

[24:44] 
and a crucial part of that reliability is excellent battery life.

[24:47] 
While debugging your app,

[24:49] 
perhaps you've noticed high energy impact in Xcode, signaling a problem.

[24:53] 
But finding the root cause can be tough.

[24:55] 
In these situations, what you really need is the ability to run your app,

[24:59] 
reproduce the issue, and record power metrics.

[25:03] 
The Power Profiler instrument is the perfect tool for this.

[25:06] 
It lets you profile your app

[25:08] 
and record power metrics which can then be visualized.

[25:11] 
The Power Profiler track shows system power usage,

[25:14] 
correlated with the thermal and charging states of the device,

[25:17] 
helping to identify unexpected power spikes.

[25:21] 
The process track shows the impact the application has

[25:24] 
on various device power subcomponents

[25:26] 
like CPU, GPU, Display, and Networking.

[25:30] 
Power Profiler supports two modes of tracing:

[25:33] 
Tethered recording, with Instruments directly connected to the target device;

[25:37] 
And "passive" recording,

[25:38] 
where a trace can be initiated on a device from Developer Settings,

[25:41] 
without being tethered.

[25:43] 
The trace can then later be imported into Instruments for analysis.

[25:48] 
By recording stable workloads,

[25:49] 
you can use the Power Profiler instrument

[25:51] 
to observe how your choice of algorithms and APIs

[25:55] 
affects sustainability of a workload.

[25:57] 
Learn more by checking out “Profile and optimize power usage in your app”.

[26:01] 
While Instruments is great

[26:03] 
for analyzing the performance of your app during development,

[26:05] 
the Xcode Organizer allows you to monitor the power and performance

[26:09] 
impact of your shipping apps via metrics and diagnostics.

[26:13] 
The Organizer in Xcode 16 introduced a feature called Trending Insights

[26:17] 
to Disk Write diagnostics, with a flame icon in the source list.

[26:21] 
These help call out issues that have increased in impact,

[26:24] 
that you may want to pay attention to.

[26:27] 
In this year’s Xcode, we’ve taken this one step further

[26:30] 
by bringing Trending Insights to Hang and Launch diagnostics as well,

[26:33] 
where the flame icon calls out Hang and Launch times

[26:36] 
that are trending in the wrong direction.

[26:38] 
Additionally, the Insights area now provides clarity about the trend

[26:42] 
by charting the increase across the last 5 app versions.

[26:46] 
This not only provides a starting point for performance optimizations,

[26:49] 
but also helps you understand where you could have introduced code

[26:52] 
that led to the overall increase in impact.

[26:55] 
And now that you know what to prioritize,

[26:57] 
you can share a diagnostic report with your colleagues using URL sharing.

[27:03] 
Another area in the Organizer to help you understand

[27:05] 
how well your app is performing across versions is Metrics.

[27:09] 
Metrics have been expanded in Xcode 26 with the addition of Recommendations.

[27:14] 
Metric Recommendations compare your app’s metrics with other sources –

[27:18] 
including similar apps and your app’s historical data –

[27:21] 
to provide an important reference point for understanding

[27:23] 
how well your app is performing across its user base.

[27:27] 
In this example, our app’s launch time is measured at around 564 milliseconds.

[27:33] 
However, based on similar apps' metrics,

[27:35] 
Xcode is recommending that our app’s launch time

[27:37] 
should be closer to 425 milliseconds,

[27:40] 
which gives us a clear target to aim for.

[27:43] 
This year, metric recommendations are available for the Launch Time metric.

[27:46] 
Apple will enable recommendations for other metrics over time.

[27:50] 
Next, I’d like to talk about Xcode’s build system.

[27:54] 
In Xcode 16, we introduced Explicitly Built Modules,

[27:57] 
enabled for C and Objective-C code.

[28:00] 
In Xcode 26, we’re excited to announce

[28:02] 
that we are enabling Explicitly Built Modules for Swift code by default.

[28:07] 
With Explicit Modules, Xcode splits up

[28:10] 
the processing of each compilation unit into three phases:

[28:13] 
Scanning, building modules, and finally building the original source code.

[28:19] 
This separation gives the build system better control of module build tasks

[28:23] 
to optimize the build pipeline.

[28:26] 
Building explicit modules improves build efficiency and reliability,

[28:30] 
with more precise and deterministic sharing of modules.

[28:33] 
It also improves the speed of debugging Swift code,

[28:36] 
as the debugger can reuse the already built modules.

[28:40] 
For more information, refer to “Demystify explicitly built modules”.

[28:45] 
Earlier this year, Apple open sourced Swift Build,

[28:48] 
a powerful and extensible build engine

[28:50] 
that is used by Xcode and Swift Playground,

[28:52] 
as well as the internal build process for Apple’s own operating systems.

[28:57] 
We've also been working to incorporate Swift Build into Swift Package Manager,

[29:01] 
to unify the build experience across Swift open source toolchains and Xcode.

[29:05] 
We’re also adding support for all platforms

[29:08] 
supported by the Swift ecosystem,

[29:09] 
including Linux, Windows, Android, and more.

[29:12] 
You can preview this new implementation on your own packages

[29:15] 
using the “build-system” option of the Swift command line tool.

[29:19] 
Or see your changes live in Xcode

[29:21] 
using the instructions in the Swift Build repository.

[29:25] 
For the first time, the community can contribute

[29:28] 
to the implementation of the build engine

[29:30] 
that powers Xcode and the Swift ecosystem.

[29:33] 
To learn more about Swift Build or get involved in development,

[29:37] 
check out the repository on GitHub.

[29:40] 
In our interconnected world,

[29:41] 
users view security as an increasingly critical requirement for applications.

[29:46] 
Xcode’s new Enhanced Security capability provides your apps

[29:50] 
with the same protections used in Apple’s apps, such as pointer authentication.

[29:54] 
You can enable these security settings for your app

[29:57] 
by adding the “Enhanced Security” capability

[29:59] 
in the “Signing and Capabilities” editor.

[30:02] 
We recommend enabling it for applications with a significant attack surface,

[30:06] 
such as social media, messaging, image viewing, and browsing.

[30:10] 
Get more details about Enhanced Security in the Apple Developer documentation.

[30:14] 
Next, let’s talk about Testing.

[30:17] 
Xcode’s UI testing has had a significant upgrade this year.

[30:20] 
UI automation recording has been enhanced

[30:23] 
with a completely new code generation system.

[30:26] 
This is great news, as I wanted to implement a UI test for Landmarks,

[30:29] 
to test the Collection editing UI.

[30:32] 
Let’s use the UI automation recording feature

[30:34] 
of Xcode 26 to build my test for me.

[30:37] 
I’ve already got a test target configured for this project

[30:40] 
and a new test method ready to fill out.

[30:43] 
By placing the cursor in the body of the test method,

[30:46] 
Xcode reveals a “Start Recording” button in the editor gutter.

[30:49] 
We can hit that button to start a recording session.

[30:53] 
Xcode then prompts to confirm and lets me know

[30:56] 
that the file will be in read-only mode until the recording is complete.

[31:01] 
Now, Xcode prepares the session.

[31:03] 
It launches the app in the simulator, in recording mode.

[31:09] 
Now, I can perform the exact interactions that I want my test to perform.

[31:13] 
I’ll start by navigating to the “Collections” screen.

[31:19] 
And notice how Xcode is adding code to my test method for each of my interactions.

[31:23] 
Very cool!

[31:26] 
Next, I’ll add a new collection and switch it to “edit” mode.

[31:31] 
Editing a collection is the main purpose of this test.

[31:34] 
So I’ll interact with each of the fields on this screen, to edit the title,

[31:37] 
description, and add a landmark.

[31:48] 
This one looks perfect!

[31:54] 
That completes our steps to add and edit a new collection.

[31:57] 
Finally, as a simple verification of our edit,

[32:00] 
let’s select the landmark we added to the collection to navigate to its details.

[32:06] 
That’s all we need for this UI test.

[32:08] 
Back in the source editor,

[32:09] 
I’ll hit “Stop Recording” in the editor gutter

[32:11] 
to end the test recording session.

[32:16] 
Now, let’s use the test diamond to see our test in action.

[32:22] 
Notice how Xcode has generated concise code for all of our interactions.

[32:27] 
Plus, we get multiple identifier options for many elements.

[32:32] 
We can use those to fine tune how an element is identified in our tests.

[32:36] 
It’s so much easier to make a new UI test

[32:38] 
when you can simply perform the interactions in the app

[32:41] 
that you want the test to perform.

[32:45] 
And that’s an example of recording a UI test in Xcode 26.

[32:49] 
Xcode takes care of all the heavy lifting

[32:51] 
of converting your interactions into the best possible test code.

[32:55] 
But UI testing code generation doesn’t stop there.

[32:58] 
The same code generation has been integrated

[33:00] 
into the test report’s Automation Explorer.

[33:04] 
Here, I’ve got a Test Report open, containing a UI test failure.

[33:08] 
It looks like the test was trying to tap a TextField

[33:11] 
but couldn’t find one with the specified identifier.

[33:15] 
On the right, the Automation Explorer

[33:16] 
contains a full video recording of the test.

[33:19] 
We can replay the whole test in real time, if we need to.

[33:23] 
The current video frame is showing the point when the failure occurred.

[33:26] 
We can certainly see a description field in the app’s UI.

[33:30] 
What’s awesome about UI testing is that Xcode records attributes

[33:34] 
about every identifiable element while running a test.

[33:37] 
We can then inspect elements in the Automation Explorer after the fact.

[33:41] 
So let’s inspect the “description” element.

[33:44] 
Looking at the element’s details, it has the correct identifier,

[33:47] 
but its type is actually a Text View,

[33:49] 
not a Text Field, as the test was expecting.

[33:52] 
It looks like the app’s UI had been updated

[33:54] 
to support multi-line descriptions.

[33:57] 
Helpfully, the correct code snippet

[33:58] 
to identify this element was generated for us.

[34:01] 
We can simply copy the code from the popover

[34:04] 
and update our test to make the correction.

[34:07] 
And that’s the improved UI testing experience.

[34:10] 
In addition to enhanced UI recording,

[34:12] 
this year’s Xcode also has better device support

[34:14] 
for automated hardware interactions,

[34:17] 
including hardware keyboard and hardware button presses.

[34:21] 
All together these enhancements make UI testing

[34:23] 
a much more streamlined experience.

[34:26] 
So give it a try, add some UI tests to your project today

[34:30] 
and take advantage of Xcode Cloud to run your tests autonomously.

[34:33] 
To learn a lot more,

[34:34] 
please see “Record, replay, and review: UI automation in Xcode”.

[34:41] 
UI testing is also great for measuring the responsiveness of your UI,

[34:44] 
using the “measure” API.

[34:46] 
In Xcode 26, we’ve expanded the API

[34:49] 
by adding an XCTHitchMetric

[34:51] 
so you can now catch hitches in your app during testing.

[34:55] 
For example, as shown here, you could use XCTHitchMetric

[34:58] 
to test the scrolling animation performance of your app.

[35:02] 
XCTHitchMetric reports multiple metrics for your app’s hitch performance,

[35:06] 
such as Hitch Time Ratio.

[35:08] 
Hitch Time Ratio represents the total amount of time your app was hitching

[35:12] 
over the duration of the measured portion of your test.

[35:16] 
For more information on hitches,

[35:18] 
see the tech talk “Explore UI animation hitches and the render loop”.

[35:23] 
Another great way to regression test your code is with Runtime API Checks.

[35:28] 
This year’s Xcode is bringing more Runtime API Checks to tests,

[35:31] 
configured in the Test Plan configuration editor.

[35:35] 
Tests can now surface framework runtime issues

[35:37] 
as well as call out threading problems using the Thread Performance Checker.

[35:42] 
The Thread Performance Checker detects threading issues like priority inversions

[35:46] 
and non-UI work on the main thread.

[35:49] 
Here, for example,

[35:50] 
Thread Performance Checker is notifying us of an API

[35:53] 
that shouldn’t be called on the main thread

[35:54] 
if we want to keep our app responsive.

[35:58] 
Test Plans also provide an option to fail a test

[36:00] 
if runtime API checks find any issues.

[36:04] 
Now your tests can provide you assurance

[36:06] 
that your code continues to follow API best practices.

[36:09] 
Those are just some of the new and exciting features this year.

[36:12] 
Xcode 26 can help you be more efficient while writing code,

[36:16] 
can guide you as you build new features,

[36:18] 
and gives you new tools that make it easy to support more platforms and languages.

[36:23] 
It can help you whether you’re debugging at your desk,

[36:25] 
inspecting the performance of your app in the wild,

[36:28] 
or testing your user interfaces.

[36:30] 
Download Xcode 26 to create, build, and debug your code.

[36:35] 
And use Xcode Cloud to test and distribute your app.

[36:38] 
Ask us any questions you may have in the Developer Forums.

[36:41] 
And to learn more, please check out our release notes on developer.apple.com.

[36:46] 
Thanks for watching!
