"""
Validation service — builds the validation report for the /admin/validation-report endpoint.

Rules implemented:
  A. Show-level
     A1. MISSING_SECTION          — published show has no section (blocking)
                                    draft show has no section (warning only)
     A2. INVALID_SECTION          — section value not in reference.json (blocking)
     A3. NO_PUBLISHED_EPISODES    — published show has zero published episodes (warning)

  B. Episode-level (published episodes only for B1/B2)
     B1. MISSING_ARTWORK          — published episode has no artwork (blocking)
     B2. MISSING_DURATION         — published episode has no duration (blocking)
     B3. DUPLICATE_CONTENT_GROUP_LANG  — same (content_group, language) pair on ≥2 rows (blocking)

  C. Cross-variant content_group consistency (blocking regardless of status)
     C1. CONTENT_GROUP_IDENTITY_CONFLICT — episodes sharing a content_group disagree on
         episode_number, show_id, or season_id across language variants.
         Issues are collected in a pre-pass keyed by episode.id to avoid duplicate
         EpisodeValidationEntry objects.

  D. Title quality warnings
     D1. TITLE_ALL_CAPS           — warning
     D2. TITLE_ALL_LOWERCASE      — warning

Design notes:
  - Does NOT modify data; read-only queries only.
  - All issues carry entity/entity_id/field for frontend deep-linking.
  - MISSING_SECTION is blocking only for published shows; drafts get a warning.
    This matches the spec: "Draft content may have a missing section, but that
    should only block publication if the affected show/record is actually required
    to be published."
  - C1 uses a pre-pass to emit one ValidationIssue per affected episode, collected
    in a dict keyed by episode.id. This ensures each episode has exactly one
    EpisodeValidationEntry even if it participates in multiple checks.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artwork, Episode, Season, Show
from app.reference import SECTIONS
from app.schemas.operations import (
    EpisodeValidationEntry,
    ShowValidationEntry,
    ValidationIssue,
    ValidationReport,
)


async def build_validation_report(db: AsyncSession) -> ValidationReport:
    """Build the full validation report from the current DB state."""
    now = datetime.now(timezone.utc)

    # ── Load all data ─────────────────────────────────────────────────────────
    all_shows: list[Show] = list(
        (await db.execute(select(Show))).scalars().all()
    )
    all_episodes: list[Episode] = list(
        (await db.execute(select(Episode))).scalars().all()
    )
    all_artworks: list[Artwork] = list(
        (await db.execute(select(Artwork))).scalars().all()
    )
    all_seasons: list[Season] = list(
        (await db.execute(select(Season))).scalars().all()
    )

    # ── Build lookup maps ─────────────────────────────────────────────────────
    show_by_id: dict[uuid.UUID, Show] = {s.id: s for s in all_shows}
    season_by_id: dict[uuid.UUID, Season] = {s.id: s for s in all_seasons}

    episodes_by_show: dict[uuid.UUID, list[Episode]] = defaultdict(list)
    for ep in all_episodes:
        episodes_by_show[ep.show_id].append(ep)

    # Artwork lookup: (owner_type, owner_id) → set of artwork kinds
    artwork_kinds: dict[tuple, set[str]] = defaultdict(set)
    for art in all_artworks:
        artwork_kinds[(art.owner_type, art.owner_id)].add(art.kind)

    # (content_group, language) → [Episode]  — for duplicate detection
    cg_lang_map: dict[tuple[str, str], list[Episode]] = defaultdict(list)
    for ep in all_episodes:
        cg_lang_map[(ep.content_group, ep.language)].append(ep)

    # content_group → [Episode]  — for cross-variant identity check
    cg_all_variants: dict[str, list[Episode]] = defaultdict(list)
    for ep in all_episodes:
        cg_all_variants[ep.content_group].append(ep)

    # summary counter
    summary: dict[str, int] = {"blocking": 0, "warning": 0, "info": 0}

    def _add_issue(issue: ValidationIssue) -> None:
        summary[issue.severity] += 1

    show_issues: list[ShowValidationEntry] = []
    episode_issues: list[EpisodeValidationEntry] = []

    # ── A. Show-level checks ──────────────────────────────────────────────────
    for show in sorted(all_shows, key=lambda s: s.slug):
        s_issues: list[ValidationIssue] = []
        show_entity_id = str(show.id)

        if show.section is None:
            # A1. MISSING_SECTION — severity depends on publication status
            severity = "blocking" if show.status == "published" else "warning"
            issue = ValidationIssue(
                entity="show",
                entity_id=show_entity_id,
                field="section",
                code="MISSING_SECTION",
                severity=severity,
                message=(
                    f"'{show.title}' has no section assigned. "
                    "Please pick a section (featured / series / minisodes / songs) "
                    "before publishing."
                ),
            )
            _add_issue(issue)
            s_issues.append(issue)

        elif show.section not in SECTIONS:
            # A2. INVALID_SECTION
            issue = ValidationIssue(
                entity="show",
                entity_id=show_entity_id,
                field="section",
                code="INVALID_SECTION",
                severity="blocking",
                message=(
                    f"'{show.title}' has an unrecognised section '{show.section}'. "
                    f"Allowed values are: {', '.join(sorted(SECTIONS))}."
                ),
            )
            _add_issue(issue)
            s_issues.append(issue)

        # A3. NO_PUBLISHED_EPISODES
        published_eps = [
            e for e in episodes_by_show.get(show.id, []) if e.status == "published"
        ]
        if show.status == "published" and not published_eps:
            issue = ValidationIssue(
                entity="show",
                entity_id=show_entity_id,
                field="episodes",
                code="NO_PUBLISHED_EPISODES",
                severity="warning",
                message=(
                    f"'{show.title}' is marked published but has no published episodes. "
                    "It will appear in the catalogue with an empty episode list."
                ),
            )
            _add_issue(issue)
            s_issues.append(issue)

        if s_issues:
            show_issues.append(ShowValidationEntry(
                show_id=show.id,
                show_title=show.title,
                slug=show.slug,
                issues=s_issues,
            ))

    # ── C1. Pre-pass: detect CONTENT_GROUP_IDENTITY_CONFLICT ─────────────────
    # Collect issues per episode.id so they can be merged cleanly in the main loop.
    c1_issues_by_ep: dict[uuid.UUID, list[ValidationIssue]] = {}

    for cg, variants in cg_all_variants.items():
        if len(variants) <= 1:
            continue

        # Use the episode with the smallest UUID string as the stable reference
        ref = min(variants, key=lambda e: str(e.id))
        conflicts: list[str] = []

        for other in variants:
            if other.id == ref.id:
                continue
            if other.episode_number != ref.episode_number:
                conflicts.append(
                    f"episode_number mismatch: "
                    f"'{other.external_id or other.id}' has ep#{other.episode_number} "
                    f"vs '{ref.external_id or ref.id}' has ep#{ref.episode_number}"
                )
            if other.show_id != ref.show_id:
                conflicts.append(
                    f"show_id mismatch: "
                    f"'{other.external_id or other.id}' belongs to a different show"
                )
            if other.season_id != ref.season_id:
                conflicts.append(
                    f"season_id mismatch: "
                    f"'{other.external_id or other.id}' is in a different season"
                )

        if conflicts:
            conflict_message = (
                f"Episodes sharing content_group='{cg}' "
                "disagree on core identity fields. "
                f"Conflicts: {'; '.join(conflicts)}. "
                "All language variants must have the same episode_number, show, and season."
            )
            for variant in variants:
                var_entity_id = variant.external_id or str(variant.id)
                issue = ValidationIssue(
                    entity="episode",
                    entity_id=var_entity_id,
                    field="content_group",
                    code="CONTENT_GROUP_IDENTITY_CONFLICT",
                    severity="blocking",
                    message=conflict_message,
                )
                _add_issue(issue)
                c1_issues_by_ep.setdefault(variant.id, []).append(issue)

    # ── B + D. Main episode loop ───────────────────────────────────────────────
    for ep in sorted(all_episodes, key=lambda e: (str(e.show_id), str(e.id))):
        e_issues: list[ValidationIssue] = []
        show = show_by_id.get(ep.show_id)
        season = season_by_id.get(ep.season_id)

        if show is None or season is None:
            continue  # orphan — should not happen with FK constraints

        ep_entity_id = ep.external_id or str(ep.id)

        # ── B1 + B2: Published episode checks ─────────────────────────────────
        if ep.status == "published":

            # B1. MISSING_ARTWORK
            ep_art_kinds = artwork_kinds.get(("episode", ep.id), set())
            if not ep_art_kinds:
                issue = ValidationIssue(
                    entity="episode",
                    entity_id=ep_entity_id,
                    field="artwork",
                    code="MISSING_ARTWORK",
                    severity="blocking",
                    message=(
                        f"Episode '{ep.title}' "
                        f"(S{season.season_number}E{ep.episode_number}, {ep.language}) "
                        "is published but has no artwork uploaded. "
                        "Please upload at least a thumbnail before publishing."
                    ),
                )
                _add_issue(issue)
                e_issues.append(issue)

            # B2. MISSING_DURATION
            if ep.duration_seconds is None:
                issue = ValidationIssue(
                    entity="episode",
                    entity_id=ep_entity_id,
                    field="duration_seconds",
                    code="MISSING_DURATION",
                    severity="blocking",
                    message=(
                        f"Episode '{ep.title}' "
                        f"(S{season.season_number}E{ep.episode_number}, {ep.language}) "
                        "has no duration set. "
                        "Please add a duration in seconds before publishing."
                    ),
                )
                _add_issue(issue)
                e_issues.append(issue)

        # ── B3. DUPLICATE_CONTENT_GROUP_LANG ─────────────────────────────────
        duplicates = cg_lang_map.get((ep.content_group, ep.language), [])
        if len(duplicates) > 1:
            dup_ids = [
                e.external_id or str(e.id)
                for e in duplicates
                if e.id != ep.id
            ]
            issue = ValidationIssue(
                entity="episode",
                entity_id=ep_entity_id,
                field="content_group",
                code="DUPLICATE_CONTENT_GROUP_LANG",
                severity="blocking",
                message=(
                    f"Episode '{ep_entity_id}' has the same "
                    f"content_group='{ep.content_group}' and language='{ep.language}' "
                    f"as: {', '.join(dup_ids)}. "
                    "Only one episode per (content_group, language) is allowed. "
                    "Delete or reassign one of the duplicates."
                ),
            )
            _add_issue(issue)
            e_issues.append(issue)

        # ── C1. Merge pre-computed identity conflict issues ────────────────────
        e_issues.extend(c1_issues_by_ep.get(ep.id, []))

        # ── D. Title quality warnings ─────────────────────────────────────────
        title = ep.title
        words = title.split()
        if len(words) > 1:
            if title == title.lower():
                issue = ValidationIssue(
                    entity="episode",
                    entity_id=ep_entity_id,
                    field="title",
                    code="TITLE_ALL_LOWERCASE",
                    severity="warning",
                    message=(
                        f"Episode title {title!r} appears to be all-lowercase. "
                        "Please check if this is intentional."
                    ),
                )
                _add_issue(issue)
                e_issues.append(issue)
            elif all(w.isupper() for w in words if w.isalpha()):
                issue = ValidationIssue(
                    entity="episode",
                    entity_id=ep_entity_id,
                    field="title",
                    code="TITLE_ALL_CAPS",
                    severity="warning",
                    message=(
                        f"Episode title {title!r} appears to be ALL-CAPS. "
                        "Please check if this is intentional."
                    ),
                )
                _add_issue(issue)
                e_issues.append(issue)

        if e_issues:
            episode_issues.append(EpisodeValidationEntry(
                show_id=show.id,
                show_title=show.title,
                slug=show.slug,
                episode_id=ep.id,
                episode_title=ep.title,
                season_number=season.season_number,
                episode_number=ep.episode_number,
                language=ep.language,
                content_group=ep.content_group,
                issues=e_issues,
            ))

    can_publish = summary["blocking"] == 0

    return ValidationReport(
        generated_at=now,
        can_publish=can_publish,
        show_issues=show_issues,
        episode_issues=episode_issues,
        summary=summary,
    )
