# WWDC Session Conversion Prompt

Convert this WWDC session page to markdown. Requirements:
1. Do not wrap the ENTIRE output in a code fence - output should be plain markdown
2. Include ALL tabs content (About, Summary, Transcript, Code samples)
3. Start with YAML front matter:
   ---
   session: [number]
   year: [year]  
   title: [full title]
   presenters: [list of presenters]
   duration: [in minutes]
   ---
4. Interleave code samples with transcript at their timestamp locations
5. For code samples in the transcript, use proper markdown code blocks with swift syntax highlighting (```swift ... ```)
6. Preserve all chapter markers with timestamps
7. Include all resource links in a Resources section
8. Format timestamps as [MM:SS] in transcript
9. Make sure all code blocks are properly opened AND closed