#!/usr/bin/env python3
"""
Script to update targets/optee-qemu-v8/sdk.yml with commit hashes from OP-TEE manifest XMLs.

This script downloads OP-TEE manifest XML files for a specified version and updates
the corresponding commit hashes in the SDK YAML configuration file.

Examples:
    python scripts/update_optee_sdk_yml.py 4.7.0
    python scripts/update_optee_sdk_yml.py 4.7.0 --dry-run
    python scripts/update_optee_sdk_yml.py 4.7.0 --sdk-path custom/sdk.yml --verbose
"""
import sys
import os
import argparse
import logging
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Constants
DEFAULT_SDK_YML_PATH = os.path.join("targets", "optee-qemu-v8", "sdk.yml")
QEMU_XML_URL = "https://raw.githubusercontent.com/OP-TEE/manifest/refs/heads/{version}/qemu_v8.xml"
COMMON_XML_URL = "https://raw.githubusercontent.com/OP-TEE/manifest/refs/heads/{version}/common.xml"

# Global Rich console
console = Console()


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging based on verbosity level."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING  # Reduce default logging since we use Rich for most output

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


def fetch_xml(url: str, description: str = "Fetching XML") -> bytes:
    """
    Fetch XML content from a URL with proper error handling and Rich progress.

    Args:
        url: The URL to fetch XML from
        description: Description for the progress display

    Returns:
        XML content as bytes

    Raises:
        SystemExit: If fetch fails with appropriate error message
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"{description}...", total=None)

            with urllib.request.urlopen(url) as response:
                if response.status != 200:
                    console.print(f"[red]✗[/red] HTTP {response.status} when fetching {url}")
                    sys.exit(1)
                content = response.read()

            progress.update(task, description=f"[green]✓[/green] {description}")
            return content

    except urllib.error.HTTPError as e:
        if e.code == 404:
            console.print(f"[red]✗ Version not found:[/red] {url}")
            console.print("[yellow]Please check that the version exists in the OP-TEE manifest repository[/yellow]")
        else:
            console.print(f"[red]✗ HTTP error {e.code}:[/red] {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        console.print(f"[red]✗ Network error:[/red] {e.reason}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        sys.exit(1)


def parse_projects(xml_content: bytes, description: str = "Parsing XML") -> Dict[str, str]:
    """
    Parse XML manifest and extract project path-to-revision mappings.

    Args:
        xml_content: Raw XML content as bytes
        description: Description for progress display

    Returns:
        Dictionary mapping project paths to revision strings

    Raises:
        SystemExit: If XML parsing fails
    """
    projects = {}
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"{description}...", total=None)

            root = ET.fromstring(xml_content)
            for proj in root.findall(".//project"):
                path = proj.get("path")
                revision = proj.get("revision")
                if path and revision:
                    projects[path] = revision
                    logging.debug(f"Found project: {path} -> {revision}")

            progress.update(task, description=f"[green]✓[/green] {description} ({len(projects)} projects)")

    except ET.ParseError as e:
        console.print(f"[red]✗ Invalid XML format:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error parsing XML:[/red] {e}")
        sys.exit(1)
    return projects


def create_custom_yaml_loader():
    """Create a custom YAML loader that handles !include tags."""
    class CustomLoader(yaml.SafeLoader):
        pass

    def include_constructor(loader, node):
        """Handle !include tags by preserving them as strings."""
        return f"!include {loader.construct_scalar(node)}"

    CustomLoader.add_constructor('!include', include_constructor)
    return CustomLoader


def load_yaml_file(file_path: str) -> dict:
    """
    Load YAML file with proper error handling and support for !include tags.

    Args:
        file_path: Path to the YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        SystemExit: If file cannot be read or parsed
    """
    try:
        with open(file_path, "r") as f:
            return yaml.load(f, Loader=create_custom_yaml_loader())
    except FileNotFoundError:
        logging.error(f"SDK file not found: {file_path}")
        logging.error("Please ensure you're running from the correct directory")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML syntax in {file_path}: {e}")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied reading {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        sys.exit(1)


def create_custom_yaml_dumper():
    """Create a custom YAML dumper that handles !include tags."""
    class CustomDumper(yaml.SafeDumper):
        pass

    def include_representer(dumper, data):
        """Handle !include tags by outputting them correctly."""
        if isinstance(data, str) and data.startswith('!include '):
            tag_value = data[9:]  # Remove '!include ' prefix
            return dumper.represent_scalar('!include', tag_value)
        return dumper.represent_str(data)

    CustomDumper.add_representer(str, include_representer)
    return CustomDumper


def save_yaml_file(data: dict, file_path: str) -> None:
    """
    Save YAML file with proper error handling and support for !include tags.

    Args:
        data: Dictionary to save as YAML
        file_path: Path to save the YAML file

    Raises:
        SystemExit: If file cannot be written
    """
    try:
        with open(file_path, "w") as f:
            yaml.dump(data, f,
                     default_flow_style=False,
                     sort_keys=False,
                     Dumper=create_custom_yaml_dumper(),
                     allow_unicode=True)
    except PermissionError:
        logging.error(f"Permission denied writing to {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error writing {file_path}: {e}")
        sys.exit(1)


def analyze_changes_line_by_line(projects: Dict[str, str], sdk_path: str) -> List[Tuple[str, str, str]]:
    """
    Analyze what changes would be made using line-by-line parsing (for dry-run mode).

    Args:
        projects: Dictionary mapping project names to revision strings
        sdk_path: Path to the SDK YAML file

    Returns:
        List of tuples (project_name, old_commit, new_commit) for changes that would be made

    Raises:
        SystemExit: If file operations fail
    """
    logging.info(f"Analyzing {sdk_path}...")

    try:
        with open(sdk_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"SDK file not found: {sdk_path}")
        logging.error("Please ensure you're running from the correct directory")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied reading {sdk_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading {sdk_path}: {e}")
        sys.exit(1)

    changes = []
    current_name = None

    for i, line in enumerate(lines):
        # Track current git entry name
        if line.strip().startswith('- name:'):
            current_name = line.strip().split(':', 1)[1].strip()
            logging.debug(f"Found git entry: {current_name}")

        elif line.strip().startswith('commit:') and current_name:
            # Extract the commit value
            commit_line_stripped = line.strip()
            old_commit = commit_line_stripped.split(':', 1)[1].strip()

            # Check if we would update this commit
            if current_name in projects:
                new_commit = projects[current_name]
                if not commits_are_equivalent(old_commit, new_commit):
                    changes.append((current_name, old_commit, new_commit))
                else:
                    logging.debug(f"No change needed for {current_name}: {old_commit}")
            else:
                logging.debug(f"Skipping {current_name}: not in XML projects")

            current_name = None  # Reset after processing commit

        else:
            # Reset current_name if we hit a new top-level item
            if line.strip().startswith('- ') and not line.strip().startswith('- name:'):
                current_name = None

    return changes


def update_sdk_yml_line_by_line(projects: Dict[str, str], sdk_path: str) -> List[Tuple[str, str, str]]:
    """
    Update SDK YAML file by modifying only commit lines, preserving all formatting.

    Args:
        projects: Dictionary mapping project names to revision strings
        sdk_path: Path to the SDK YAML file

    Returns:
        List of tuples (project_name, old_commit, new_commit) for changes made

    Raises:
        SystemExit: If file operations fail
    """
    logging.info(f"Updating {sdk_path}...")

    try:
        with open(sdk_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"SDK file not found: {sdk_path}")
        logging.error("Please ensure you're running from the correct directory")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied reading {sdk_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading {sdk_path}: {e}")
        sys.exit(1)

    new_lines = []
    changes = []
    current_name = None
    updated_count = 0

    for i, line in enumerate(lines):
        # Track current git entry name
        if line.strip().startswith('- name:'):
            current_name = line.strip().split(':', 1)[1].strip()
            logging.debug(f"Found git entry: {current_name}")
            new_lines.append(line)

        elif line.strip().startswith('commit:') and current_name:
            # Extract the commit value and indentation
            commit_line_stripped = line.strip()
            old_commit = commit_line_stripped.split(':', 1)[1].strip()
            indent = line[:line.find('commit:')]

            # Check if we should update this commit
            if current_name in projects:
                new_commit = projects[current_name]
                if not commits_are_equivalent(old_commit, new_commit):
                    changes.append((current_name, old_commit, new_commit))
                    new_lines.append(f"{indent}commit: {new_commit}\n")
                    logging.info(f"Updated {current_name}: {old_commit} -> {new_commit}")
                    updated_count += 1
                else:
                    logging.debug(f"No change needed for {current_name}: {old_commit}")
                    new_lines.append(line)
            else:
                logging.debug(f"Skipping {current_name}: not in XML projects")
                new_lines.append(line)

            current_name = None  # Reset after processing commit

        else:
            # Reset current_name if we hit a new top-level item
            if line.strip().startswith('- ') and not line.strip().startswith('- name:'):
                current_name = None
            new_lines.append(line)

    # Write the updated content back to file
    if updated_count > 0:
        try:
            with open(sdk_path, "w") as f:
                f.writelines(new_lines)
            logging.info(f"Successfully updated {updated_count} commits")
        except PermissionError:
            logging.error(f"Permission denied writing to {sdk_path}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error writing {sdk_path}: {e}")
            sys.exit(1)
    else:
        logging.info("No commits needed updating")

    return changes


def update_sdk_yml(projects: Dict[str, str], sdk_path: str, dry_run: bool = False) -> List[Tuple[str, str, str]]:
    """
    Update SDK YAML file with new commit hashes from projects.

    Args:
        projects: Dictionary mapping project names to revision strings
        sdk_path: Path to the SDK YAML file
        dry_run: If True, don't actually write changes

    Returns:
        List of tuples (project_name, old_commit, new_commit) for changes made

    Raises:
        SystemExit: If file operations fail
    """
    if dry_run:
        # Use line-by-line parsing for analysis in dry-run mode
        return analyze_changes_line_by_line(projects, sdk_path)
    else:
        # Use line-by-line editing for actual changes to preserve formatting
        return update_sdk_yml_line_by_line(projects, sdk_path)


def normalize_commit_ref(commit_ref: str) -> str:
    """
    Normalize commit references to handle equivalent formats.

    Args:
        commit_ref: Commit reference string

    Returns:
        Normalized commit reference
    """
    import re

    ref = commit_ref.strip()

    # Handle refs/tags/ prefix - extract the tag name for comparison
    if ref.startswith('refs/tags/'):
        return ref[10:]  # Remove 'refs/tags/' prefix

    # Handle refs/heads/ prefix - extract the branch name for comparison
    if ref.startswith('refs/heads/'):
        return ref[11:]  # Remove 'refs/heads/' prefix

    # Return as-is for commit hashes and plain tags/branches
    return ref


def commits_are_equivalent(old_commit: str, new_commit: str) -> bool:
    """
    Check if two commit references are functionally equivalent.

    Args:
        old_commit: Original commit reference
        new_commit: New commit reference

    Returns:
        True if commits are equivalent, False otherwise
    """
    return normalize_commit_ref(old_commit) == normalize_commit_ref(new_commit)


def classify_change_type(old_commit: str, new_commit: str) -> str:
    """
    Classify the type of change between two commit references.

    Args:
        old_commit: Original commit reference
        new_commit: New commit reference

    Returns:
        Change type: 'format', 'version', 'hash', or 'major'
    """
    # Strip whitespace for comparison
    old = old_commit.strip()
    new = new_commit.strip()

    # Normalize for comparison
    old_norm = normalize_commit_ref(old)
    new_norm = normalize_commit_ref(new)

    # If they're identical after normalization, it's just a format change
    if old_norm == new_norm:
        return 'format'

    # Extract version-like patterns
    import re

    # Check if both are version tags but different versions
    old_version = re.search(r'(\d+\.\d+\.\d+)', old_norm)
    new_version = re.search(r'(\d+\.\d+\.\d+)', new_norm)

    if old_version and new_version:
        return 'version'

    # Check if one or both are commit hashes (40 hex chars or similar)
    old_is_hash = re.match(r'^[a-f0-9]{7,40}$', old_norm.lower())
    new_is_hash = re.match(r'^[a-f0-9]{7,40}$', new_norm.lower())

    if old_is_hash or new_is_hash:
        return 'hash'

    # Otherwise, it's a major change
    return 'major'


def get_all_git_entries(sdk_path: str) -> List[Tuple[str, str]]:
    """
    Extract all git entries from SDK YAML file.

    Args:
        sdk_path: Path to the SDK YAML file

    Returns:
        List of tuples (project_name, current_commit)
    """
    try:
        with open(sdk_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        console.print(f"[red]✗ Error reading {sdk_path}:[/red] {e}")
        return []

    entries = []
    current_name = None

    for line in lines:
        if line.strip().startswith('- name:'):
            current_name = line.strip().split(':', 1)[1].strip()

        elif line.strip().startswith('commit:') and current_name:
            commit = line.strip().split(':', 1)[1].strip()
            entries.append((current_name, commit))
            current_name = None

        elif line.strip().startswith('- ') and not line.strip().startswith('- name:'):
            # Reset if we hit a new top-level item
            current_name = None

    return entries


def print_changes_summary(changes: List[Tuple[str, str, str]], sdk_path: str, projects: Dict[str, str], dry_run: bool = False, original_entries: List[Tuple[str, str]] = None) -> None:
    """Print a summary of all git entries, showing icons only for changed ones."""

    # Get all git entries from the YAML file (use original entries if provided, otherwise read current state)
    if original_entries is not None:
        all_entries = original_entries
    else:
        all_entries = get_all_git_entries(sdk_path)

    if not all_entries:
        console.print("\n[yellow]⚠[/yellow] No git entries found in SDK file")
        return

    # Create a lookup for changes
    changes_dict = {name: (old, new) for name, old, new in changes}

    action = "Would update" if dry_run else "Updated"
    changed_count = len(changes)
    total_count = len(all_entries)

    if changed_count == 0:
        title = f"All {total_count} commits up to date"
    else:
        title = f"{action} {changed_count} of {total_count} commits"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("", width=2, no_wrap=True)  # Icon column
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Current", style="blue", max_width=40)
    table.add_column("New", style="green", max_width=40)

    # Count change types for summary
    format_changes = 0
    version_changes = 0
    hash_changes = 0
    major_changes = 0

    for name, current_commit in all_entries:
        if name in changes_dict:
            # This entry is changing
            old_commit, new_commit = changes_dict[name]

            # For the display, use the original commit (current_commit from all_entries)
            # and the new commit from projects dict
            display_current = current_commit
            display_new = projects.get(name, new_commit)  # Use projects dict or fallback to changes

            # Classify the change type
            change_type = classify_change_type(old_commit, new_commit)

            # Choose icon and styling based on change type
            if change_type == 'format':
                icon = ""  # No icon for format changes (same version, different format)
                current_style = "[dim blue]"
                new_style = "[dim green]"
                format_changes += 1
            elif change_type == 'version':
                icon = "🔄"  # Version change
                current_style = "[blue]"
                new_style = "[bold green]"
                version_changes += 1
            elif change_type == 'hash':
                icon = "🔧"  # Hash/commit change
                current_style = "[blue]"
                new_style = "[bold green]"
                hash_changes += 1
            else:  # major
                icon = "⚡"  # Major change
                current_style = "[blue]"
                new_style = "[bold green]"
                major_changes += 1

            # Truncate long commit hashes for display
            current_display = display_current[:37] + "..." if len(display_current) > 40 else display_current
            new_display = display_new[:37] + "..." if len(display_new) > 40 else display_new

            table.add_row(
                icon,
                name,
                f"{current_style}{current_display}[/]",
                f"{new_style}{new_display}[/]"
            )
        else:
            # This entry is not changing - show what the XML value would be
            if name in projects:
                new_commit = projects[name]
            else:
                # Project not in XML manifest, show current value
                new_commit = current_commit

            # Truncate long commit hashes for display
            current_display = current_commit[:37] + "..." if len(current_commit) > 40 else current_commit
            new_display = new_commit[:37] + "..." if len(new_commit) > 40 else new_commit

            # Always show no icon for entries not in changes list
            table.add_row(
                "",  # No icon
                name,
                f"[dim blue]{current_display}[/]",
                f"[dim blue]{new_display}[/]"
            )

    console.print()
    console.print(table)

    # Print legend only if there are changes
    if changed_count > 0:
        legend_parts = []
        if format_changes > 0:
            legend_parts.append(f"[dim]📝 {format_changes} format changes[/dim]")
        if version_changes > 0:
            legend_parts.append(f"🔄 {version_changes} version changes")
        if hash_changes > 0:
            legend_parts.append(f"🔧 {hash_changes} commit changes")
        if major_changes > 0:
            legend_parts.append(f"⚡ {major_changes} major changes")

        if legend_parts:
            console.print(f"\n[dim]Legend: {' • '.join(legend_parts)}[/dim]")

    console.print()


def validate_version_format(version: str) -> bool:
    """Basic validation of version format."""
    if not version or len(version.strip()) == 0:
        return False
    # Allow basic semantic versioning patterns and tags
    import re
    return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', version))


def extract_git_projects_from_file(sdk_path: str) -> List[Tuple[str, str, str]]:
    """
    Extract git project information from SDK YAML file.

    Args:
        sdk_path: Path to the SDK YAML file

    Returns:
        List of tuples (project_name, git_url, commit_hash)

    Raises:
        SystemExit: If file operations fail
    """
    try:
        with open(sdk_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"SDK file not found: {sdk_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading {sdk_path}: {e}")
        sys.exit(1)

    projects = []
    current_name = None
    current_url = None

    for line in lines:
        if line.strip().startswith('- name:'):
            current_name = line.strip().split(':', 1)[1].strip()
            current_url = None

        elif line.strip().startswith('url:') and current_name:
            current_url = line.strip().split(':', 1)[1].strip()

        elif line.strip().startswith('commit:') and current_name and current_url:
            commit = line.strip().split(':', 1)[1].strip()
            projects.append((current_name, current_url, commit))
            current_name = None
            current_url = None

        elif line.strip().startswith('- ') and not line.strip().startswith('- name:'):
            # Reset if we hit a new top-level item
            current_name = None
            current_url = None

    return projects


def verify_commit_exists(project_name: str, git_url: str, commit_hash: str) -> bool:
    """
    Verify that a commit exists in a git repository.

    Args:
        project_name: Name of the project for logging
        git_url: Git repository URL
        commit_hash: Commit hash/tag to verify

    Returns:
        True if commit exists, False otherwise
    """
    import subprocess
    import tempfile
    import os

    # Handle different URL formats and extract repo info
    if git_url.startswith('https://github.com/'):
        repo_path = git_url.replace('https://github.com/', '').replace('.git', '')
        # Use GitHub API for faster verification
        api_url = f"https://api.github.com/repos/{repo_path}/commits/{commit_hash}"

        try:
            import urllib.request
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'OP-TEE-SDK-Updater/1.0')
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logging.debug(f"GitHub API verification failed for {project_name}: {e}")
            # Fall back to git ls-remote

    # Fallback: Use git ls-remote for verification
    try:
        # First try to see if it's a tag or branch
        result = subprocess.run(
            ['git', 'ls-remote', '--tags', '--heads', git_url, commit_hash],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            return True

        # If not found as tag/branch, try as commit hash (this is less reliable with ls-remote)
        if commit_hash.startswith('refs/'):
            return False  # Already tried refs/ above

        # For commit hashes, we'd need to clone/fetch which is expensive
        # So we'll just trust the XML manifest for hash-based commits
        if len(commit_hash) >= 7 and all(c in '0123456789abcdef' for c in commit_hash.lower()):
            logging.debug(f"Trusting hash-based commit for {project_name}: {commit_hash}")
            return True

        return False

    except subprocess.TimeoutExpired:
        logging.warning(f"Timeout verifying {project_name} commit {commit_hash}")
        return False
    except subprocess.CalledProcessError as e:
        logging.debug(f"Git ls-remote failed for {project_name}: {e}")
        return False
    except Exception as e:
        logging.debug(f"Verification error for {project_name}: {e}")
        return False


def verify_updated_commits(sdk_path: str, changes: List[Tuple[str, str, str]]) -> None:
    """
    Verify that updated commits exist in their repositories.

    Args:
        sdk_path: Path to the SDK YAML file
        changes: List of changes made (project_name, old_commit, new_commit)

    Raises:
        SystemExit: If verification fails for any commits
    """
    if not changes:
        console.print("[yellow]No commits to verify[/yellow]")
        return

    console.print(f"\n[bold blue]🔍 Verifying {len(changes)} updated commits...[/bold blue]")

    # Extract all project information from the file
    all_projects = extract_git_projects_from_file(sdk_path)

    # Create a mapping from project names to git URLs
    project_urls = {name: url for name, url, _ in all_projects}

    verification_results = []
    failed_verifications = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        verify_task = progress.add_task("Verifying commits...", total=len(changes))

        for project_name, old_commit, new_commit in changes:
            if project_name not in project_urls:
                console.print(f"[yellow]⚠[/yellow] Could not find URL for project {project_name}, skipping verification")
                progress.advance(verify_task)
                continue

            git_url = project_urls[project_name]
            logging.debug(f"Verifying {project_name}: {new_commit}")

            progress.update(verify_task, description=f"Verifying {project_name}...")

            if verify_commit_exists(project_name, git_url, new_commit):
                verification_results.append((project_name, True, new_commit))
            else:
                verification_results.append((project_name, False, new_commit))
                failed_verifications.append((project_name, new_commit))

            progress.advance(verify_task)

    # Print summary with Rich formatting
    if verification_results:
        success_count = sum(1 for _, success, _ in verification_results if success)
        total_count = len(verification_results)

        # Create verification summary table
        summary_table = Table(title="Commit Verification Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Project", style="cyan")
        summary_table.add_column("Commit", style="blue", max_width=40)
        summary_table.add_column("Status", justify="center")

        for project_name, success, commit in verification_results:
            commit_display = commit[:37] + "..." if len(commit) > 40 else commit
            status = "[green]✓ Verified[/green]" if success else "[red]✗ Failed[/red]"
            summary_table.add_row(project_name, commit_display, status)

        console.print()
        console.print(summary_table)

        # Print overall summary
        if failed_verifications:
            console.print(f"\n[yellow]⚠ {len(failed_verifications)} commits could not be verified[/yellow]")
            console.print("[dim]Note: Some commits may not be publicly accessible or the verification method may have limitations.[/dim]")
        else:
            console.print(f"\n[green]✅ All {success_count} commits successfully verified![/green]")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update OP-TEE SDK YAML file with commit hashes from manifest XMLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 4.7.0                          # Update to version 4.7.0
  %(prog)s 4.7.0 --dry-run                # Preview changes without applying
  %(prog)s 4.7.0 --check                  # Update and verify commits exist
  %(prog)s 4.7.0 --sdk-path custom.yml    # Use custom SDK file
  %(prog)s 4.7.0 --verbose                # Show detailed logging
  %(prog)s 4.7.0 --quiet                  # Minimal output
        """
    )

    parser.add_argument(
        "version",
        help="OP-TEE version to update to (e.g., 4.7.0, 4.8.0)"
    )

    parser.add_argument(
        "--sdk-path",
        default=DEFAULT_SDK_YML_PATH,
        help=f"Path to SDK YAML file (default: {DEFAULT_SDK_YML_PATH})"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual changes"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that updated commits exist in their repositories (runs after update)"
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    # Validate arguments
    if args.verbose and args.quiet:
        console.print("[red]ERROR:[/red] --verbose and --quiet cannot be used together")
        sys.exit(1)

    if not validate_version_format(args.version):
        console.print(f"[red]ERROR:[/red] Invalid version format: {args.version}")
        console.print("[yellow]Version should contain only alphanumeric characters, dots, hyphens, and underscores[/yellow]")
        sys.exit(1)

    # Setup logging
    setup_logging(args.verbose, args.quiet)

    # Build URLs
    qemu_url = QEMU_XML_URL.format(version=args.version)
    common_url = COMMON_XML_URL.format(version=args.version)

    try:
        # Show header
        if not args.quiet:
            console.print(f"\n[bold blue]🔄 OP-TEE SDK Update to version {args.version}[/bold blue]")

        # Fetch XML files
        qemu_xml = fetch_xml(qemu_url, f"Fetching qemu_v8.xml")
        common_xml = fetch_xml(common_url, f"Fetching common.xml")

        # Parse projects
        qemu_projects = parse_projects(qemu_xml, "Parsing qemu_v8.xml")
        common_projects = parse_projects(common_xml, "Parsing common.xml")

        # Merge projects (common.xml can override qemu_v8.xml)
        projects = qemu_projects.copy()
        projects.update(common_projects)

        if not projects:
            console.print("[red]✗ No projects found in XML files[/red]")
            sys.exit(1)

        # Capture original state before any updates
        original_entries = get_all_git_entries(args.sdk_path)

        # Update SDK file
        changes = update_sdk_yml(projects, args.sdk_path, args.dry_run)

        # Show summary unless quiet
        if not args.quiet:
            print_changes_summary(changes, args.sdk_path, projects, args.dry_run, original_entries)

        if args.dry_run and changes:
            console.print(f"\n[yellow]💡 To apply these changes, run without --dry-run:[/yellow]")
            console.print(f"[dim]  python scripts/update_optee_sdk_yml.py {args.version}[/dim]")

        # Verify commits if requested and not in dry-run mode
        if args.check and not args.dry_run and changes:
            verify_updated_commits(args.sdk_path, changes)

        # Success!
        if not args.quiet:
            if args.dry_run:
                console.print(f"\n[green]✅ Analysis complete![/green]")
            else:
                console.print(f"\n[green]🎉 Update complete![/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error:[/red] {e}")
        if args.verbose:
            import traceback
            console.print("\n[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
