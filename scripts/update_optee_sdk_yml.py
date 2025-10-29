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

# Constants
DEFAULT_SDK_YML_PATH = os.path.join("targets", "optee-qemu-v8", "sdk.yml")
QEMU_XML_URL = "https://raw.githubusercontent.com/OP-TEE/manifest/refs/heads/{version}/qemu_v8.xml"
COMMON_XML_URL = "https://raw.githubusercontent.com/OP-TEE/manifest/refs/heads/{version}/common.xml"


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


def fetch_xml(url: str) -> bytes:
    """
    Fetch XML content from a URL with proper error handling.

    Args:
        url: The URL to fetch XML from

    Returns:
        XML content as bytes

    Raises:
        SystemExit: If fetch fails with appropriate error message
    """
    try:
        logging.info(f"Fetching: {url}")
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                logging.error(f"HTTP {response.status} when fetching {url}")
                sys.exit(1)
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.error(f"Version not found: {url}")
            logging.error("Please check that the version exists in the OP-TEE manifest repository")
        else:
            logging.error(f"HTTP error {e.code} when fetching {url}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        logging.error(f"Network error when fetching {url}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error fetching {url}: {e}")
        sys.exit(1)


def parse_projects(xml_content: bytes) -> Dict[str, str]:
    """
    Parse XML manifest and extract project path-to-revision mappings.

    Args:
        xml_content: Raw XML content as bytes

    Returns:
        Dictionary mapping project paths to revision strings

    Raises:
        SystemExit: If XML parsing fails
    """
    projects = {}
    try:
        root = ET.fromstring(xml_content)
        for proj in root.findall(".//project"):
            path = proj.get("path")
            revision = proj.get("revision")
            if path and revision:
                projects[path] = revision
                logging.debug(f"Found project: {path} -> {revision}")
        logging.info(f"Parsed {len(projects)} projects from XML")
    except ET.ParseError as e:
        logging.error(f"Invalid XML format: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error parsing XML: {e}")
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
    logging.info(f"{'Analyzing' if dry_run else 'Updating'} {sdk_path}...")

    # Load the YAML file
    sdk_data = load_yaml_file(sdk_path)

    if "gits" not in sdk_data:
        logging.error(f"No 'gits' section found in {sdk_path}")
        sys.exit(1)

    changes = []
    updated_count = 0

    # Update commits for matching projects
    for git_entry in sdk_data["gits"]:
        if not isinstance(git_entry, dict) or "name" not in git_entry:
            continue

        name = git_entry["name"]
        if name in projects and "commit" in git_entry:
            old_commit = git_entry["commit"]
            new_commit = projects[name]

            if old_commit != new_commit:
                changes.append((name, old_commit, new_commit))
                if not dry_run:
                    git_entry["commit"] = new_commit
                    logging.info(f"Updated {name}: {old_commit} -> {new_commit}")
                updated_count += 1
            else:
                logging.debug(f"No change needed for {name}: {old_commit}")
        else:
            logging.debug(f"Skipping {name}: not in XML projects or no commit field")

    if dry_run:
        return changes

    # Save the updated YAML
    if updated_count > 0:
        save_yaml_file(sdk_data, sdk_path)
        logging.info(f"Successfully updated {updated_count} commits")
    else:
        logging.info("No commits needed updating")

    return changes


def print_changes_summary(changes: List[Tuple[str, str, str]], dry_run: bool = False) -> None:
    """Print a summary of changes to be made or that were made."""
    if not changes:
        print("No changes needed - all commits are already up to date!")
        return

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {len(changes)} commits:")
    print("-" * 80)

    for name, old_commit, new_commit in changes:
        # Truncate long commit hashes for display
        old_display = old_commit[:40] + "..." if len(old_commit) > 43 else old_commit
        new_display = new_commit[:40] + "..." if len(new_commit) > 43 else new_commit
        print(f"  {name:20} {old_display:43} -> {new_display}")

    print("-" * 80)


def validate_version_format(version: str) -> bool:
    """Basic validation of version format."""
    if not version or len(version.strip()) == 0:
        return False
    # Allow basic semantic versioning patterns and tags
    import re
    return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', version))


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update OP-TEE SDK YAML file with commit hashes from manifest XMLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 4.7.0                          # Update to version 4.7.0
  %(prog)s 4.7.0 --dry-run                # Preview changes without applying
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

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    # Validate arguments
    if args.verbose and args.quiet:
        print("ERROR: --verbose and --quiet cannot be used together", file=sys.stderr)
        sys.exit(1)

    if not validate_version_format(args.version):
        print(f"ERROR: Invalid version format: {args.version}", file=sys.stderr)
        print("Version should contain only alphanumeric characters, dots, hyphens, and underscores", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    if args.quiet:
        setup_logging(False)
        logging.getLogger().setLevel(logging.ERROR)
    else:
        setup_logging(args.verbose)

    # Build URLs
    qemu_url = QEMU_XML_URL.format(version=args.version)
    common_url = COMMON_XML_URL.format(version=args.version)

    try:
        # Fetch XML files
        qemu_xml = fetch_xml(qemu_url)
        common_xml = fetch_xml(common_url)

        # Parse projects
        logging.info("Parsing XML files...")
        projects = parse_projects(qemu_xml)
        projects.update(parse_projects(common_xml))  # common.xml can override qemu_v8.xml

        if not projects:
            logging.error("No projects found in XML files")
            sys.exit(1)

        # Update SDK file
        changes = update_sdk_yml(projects, args.sdk_path, args.dry_run)

        # Show summary unless quiet
        if not args.quiet:
            print_changes_summary(changes, args.dry_run)

        if args.dry_run and changes:
            print(f"\nTo apply these changes, run without --dry-run:")
            print(f"  python scripts/update_optee_sdk_yml.py {args.version}")

        # Success!
        if not args.quiet:
            action = "Analysis complete" if args.dry_run else "Update complete"
            print(f"\n{action}!")

    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
