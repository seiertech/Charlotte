"""Prerequisite validation and config parsing for Charlotte editorial rewrite pipeline.

Validates that all required foundation documents, directives, and configuration
are in place before the pipeline begins processing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml


class PipelineError(Exception):
    """Raised when the editorial rewrite pipeline cannot proceed due to a prerequisite or config issue."""
    pass


# The 7 required sections in EDITORIAL_DIRECTIVES_D4.md
REQUIRED_ED4_SECTIONS = [
    "Character Consolidation Rules",
    "Repetition-Reduction Targets",
    "Production-Artifact Definitions",
    "Author-Presence Insertion Points",
    "Sourcing Requirements",
    "Layer-Boundary Clarifications",
    "Taxonomy-Reframing Guidance",
]

# Heading patterns: "## 1.", "## 2.", ..., "## 7." or the named section titles
ED4_SECTION_PATTERNS = [
    re.compile(rf"^##\s+{i}\.\s", re.MULTILINE) for i in range(1, 8)
]

# Per-chapter word count target table indicator
WORD_COUNT_TABLE_PATTERN = re.compile(
    r"Word Count Target", re.IGNORECASE
)


def validate_prerequisites(config: dict, project_root: str = ".") -> None:
    """Validate that all required foundation documents and directives exist.

    Raises PipelineError with clear message if:
      - foundation/EDITORIAL_DIRECTIVES_D4.md doesn't exist
      - ED4 file is missing any of the 7 required sections
      - Per-chapter word count target table not found in ED4
      - foundation/model_bible.md doesn't exist
      - foundation/character_bible.md doesn't exist
      - No Draft 3 chapters found in output/draft3/ or output/final_chapters/
    """
    root = Path(project_root)

    # Check EDITORIAL_DIRECTIVES_D4.md exists
    ed4_path = root / "foundation" / "EDITORIAL_DIRECTIVES_D4.md"
    if not ed4_path.exists():
        raise PipelineError(
            f"Required directives file missing: {ed4_path}. "
            f"Create foundation/EDITORIAL_DIRECTIVES_D4.md with all 7 required sections "
            f"before running the editorial rewrite pipeline."
        )

    # Read and validate ED4 sections
    try:
        ed4_content = ed4_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PipelineError(f"Cannot read directives file at {ed4_path}: {exc}") from exc

    missing_sections: List[str] = []
    for i, pattern in enumerate(ED4_SECTION_PATTERNS):
        if not pattern.search(ed4_content):
            # Also check for section name without number prefix
            name = REQUIRED_ED4_SECTIONS[i]
            if name.lower() not in ed4_content.lower():
                missing_sections.append(f"Section {i + 1}: {name}")

    if missing_sections:
        raise PipelineError(
            f"EDITORIAL_DIRECTIVES_D4.md is missing required sections: "
            f"{', '.join(missing_sections)}. "
            f"All 7 sections are required: {', '.join(REQUIRED_ED4_SECTIONS)}."
        )

    # Check per-chapter word count target table
    if not WORD_COUNT_TABLE_PATTERN.search(ed4_content):
        raise PipelineError(
            f"EDITORIAL_DIRECTIVES_D4.md is missing the per-chapter word count target table. "
            f"Add a section with per-chapter D3 word count, D4 target min, and D4 target max "
            f"for each chapter."
        )

    # Check model_bible.md exists
    model_bible_path = root / "foundation" / "model_bible.md"
    if not model_bible_path.exists():
        raise PipelineError(
            f"Required foundation document missing: {model_bible_path}. "
            f"The Model Bible must be created before chapter rewriting can begin."
        )

    # Check character_bible.md exists
    character_bible_path = root / "foundation" / "character_bible.md"
    if not character_bible_path.exists():
        raise PipelineError(
            f"Required foundation document missing: {character_bible_path}. "
            f"The Character Bible must be created before chapter rewriting can begin."
        )

    # Check Draft 3 chapters exist
    draft3_dir = root / "output" / "draft3"
    final_chapters_dir = root / "output" / "final_chapters"

    draft3_chapters = list(draft3_dir.glob("ch*.md")) if draft3_dir.exists() else []
    final_chapters = list(final_chapters_dir.glob("ch*.md")) if final_chapters_dir.exists() else []

    if not draft3_chapters and not final_chapters:
        raise PipelineError(
            f"No Draft 3 chapters found in output/draft3/ or output/final_chapters/. "
            f"Run the first-draft pipeline to produce Draft 3 before starting the editorial rewrite."
        )


# --- Config loading and validation ------------------------------------------

# Required top-level keys in editorial_rewrite section
REQUIRED_CONFIG_KEYS = [
    "max_revisions",
    "word_reduction_target_min",
    "word_reduction_target_max",
    "run_artifact_scrubber",
    "run_continuity_auditor",
    "run_editorial_gate",
    "resume",
]

# Required agent keys in editorial_rewrite.agents mapping
REQUIRED_AGENT_KEYS = [
    "rewrite_agent",
    "artifact_scrubber",
    "continuity_auditor",
    "evidence_agent",
]


def load_rewrite_config(config_path: str = "config.yaml") -> dict:
    """Parse and validate the editorial_rewrite section from config.yaml.

    Returns the editorial_rewrite config dict if valid.

    Raises PipelineError with clear message naming the missing/invalid key if:
      - config.yaml doesn't exist or can't be parsed
      - 'editorial_rewrite' section is missing
      - Any required key is missing
      - editorial_rewrite.agents mapping is missing required agent keys
      - Numeric ranges are invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise PipelineError(
            f"Configuration file not found: {config_path}. "
            f"Ensure config.yaml exists in the project root."
        )

    try:
        raw = config_file.read_text(encoding="utf-8")
        full_config = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise PipelineError(
            f"Cannot parse configuration file {config_path}: {exc}"
        ) from exc

    if not isinstance(full_config, dict):
        raise PipelineError(
            f"Configuration file {config_path} does not contain a valid YAML mapping."
        )

    # Check editorial_rewrite section exists
    if "editorial_rewrite" not in full_config:
        raise PipelineError(
            "Missing 'editorial_rewrite' section in config.yaml. "
            "Add an 'editorial_rewrite' section with the required keys: "
            f"{', '.join(REQUIRED_CONFIG_KEYS)}."
        )

    er_config = full_config["editorial_rewrite"]
    if not isinstance(er_config, dict):
        raise PipelineError(
            "The 'editorial_rewrite' section in config.yaml must be a mapping."
        )

    # Check required keys
    for key in REQUIRED_CONFIG_KEYS:
        if key not in er_config:
            raise PipelineError(
                f"Missing required key 'editorial_rewrite.{key}' in config.yaml."
            )

    # Check agents mapping
    if "agents" not in er_config:
        raise PipelineError(
            "Missing required key 'editorial_rewrite.agents' in config.yaml. "
            f"Must contain agent mappings for: {', '.join(REQUIRED_AGENT_KEYS)}."
        )

    agents = er_config["agents"]
    if not isinstance(agents, dict):
        raise PipelineError(
            "The 'editorial_rewrite.agents' section must be a mapping."
        )

    for agent_key in REQUIRED_AGENT_KEYS:
        if agent_key not in agents:
            raise PipelineError(
                f"Missing required agent 'editorial_rewrite.agents.{agent_key}' in config.yaml."
            )

    # Validate ranges
    max_revisions = er_config["max_revisions"]
    if not isinstance(max_revisions, int) or max_revisions < 1 or max_revisions > 10:
        raise PipelineError(
            f"Invalid value for 'editorial_rewrite.max_revisions': {max_revisions}. "
            f"Must be an integer between 1 and 10."
        )

    target_min = er_config["word_reduction_target_min"]
    if not isinstance(target_min, (int, float)) or target_min < 0.0 or target_min > 1.0:
        raise PipelineError(
            f"Invalid value for 'editorial_rewrite.word_reduction_target_min': {target_min}. "
            f"Must be a float between 0.0 and 1.0."
        )

    target_max = er_config["word_reduction_target_max"]
    if not isinstance(target_max, (int, float)) or target_max < 0.0 or target_max > 1.0:
        raise PipelineError(
            f"Invalid value for 'editorial_rewrite.word_reduction_target_max': {target_max}. "
            f"Must be a float between 0.0 and 1.0."
        )

    if target_max <= target_min:
        raise PipelineError(
            f"Invalid range: 'editorial_rewrite.word_reduction_target_max' ({target_max}) "
            f"must be greater than 'editorial_rewrite.word_reduction_target_min' ({target_min})."
        )

    return er_config
