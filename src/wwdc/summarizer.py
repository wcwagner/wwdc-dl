"""AI-powered summarization for WWDC sessions."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import click

console = Console()

# Default summarization prompt for WWDC sessions
DEFAULT_WWDC_PROMPT = """You are an expert iOS/macOS developer. Summarize this WWDC session following this format:

## Session Info
- Number, title, presenter
- One sentence about what's new

## Context
2-4 sentences explaining the problem and when you need these features

## Requirements
- iOS/macOS version requirements
- Any mandatory changes

## New APIs
- List new methods/classes with brief descriptions
- Include simple code examples where relevant

## Key Points
- Must-know items
- Important method names
- Common pitfalls

## Migration Guide
- Breaking changes
- Step-by-step migration if applicable

Keep it concise and developer-focused. Focus on actionable information."""

# Token limits and pricing (approximate)
TOKEN_LIMITS = {
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "gemini-2.0-flash": 32000,
}

# Approximate cost per 1K tokens (input + output averaged)
COST_PER_1K_TOKENS = {
    "gpt-4": 0.04,  # $0.03 input + $0.06 output averaged
    "gpt-4-turbo": 0.015,  # $0.01 input + $0.03 output averaged
    "gpt-4o": 0.0075,  # $0.005 input + $0.015 output averaged
    "gpt-4o-mini": 0.00075,  # $0.00015 input + $0.0006 output averaged
    "claude-3-opus": 0.045,  # $0.015 input + $0.075 output averaged
    "claude-3-sonnet": 0.009,  # $0.003 input + $0.015 output averaged
    "claude-3-haiku": 0.000625,  # $0.00025 input + $0.00125 output averaged
    "gemini-2.0-flash": 0.00015,  # Very cheap
}

# Safety margin for token counting
TOKEN_SAFETY_MARGIN = 0.8  # Use only 80% of limit
MAX_CONTENT_TOKENS = 100000  # Hard limit regardless of model


class LLMSummarizer:
    """Summarize WWDC content using LLM CLI."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        verbose: bool = False,
        llm_binary: str = "llm",
        max_tokens_per_request: Optional[int] = None,
        max_cost_per_session: float = 0.50,  # Default $0.50 per session
    ):
        self.model = model
        self.verbose = verbose
        self.llm_binary = llm_binary
        self.prompt_template = None
        self.max_tokens_per_request = max_tokens_per_request
        self.max_cost_per_session = max_cost_per_session
        self._check_llm_cli()
        self._load_prompt_template()

    def _check_llm_cli(self):
        """Check if LLM CLI is installed."""
        try:
            result = subprocess.run(
                [self.llm_binary, "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(
                    "[red]LLM CLI not found. Install with: pip install llm[/red]"
                )
                raise RuntimeError("LLM CLI not installed")
        except FileNotFoundError:
            console.print(
                "[red]LLM CLI not found. Install with: pip install llm[/red]"
            )
            raise RuntimeError("LLM CLI not installed")

    def _load_prompt_template(self):
        """Load custom prompt template if available."""
        prompt_file = Path(__file__).parent / "prompts" / "wwdc_summary.txt"
        if prompt_file.exists():
            self.prompt_template = prompt_file.read_text()
        else:
            self.prompt_template = DEFAULT_WWDC_PROMPT

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters or 0.75 words
        # This is conservative to avoid underestimating
        return max(len(text) // 4, len(text.split()) * 4 // 3)

    def _estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for token usage."""
        cost_per_1k = COST_PER_1K_TOKENS.get(model, 0.01)  # Default to $0.01 if unknown
        return (tokens / 1000) * cost_per_1k

    def _check_token_limits(self, content: str, model: str) -> tuple[bool, str, int, float]:
        """Check if content exceeds token limits or cost threshold.
        
        Returns: (is_safe, message, estimated_tokens, estimated_cost)
        """
        # Estimate tokens
        prompt_tokens = self._estimate_tokens(self.prompt_template)
        content_tokens = self._estimate_tokens(content)
        total_tokens = prompt_tokens + content_tokens + 1000  # Buffer for response
        
        # Get model limits
        model_base = model.split("-")[0] + "-" + model.split("-")[1] if "-" in model else model
        max_tokens = TOKEN_LIMITS.get(model, TOKEN_LIMITS.get(model_base, 8192))
        safe_limit = int(max_tokens * TOKEN_SAFETY_MARGIN)
        
        # Check hard limit
        if content_tokens > MAX_CONTENT_TOKENS:
            return False, f"Content too large: ~{content_tokens:,} tokens (max {MAX_CONTENT_TOKENS:,})", total_tokens, 0
        
        # Check model limit
        if total_tokens > safe_limit:
            return False, f"Exceeds {model} limit: ~{total_tokens:,} tokens (safe limit {safe_limit:,})", total_tokens, 0
        
        # Estimate cost
        estimated_cost = self._estimate_cost(total_tokens, model)
        
        # Check cost threshold
        if estimated_cost > self.max_cost_per_session:
            return False, f"Estimated cost ${estimated_cost:.2f} exceeds limit ${self.max_cost_per_session:.2f}", total_tokens, estimated_cost
        
        return True, "OK", total_tokens, estimated_cost

    async def summarize_session(
        self, content_path: Path, output_path: Optional[Path] = None
    ) -> str:
        """Summarize a single session."""
        if not content_path.exists():
            raise FileNotFoundError(f"Content file not found: {content_path}")

        # Read content
        async with aiofiles.open(content_path, "r") as f:
            content = await f.read()

        # Check token limits and cost
        is_safe, message, tokens, cost = self._check_token_limits(content, self.model)
        
        if not is_safe:
            console.print(f"[red]Cannot summarize {content_path.name}: {message}[/red]")
            console.print(f"[yellow]Consider using a model with higher limits or reducing content[/yellow]")
            raise ValueError(f"Token/cost limit exceeded: {message}")
        
        if self.verbose:
            console.print(f"[blue]Summarizing {content_path.name}...[/blue]")
            console.print(f"[dim]Estimated: ~{tokens:,} tokens, ~${cost:.3f}[/dim]")

        # Run LLM CLI
        cmd = [
            self.llm_binary,
            "-m", self.model,
            "-s", self.prompt_template,
        ]
        
        # Add max tokens if specified
        if self.max_tokens_per_request:
            cmd.extend(["-o", f"max_tokens {self.max_tokens_per_request}"])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate(input=content.encode())

        if process.returncode != 0:
            error_msg = stderr.decode()
            console.print(f"[red]LLM error: {error_msg}[/red]")
            raise RuntimeError(f"LLM failed: {error_msg}")

        summary = stdout.decode()

        # Save if output path provided
        if output_path:
            async with aiofiles.open(output_path, "w") as f:
                await f.write(summary)

        return summary

    async def summarize_topic(
        self, topic_dir: Path, force: bool = False
    ) -> Dict[str, str]:
        """Summarize all sessions in a topic."""
        summaries = {}
        sessions = []
        total_estimated_cost = 0.0

        # Collect sessions and estimate total cost
        for session_dir in topic_dir.iterdir():
            if not session_dir.is_dir():
                continue

            content_file = session_dir / "content.md"
            summary_file = session_dir / "summary.md"

            if not content_file.exists():
                continue

            if summary_file.exists() and not force:
                console.print(
                    f"[yellow]Summary exists for {session_dir.name}, skipping[/yellow]"
                )
                continue

            # Quick cost estimation
            try:
                async with aiofiles.open(content_file, "r") as f:
                    content = await f.read()
                    _, _, _, cost = self._check_token_limits(content, self.model)
                    total_estimated_cost += cost
                    sessions.append((session_dir.name, content_file, summary_file, cost))
            except Exception:
                sessions.append((session_dir.name, content_file, summary_file, 0))

        if not sessions:
            console.print("[yellow]No sessions to summarize[/yellow]")
            return summaries
        
        # Warn about cost
        if total_estimated_cost > 5.0:  # Warn if over $5
            console.print(f"[bold yellow]Estimated total cost: ${total_estimated_cost:.2f}[/bold yellow]")
            console.print(f"[yellow]Processing {len(sessions)} sessions with {self.model}[/yellow]")
            if not click.confirm("Continue?", default=True):
                console.print("[red]Aborted[/red]")
                return summaries

        # Process sessions
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Summarizing {len(sessions)} sessions...", total=len(sessions)
            )

            for session_data in sessions:
                if len(session_data) == 4:
                    session_name, content_file, summary_file, est_cost = session_data
                else:
                    session_name, content_file, summary_file = session_data
                    est_cost = 0
                    
                progress.update(
                    task, description=f"Summarizing {session_name}..."
                )

                try:
                    summary = await self.summarize_session(content_file, summary_file)
                    summaries[session_name] = summary
                    progress.advance(task)
                except Exception as e:
                    console.print(
                        f"[red]Error summarizing {session_name}: {e}[/red]"
                    )
                    if "token" in str(e).lower() or "cost" in str(e).lower():
                        console.print(f"[yellow]Skipping remaining sessions in topic to avoid further costs[/yellow]")
                        break

        return summaries

    async def batch_summarize(
        self, year_dir: Path, topics: Optional[List[str]] = None, force: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """Batch summarize multiple topics."""
        all_summaries = {}

        if topics:
            topic_dirs = [year_dir / topic for topic in topics]
        else:
            topic_dirs = [d for d in year_dir.iterdir() if d.is_dir()]

        for topic_dir in topic_dirs:
            if not topic_dir.exists():
                console.print(f"[red]Topic directory not found: {topic_dir}[/red]")
                continue

            console.print(f"\n[bold blue]Summarizing topic: {topic_dir.name}[/bold blue]")
            summaries = await self.summarize_topic(topic_dir, force)
            if summaries:
                all_summaries[topic_dir.name] = summaries

        return all_summaries


class LLMExporter:
    """Export summaries to LLM-ready format."""

    def __init__(self):
        self.export_prompt = self._load_export_prompt()

    def _load_export_prompt(self) -> str:
        """Load export prompt template."""
        prompt_file = Path(__file__).parent / "prompts" / "llm_export.txt"
        if prompt_file.exists():
            return prompt_file.read_text()
        else:
            return """Extract the most important information from these WWDC session summaries.
Focus on:
1. New APIs and their usage
2. Breaking changes and migrations
3. Best practices and recommendations
4. Common patterns across sessions

Format as a concise reference guide for developers."""

    async def export_topic_to_llm(
        self, topic_dir: Path, output_file: Path
    ) -> None:
        """Export all summaries in a topic to LLM format."""
        summaries = []

        # Collect all summaries
        for session_dir in sorted(topic_dir.iterdir()):
            if not session_dir.is_dir():
                continue

            summary_file = session_dir / "summary.md"
            if summary_file.exists():
                async with aiofiles.open(summary_file, "r") as f:
                    content = await f.read()
                    summaries.append(f"## {session_dir.name}\n\n{content}")

        if not summaries:
            console.print("[yellow]No summaries found to export[/yellow]")
            return

        # Combine summaries
        combined = "\n\n---\n\n".join(summaries)

        # Write to output
        async with aiofiles.open(output_file, "w") as f:
            await f.write(f"# {topic_dir.name} - WWDC Summary\n\n{combined}")

        console.print(f"[green]Exported {len(summaries)} summaries to {output_file}[/green]")

    async def export_all_topics(
        self, year_dir: Path, output_dir: Path
    ) -> None:
        """Export all topics to separate LLM files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for topic_dir in year_dir.iterdir():
            if not topic_dir.is_dir():
                continue

            output_file = output_dir / f"{topic_dir.name}-llm.txt"
            await self.export_topic_to_llm(topic_dir, output_file)

    async def create_consolidated_export(
        self, year_dir: Path, output_file: Path, topics: Optional[List[str]] = None
    ) -> None:
        """Create a single consolidated LLM export file."""
        all_content = []

        if topics:
            topic_dirs = [year_dir / topic for topic in topics if (year_dir / topic).exists()]
        else:
            topic_dirs = [d for d in year_dir.iterdir() if d.is_dir()]

        for topic_dir in sorted(topic_dirs):
            topic_summaries = []
            
            for session_dir in sorted(topic_dir.iterdir()):
                if not session_dir.is_dir():
                    continue

                summary_file = session_dir / "summary.md"
                if summary_file.exists():
                    async with aiofiles.open(summary_file, "r") as f:
                        content = await f.read()
                        topic_summaries.append(f"### {session_dir.name}\n\n{content}")

            if topic_summaries:
                topic_content = f"# Topic: {topic_dir.name}\n\n" + "\n\n".join(topic_summaries)
                all_content.append(topic_content)

        if not all_content:
            console.print("[yellow]No summaries found to export[/yellow]")
            return

        # Write consolidated file
        async with aiofiles.open(output_file, "w") as f:
            await f.write("\n\n---\n\n".join(all_content))

        console.print(f"[green]Created consolidated export: {output_file}[/green]")


# Utility functions for integration with CLI
async def setup_llm_cli():
    """Interactive setup for LLM CLI."""
    console.print("[bold]Setting up LLM CLI...[/bold]")
    
    # Check installation
    try:
        subprocess.run(["llm", "--version"], check=True, capture_output=True)
        console.print("[green]LLM CLI is installed[/green]")
    except:
        console.print("[yellow]Installing LLM CLI...[/yellow]")
        subprocess.run(["pip", "install", "llm"], check=True)
    
    # Configure API keys
    console.print("\n[bold]Configure API keys:[/bold]")
    console.print("1. OpenAI (gpt-4, gpt-4o-mini)")
    console.print("2. Anthropic (claude-3)")
    console.print("3. Google (gemini)")
    console.print("4. Skip")
    
    choice = input("\nSelect provider (1-4): ")
    
    if choice == "1":
        subprocess.run(["llm", "keys", "set", "openai"])
    elif choice == "2":
        subprocess.run(["llm", "install", "llm-anthropic"])
        subprocess.run(["llm", "keys", "set", "anthropic"])
    elif choice == "3":
        subprocess.run(["llm", "install", "llm-gemini"]) 
        subprocess.run(["llm", "keys", "set", "gemini"])
    
    # Save WWDC template
    console.print("\n[bold]Creating WWDC summarization template...[/bold]")
    subprocess.run([
        "llm", "-s", DEFAULT_WWDC_PROMPT, 
        "--save", "wwdc-summary",
        "test"
    ], input=b"", capture_output=True)
    
    console.print("[green]Setup complete![/green]")